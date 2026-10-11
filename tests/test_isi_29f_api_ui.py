from uuid import UUID
import hashlib
import pytest
from streamlit.testing.v1 import AppTest
from test_isi_29b_spatial_api import api as scoped_api, params
from test_isi_29f_linked_reports import accepted
from src.platform.data.storage import LocalFilesystemStorage
from src.streamlit_app import reporting_api

api = scoped_api


@pytest.mark.parametrize("product", ["SIMPA", "ORDO"])
def test_api_preview_complete_lifecycle_and_all_saved_quote_paths_revalidate(api, tmp_path, monkeypatch, product):
    client, c, factory = api
    storage = LocalFilesystemStorage(tmp_path)
    monkeypatch.setattr("src.platform.extraction.service.build_storage", lambda: storage)
    with factory() as db:
        row, _version, profile, _geo = accepted(dict(c, db=db, storage=storage), product)
        request_id, profile_id = row.id, profile.id
    scope = {**params(c, product), "product_code": product}
    link = {"claim_id": "c1", "attested": True, "note": "Synthetic contextual association"}
    response = client.post("/api/v1/reporting/linked-preview", json={**scope, "request_id": str(request_id), "evidence_link": link})
    assert response.status_code == 200, response.text
    generated = client.post("/api/v1/reporting/reports", json={**scope, "title": "Synthetic linked report", "report_type": "linked_evidence", "source_kind": "extraction_request", "source_id": str(request_id), "evidence_link": link})
    assert generated.status_code == 201, generated.text
    report_id, version_id = generated.json()["id"], generated.json()["version"]["id"]
    prefix = "/api/v1/reporting/versions/" + version_id
    assert client.post(prefix + "/submit", json=scope).status_code == 200
    assert client.post(prefix + "/review", json={**scope, "decision": "approved", "note": "Synthetic approval"}).status_code == 200
    assert client.post(prefix + "/publish", json=scope).status_code == 200
    export = client.post(prefix + "/exports", json={**scope, "format": "json"})
    assert export.status_code == 201, export.text
    download = "/api/v1/reporting/exports/" + export.json()["id"] + "/download"
    assert client.get(download, params=scope).status_code == 200
    assert hashlib.sha256(export.json()["content_text"].encode()).hexdigest() == export.json()["sha256"]
    with factory() as db:
        from src.platform.reporting.models import ReportExport
        saved = db.get(ReportExport, UUID(export.json()["id"]))
        original = saved.content_text
        saved.content_text = "tampered synthetic export"
        db.commit()
    assert client.get(download, params=scope).status_code == 409
    with factory() as db:
        db.get(ReportExport, UUID(export.json()["id"])).content_text = original
        db.commit()
    with factory() as db:
        from src.platform.data.models import DataSourceGovernanceProfile
        db.get(DataSourceGovernanceProfile, profile_id).governance_state = "DRAFT"
        db.commit()
    get = client.get("/api/v1/reporting/reports/" + report_id, params=scope)
    assert get.status_code == 409 and "Synthetic has" not in get.text
    assert client.get(download, params=scope).status_code == 409
    for suffix, extra in [("submit", {}), ("review", {"decision": "approved"}), ("publish", {}), ("exports", {"format": "html"})]:
        assert client.post(prefix + "/" + suffix, json={**scope, **extra}).status_code == 409


def test_linked_ui_inputs_help_and_readonly_preview(monkeypatch):
    shell = {"organization": {"id": "synthetic-org"}, "workspace": {"id": "synthetic-workspace"},
             "product": {"code": "SIMPA", "permission_codes": ["report.read", "analysis.run", "data.read"]}}
    monkeypatch.setattr(reporting_api, "sources", lambda *a: [{"id": str(UUID(int=1)), "kind": "extraction_request", "label": "Synthetic accepted claim"}])
    monkeypatch.setattr(reporting_api, "reports", lambda *a: [])
    code = 'from src.streamlit_app.reporting_workspace import render_reporting\nrender_reporting(token="", shell=' + repr(shell) + ')'
    at = AppTest.from_string(code).run(timeout=30)
    assert not at.exception
    assert not at.text_input and not at.checkbox
    assert at.selectbox[0].value is None
    at.selectbox[0].select(str(UUID(int=1))).run(timeout=30)
    assert not at.exception
    assert len(at.text_input) == 3 and len(at.text_area) == 1 and len(at.checkbox) == 2
    assert next(x for x in at.text_input if x.label.startswith("ID prihvaćenog")).value == ""
    assert next(x for x in at.button if x.label == "Kreiraj draft izveštaj").disabled
    assert any("povezani" in b.label.lower() for b in at.button)
    assert any("Pomoć" in x.label for x in at.expander)
    shell["product"]["permission_codes"] = ["report.read"]
    viewer = AppTest.from_string('from src.streamlit_app.reporting_workspace import render_reporting\nrender_reporting(token="", shell=' + repr(shell) + ')').run(timeout=30)
    assert not viewer.exception and not viewer.button
