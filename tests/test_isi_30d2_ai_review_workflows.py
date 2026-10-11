from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID, uuid4
from pathlib import Path

import pytest
from sqlalchemy import select
from streamlit.testing.v1 import AppTest

from src.platform.ai.evaluation import (
    create_evaluation_run,
    finalize_evaluation_run,
    load_evaluation_manifest,
    register_evaluation_dataset,
)
from src.platform.ai.governance import register_model
from src.platform.ai.models import AIEvaluationReview
from src.platform.access.models import RoleAssignment, Role
from src.streamlit_app import ai_api as api, ai_workspace as workspace
from src.streamlit_app.evidence_view import evidence_rows
from src.streamlit_app.api_client import AccessDenied
from tests.test_isi_29b_spatial_api import api as fixture, params

server = fixture
IDS = [str(UUID(int=i)) for i in range(1, 7)]
SCOPE = dict(organization_id=IDS[0], product_code="SIMPA", workspace_id=IDS[1])
RUN = dict(id=IDS[2], status="completed", result_fingerprint="a" * 64, input_fingerprint="b" * 64)
RESULTS = [
    dict(result_type="metric", result_key="synthetic", payload=dict(value=0, state="available"), fingerprint="c" * 64)
]
XAI = dict(
    unsupported_xai=dict(shap=dict(state="unavailable", reason="no validated SHAP evidence")), metrics=[dict(value=0)]
)


def seed(factory, c, terminal=True):
    with factory() as db:
        reg = register_model(
            db,
            organization_id=c["org"].id,
            workspace_id=c["simpa"].id,
            product_code="SIMPA",
            capability_key="synthetic-review",
            product_scope="SIMPA",
            model_family="llm",
            model_key="synthetic-review",
            version=str(uuid4()),
            lifecycle_state="candidate",
            actor_id=c["member"].id,
            provenance={"source": "synthetic"},
        )
        dataset = register_evaluation_dataset(
            db,
            manifest=load_evaluation_manifest("tests/evals/SIMPA-EVAL-v1.json"),
            product_code="SIMPA",
            actor_id=c["member"].id,
        )
        run = create_evaluation_run(
            db,
            organization_id=c["org"].id,
            workspace_id=c["simpa"].id,
            product_code="SIMPA",
            dataset_id=dataset.id,
            model_registration_id=reg.id,
            baseline_registration_id=None,
            prompt_version_id=None,
            policy_profile_id=None,
            input_fingerprint="a" * 64,
            environment_fingerprint="b" * 64,
            provenance={"source": "synthetic"},
            actor_id=c["member"].id,
        )
        if terminal:
            finalize_evaluation_run(db, run=run, status="completed")
        db.commit()
        return str(run.id)


def request(client, c, rid, **updates):
    scope = params(c) | dict(product_code="SIMPA")
    row = client.get("/api/v1/ai/evaluation/runs/" + rid, params=scope).json()
    return (
        dict(
            **scope,
            reviewed_status=row["status"],
            reviewed_result_fingerprint=row["result_fingerprint"],
            decision="approved",
            notes="Synthetic human review",
            evidence_reference="synthetic-review-proof",
        )
        | updates
    )


