from uuid import uuid4
from pathlib import Path
import httpx
import pytest
from sqlalchemy import select
from streamlit.testing.v1 import AppTest
from test_isi_29b_spatial_api import api as scoped_api, params
from test_isi_29e_service import document
from src.platform.access.models import Role, RoleAssignment
from src.platform.data.storage import LocalFilesystemStorage
from src.platform.extraction.contracts import Create
from src.streamlit_app import extraction_api
from src.streamlit_app.api_client import AccessDenied, AuthenticationRequired, ApiUnavailable

api = scoped_api


def test_api_queue_idempotency_scoping_and_viewer_denial(api, tmp_path, monkeypatch):
    client, c, factory = api
    storage = LocalFilesystemStorage(tmp_path)
    monkeypatch.setattr("src.platform.extraction.service.build_storage", lambda: storage)
    calls = []
    monkeypatch.setattr("src.api.extraction_routes.dispatch_ai_job", lambda job: calls.append(job))
    with factory() as db:
        v, _ = document(dict(c, db=db, storage=storage))
        body = Create(
            **params(c),
            input_kind="document",
            input_id=v.id,
            language="en",
            model_key="isi-ollama-chat-default",
            request_key=uuid4(),
        ).model_dump(mode="json")
    url = "/api/v1/extraction/SIMPA/requests"
    response = client.post(url, json=body)
    assert response.status_code == 201, response.text
    row = response.json()
    assert client.post(url, json=body).json()["id"] == row["id"] and len(calls) == 1
    assert client.get(url + "/" + row["id"], params=params(c)).status_code == 200
    assert client.get("/api/v1/extraction/ORDO/requests/" + row["id"], params=params(c, "ORDO")).status_code == 409
    with factory() as db:
        assignment = db.scalar(select(RoleAssignment).where(RoleAssignment.membership_id == c["member"].id))
        assignment.role_id = db.scalar(select(Role.id).where(Role.code == "viewer"))
        db.commit()
    body["request_key"] = str(uuid4())
    assert client.post(url, json=body).status_code == 403
    assert client.post(url + "/" + row["id"] + "/cancel", params=params(c)).status_code == 403
    assert client.get(url, params=params(c)).status_code == 200
    assert len(calls) == 1


def test_dispatch_failure_safe_and_no_automatic_retry(api, tmp_path, monkeypatch):
    client, c, factory = api
    storage = LocalFilesystemStorage(tmp_path)
    monkeypatch.setattr("src.platform.extraction.service.build_storage", lambda: storage)
    calls = []

    def fail(job):
        calls.append(job)
        raise RuntimeError("SENSITIVE_PROVIDER_DETAIL")

    monkeypatch.setattr("src.api.extraction_routes.dispatch_ai_job", fail)
    with factory() as db:
        v, _ = document(dict(c, db=db, storage=storage))
        body = Create(
            **params(c),
            input_kind="document",
            input_id=v.id,
            language="en",
            model_key="isi-ollama-chat-default",
            request_key=uuid4(),
        ).model_dump(mode="json")
    url = "/api/v1/extraction/SIMPA/requests"
    first = client.post(url, json=body)
    assert first.status_code == 201 and first.json()["state"] == "failed" and "SENSITIVE" not in first.text
    assert client.post(url, json=body).json() == first.json() and len(calls) == 1


@pytest.mark.parametrize(
    "code,error",
    [
        (401, AuthenticationRequired),
        (403, AccessDenied),
        (409, AccessDenied),
        (422, AccessDenied),
        (500, ApiUnavailable),
    ],
)
def test_transport_scoped_and_no_error_payload_echo(monkeypatch, code, error):
    seen = []
    monkeypatch.setattr(
        extraction_api,
        "request",
        lambda *a, **kw: seen.append((a, kw)) or httpx.Response(code, json={"detail": "PRIVATE_SOURCE"}),
    )
    with pytest.raises(error) as exc:
        extraction_api.call("", "SIMPA", "requests", organization_id="org", workspace_id="ws")
    assert "PRIVATE" not in str(exc.value) and seen[0][1]["params"] == dict(organization_id="org", workspace_id="ws")


def app_code(permissions):
    shell = dict(
        organization=dict(id="synthetic-org"),
        workspace=dict(id="synthetic-workspace"),
        product=dict(code="SIMPA", permission_codes=permissions),
    )
    return (
        'from src.streamlit_app.extraction_workspace import render_extraction_workspace\nrender_extraction_workspace(token="",shell='
        + repr(shell)
        + ")"
    )


def test_viewer_explicit_load_and_scope_keys(monkeypatch):
    calls = []
    monkeypatch.setattr(
        extraction_api, "call", lambda *a, **kw: calls.append((a, kw)) or dict(items=[], truncated=False)
    )
    at = AppTest.from_string(app_code(["data.read"])).run(timeout=30)
    assert not at.exception and not calls and not at.button
    at.checkbox[0].check().run(timeout=30)
    assert not at.exception and len(calls) == 1 and calls[0][1]["workspace_id"] == "synthetic-workspace"
    assert len(at.expander) == 1 and not at.button
    at.checkbox[0].uncheck().run(timeout=30)
    assert not at.exception and len(calls) == 1


def test_creator_disabled_without_local_model_and_help_contract(monkeypatch):
    from src.streamlit_app import ai_api

    monkeypatch.setattr(extraction_api, "call", lambda *a, **kw: dict(items=[], truncated=False))
    monkeypatch.setattr(ai_api, "models", lambda *a, **kw: [])
    at = AppTest.from_string(app_code(["data.read", "ai.run"])).run(timeout=30)
    at.checkbox[0].check().run(timeout=30)
    assert not at.exception and at.button[0].disabled
    guide = Path("docs/help/ISI-EXTRACTION-GUIDE.md").read_text()
    for i in range(1, 11):
        assert f"## {i}. " in guide


def test_review_form_fields_available_before_selection_and_safe_quotes(monkeypatch):
    from src.streamlit_app import spatial_api
    from test_isi_29e_contracts import example

    output = example()
    value = dict(
        id="synthetic-request",
        state="EXTRACTED_UNVERIFIED",
        artifact_fingerprint="a" * 64,
        artifact=dict(output=output, links={"m1": dict(state="UNRESOLVED")}, source={"version": "synthetic"}),
    )
    seen = []

    def call(*a, **kw):
        seen.append((a, kw))
        if a[2] == "requests":
            return dict(items=[dict(id=value["id"], state=value["state"])], truncated=False)
        return value

    monkeypatch.setattr(extraction_api, "call", call)
    monkeypatch.setattr(spatial_api, "call", lambda *a, **kw: [])
    at = AppTest.from_string(app_code(["data.read", "data.validate"])).run(timeout=30)
    at.checkbox[0].check().run(timeout=30)
    at.checkbox[1].check().run(timeout=30)
    assert not at.exception
    assert any(x.label == "Dokaz identiteta m1" for x in at.text_input)
    assert any(x.label == "Dokaz obuhvata c1" for x in at.text_input)
    assert any(x.label == "Datum granice c1" for x in at.date_input)
    assert len(at.button) == 2 and any("Prihvatanje ekstrakcije" in x.value for x in at.warning)
    at.text_area[0].set_value("Synthetic rejection")
    at.button[0].click().run(timeout=30)
    posted = [kw["payload"] for a, kw in seen if kw.get("method") == "POST"]
    assert posted[0]["decision"] == "REJECTED" and posted[0]["territories"] == posted[0]["entity_links"] == []
