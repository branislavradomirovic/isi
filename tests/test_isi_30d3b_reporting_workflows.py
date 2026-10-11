from copy import deepcopy
from pathlib import Path
from uuid import UUID
import httpx
import pytest
from pydantic import ValidationError
from streamlit.testing.v1 import AppTest
from test_isi_29b_spatial_api import api as scoped_api, params
from test_isi_29f_linked_reports import accepted
from src.platform.data.storage import LocalFilesystemStorage
from src.platform.reporting.schemas import ReportLifecycleRequest
from src.streamlit_app import reporting_api as api_client
from src.streamlit_app.api_client import AccessDenied

api = scoped_api
IDS = [str(UUID(int=i)) for i in range(1, 8)]
SCOPE = dict(organization_id=IDS[0], workspace_id=IDS[1], product_code="SIMPA")
PERMISSIONS = ["report.read", "data.read", "analysis.run", "organization.manage"]


def native_version(api, tmp_path, monkeypatch, product, action):
    client, context, factory = api
    storage = LocalFilesystemStorage(tmp_path)
    monkeypatch.setattr("src.platform.extraction.service.build_storage", lambda: storage)
    with factory() as db:
        row, _, _, _ = accepted(dict(context, db=db, storage=storage), product)
        identity = str(row.id)
    scope = dict(params(context, product), product_code=product)
    generated = client.post(
        "/api/v1/reporting/reports",
        json=dict(
            scope,
            title="Synthetic report",
            report_type="linked_evidence",
            source_kind="extraction_request",
            source_id=identity,
            evidence_link=dict(claim_id="c1", note="Synthetic association", attested=True),
        ),
    )
    assert generated.status_code == 201, generated.text
    version = generated.json()["version"]
    path = "/api/v1/reporting/versions/" + version["id"]
    if action in {"review", "publish"}:
        response = client.post(path + "/submit", json=scope)
        assert response.status_code == 200
        version = response.json()
    if action == "publish":
        response = client.post(path + "/review", json=dict(scope, decision="approved", note="Synthetic approval"))
        assert response.status_code == 200
        version = response.json()["version"]
    payload = dict(
        scope,
        **{"reviewed_" + field: version[field] for field in ("status", "content_sha256", "source_manifest_sha256")},
    )
    if action == "review":
        payload.update(decision="approved", note="Synthetic review")
    return client, factory, path, version, payload


@pytest.mark.parametrize("product", ["SIMPA", "ORDO"])
@pytest.mark.parametrize("action", ["submit", "review", "publish"])
@pytest.mark.parametrize("field", ["status", "content_sha256", "source_manifest_sha256"])
def test_native_reviewed_evidence_drift_rejected_without_persistence(
    api, tmp_path, monkeypatch, product, action, field
):
    client, factory, path, version, payload = native_version(api, tmp_path, monkeypatch, product, action)
    payload["reviewed_" + field] = "rejected" if field == "status" else "f" * 64
    response = client.post(path + "/" + action, json=payload)
    assert response.status_code == 409 and response.json()["detail"] == "report_reviewed_evidence_changed"
    from src.platform.reporting.models import ReportVersion
    from src.platform.reporting.service import list_reviews

    with factory() as db:
        saved = db.get(ReportVersion, UUID(version["id"]))
        assert saved.status == version["status"] and saved.content_sha256 == version["content_sha256"]
        assert len(list_reviews(db, saved.id)) == (1 if action == "publish" else 0)
        assert saved.published_at is None


@pytest.mark.parametrize("product", ["SIMPA", "ORDO"])
@pytest.mark.parametrize("action", ["submit", "review", "publish"])
def test_native_matching_precondition_accepts_existing_lifecycle(api, tmp_path, monkeypatch, product, action):
    client, _, path, _, payload = native_version(api, tmp_path, monkeypatch, product, action)
    response = client.post(path + "/" + action, json=payload)
    assert response.status_code == 200, response.text
    value = response.json()["version"] if action == "review" else response.json()
    assert value["status"] == dict(submit="in_review", review="approved", publish="published")[action]


