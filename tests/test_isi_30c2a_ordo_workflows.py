from types import SimpleNamespace
from unittest.mock import Mock
import uuid

import pytest
from streamlit.testing.v1 import AppTest

from src.streamlit_app import ordo_methodology_api as api, ordo_methodology_workspace as ui
from src.streamlit_app import ordo_analytics_api as forecast
from tests.test_isi_24e_forecast_workflow_api import _authoring_payload

IDS = [str(uuid.UUID(int=i)) for i in range(1, 7)]
SCOPE = dict(organization_id=IDS[0], workspace_id=IDS[1])
METHOD = dict(
    id=IDS[2],
    indicator_code="synthetic",
    version_no=1,
    status="proposed",
    computation_type="direct_observation",
    methodology_note="Synthetic only",
    source_requirements={"spatial_aggregation": {"aggregation_rule": "mean"}},
)
SPEC = dict(
    id=IDS[3],
    status="validated",
    series_key="synthetic",
    version_no=1,
    target_indicator_code="synthetic",
    contract_json={"candidate_families": ["naive"]},
    contract_fingerprint="a" * 64,
)


def request_mock(monkeypatch, module):
    req = Mock(return_value=SimpleNamespace(status_code=200, json=lambda: {"id": IDS[5]}))
    monkeypatch.setattr(module, "request", req)
    return req


@pytest.mark.parametrize("rule", [None, "count", "sum", "mean", "min", "max"])
def test_method_explicit_spatial_metadata(monkeypatch, rule):
    req = request_mock(monkeypatch, api)
    api.create_methodology(
        "synthetic", scope=SCOPE, indicator_code="synthetic", note="Synthetic only", spatial_rule=rule
    )
    payload = req.call_args.kwargs["json"]
    assert payload["organization_id"] == IDS[0] and payload["workspace_id"] == IDS[1]
    assert payload["computation_type"] == "direct_observation"
    if rule is None:
        assert payload["source_requirements"] == {}
    else:
        contract = payload["source_requirements"]["spatial_aggregation"]
        assert contract["aggregation_rule"] == rule and contract["non_causal"] and not contract["weighted"]
        assert not contract["spatial_join_performed"]


@pytest.mark.parametrize(
    "action,fields",
    [
        ("propose", {}),
        ("validate", {"validation_note": "Reviewed synthetic"}),
        ("retire", {"retirement_note": "Superseded"}),
    ],
)
def test_method_transition_scope_and_escape(monkeypatch, action, fields):
    req = request_mock(monkeypatch, api)
    api.transition("synthetic", scope=SCOPE, record_id="id/+", action=action, fields={**fields, "workspace_id": IDS[5]})
    assert req.call_args.args[1] == f"/api/v1/ordo/analytics/methodologies/id%2F%2B/{action}"
    assert req.call_args.kwargs["json"]["workspace_id"] == IDS[1]


def test_invalid_spatial_or_human_note_not_transmitted(monkeypatch):
    req = request_mock(monkeypatch, api)
    with pytest.raises(ValueError):
        api.create_methodology(
            "synthetic", scope=SCOPE, indicator_code="synthetic", note="Synthetic", spatial_rule="weighted"
        )
    with pytest.raises(ValueError):
        api.transition(
            "synthetic", scope=SCOPE, record_id=IDS[2], action="validate", fields={"validation_note": "short"}
        )
    req.assert_not_called()


def test_spec_locks_resolved_scope_and_preserves_authored_values(monkeypatch):
    req = request_mock(monkeypatch, forecast)
    forecast.create_time_series_spec("synthetic", **SCOPE, spec=_authoring_payload())
    body = req.call_args.kwargs["json"]
    assert body["organization_id"] == IDS[0] and body["workspace_id"] == IDS[1]
    assert body["minimum_history_periods"] == 10 and body["maximum_missing_ratio"] == 0


