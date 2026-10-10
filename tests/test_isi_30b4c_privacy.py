from types import SimpleNamespace
from unittest.mock import Mock
import uuid

import pytest
from pydantic import ValidationError
from streamlit.testing.v1 import AppTest

from src.streamlit_app import data_privacy_api as api
from tests.test_isi_21b_export_governance import export_setup as export_setup

IDS = [str(uuid.UUID(int=i)) for i in range(1, 9)]
SCOPE = dict(organization_id=IDS[0], workspace_id=IDS[1], product_code="SIMPA")
VERSION = dict(id=IDS[2], version_no=1, original_filename="synthetic.csv", content_state="AVAILABLE")
STATE = dict(id=IDS[3], revision=1, hold_active=False, purge_status="NONE")
RECORD = dict(
    id=IDS[4],
    status="PROPOSED",
    input_version_id=IDS[2],
    output_version_id=IDS[5],
    method_code="synthetic",
    method_version="1",
)


@pytest.mark.parametrize("action", ["hold", "release", "request"])
@pytest.mark.parametrize("product", ["SIMPA", "ORDO"])
def test_retention_action_pins_scope_revision(monkeypatch, action, product):
    req = Mock(return_value=SimpleNamespace(status_code=200, json=lambda: {}))
    monkeypatch.setattr(api, "request", req)
    api.retention_action(
        "synthetic",
        version_id="v/+",
        scope={**SCOPE, "product_code": product},
        revision=3,
        action=action,
        reason="synthetic-review",
    )
    payload = req.call_args.kwargs["json"]
    assert payload["expected_revision"] == 3 and payload["product_code"] == product
    assert "/v%2F%2B/" in req.call_args.args[1]
    assert req.call_args.kwargs.get("params") is None


def test_no_physical_purge_api_wrapper():
    with pytest.raises(KeyError):
        api.retention_action("synthetic", version_id=IDS[2], scope=SCOPE, revision=1, action="execute")


def test_author_policy_days_not_invented(monkeypatch):
    req = Mock(return_value=SimpleNamespace(status_code=201, json=lambda: {}))
    monkeypatch.setattr(api, "request", req)
    api.create_policy("synthetic", scope=SCOPE, fields=dict(policy_code="SYNTHETIC", version_no=1, name="Synthetic"))
    payload = req.call_args.kwargs["json"]
    assert payload["retention_days"] is None and payload["no_auto_delete"] and payload["manual_review_required"]
    assert req.call_args.kwargs["params"] == SCOPE


def test_review_cannot_choose_proposed(monkeypatch):
    req = Mock()
    monkeypatch.setattr(api, "request", req)
    with pytest.raises(ValueError):
        api.review_anonymization(
            "synthetic", record_id=IDS[4], scope=SCOPE, fields=dict(decision="PROPOSED", review_reference="synthetic")
        )
    req.assert_not_called()


def test_invalid_proposal_no_http(monkeypatch):
    req = Mock()
    monkeypatch.setattr(api, "request", req)
    with pytest.raises(ValidationError):
        api.propose_anonymization("synthetic", scope=SCOPE, fields={})
    req.assert_not_called()


def test_paginated_record_list_scoped(monkeypatch):
    req = Mock(return_value=SimpleNamespace(status_code=200, json=lambda: []))
    monkeypatch.setattr(api, "request", req)
    api.list_records("synthetic", scope=SCOPE, offset=50)
    assert req.call_args.kwargs["params"] == {**SCOPE, "offset": 50, "limit": 50}


def test_export_requires_manifest_and_keeps_binary(monkeypatch):
    req = Mock(
        return_value=SimpleNamespace(
            status_code=200,
            content=b"synthetic",
            headers={"X-Data-Export-Manifest-ID": IDS[6], "content-type": "text/csv"},
        )
    )
    monkeypatch.setattr(api, "request", req)
    result = api.export_version("synthetic", version_id=IDS[2], scope=SCOPE, purpose="synthetic-review")
    assert result == dict(payload=b"synthetic", content_type="text/csv", manifest_id=IDS[6])
    req.return_value.headers = {}
    from src.streamlit_app.api_client import ApiUnavailable

    with pytest.raises(ApiUnavailable):
        api.export_version("synthetic", version_id=IDS[2], scope=SCOPE, purpose="synthetic-review")


def script():
    import streamlit as st
    from src.streamlit_app.data_privacy_workspace import render_source_privacy

    render_source_privacy(
        token="synthetic",
        shell=st.session_state["shell"],
        source_id=st.session_state["source_id"],
        versions=st.session_state["versions"],
    )