def test_schema_hashes_require_reviewed_status_and_legacy_compatible():
    assert ReportLifecycleRequest(**SCOPE).reviewed_status is None
    with pytest.raises(ValidationError):
        ReportLifecycleRequest(**SCOPE, reviewed_content_sha256="a" * 64)
    with pytest.raises(ValidationError):
        ReportLifecycleRequest(**SCOPE, reviewed_status="draft", reviewed_content_sha256="invalid")


def test_client_pins_exact_reviewed_fields_before_transport(monkeypatch):
    calls = []
    monkeypatch.setattr(
        api_client,
        "request",
        lambda *a, **kw: calls.append((a, kw)) or httpx.Response(200, json={"status": "in_review"}),
    )
    version = dict(status="draft", content_sha256="a" * 64, source_manifest_sha256="b" * 64)
    api_client.submit("synthetic", **SCOPE, version_id=IDS[2], version=version)
    assert calls[0][0] == ("POST", "/api/v1/reporting/versions/" + IDS[2] + "/submit")
    assert calls[0][1]["json"] == dict(
        SCOPE, reviewed_status="draft", reviewed_content_sha256="a" * 64, reviewed_source_manifest_sha256="b" * 64
    )
    calls.clear()
    with pytest.raises(ValueError):
        api_client.report("synthetic", "not-a-uuid", **SCOPE)
    assert not calls


@pytest.mark.parametrize("body", [dict(detail="SYNTHETIC_PRIVATE"), dict(detail=[dict(input="SYNTHETIC_PRIVATE")])])
def test_client_never_echoes_private_error_body(body):
    with pytest.raises(AccessDenied) as exc:
        api_client._checked(httpx.Response(422, json=body), unavailable="Unavailable")
    assert "SYNTHETIC_PRIVATE" not in str(exc.value)


def setup_ui(monkeypatch, *, status="draft", permissions=None, linked=False):
    source = dict(
        id=IDS[2], kind="extraction_request" if linked else "analytics_run", label="Synthetic reviewed source"
    )
    version = dict(
        id=IDS[4],
        version_no=1,
        status=status,
        content_sha256="a" * 64,
        source_manifest_sha256="b" * 64,
        content=dict(sections=[]),
        source_manifest=[dict(kind="synthetic", id=IDS[2], product_code="SIMPA", checksum="c" * 64)],
        reviews=[],
    )
    report = dict(
        id=IDS[3],
        title="Synthetic report",
        report_type="linked_evidence" if linked else "monitoring_summary",
        product_code="SIMPA",
        workspace_id=IDS[1],
        status="active",
        versions=[version],
    )
    state = dict(source=source, version=version, report=report, records=[dict(report)], calls=[])
    monkeypatch.setattr(api_client, "sources", lambda *a: [deepcopy(state["source"])])
    monkeypatch.setattr(api_client, "reports", lambda *a: deepcopy(state["records"]))
    monkeypatch.setattr(api_client, "report", lambda *a: deepcopy(state["report"]))

    def operation(name, **kw):
        state["calls"].append((name, deepcopy(kw)))
        if name in {"submit", "review", "publish"}:
            state["version"]["status"] = dict(submit="in_review", review=kw.get("decision"), publish="published")[name]
        return {"completed": True}

    for name in ["generate", "new_version", "submit", "review", "publish"]:
        monkeypatch.setattr(api_client, name, lambda *a, _name=name, **kw: operation(_name, **kw))
    shell = dict(
        organization=dict(id=IDS[0]),
        workspace=dict(id=IDS[1]),
        product=dict(code="SIMPA", permission_codes=PERMISSIONS if permissions is None else permissions),
    )
    app = AppTest.from_string(
        "import streamlit as st\nfrom src.streamlit_app.reporting_workspace import render_reporting\nshell="
        + repr(shell)
        + '\nshell["workspace"]["id"]=st.session_state.get("qa_workspace",shell["workspace"]["id"])\nrender_reporting(token="synthetic",shell=shell)'
    ).run(timeout=30)
    assert not app.exception
    return app, state