@pytest.mark.parametrize(
    "field",
    [
        "minimum_history_periods",
        "maximum_missing_ratio",
        "horizon",
        "initial_train_periods",
        "step_size",
        "minimum_origins",
        "observation_window_start",
        "target_semantic",
    ],
)
def test_missing_explicit_parameter_never_transmits(monkeypatch, field):
    req = request_mock(monkeypatch, forecast)
    with pytest.raises(ValueError):
        forecast.create_time_series_spec("synthetic", **SCOPE, spec=_authoring_payload(**{field: None}))
    req.assert_not_called()


@pytest.mark.parametrize("family,interval", [("naive", None), (None, 0.9), ("champion", 0.9), ("naive", 0.99)])
def test_invalid_forecast_never_transmits(monkeypatch, family, interval):
    req = request_mock(monkeypatch, forecast)
    with pytest.raises(ValueError):
        forecast.execute_forecast(
            "synthetic",
            **SCOPE,
            time_series_spec_id=IDS[3],
            requested_family=family,
            interval_level=interval,
            series_identity={"destination": "qa"},
        )
    req.assert_not_called()


def button(at, label):
    return next(x for x in at.button if x.label == label)


def checkbox(at, label):
    return next(x for x in at.checkbox if x.label == label)


def method_app(monkeypatch, *, product="ORDO", permissions=None):
    monkeypatch.setattr(ui.ordo_api, "catalog", lambda *a, **kw: dict(indicators=[dict(code="synthetic", active=True)]))
    monkeypatch.setattr(ui.read_api, "methodologies", lambda *a, **kw: [METHOD])
    shell = dict(
        organization={"id": IDS[0]},
        workspace={"id": IDS[1]},
        product=dict(
            code=product,
            permission_codes=permissions if permissions is not None else ["analysis.read", "indicator.manage"],
        ),
    )
    return AppTest.from_string(
        "from src.streamlit_app.ordo_methodology_workspace import render_ordo_methodology\n"
        + f'render_ordo_methodology(token="synthetic",shell={shell!r})'
    ).run()


@pytest.mark.parametrize(
    "product,permissions",
    [("SIMPA", ["analysis.read", "indicator.manage"]), ("ORDO", ["analysis.read"]), ("ORDO", ["indicator.manage"])],
)
def test_method_hidden_outside_product_or_permission(monkeypatch, product, permissions):
    at = method_app(monkeypatch, product=product, permissions=permissions)
    assert not at.button and not at.exception


def test_method_confirmation_and_refresh_reset(monkeypatch):
    change = Mock(return_value={"id": IDS[2]})
    monkeypatch.setattr(api, "transition", change)
    at = method_app(monkeypatch)
    button(at, "Učitaj / osveži ORDO metodološki registar").click().run()
    assert any("Globalni ORDO" in x.value for x in at.warning)
    next(x for x in at.text_area if x.label == "Obrazloženje ljudskog ORDO odobrenja").set_value(
        "Reviewed synthetic"
    ).run()
    button(at, "Odobri ORDO VALIDATED").click().run()
    change.assert_not_called()
    checkbox(at, "Potvrđujem ORDO prelaz VALIDATE pregledane verzije").check().run()
    button(at, "Odobri ORDO VALIDATED").click().run()
    assert change.call_args.kwargs["record_id"] == IDS[2]
    button(at, "Učitaj / osveži ORDO metodološki registar").click().run()
    assert not checkbox(at, "Potvrđujem ORDO prelaz VALIDATE pregledane verzije").value
    assert not at.exception


def series_app(monkeypatch, *, permissions=None):
    monkeypatch.setattr(forecast, "time_series_specs", lambda *a, **kw: [SPEC])
    monkeypatch.setattr(forecast, "time_series_spec_detail", lambda *a, **kw: SPEC)
    monkeypatch.setattr(forecast, "time_series_identities", lambda *a, **kw: [{"destination": "qa"}])
    kwargs = dict(
        token="synthetic",
        **SCOPE,
        permissions=set(
            permissions if permissions is not None else ["analysis.read", "indicator.manage", "analysis.run"]
        ),
        runs=[dict(id=IDS[4], analytical_artifact_type="snapshot")],
    )
    return AppTest.from_string(
        "from src.streamlit_app.ordo_analytics_workspace import _render_time_series_workflow\n"
        + f"_render_time_series_workflow(**{kwargs!r})"
    ).run()