def app(monkeypatch, permissions=("data.read", "data.governance.manage", "data.export")):
    for name, value in [
        ("read_retention", STATE),
        ("retention_action", STATE),
        ("list_records", [RECORD]),
        ("review_anonymization", dict(id=IDS[4])),
        ("create_policy", dict(id=IDS[6])),
        ("export_version", dict(payload=b"synthetic", content_type="text/csv", manifest_id=IDS[6])),
    ]:
        monkeypatch.setattr(api, name, Mock(return_value=value))
    at = AppTest.from_function(script)
    at.session_state["shell"] = dict(
        organization=dict(id=IDS[0]),
        workspace=dict(id=IDS[1]),
        product=dict(code="SIMPA", permission_codes=permissions),
    )
    at.session_state["versions"] = [VERSION]
    at.session_state["source_id"] = IDS[7]
    # AppTest function executes in an independent module; pass source via session state.
    at.run()
    assert not at.exception
    return at


def click(at, label):
    next(x for x in at.button if x.label == label).click().run()
    assert not at.exception


def test_readonly_and_explicit_read(monkeypatch):
    at = app(monkeypatch, permissions=("data.read",))
    api.read_retention.assert_not_called()
    click(at, "Učitaj / osveži stanje čuvanja")
    assert not at.checkbox and not at.text_input
    api.list_records.assert_not_called()
    api.export_version.assert_not_called()


def test_hold_confirmation_and_revision(monkeypatch):
    at = app(monkeypatch)
    click(at, "Učitaj / osveži stanje čuvanja")
    click(at, "Postavi hold")
    api.retention_action.assert_not_called()
    next(x for x in at.text_input if x.label == "Referenca zabrane brisanja (hold)").set_value("synthetic-hold")
    next(x for x in at.checkbox if x.label == "Potvrđujem postavljanje hold-a").check()
    click(at, "Postavi hold")
    api.retention_action.assert_called_once_with(
        "synthetic", version_id=IDS[2], scope=SCOPE, revision=1, action="hold", reason="synthetic-hold"
    )
    api.read_retention.return_value = {**STATE, "hold_active": True, "revision": 2}
    click(at, "Učitaj / osveži stanje čuvanja")
    assert not any(x.label == "Zatraži pregled purge-a" for x in at.button)
    assert not next(x for x in at.checkbox if x.label == "Potvrđujem ukidanje hold-a").value


def test_review_requires_explicit_decision_confirmation(monkeypatch):
    at = app(monkeypatch)
    click(at, "Učitaj / osveži dokaze anonimizacije")
    assert next(x for x in at.selectbox if x.label == "Odluka o dokazu anonimizacije").value is None
    click(at, "Registruj pregled anonimizacije")
    api.review_anonymization.assert_not_called()
    next(x for x in at.selectbox if x.label == "Odluka o dokazu anonimizacije").set_value("REJECTED")
    next(x for x in at.text_input if x.label == "Referenca ljudskog pregleda anonimizacije").set_value(
        "synthetic-review"
    )
    next(x for x in at.checkbox if x.label == "Potvrđujem proveru ulaza, izlaza, metode i dokaza anonimizacije").check()
    click(at, "Registruj pregled anonimizacije")
    api.review_anonymization.assert_called_once_with(
        "synthetic",
        record_id=IDS[4],
        scope=SCOPE,
        fields=dict(decision="REJECTED", review_reference="synthetic-review", review_reason=""),
    )


def test_export_not_prepared_without_confirmation(monkeypatch):
    at = app(monkeypatch)
    click(at, "Pripremi dozvoljeni izvoz verzije")
    api.export_version.assert_not_called()
    next(x for x in at.text_input if x.label == "Referenca svrhe izvoza verzije").set_value("synthetic-review")
    next(x for x in at.checkbox if x.label == "Potvrđujem svrhu i dozvoljeni izvoz izabrane verzije").check()
    click(at, "Pripremi dozvoljeni izvoz verzije")
    api.export_version.assert_called_once_with("synthetic", version_id=IDS[2], scope=SCOPE, purpose="synthetic-review")
    assert any("Manifest izvoza" in x.value for x in at.caption)


def test_no_purge_execute_ui_and_no_permission_reads(monkeypatch):
    at = app(monkeypatch)
    assert all("izvrši purge" not in x.label.lower() for x in at.button)
    at = app(monkeypatch, permissions=())
    assert not at.button
    api.read_retention.assert_not_called()


