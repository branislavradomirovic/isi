from __future__ import annotations

import inspect
import uuid
from datetime import date

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import src.platform.models  # noqa: F401
from src.api.ordo_analytics_routes import router
from src.core.database import Base
from src.domains.ordo import analytics_service
from src.domains.ordo.analytics_models import OrdoTimeSeriesSpec
from src.domains.ordo.analytics_schemas import TimeSeriesSpecCreateRequest
from src.domains.ordo.analytics_service import OrdoAnalyticsError, get_time_series_spec
from src.domains.ordo.time_series_contracts import OrdoTimeSeriesSpecV1
from src.platform.access.models import Product
from src.platform.data.analytical_service import GovernedAnalyticalInput, GovernedAnalyticalRecord
from src.platform.identity.models import Organization
from src.platform.workspaces.models import Workspace


def _authoring_payload(**changes):
    value = {
        "organization_id": uuid.uuid4(), "workspace_id": uuid.uuid4(),
        "analytics_run_id": uuid.uuid4(), "series_key": "destination-demand",
        "target_indicator_code": "arrivals", "target_semantic": "continuous",
        "time_index_field": "observed_at", "frequency": "monthly",
        "series_key_fields": ["destination"],
        "observation_window_start": date(2025, 1, 1),
        "observation_window_end": date(2025, 12, 1), "observation_as_of": date(2025, 12, 31),
        "minimum_history_periods": 10, "maximum_missing_ratio": 0,
        "missing_data_rule": "fail", "outlier_policy": "Review explicit outliers.",
        "revision_policy": "Create a new governed input.",
        "comparability_policy": "Require stable methodology.", "transformation": "none",
        "trend_requirement": "allowed", "seasonality_period": None,
        "candidate_families": ["naive"], "horizon": 1, "horizon_unit": "months",
        "diagnostic_requirements": ["rolling-origin diagnostics"],
        "limitations": ["No causal interpretation."], "initial_train_periods": 8,
        "step_size": 1, "minimum_origins": 2, "required_metrics": ["MAE"],
    }
    value.update(changes)
    return value


def test_time_series_and_forecast_routes_are_complete_and_preserved():
    paths = {(route.path, method) for route in router.routes for method in route.methods}
    expected = {
        ("/api/v1/ordo/analytics/time-series-specs", "GET"),
        ("/api/v1/ordo/analytics/time-series-specs/{time_series_spec_id}", "GET"),
        ("/api/v1/ordo/analytics/time-series-specs", "POST"),
        ("/api/v1/ordo/analytics/time-series-specs/{time_series_spec_id}/propose", "POST"),
        ("/api/v1/ordo/analytics/time-series-specs/{time_series_spec_id}/validate", "POST"),
        ("/api/v1/ordo/analytics/time-series-specs/{time_series_spec_id}/retire", "POST"),
        ("/api/v1/ordo/analytics/time-series-specs/{time_series_spec_id}/series-identities", "GET"),
        ("/api/v1/ordo/analytics/forecasts", "POST"),
        ("/api/v1/ordo/analytics/forecasts", "GET"),
        ("/api/v1/ordo/analytics/forecasts/{forecast_run_id}", "GET"),
    }
    assert expected <= paths


def test_authoring_request_is_strict_and_server_authority_fields_are_not_customer_input():
    request = TimeSeriesSpecCreateRequest.model_validate(_authoring_payload())
    assert request.target_indicator_code == "arrivals"
    fields = TimeSeriesSpecCreateRequest.model_fields
    for forbidden in (
        "target_methodology_id", "target_methodology_version", "target_methodology_fingerprint",
        "forecast_execution", "automatic_model_selection", "non_causal",
    ):
        assert forbidden not in fields
        with pytest.raises(ValidationError):
            TimeSeriesSpecCreateRequest.model_validate(_authoring_payload(**{forbidden: True}))
    source = inspect.getsource(analytics_service.author_time_series_spec)
    for authority in (
        '"target_methodology_id": methodology.id',
        '"target_methodology_version": methodology.version_no',
        '"target_methodology_fingerprint": _methodology_fingerprint(methodology)',
        '"forecast_execution": False', '"automatic_model_selection": False', '"non_causal": True',
    ):
        assert authority in source


def test_spec_lookup_is_exact_scope_and_cross_scope_fails_closed():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        product = Product(code="ORDO", name="ORDO")
        first_org = Organization(slug=f"org-{uuid.uuid4().hex}", name="First")
        second_org = Organization(slug=f"org-{uuid.uuid4().hex}", name="Second")
        db.add_all([product, first_org, second_org])
        db.flush()
        first_workspace = Workspace(
            organization_id=first_org.id, product_code="ORDO", slug="first", name="First"
        )
        second_workspace = Workspace(
            organization_id=second_org.id, product_code="ORDO", slug="second", name="Second"
        )
        db.add_all([first_workspace, second_workspace])
        db.flush()
        row = OrdoTimeSeriesSpec(
            organization_id=first_org.id, workspace_id=first_workspace.id,
            analytics_run_id=uuid.uuid4(), target_indicator_id=uuid.uuid4(),
            target_methodology_id=uuid.uuid4(), target_methodology_version=1,
            methodology_fingerprint="a" * 64, input_snapshot_sha256="b" * 64,
            series_key="demand", version_no=1, schema_version="ORDO-TIME-SERIES-SPEC-v1",
            target_semantic="continuous", frequency="monthly", transformation="none",
            contract_json={}, contract_fingerprint="c" * 64,
        )
        db.add(row)
        db.flush()
        assert get_time_series_spec(
            db, time_series_spec_id=row.id,
            organization_id=first_org.id, workspace_id=first_workspace.id,
        ).id == row.id
        with pytest.raises(OrdoAnalyticsError, match="time_series_spec_not_found"):
            get_time_series_spec(
                db, time_series_spec_id=row.id,
                organization_id=second_org.id, workspace_id=second_workspace.id,
            )