def test_numeric_dates_and_choices_have_no_unauthored_defaults(monkeypatch):
    at = series_app(monkeypatch)
    assert all(x.value is None for x in at.number_input)
    assert all(x.value is None for x in at.date_input)
    assert all(x.value == [] for x in at.multiselect)
    assert next(x for x in at.selectbox if x.label == "Eksplicitno zahtevana porodica").value is None
    assert next(x for x in at.selectbox if x.label == "Nivo intervala").value is None
    assert not at.exception


def test_forecast_explicit_choices_confirmation_and_refresh(monkeypatch):
    call = Mock(return_value=None)
    monkeypatch.setattr(forecast, "execute_forecast", call)
    at = series_app(monkeypatch)
    assert button(at, "Pokreni forecast").disabled
    next(x for x in at.selectbox if x.label == "Eksplicitno zahtevana porodica").select("naive").run()
    next(x for x in at.selectbox if x.label == "Nivo intervala").select(0.9).run()
    checkbox(at, "Potvrđujem izvršenje forecast-a iz pregledane specifikacije").check().run()
    assert not button(at, "Pokreni forecast").disabled
    button(at, "Pokreni forecast").click().run()
    assert call.call_args.kwargs["requested_family"] == "naive" and call.call_args.kwargs["series_identity"] == {
        "destination": "qa"
    }
    next(x for x in at.selectbox if x.label == "Nivo intervala").select(0.8).run()
    assert not checkbox(at, "Potvrđujem izvršenje forecast-a iz pregledane specifikacije").value
    button(at, "Osveži specifikacije i resetuj potvrde").click().run()
    assert not checkbox(at, "Potvrđujem izvršenje forecast-a iz pregledane specifikacije").value
    assert not at.exception


def test_readonly_series_has_no_mutation_controls(monkeypatch):
    at = series_app(monkeypatch, permissions=["analysis.read"])
    assert not any(
        x.label in ["Pokreni forecast", "Kreiraj DRAFT specifikaciju", "Povuci specifikaciju"] for x in at.button
    )
    assert not at.number_input and not at.exception


def test_draft_submit_requires_confirmation_and_missing_values_fail_before_http(monkeypatch):
    req = request_mock(monkeypatch, forecast)
    at = series_app(monkeypatch)
    button(at, "Kreiraj DRAFT specifikaciju").click().run()
    req.assert_not_called()
    checkbox(at, "Potvrđujem autorstvo time-series DRAFT parametara").check().run()
    button(at, "Kreiraj DRAFT specifikaciju").click().run()
    req.assert_not_called()
    assert any("Zahtev nije poslat" in x.value for x in at.error)
    assert not at.exception


def test_review_response_contains_authored_requirements(monkeypatch):
    from src.api import ordo_analytics_routes as routes

    scope_check = Mock()
    monkeypatch.setattr(routes, "_require_scope", scope_check)
    method = SimpleNamespace(
        **METHOD, proposed_at=None, validation_note=None, approved_at=None, retired_at=None, retirement_note=None
    )
    indicator = SimpleNamespace(code="synthetic", name_sr="Synthetic")
    monkeypatch.setattr(routes, "list_methodologies", lambda db: [(method, indicator)])
    rows = routes.get_methodologies(**SCOPE, context=object(), db=object())
    assert rows[0]["source_requirements"] == METHOD["source_requirements"]
    assert rows[0]["methodology_note"] == "Synthetic only"
    assert scope_check.call_args.kwargs["permission_code"] == "analysis.read"