def test_native_scoped_review_actor_immutable_and_legacy_compatibility(server):
    client, c, factory = server
    rid = seed(factory, c)
    payload = request(client, c, rid)
    url = "/api/v1/ai/evaluation/runs/" + rid + "/reviews"
    response = client.post(url, json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["reviewer_membership_id"] == str(c["member"].id)
    assert client.post(url, json=payload).status_code == 409
    rid2 = seed(factory, c)
    legacy = request(client, c, rid2)
    legacy.pop("reviewed_status")
    legacy.pop("reviewed_result_fingerprint")
    assert client.post("/api/v1/ai/evaluation/runs/" + rid2 + "/reviews", json=legacy).status_code == 201


@pytest.mark.parametrize("change", [dict(reviewed_status="running"), dict(reviewed_result_fingerprint="f" * 64)])
def test_changed_review_evidence_rejected_without_persistence(server, change):
    client, c, factory = server
    rid = seed(factory, c)
    response = client.post("/api/v1/ai/evaluation/runs/" + rid + "/reviews", json=request(client, c, rid, **change))
    assert response.status_code == 409 and response.json()["detail"] == "evaluation_reviewed_evidence_changed"
    with factory() as db:
        assert db.scalar(select(AIEvaluationReview).where(AIEvaluationReview.evaluation_run_id == UUID(rid))) is None


def test_final_review_terminal_evidence_and_scope(server):
    client, c, factory = server
    rid = seed(factory, c, terminal=False)
    url = "/api/v1/ai/evaluation/runs/" + rid + "/reviews"
    assert client.post(url, json=request(client, c, rid)).status_code == 409
    assert client.post(url, json=request(client, c, rid, decision="pending")).status_code == 201
    assert client.post(url, json=request(client, c, rid, organization_id=str(uuid4()))).status_code == 403
    assert (
        client.post(url, json=request(client, c, rid, product_code="ORDO", workspace_id=str(c["ordo"].id))).status_code
        == 404
    )
    rid2 = seed(factory, c)
    assert (
        client.post(
            "/api/v1/ai/evaluation/runs/" + rid2 + "/reviews", json=request(client, c, rid2, evidence_reference=" ")
        ).status_code
        == 400
    )


def test_viewer_read_allowed_review_forbidden(server):
    client, c, factory = server
    rid = seed(factory, c)
    with factory() as db:
        grant = db.scalar(select(RoleAssignment).where(RoleAssignment.membership_id == c["member"].id))
        grant.role_id = db.scalar(select(Role.id).where(Role.code == "viewer"))
        db.commit()
    payload = request(client, c, rid)
    assert client.get("/api/v1/ai/evaluation/runs", params=params(c) | dict(product_code="SIMPA")).status_code == 200
    assert client.post("/api/v1/ai/evaluation/runs/" + rid + "/reviews", json=payload).status_code == 403


def test_evidence_preserves_zero_false_none_and_limits():
    rows = evidence_rows(dict(zero=0, flag=False, missing=None, nested=[dict(value=0)]))
    assert {r["Polje"]: r["Vrednost"] for r in rows} == dict(
        zero="0", flag="False", missing="Nije navedeno", **{"nested.0.value": "0"}
    )
    assert len(evidence_rows(list(range(500)))) == 201
    assert "kompletnosti" in evidence_rows(list(range(500)))[-1]["Vrednost"]
    assert "skraćeno" in evidence_rows("a" * 5000)[0]["Vrednost"]
    assert "dubine" in evidence_rows(dict(a=dict(b=1)), max_depth=1)[0]["Vrednost"]


@pytest.mark.parametrize("detail", [dict(secret="private"), [dict(input="private")], "private"])
def test_errors_do_not_reflect_request(detail):
    with pytest.raises(AccessDenied) as caught:
        api._checked(SimpleNamespace(status_code=422, json=lambda: dict(detail=detail)), unavailable="offline")
    assert "private" not in str(caught.value)


def test_review_transport_pins_scope_and_result(monkeypatch):
    req = Mock(return_value=SimpleNamespace(status_code=201, json=lambda: dict(id=IDS[3])))
    monkeypatch.setattr(api, "request", req)
    api.review_evaluation(
        "synthetic", scope=SCOPE, run=RUN, decision="approved", notes="Synthetic", evidence_reference="synthetic-proof"
    )
    body = req.call_args.kwargs["json"]
    assert body["reviewed_status"] == "completed" and body["reviewed_result_fingerprint"] == "a" * 64
    assert all(body[k] == v for k, v in SCOPE.items())


@pytest.mark.parametrize(
    "change",
    [dict(decision="unsupported"), dict(evidence_reference=" "), dict(scope=SCOPE | dict(product_code="OTHER"))],
)
def test_invalid_review_not_sent(monkeypatch, change):
    req = Mock()
    monkeypatch.setattr(api, "request", req)
    body = dict(scope=SCOPE, run=RUN, decision="approved", notes="Synthetic", evidence_reference="proof") | change
    with pytest.raises(AccessDenied):
        api.review_evaluation("synthetic", **body)
    req.assert_not_called()


def app():
    import streamlit as st
    from tests.test_isi_30d2_ai_review_workflows import SCOPE
    from src.streamlit_app.ai_governance_workspace import render_ai_governance

    scope = SCOPE | dict(organization_id=st.session_state["org"], product_code=st.session_state["product"])
    render_ai_governance(
        token="synthetic", shell=dict(product=dict(permission_codes=st.session_state["permissions"])), scope=scope
    )


def mounted(monkeypatch, permissions=None):
    rows = dict(
        registrations=[],
        runs=[RUN.copy()],
        run=RUN.copy(),
        results=deepcopy(RESULTS),
        reviews=[],
        evaluation_xai=deepcopy(XAI),
    )
    read = Mock(side_effect=lambda *a, kind, **kw: deepcopy(rows[kind]))
    monkeypatch.setattr(api, "evidence_get", read)
    at = AppTest.from_function(app)
    at.session_state["org"] = IDS[0]
    at.session_state["product"] = "SIMPA"
    at.session_state["permissions"] = ["analysis.read", "report.publish"] if permissions is None else permissions
    at.run()
    return at, rows, read


def label(items, name):
    return next(x for x in items if x.label == name)


def load(at):
    label(at.button, "Učitaj / osveži AI evaluacione dokaze").click().run()
    label(at.selectbox, "Evaluacioni run za pregled").select_index(0).run()


def test_ui_explicit_load_decision_confirm_values_roundtrip_success_reset(monkeypatch):
    at, rows, read = mounted(monkeypatch)
    read.assert_not_called()
    load(at)
    assert not at.json and not at.exception and label(at.selectbox, "Odluka ljudskog pregleda").value is None
    label(at.selectbox, "Odluka ljudskog pregleda").select("approved").run()
    label(at.text_area, "Obrazloženje AI pregleda").input("Synthetic human review").run()
    label(at.text_input, "Referenca dokaza AI pregleda").input("synthetic-proof").run()
    label(at.checkbox, "Potvrđujem pregledane AI dokaze i ovu ljudsku odluku").check().run()
    label(at.text_input, "Referenca dokaza AI pregleda").input("changed").run()
    label(at.text_input, "Referenca dokaza AI pregleda").input("synthetic-proof").run()
    assert not label(at.checkbox, "Potvrđujem pregledane AI dokaze i ovu ljudsku odluku").value
    fn = Mock(return_value=dict(id=IDS[3]))
    monkeypatch.setattr(api, "review_evaluation", fn)
    label(at.checkbox, "Potvrđujem pregledane AI dokaze i ovu ljudsku odluku").check().run()
    label(at.button, "Sačuvaj ljudski AI pregled").click().run()
    assert at.success and not at.selectbox and not at.exception
    assert fn.call_args.kwargs["run"] == RUN


def test_evidence_changes_reset_and_scope_requires_new_load(monkeypatch):
    at, rows, _ = mounted(monkeypatch)
    load(at)
    label(at.checkbox, "Potvrđujem pregledane AI dokaze i ovu ljudsku odluku").check().run()
    rows["run"]["result_fingerprint"] = "d" * 64
    at.run()
    assert not label(at.checkbox, "Potvrđujem pregledane AI dokaze i ovu ljudsku odluku").value
    at.session_state["org"] = IDS[5]
    at.run()
    assert not at.selectbox
    at.session_state["org"] = IDS[0]
    at.run()
    assert not at.selectbox


def test_readonly_no_review_and_nonterminal_pending_only(monkeypatch):
    at, rows, _ = mounted(monkeypatch, ["analysis.read"])
    load(at)
    assert not at.text_input and not at.checkbox
    at.session_state["permissions"] = ["analysis.read", "report.publish"]
    rows["run"]["status"] = "created"
    at.run()
    assert label(at.selectbox, "Odluka ljudskog pregleda").options == ["pending"]


def test_failed_review_visible_no_success(monkeypatch):
    at, _, _ = mounted(monkeypatch)
    load(at)
    label(at.selectbox, "Odluka ljudskog pregleda").select("pending").run()
    label(at.checkbox, "Potvrđujem pregledane AI dokaze i ovu ljudsku odluku").check().run()
    monkeypatch.setattr(api, "review_evaluation", Mock(side_effect=AccessDenied("Dokaz se promenio")))
    label(at.button, "Sačuvaj ljudski AI pregled").click().run()
    assert at.error and not at.success and not at.exception


def diagnostic_app():
    from tests.test_isi_30d2_ai_review_workflows import SCOPE
    from src.streamlit_app.ai_workspace import _render_local_ollama_diagnostic

    _render_local_ollama_diagnostic(
        "synthetic",
        dict(product=dict(permission_codes=["analysis.run"])),
        tuple(SCOPE[k] for k in ["organization_id", "product_code", "workspace_id"]),
        {},
        [
            dict(
                model_key="isi-ollama-chat-default",
                provider_type="ollama",
                purpose="chat",
                model_name="Synthetic model",
                enabled=True,
            )
        ],
    )


def test_diagnostic_no_default_model_sensitivity_and_confirmed_registration(monkeypatch):
    at = AppTest.from_function(diagnostic_app).run()
    assert all(x.value is None for x in at.selectbox) and at.button[0].disabled
    at.selectbox[0].select_index(0).run()
    at.selectbox[1].select("sensitive").run()
    fn = Mock(return_value=dict(id=IDS[3], status="queued"))
    monkeypatch.setattr(workspace.ai_api, "create_job", fn)
    at.checkbox[0].check().run()
    at.button[0].click().run()
    assert at.success and all(x.value is None for x in at.selectbox)
    assert fn.call_args.kwargs["sensitivity"] == "sensitive" and fn.call_args.kwargs["input_text"].startswith(
        "Local Ollama infrastructure diagnostic"
    )


def test_help_ten_items_limits():
    text = Path("docs/help/ISI-AI-REVIEW-WORKFLOWS-GUIDE.md").read_text()
    assert all(f"## {i}." in text for i in range(1, 11))
    assert all(x in text for x in ["report.publish", "local_only", "SHAP", "Datirane ilustracije"])


def test_fingerprint_without_reviewed_status_rejected(server):
    client, c, factory = server
    rid = seed(factory, c)
    body = request(client, c, rid)
    body.pop("reviewed_status")
    assert client.post("/api/v1/ai/evaluation/runs/" + rid + "/reviews", json=body).status_code == 422