def widget(items, label):
    return next(x for x in items if x.label == label)


def test_source_no_default_and_value_roundtrip_invalidates_confirmation(monkeypatch):
    at, state = setup_ui(monkeypatch)
    assert widget(at.selectbox, "Izvor").value is None and not at.text_input
    widget(at.selectbox, "Izvor").select(IDS[2]).run()
    widget(at.text_input, "Naslov izveštaja").set_value("Synthetic title").run()
    confirm = "Potvrđujem tačan izvor, naslov i kreiranje ovog nacrta"
    widget(at.checkbox, confirm).check().run()
    assert not widget(at.button, "Kreiraj draft izveštaj").disabled
    widget(at.text_input, "Naslov izveštaja").set_value("Changed title").run()
    assert not widget(at.checkbox, confirm).value
    widget(at.text_input, "Naslov izveštaja").set_value("Synthetic title").run()
    assert not widget(at.checkbox, confirm).value and not state["calls"]
    widget(at.checkbox, confirm).check().run()
    widget(at.button, "Kreiraj draft izveštaj").click().run()
    assert not at.exception and state["calls"][0][0] == "generate" and at.success
    assert widget(at.selectbox, "Izvor").value is None


def test_fresh_version_drift_invalidates_submit_confirmation(monkeypatch):
    at, state = setup_ui(monkeypatch)
    label = "Potvrđujem slanje ove pregledane verzije na review"
    widget(at.checkbox, label).check().run()
    state["version"]["content_sha256"] = "d" * 64
    at.run()
    assert not widget(at.checkbox, label).value and widget(at.button, "Pošalji na review").disabled
    widget(at.checkbox, label).check().run()
    widget(at.button, "Pošalji na review").click().run()
    assert not at.exception and state["calls"][0][1]["version"]["content_sha256"] == "d" * 64
    assert widget(at.selectbox, "Odluka o verziji").value is None


def test_review_choice_note_confirmation_and_success_are_separate(monkeypatch):
    at, state = setup_ui(monkeypatch, status="in_review")
    assert widget(at.selectbox, "Odluka o verziji").value is None
    widget(at.selectbox, "Odluka o verziji").select("approved").run()
    widget(at.text_area, "Review napomena").set_value("Synthetic review").run()
    label = "Potvrđujem pregled sadržaja, porekla i ovu odluku o verziji"
    widget(at.checkbox, label).check().run()
    widget(at.selectbox, "Odluka o verziji").select("rejected").run()
    assert not widget(at.checkbox, label).value
    widget(at.selectbox, "Odluka o verziji").select("approved").run()
    assert not widget(at.checkbox, label).value
    widget(at.checkbox, label).check().run()
    widget(at.button, "Sačuvaj odluku o verziji").click().run()
    assert not at.exception and state["calls"][0][0] == "review"
    assert state["calls"][0][1]["decision"] == "approved" and widget(at.button, "Publikuj verziju").disabled


def test_new_version_requires_selected_source_and_confirmation(monkeypatch):
    at, state = setup_ui(monkeypatch)
    assert widget(at.selectbox, "Izvor za novu verziju").value is None
    assert not any(x.label == "Kreiraj novu verziju iz izabranog izvora" for x in at.button)
    widget(at.selectbox, "Izvor za novu verziju").select(IDS[2]).run()
    assert widget(at.button, "Kreiraj novu verziju iz izabranog izvora").disabled
    widget(at.checkbox, "Potvrđujem izabrani izvor za zasebnu novu verziju").check().run()
    widget(at.button, "Kreiraj novu verziju iz izabranog izvora").click().run()
    assert not at.exception and state["calls"][0][1]["source_id"] == IDS[2]


def test_linked_attestation_changes_reset_and_no_default_claim():
    at = AppTest.from_string(
        'from src.streamlit_app.linked_reporting_workspace import inputs\ninputs("synthetic-link:")'
    ).run()
    assert at.text_input[0].value == ""
    at.text_input[0].set_value("c1").run()
    at.text_area[0].set_value("Synthetic contextual link").run()
    at.checkbox[0].check().run()
    at.text_area[0].set_value("Different contextual link").run()
    assert not at.checkbox[0].value
    at.text_area[0].set_value("Synthetic contextual link").run()
    assert not at.checkbox[0].value