def test_backend_anonymization_page_scope_and_final_review(export_setup):
    from src.platform.data.privacy_service import (
        propose_anonymization,
        list_anonymization_records,
        review_anonymization,
    )
    from src.platform.data.schemas import AnonymizationProposalCreate
    from src.platform.data.service import create_source_upload, DataPlatformError
    from src.platform.data.governance import AnonymizationStatus

    db, org, ws, ordo, member, source, version, storage = export_setup
    output, output_version, _, _ = create_source_upload(
        db,
        storage,
        organization_id=org.id,
        workspace_id=ws.id,
        product_code="SIMPA",
        source_name="synthetic output",
        filename="synthetic.csv",
        content_type="text/csv",
        payload=b"synthetic-output",
        actor_id=member.id,
        backend="inline",
    )
    scope = dict(organization_id=org.id, workspace_id=ws.id, product_code="SIMPA")
    row = propose_anonymization(
        db,
        payload=AnonymizationProposalCreate(
            **scope,
            input_version_id=version.id,
            output_version_id=output_version.id,
            method_code="SYNTHETIC",
            method_version="1",
            method_reference="synthetic-method",
            evidence_reference="synthetic-evidence",
            classification_after="INTERNAL",
            privacy_category_after="AGGREGATE_NON_PERSONAL",
        ),
        actor_id=member.id,
    )
    assert list_anonymization_records(db, **scope, limit=1)[0].id == row.id
    assert list_anonymization_records(db, **scope, offset=1) == []
    assert list_anonymization_records(db, organization_id=org.id, workspace_id=ordo.id, product_code="ORDO") == []
    with pytest.raises(DataPlatformError, match="invalid_anonymization_page"):
        list_anonymization_records(db, **scope, limit=101)
    result = review_anonymization(
        db,
        record_id=row.id,
        **scope,
        decision=AnonymizationStatus.REJECTED,
        review_reference="synthetic-review",
        actor_id=member.id,
    )
    assert result.status == "REJECTED"
    with pytest.raises(DataPlatformError, match="anonymization_state_conflict"):
        review_anonymization(
            db,
            record_id=row.id,
            **scope,
            decision=AnonymizationStatus.VERIFIED,
            review_reference="synthetic-second",
            actor_id=member.id,
        )


def test_route_requires_governance_permission(monkeypatch):
    from src.api import data_routes

    required = Mock()
    monkeypatch.setattr(data_routes, "_require_scope", required)
    service = Mock(return_value=[])
    monkeypatch.setattr(data_routes, "list_anonymization_records", service)
    db = Mock()
    context = Mock()
    assert data_routes.get_anonymization_records(**SCOPE, offset=0, limit=50, context=context, db=db) == []
    assert required.call_args.kwargs["permission_code"] == "data.governance.manage"
    service.assert_called_once_with(db, **SCOPE, offset=0, limit=50)


def test_proposal_binds_selected_other_source_output(monkeypatch):
    from src.streamlit_app import data_api

    monkeypatch.setattr(
        data_api, "list_data_sources", Mock(return_value=[dict(id=IDS[6], name="Synthetic output source")])
    )
    monkeypatch.setattr(data_api, "get_source_detail", Mock(return_value=dict(versions=[{**VERSION, "id": IDS[5]}])))
    monkeypatch.setattr(api, "propose_anonymization", Mock(return_value=dict(id=IDS[4])))
    at = app(monkeypatch)
    click(at, "Učitaj dostupne izlazne verzije drugih izvora")
    assert next(x for x in at.selectbox if x.label == "Klasifikacija izlaza posle anonimizacije").value is None
    for label, value in [
        ("Oznaka metode anonimizacije", "SYNTHETIC"),
        ("Verzija metode anonimizacije", "1"),
        ("Referenca metode anonimizacije", "synthetic-method"),
        ("Referenca dokaza anonimizacije", "synthetic-evidence"),
    ]:
        next(x for x in at.text_input if x.label == label).set_value(value)
    next(x for x in at.selectbox if x.label == "Klasifikacija izlaza posle anonimizacije").set_value("INTERNAL")
    next(x for x in at.selectbox if x.label == "Privatnost izlaza posle anonimizacije").set_value(
        "AGGREGATE_NON_PERSONAL"
    )
    click(at, "Registruj predlog anonimizacije")
    api.propose_anonymization.assert_not_called()
    next(x for x in at.checkbox if x.label == "Potvrđujem odvojeni izlaz i dokumentovanu metodu anonimizacije").check()
    click(at, "Registruj predlog anonimizacije")
    fields = api.propose_anonymization.call_args.kwargs["fields"]
    assert fields["input_version_id"] == IDS[2] and fields["output_version_id"] == IDS[5]
    assert api.propose_anonymization.call_args.kwargs["scope"] == SCOPE


def test_export_denial_has_no_download(monkeypatch):
    from src.streamlit_app.api_client import AccessDenied

    at = app(monkeypatch)
    api.export_version.side_effect = AccessDenied("step_up_authentication_required")
    next(x for x in at.text_input if x.label == "Referenca svrhe izvoza verzije").set_value("synthetic-review")
    next(x for x in at.checkbox if x.label == "Potvrđujem svrhu i dozvoljeni izvoz izabrane verzije").check()
    click(at, "Pripremi dozvoljeni izvoz verzije")
    assert at.error and not any("Manifest izvoza" in x.value for x in at.caption)
