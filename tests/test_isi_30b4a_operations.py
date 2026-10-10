from types import SimpleNamespace
from unittest.mock import Mock
import uuid

import pytest
from pydantic import ValidationError
from streamlit.testing.v1 import AppTest

from src.streamlit_app import data_operations_api as api
from src.streamlit_app import data_ingestion_api as contracts_api
from src.streamlit_app.data_operations_workspace import replay_candidates

IDS = [str(uuid.UUID(int=i)) for i in range(1, 9)]
SCOPE = dict(organization_id=IDS[0], workspace_id=IDS[1], product_code="SIMPA")
RUN = dict(id=IDS[2], run_no=1, status="SUCCEEDED", operational_policy_version_id=IDS[3])
POLICY = dict(id=IDS[3], lifecycle_state="ACTIVE", backfill_contract=dict(replay_allowed=True, backfill_allowed=False))
DEAD = dict(id=IDS[4], status="OPEN", reason_code="synthetic", ingestion_run_id=IDS[2])


@pytest.mark.parametrize(
    "value,expected",
    [
        ("", None),
        ("  ", None),
        ("2026-10-10T12:00:00+02:00", "2026-10-10T10:00:00+00:00"),
        ("2026-10-10T10:00:00Z", "2026-10-10T10:00:00+00:00"),
    ],
)
def test_observation_time(value, expected):
    assert api.observed_time(value) == expected


@pytest.mark.parametrize("value", ["yesterday", "2026-10-10", "2026-10-10T10:00:00"])
def test_missing_offset_not_fabricated(value):
    with pytest.raises(ValueError):
        api.observed_time(value)


@pytest.mark.parametrize(
    "operation,fields",
    [
        ("replay", dict(idempotency_key="synthetic")),
        ("requeue", dict(idempotency_key="synthetic")),
        ("resolve", dict(status="DISCARDED", resolution_note="Synthetic review")),
    ],
)
@pytest.mark.parametrize("product", ["SIMPA", "ORDO"])
def test_scope_and_path(monkeypatch, operation, fields, product):
    req = Mock(return_value=SimpleNamespace(status_code=200, json=lambda: {}))
    monkeypatch.setattr(api, "request", req)
    scope = {**SCOPE, "product_code": product}
    api.recover(
        "synthetic",
        source_id="s/+",
        artifact_id="r/+",
        operation=operation,
        scope=scope,
        fields={**fields, "workspace_id": IDS[7], "product_code": "ORDO"},
    )
    assert "/s%2F%2B/" in req.call_args.args[1] and "/r%2F%2B/" in req.call_args.args[1]
    assert req.call_args.kwargs["json"] == {**fields, **scope}


@pytest.mark.parametrize("operation", ["replay", "requeue", "resolve", "backfill"])
def test_invalid_payload_no_http(monkeypatch, operation):
    req = Mock()
    monkeypatch.setattr(api, "request", req)
    with pytest.raises(ValidationError):
        api.recover("synthetic", source_id=IDS[5], artifact_id=IDS[2], operation=operation, scope=SCOPE, fields={})
    req.assert_not_called()


@pytest.mark.parametrize(
    "state,allowed",
    [("SUCCEEDED", True), ("FAILED", True), ("CANCELLED", False), ("RUNNING", False), ("QUEUED", False)],
)
def test_terminal_replay_filter(state, allowed):
    assert bool(replay_candidates([{**RUN, "status": state}], [POLICY])) == allowed


def test_policy_required_and_historical_policy_allowed():
    assert not replay_candidates([RUN], [])
    assert not replay_candidates([RUN], [{**POLICY, "backfill_contract": dict(replay_allowed=False)}])
    assert replay_candidates([RUN], [{**POLICY, "lifecycle_state": "RETIRED"}])


def script():
    import streamlit as st
    from src.streamlit_app.data_operations_workspace import render_ingestion_operations

    render_ingestion_operations(
        token="synthetic",
        shell=st.session_state["shell"],
        source_id=st.session_state["source_id"],
        runs=st.session_state["runs"],
    )


def app(monkeypatch, permissions=("data.read", "data.upload", "data.governance.manage")):
    monkeypatch.setattr(
        contracts_api,
        "list_contracts",
        Mock(side_effect=lambda token, resource, **kw: [POLICY] if resource == "operations" else []),
    )
    monkeypatch.setattr(api, "list_dead_letters", Mock(return_value=[DEAD]))
    monkeypatch.setattr(api, "recover", Mock(return_value=dict(id=IDS[4])))
    at = AppTest.from_function(script)
    at.session_state["shell"] = dict(
        organization=dict(id=IDS[0]),
        workspace=dict(id=IDS[1]),
        product=dict(code="SIMPA", permission_codes=permissions),
    )
    at.session_state["source_id"] = IDS[5]
    at.session_state["runs"] = [RUN]
    at.run()
    assert not at.exception
    return at


def load(at):
    next(x for x in at.button if x.label == "Učitaj / osveži operativni pregled").click().run()
    assert not at.exception


