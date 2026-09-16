import uuid
from datetime import date

import pytest
from pydantic import ValidationError

from src.domains.ordo.analytics_models import OrdoTimeSeriesSpec
from src.domains.ordo.time_series_contracts import OrdoTimeSeriesSpecV1, contract_fingerprint


def _spec(**changes):
    value = {
        "series_key": "monthly-arrivals", "target_indicator_code": "arrivals",
        "target_methodology_id": uuid.UUID(int=1), "target_methodology_version": 2,
        "target_methodology_fingerprint": "b" * 64, "target_semantic": "count",
        "time_index_field": "period", "frequency": "monthly", "series_key_fields": ["destination"],
        "observation_window_start": date(2020, 1, 1), "observation_window_end": date(2025, 1, 1),
        "observation_as_of": date(2025, 2, 1), "minimum_history_periods": 36,
        "maximum_missing_ratio": 0.05, "missing_data_rule": "explicit_gap",
        "outlier_policy": "Flag for human review.", "revision_policy": "Version revisions.",
        "comparability_policy": "Require stable methodology.", "transformation": "none",
        "trend_requirement": "allowed", "seasonality_period": 12,
        "candidate_families": ["naive", "seasonal_naive", "count_time_series"],
        "horizon": 6, "horizon_unit": "months", "uncertainty_output_required": True,
        "diagnostic_requirements": ["residual review"], "limitations": ["Specification only."],
        "temporal_validation": {"backtest_strategy": "rolling_origin_plan_only", "initial_train_periods": 24, "step_size": 1, "horizon": 6, "minimum_origins": 3, "required_metrics": ["MAE", "RMSE", "interval_coverage", "seasonal_baseline_comparison"]},
        "forecast_execution": False, "automatic_model_selection": False, "non_causal": True,
    }
    value.update(changes); return value


def test_time_series_is_plan_only_and_fingerprinted():
    spec = OrdoTimeSeriesSpecV1.model_validate(_spec())
    assert spec.temporal_validation.backtest_strategy == "rolling_origin_plan_only"
    assert not spec.forecast_execution and not spec.automatic_model_selection and spec.non_causal
    assert len(contract_fingerprint(spec)) == 64
    for change in ({"forecast_execution": True}, {"automatic_model_selection": True}, {"frequency": "hourly"}):
        with pytest.raises(ValidationError):
            OrdoTimeSeriesSpecV1.model_validate(_spec(**change))


def test_time_series_target_family_and_backtest_plan_validation():
    with pytest.raises(ValidationError):
        OrdoTimeSeriesSpecV1.model_validate(_spec(candidate_families=["naive"]))
    broken = _spec(); broken["temporal_validation"] = {**broken["temporal_validation"], "backtest_strategy": "executed"}
    with pytest.raises(ValidationError):
        OrdoTimeSeriesSpecV1.model_validate(broken)
    for name in ("analytics_run_id", "methodology_fingerprint", "input_snapshot_sha256", "forecast_execution", "automatic_model_selection"):
        assert name in OrdoTimeSeriesSpec.__table__.columns
