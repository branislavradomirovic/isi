from types import SimpleNamespace
from unittest.mock import Mock
import uuid

import pytest
from pydantic import ValidationError
from streamlit.testing.v1 import AppTest

from src.streamlit_app import data_governance_api as api
from src.streamlit_app.data_governance_workspace import profile_changes

IDS = [str(uuid.UUID(int=i)) for i in range(1, 9)]
SCOPE = dict(organization_id=IDS[0], workspace_id=IDS[1], product_code="SIMPA")
PROFILE = dict(
    id=IDS[2],
    revision=1,
    classification="UNCLASSIFIED",
    privacy_category="UNKNOWN",
    governance_state="DRAFT",
    ai_use_policy="PROHIBITED",
    export_policy="PROHIBITED",
    processing_purpose="",
    data_owner_ref="",
    classification_rationale="",
    retention_policy_id=None,
    data_steward_membership_id=None,
)
ROW = dict(
    id=IDS[3], source_record_ordinal=2, quarantine_reason="IDENTITY_CONTENT_CONFLICT", content_fingerprint="synthetic"
)
DETAIL = {
    **ROW,
    "normalized_record": dict(unit="synthetic", value=2),
    "current_accepted_record": dict(unit="synthetic", value=1),
    "current_accepted_record_id": IDS[4],
}


@pytest.mark.parametrize("product", ["SIMPA", "ORDO"])
def test_update_scope_revision_and_unset_preserved(monkeypatch, product):
    req = Mock(return_value=SimpleNamespace(status_code=200, json=lambda: {}))
    monkeypatch.setattr(api, "request", req)
    scope = {**SCOPE, "product_code": product}
    api.update_profile(
        "synthetic",
        source_id="s/+",
        scope=scope,
        revision=4,
        fields=dict(classification="INTERNAL", expected_revision=99),
    )
    assert req.call_args.args == ("PUT", "/api/v1/data/sources/s%2F%2B/governance")
    assert req.call_args.kwargs["json"] == dict(classification="INTERNAL", expected_revision=4)
    assert req.call_args.kwargs["params"] == scope


def test_bad_classification_no_request(monkeypatch):
    req = Mock()
    monkeypatch.setattr(api, "request", req)
    with pytest.raises(ValidationError):
        api.update_profile(
            "synthetic", source_id=IDS[2], scope=SCOPE, revision=1, fields=dict(classification="MADE_UP")
        )
    req.assert_not_called()


@pytest.mark.parametrize("expected", [None, IDS[4]])
def test_record_pins_reviewed_current_and_scope(monkeypatch, expected):
    req = Mock(return_value=SimpleNamespace(status_code=200, json=lambda: {}))
    monkeypatch.setattr(api, "request", req)
    fields = dict(
        decision="REJECT_INCOMING",
        resolution_reference="synthetic-review",
        expected_current_accepted_record_id=expected,
    )
    api.resolve_record(
        "synthetic", source_id=IDS[2], record_id="r/+", scope=SCOPE, fields={**fields, "workspace_id": IDS[7]}
    )
    assert "/r%2F%2B/resolve" in req.call_args.args[1]
    payload = req.call_args.kwargs["json"]
    assert (
        payload["expected_current_accepted_record_id"] == expected and payload["workspace_id"] == SCOPE["workspace_id"]
    )


def test_changes_preserve_unchanged_policy():
    assert profile_changes(PROFILE, dict(classification="INTERNAL", retention_policy_id=None)) == dict(
        classification="INTERNAL"
    )


def script():
    import streamlit as st
    from src.streamlit_app.data_governance_workspace import render_source_governance

    render_source_governance(
        token="synthetic", shell=st.session_state["shell"], source_id=st.session_state["source_id"]
    )


def app(monkeypatch, permissions=("data.read", "data.governance.manage")):
    for name, value in [
        ("read_profile", PROFILE),
        ("list_retention_policies", []),
        ("list_quarantine", [ROW]),
        ("read_quarantine", DETAIL),
        ("update_profile", dict(id=IDS[2])),
        ("resolve_record", dict(id=IDS[3])),
    ]:
        monkeypatch.setattr(api, name, Mock(return_value=value))
    at = AppTest.from_function(script)
    at.session_state["shell"] = dict(
        organization=dict(id=IDS[0]),
        workspace=dict(id=IDS[1]),
        product=dict(code="SIMPA", permission_codes=permissions),
    )
    at.session_state["source_id"] = IDS[2]
    at.run()
    assert not at.exception
    return at


def click(at, label):
    next(x for x in at.button if x.label == label).click().run()
    assert not at.exception


def load(at):
    click(at, "Učitaj / osveži governance profil")


def test_permission_and_explicit_reads(monkeypatch):
    at = app(monkeypatch, permissions=())
    assert not at.button
    api.read_profile.assert_not_called()
    at = app(monkeypatch)
    api.read_profile.assert_not_called()
    load(at)
    api.read_profile.assert_called_once_with("synthetic", source_id=IDS[2], scope=SCOPE)


def test_readonly_no_quarantine_or_forms(monkeypatch):
    at = app(monkeypatch, permissions=("data.read",))
    load(at)
    assert not at.checkbox and not at.text_input
    api.list_quarantine.assert_not_called()
    assert not any("karantin" in x.label.lower() for x in at.button)