def test_series_identity_discovery_returns_only_unique_keys_in_deterministic_order(monkeypatch):
    spec = OrdoTimeSeriesSpecV1.model_validate({
        **{key: value for key, value in _authoring_payload().items() if key not in {
            "organization_id", "workspace_id", "analytics_run_id", "initial_train_periods",
            "step_size", "minimum_origins", "required_metrics",
        }},
        "target_methodology_id": uuid.uuid4(), "target_methodology_version": 1,
        "target_methodology_fingerprint": "a" * 64, "uncertainty_output_required": True,
        "temporal_validation": {
            "backtest_strategy": "rolling_origin_plan_only", "initial_train_periods": 8,
            "step_size": 1, "horizon": 1, "minimum_origins": 2, "required_metrics": ["MAE"],
        },
        "forecast_execution": False, "automatic_model_selection": False, "non_causal": True,
    })

    def record(payload):
        return GovernedAnalyticalRecord(
            governed_output_id=uuid.uuid4(), normalized_record_id=uuid.uuid4(),
            source_id=uuid.uuid4(), source_version_id=uuid.uuid4(), ingestion_run_id=uuid.uuid4(),
            identity_fingerprint=uuid.uuid4().hex, content_fingerprint=uuid.uuid4().hex,
            source_record_ordinal=1, source_locator="fixture", payload=payload,
        )

    governed = GovernedAnalyticalInput(
        artifact_type="snapshot", artifact_id=uuid.uuid4(), artifact_fingerprint="a" * 64,
        dataset_contract_version_id=uuid.uuid4(), dataset_contract_fingerprint="b" * 64,
        analytical_quality_state="ACCEPTED_CLEAN", snapshot_id=uuid.uuid4(),
        snapshot_fingerprint="c" * 64,
        field_contract=tuple({"field_key": key} for key in (
            "indicator_code", "quality_status", "value_numeric", "observed_at", "destination"
        )),
        records=(
            record({"indicator_code": "arrivals", "quality_status": "validated", "value_numeric": 2, "observed_at": "2025-02-01", "destination": "B", "raw": "secret"}),
            record({"indicator_code": "arrivals", "quality_status": "validated", "value_numeric": 3, "observed_at": "2025-03-01", "destination": "A"}),
            record({"indicator_code": "arrivals", "quality_status": "validated", "value_numeric": 4, "observed_at": "2025-04-01", "destination": "B"}),
            record({"indicator_code": "arrivals", "quality_status": "draft", "value_numeric": 5, "observed_at": "2025-05-01", "destination": "C"}),
        ),
    )
    monkeypatch.setattr(analytics_service, "_forecast_binding", lambda *args, **kwargs: (object(), spec, object(), governed))
    identities = analytics_service.list_time_series_identities(
        object(), time_series_spec_id=uuid.uuid4(),
        organization_id=uuid.uuid4(), workspace_id=uuid.uuid4(),
    )
    assert identities == [{"destination": "A"}, {"destination": "B"}]
    assert all(set(item) == {"destination"} for item in identities)


def test_frozen_permission_and_execution_semantics_remain_explicit():
    routes_source = inspect.getsource(__import__("src.api.ordo_analytics_routes", fromlist=["router"]))
    assert 'permission_code="analysis.read"' in routes_source
    assert 'permission_code="indicator.manage"' in routes_source
    assert 'permission_code="analysis.run"' in routes_source
    assert "analysis.review" not in routes_source
    runtime = inspect.getsource(analytics_service.execute_forecast)
    assert 'requested_family not in spec.candidate_families' in runtime
    assert 'time_series_spec_not_validated' in inspect.getsource(analytics_service._forecast_binding)
    assert 'requested_family not in {"naive", "seasonal_naive"}' in runtime
    assert "fallback" not in runtime.casefold()


def test_lifecycle_routes_prove_payload_scope_before_existing_mutation_service():
    routes_module = __import__("src.api.ordo_analytics_routes", fromlist=["router"])
    for handler_name, mutation_name in (
        ("post_propose_time_series_spec", "propose_time_series_spec"),
        ("post_validate_time_series_spec", "validate_time_series_spec"),
        ("post_retire_time_series_spec", "retire_time_series_spec"),
    ):
        source = inspect.getsource(getattr(routes_module, handler_name))
        assert source.index("get_time_series_spec(") < source.index(f"row = {mutation_name}(")
        assert "organization_id=payload.organization_id" in source
        assert "workspace_id=payload.workspace_id" in source
