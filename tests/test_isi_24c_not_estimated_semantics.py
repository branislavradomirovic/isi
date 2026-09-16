import uuid
from datetime import date
from types import SimpleNamespace

import pytest

from src.domains.ordo.analytics_models import OrdoForecastRun, OrdoScenarioAssessment
from src.domains.ordo.analytics_service import (
    OrdoAnalyticsError,
    _extract_forecast_series,
    _scenario_assessment_payload,
)
from src.domains.ordo.forecasting import ForecastNotEstimated, INTERVAL_METHOD
from src.domains.ordo.time_series_contracts import OrdoTimeSeriesSpecV1


REASONS = {
    "EXECUTABLE_FAMILY_NOT_DEFINED_24C", "TRANSFORMATION_EXECUTION_NOT_DEFINED_24C",
    "SERIES_EVIDENCE_NOT_FOUND", "DUPLICATE_TIME_INDEX", "INVALID_SERIES_VALUE",
    "IRREGULAR_OR_MISSING_PERIODS", "INSUFFICIENT_HISTORY", "INSUFFICIENT_ROLLING_ORIGINS",
    "SEASONAL_PERIOD_REQUIRED", "SEASONAL_HISTORY_INSUFFICIENT",
    "INSUFFICIENT_INTERVAL_CALIBRATION", "REQUIRED_BACKTEST_METRIC_UNAVAILABLE",
}


def test_runtime_models_preserve_not_estimated_and_no_forecast_boundaries():
    forecast_checks = " ".join(str(item.sqltext) for item in OrdoForecastRun.__table__.constraints if hasattr(item, "sqltext"))
    scenario_checks = " ".join(str(item.sqltext) for item in OrdoScenarioAssessment.__table__.constraints if hasattr(item, "sqltext"))
    assert "ESTIMATED" in forecast_checks and "NOT_ESTIMATED" in forecast_checks
    assert "automatic_model_selection = false" in forecast_checks
    assert "forecast_performed = false" in scenario_checks
    assert "LEGACY_NOT_EVALUATED" in scenario_checks and "NO_APPROVED_RESPONSE_MODEL" in scenario_checks
    assert INTERVAL_METHOD == "rolling_origin_empirical_residual_quantile_v1"


def test_all_stable_reason_codes_are_implemented():
    source = __import__("inspect").getsource(__import__("src.domains.ordo.analytics_service", fromlist=["execute_forecast"]))
    engine = __import__("pathlib").Path("src/domains/ordo/forecasting.py").read_text()
    service = __import__("pathlib").Path("src/domains/ordo/analytics_service.py").read_text()
    assert source
    assert all(reason in engine + service for reason in REASONS)


def _spec():
    return OrdoTimeSeriesSpecV1.model_validate({
        "series_key": "arrivals", "target_indicator_code": "arrivals",
        "target_methodology_id": uuid.UUID(int=1), "target_methodology_version": 1,
        "target_methodology_fingerprint": "a" * 64, "target_semantic": "continuous",
        "time_index_field": "period", "frequency": "monthly", "series_key_fields": ["destination"],
        "observation_window_start": date(2024, 1, 1), "observation_window_end": date(2024, 4, 1),
        "observation_as_of": date(2024, 4, 1), "minimum_history_periods": 4,
        "maximum_missing_ratio": 0, "missing_data_rule": "fail", "outlier_policy": "Review.",
        "revision_policy": "Version.", "comparability_policy": "Stable.", "transformation": "none",
        "trend_requirement": "none", "candidate_families": ["naive"], "horizon": 1,
        "horizon_unit": "months", "uncertainty_output_required": True,
        "diagnostic_requirements": ["residuals"], "limitations": ["non-causal"],
        "temporal_validation": {"initial_train_periods": 3, "step_size": 1, "horizon": 1,
                                "minimum_origins": 2, "required_metrics": ["MAE"]},
    })


def _input(rows):
    keys = ("indicator_code", "quality_status", "value_numeric", "period", "destination")
    return SimpleNamespace(
        field_contract=tuple({"field_key": key} for key in keys),
        records=tuple(SimpleNamespace(payload=row) for row in rows),
    )


def test_governed_series_extraction_fails_closed_for_identity_and_periods():
    rows = [
        {"indicator_code": "arrivals", "quality_status": "validated", "value_numeric": index,
         "period": f"2024-0{index}-01", "destination": "A"}
        for index in range(1, 5)
    ]
    dates, values = _extract_forecast_series(_input(rows), _spec(), {"destination": "A"})
    assert dates[-1] == date(2024, 4, 1) and values == [1.0, 2.0, 3.0, 4.0]
    with pytest.raises(OrdoAnalyticsError, match="forecast_series_identity_invalid"):
        _extract_forecast_series(_input(rows), _spec(), {})
    with pytest.raises(ForecastNotEstimated, match="DUPLICATE_TIME_INDEX"):
        _extract_forecast_series(_input(rows + [rows[-1]]), _spec(), {"destination": "A"})
    with pytest.raises(ForecastNotEstimated, match="IRREGULAR_OR_MISSING_PERIODS"):
        _extract_forecast_series(_input(rows[:2] + rows[3:]), _spec(), {"destination": "A"})


def test_new_scenario_payload_explicitly_reports_impact_not_estimated():
    scenario = SimpleNamespace(name="Scenario", assumptions=["A"], measures=["M"])
    goal = SimpleNamespace(code="G", title="Goal", focus_area="custom", target_horizon=None)
    run = SimpleNamespace(
        snapshot={}, analytical_artifact_fingerprint="", dataset_contract_fingerprint=""
    )
    payload = _scenario_assessment_payload(scenario=scenario, goal=goal, run=run)
    assert payload["forecast_performed"] is False
    assert payload["impact"] == "NOT_ESTIMATED"
    assert payload["impact_estimation_reason_code"] == "NO_APPROVED_RESPONSE_MODEL"