def test_readonly_no_mutations_and_unavailable_not_empty(monkeypatch):
    at, state = setup_ui(monkeypatch, permissions=["report.read"])
    assert not at.exception and not at.button and not state["calls"]
    monkeypatch.setattr(api_client, "sources", lambda *a: (_ for _ in ()).throw(AccessDenied("SYNTHETIC_PRIVATE")))
    at.run()
    assert not at.exception and at.error and any("nije potvrda" in x.value for x in at.info)
    assert "SYNTHETIC_PRIVATE" not in repr([x.value for x in at.error])


def test_export_revalidates_every_render_and_failure_hides_previous_content(monkeypatch):
    at, state = setup_ui(monkeypatch, status="approved", permissions=["report.read"])
    calls = []

    def export(*a, **kw):
        calls.append(kw)
        if len(calls) > 1:
            raise AccessDenied("Synthetic revoked source")
        return dict(
            content_text="Synthetic approved quote", filename="synthetic.html", mime_type="text/html", sha256="f" * 64
        )

    monkeypatch.setattr(api_client, "export", export)
    widget(at.checkbox, "Pripremi download artefakt").check().run()
    assert not at.exception and at.get("download_button")
    at.run()
    assert not at.exception and len(calls) == 2 and not at.get("download_button") and at.error
    assert not state["calls"]


def test_guide_ten_items_and_technical_boundaries():
    text = Path("docs/help/ISI-REPORTING-WORKFLOWS-GUIDE.md").read_text()
    assert all(f"## {i}." in text for i in range(1, 11))
    assert all(x in text for x in ["UNCALIBRATED", "409", "superseded", "Datirane ilustracije", "report.read"])


def test_context_roundtrip_does_not_revive_previous_confirmation(monkeypatch):
    at, state = setup_ui(monkeypatch)
    label = "Potvrđujem slanje ove pregledane verzije na review"
    widget(at.checkbox, label).check().run()
    at.session_state["qa_workspace"] = IDS[6]
    at.run()
    assert not widget(at.checkbox, label).value
    at.session_state["qa_workspace"] = IDS[1]
    at.run()
    assert not widget(at.checkbox, label).value and not state["calls"]


def test_source_metadata_drift_invalidates_creation(monkeypatch):
    at, state = setup_ui(monkeypatch)
    widget(at.selectbox, "Izvor").select(IDS[2]).run()
    widget(at.text_input, "Naslov izveštaja").set_value("Synthetic title").run()
    label = "Potvrđujem tačan izvor, naslov i kreiranje ovog nacrta"
    widget(at.checkbox, label).check().run()
    state["source"]["fingerprint"] = "e" * 64
    at.run()
    assert not widget(at.checkbox, label).value and not state["calls"]


def test_failed_publish_keeps_failure_visible_and_no_false_success(monkeypatch):
    at, state = setup_ui(monkeypatch, status="approved")
    calls = []

    def fail(*a, **kw):
        calls.append(kw)
        raise AccessDenied("Synthetic stale evidence")

    monkeypatch.setattr(api_client, "publish", fail)
    widget(at.checkbox, "Potvrđujem objavljivanje ove odobrene verzije unutar platforme").check().run()
    widget(at.button, "Publikuj verziju").click().run()
    assert not at.exception and at.error and not at.success and len(calls) == 1
    assert state["version"]["status"] == "approved" and not state["calls"]
    at.run()
    assert len(calls) == 1  # no automatic retry


def test_native_version_scope_checked_before_reviewed_precondition(api, tmp_path, monkeypatch):
    client, _, path, _, payload = native_version(api, tmp_path, monkeypatch, "SIMPA", "submit")
    _, context, _ = api
    payload.update(params(context, "ORDO"), product_code="ORDO")
    response = client.post(path + "/submit", json=payload)
    assert response.status_code == 404 and response.json()["detail"] == "report_version_not_accessible"