def test_confirmed_changed_fields_only(monkeypatch):
    at = app(monkeypatch)
    load(at)
    next(x for x in at.selectbox if x.label == "Klasifikacija").set_value("INTERNAL")
    click(at, "Sačuvaj governance profil")
    api.update_profile.assert_not_called()
    next(x for x in at.checkbox if x.label == "Potvrđujem governance promene i njihovo obrazloženje").check()
    click(at, "Sačuvaj governance profil")
    api.update_profile.assert_called_once_with(
        "synthetic", source_id=IDS[2], scope=SCOPE, revision=1, fields=dict(classification="INTERNAL")
    )


def test_revision_refresh_clears_confirmation(monkeypatch):
    at = app(monkeypatch)
    load(at)
    next(x for x in at.checkbox).check().run()
    api.read_profile.return_value = {**PROFILE, "revision": 2}
    load(at)
    assert not at.checkbox[0].value


def test_detail_required_then_confirmed_pin(monkeypatch):
    at = app(monkeypatch)
    load(at)
    click(at, "Učitaj karantin izvora")
    assert not any(x.label == "Registruj odluku o zapisu" for x in at.button)
    click(at, "Učitaj zapis i aktuelni prihvaćeni zapis")
    click(at, "Registruj odluku o zapisu")
    api.resolve_record.assert_not_called()
    next(x for x in at.text_input if x.label == "Referenca pregleda odluke").set_value("synthetic-review")
    next(x for x in at.checkbox if x.label == "Potvrđujem ljudski pregled identiteta, sadržaja i odluke").check()
    click(at, "Registruj odluku o zapisu")
    api.resolve_record.assert_called_once_with(
        "synthetic",
        source_id=IDS[2],
        scope=SCOPE,
        record_id=ROW["id"],
        fields=dict(
            decision="REJECT_INCOMING",
            resolution_reference="synthetic-review",
            reason=None,
            expected_current_accepted_record_id=IDS[4],
        ),
    )


def test_detail_refresh_clears_record_approval(monkeypatch):
    at = app(monkeypatch)
    load(at)
    click(at, "Učitaj karantin izvora")
    click(at, "Učitaj zapis i aktuelni prihvaćeni zapis")
    next(x for x in at.checkbox if x.label == "Potvrđujem ljudski pregled identiteta, sadržaja i odluke").check().run()
    click(at, "Učitaj zapis i aktuelni prihvaćeni zapis")
    assert not next(
        x for x in at.checkbox if x.label == "Potvrđujem ljudski pregled identiteta, sadržaja i odluke"
    ).value


def test_failed_profile_refresh_removes_forms(monkeypatch):
    from src.streamlit_app.api_client import ApiUnavailable

    at = app(monkeypatch)
    load(at)
    api.read_profile.side_effect = ApiUnavailable("Nedostupno")
    load(at)
    assert at.error and not at.checkbox


@pytest.mark.parametrize("mode", ["correct", "stale", "explicit_absence", "legacy_omission"])
def test_backend_record_review_guard(tmp_path, mode):
    from tests.test_isi_22d_record_governance import _build_case, _create_and_activate_policy, _create_run
    from src.platform.data.ingestion import StructuredRecord
    from src.platform.data.record_governance_service import (
        materialize_ingestion_run_records,
        list_record_quarantine,
        get_record_quarantine_detail,
        resolve_quarantined_record,
    )
    from src.platform.data.schemas import RecordResolutionCreate
    from src.platform.data.service import DataPlatformError

    case = _build_case(tmp_path)
    _create_and_activate_policy(case)
    run = _create_run(case, b"synthetic", key="synthetic-review-guard")
    materialize_ingestion_run_records(
        case["db"],
        run=run,
        records=(
            StructuredRecord(1, "r:1", {"external_id": "1", "name": "synthetic-a"}),
            StructuredRecord(2, "r:2", {"external_id": "1", "name": "synthetic-b"}),
        ),
    )
    scope = dict(organization_id=case["organization"].id, workspace_id=case["workspace"].id, product_code="SIMPA")
    row = list_record_quarantine(case["db"], source_id=case["source"].id, **scope)[0]
    detail = get_record_quarantine_detail(case["db"], source_id=case["source"].id, record_id=row.id, **scope)
    extra = (
        {}
        if mode == "legacy_omission"
        else dict(
            expected_current_accepted_record_id=detail.current_accepted_record_id
            if mode == "correct"
            else uuid.uuid4()
            if mode == "stale"
            else None
        )
    )
    payload = RecordResolutionCreate(
        **scope, decision="ACCEPT_INCOMING", resolution_reference="synthetic-review", **extra
    )

    def resolve():
        return resolve_quarantined_record(
            case["db"], source_id=case["source"].id, record_id=row.id, payload=payload, actor_id=case["membership"].id
        )

    if mode in {"stale", "explicit_absence"}:
        with pytest.raises(DataPlatformError, match="record_resolution_state_conflict"):
            resolve()
        assert list_record_quarantine(case["db"], source_id=case["source"].id, **scope)[0].id == row.id
    else:
        assert resolve().decision == "ACCEPT_INCOMING"