def test_explicit_read_and_no_permission(monkeypatch):
    at = app(monkeypatch)
    api.list_dead_letters.assert_not_called()
    load(at)
    api.list_dead_letters.assert_called_once_with("synthetic", source_id=IDS[5], scope=SCOPE)
    at = app(monkeypatch, permissions=())
    assert not at.button
    api.list_dead_letters.assert_not_called()


def test_readonly_hides_mutations(monkeypatch):
    at = app(monkeypatch, permissions=("data.read",))
    load(at)
    assert not at.checkbox and not at.text_input
    assert [x.label for x in at.button] == ["Učitaj / osveži operativni pregled"]


def test_replay_confirmation_and_pinned_id(monkeypatch):
    at = app(monkeypatch)
    load(at)
    next(x for x in at.button if x.label == "Pokreni replay").click().run()
    api.recover.assert_not_called()
    next(x for x in at.text_input if x.label == "Replay idempotency ključ").set_value("synthetic-replay")
    next(x for x in at.checkbox if x.label == "Potvrđujem replay izabrane obrade").check()
    next(x for x in at.button if x.label == "Pokreni replay").click().run()
    api.recover.assert_called_once_with(
        "synthetic",
        source_id=IDS[5],
        scope=SCOPE,
        operation="replay",
        artifact_id=RUN["id"],
        fields=dict(idempotency_key="synthetic-replay"),
    )


def test_refresh_clears_approval(monkeypatch):
    at = app(monkeypatch)
    load(at)
    next(x for x in at.checkbox if x.label == "Potvrđujem replay izabrane obrade").check().run()
    load(at)
    assert not next(x for x in at.checkbox if x.label == "Potvrđujem replay izabrane obrade").value


def test_dead_letter_permission_separate_from_upload(monkeypatch):
    at = app(monkeypatch, permissions=("data.read", "data.upload"))
    load(at)
    assert not any(x.label == "Vrati stavku u obradu" for x in at.button)
    assert any(x.label == "Pokreni replay" for x in at.button)


def test_confirmed_dead_letter_resolution(monkeypatch):
    at = app(monkeypatch)
    load(at)
    next(x for x in at.text_area if x.label == "Obrazloženje zatvaranja").set_value("Synthetic review")
    next(x for x in at.checkbox if x.label == "Potvrđujem ishod pregleda i obrazloženje").check()
    next(x for x in at.button if x.label == "Zatvori dead-letter stavku").click().run()
    api.recover.assert_called_once_with(
        "synthetic",
        source_id=IDS[5],
        scope=SCOPE,
        operation="resolve",
        artifact_id=DEAD["id"],
        fields=dict(status="RESOLVED", resolution_note="Synthetic review"),
    )


def test_missing_backfill_chain_no_upload(monkeypatch):
    at = app(monkeypatch)
    load(at)
    assert not at.file_uploader
    assert any("aktivan usaglašen lanac" in x.value for x in at.caption)


def test_backfill_payload_pins_window_and_contracts(monkeypatch):
    req = Mock(return_value=SimpleNamespace(status_code=201, json=lambda: {}))
    monkeypatch.setattr(api, "request", req)
    fields = dict(
        connector_contract_version_id=IDS[2],
        schema_mapping_version_id=IDS[3],
        idempotency_key="synthetic-backfill",
        filename="synthetic.csv",
        content_type="text/csv",
        content_base64="YQ==",
        source_observed_at=api.observed_time("2026-10-10T12:00:00Z"),
        window_start_cursor="a",
        window_end_cursor="b",
    )
    api.recover("synthetic", source_id=IDS[5], operation="backfill", scope=SCOPE, fields=fields)
    payload = req.call_args.kwargs["json"]
    assert payload["window_start_cursor"] == "a" and payload["window_end_cursor"] == "b"
    assert payload["connector_contract_version_id"] == IDS[2]
    assert payload["source_observed_at"] == "2026-10-10T12:00:00Z"


def test_requeue_requires_confirmation(monkeypatch):
    at = app(monkeypatch)
    load(at)
    next(x for x in at.button if x.label == "Vrati stavku u obradu").click().run()
    api.recover.assert_not_called()
    next(x for x in at.text_input if x.label == "Requeue idempotency ključ").set_value("synthetic-requeue")
    next(x for x in at.checkbox if x.label == "Potvrđujem kontrolisani replay dead-letter stavke").check()
    next(x for x in at.button if x.label == "Vrati stavku u obradu").click().run()
    api.recover.assert_called_once_with(
        "synthetic",
        source_id=IDS[5],
        scope=SCOPE,
        operation="requeue",
        artifact_id=DEAD["id"],
        fields=dict(idempotency_key="synthetic-requeue"),
    )


def test_failed_refresh_removes_cached_forms(monkeypatch):
    from src.streamlit_app.api_client import ApiUnavailable

    at = app(monkeypatch)
    load(at)
    api.list_dead_letters.side_effect = ApiUnavailable("Nedostupno")
    load(at)
    assert at.error and not at.checkbox
    api.recover.assert_not_called()
