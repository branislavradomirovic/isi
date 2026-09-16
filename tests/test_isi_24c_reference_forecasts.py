import uuid
from datetime import date, timedelta

import pytest

from src.domains.ordo.forecast_metrics import aggregate_point_metrics, mase, smape
from src.domains.ordo.analytics_service import _canonical_sha256, _forecast_result_data
from src.domains.ordo.forecasting import naive_forecast, run_rolling_origin
from src.domains.ordo.time_series_contracts import OrdoTimeSeriesSpecV1


def test_reference_forecast_and_exact_metric_definitions():
    forecast = naive_forecast([10, 12, 14], 2)
    assert forecast == [14, 14]
    metrics = aggregate_point_metrics([15, 17], forecast)
    assert metrics["MAE"] == 2
    assert metrics["RMSE"] == pytest.approx(5 ** 0.5)
    assert metrics["bias"] == -2
    assert smape([0], [0]) == 0
    assert mase([15, 17], forecast, [10, 12, 14], 1) == 1


def test_reference_backtest_does_not_consume_future_values():
    records = run_rolling_origin(
        [1, 2, 3, 100, 200, 300], family="naive",
        initial_train_periods=3, step_size=1, horizon=1, minimum_origins=3,
    )
    assert [row["forecast"] for row in records] == [[3.0], [100.0], [200.0]]


def test_canonical_fingerprints_are_order_independent():
    assert _canonical_sha256({"a": 1, "b": {"x": 2}}) == _canonical_sha256({"b": {"x": 2}, "a": 1})


def test_reference_execution_has_prequential_and_final_intervals():
    spec = OrdoTimeSeriesSpecV1.model_validate({
        "series_key": "daily", "target_indicator_code": "arrivals",
        "target_methodology_id": uuid.UUID(int=1), "target_methodology_version": 1,
        "target_methodology_fingerprint": "a" * 64, "target_semantic": "continuous",
        "time_index_field": "period", "frequency": "daily", "series_key_fields": ["destination"],
        "observation_window_start": date(2024, 1, 1), "observation_window_end": date(2024, 1, 8),
        "observation_as_of": date(2024, 1, 8), "minimum_history_periods": 4,
        "maximum_missing_ratio": 0, "missing_data_rule": "fail", "outlier_policy": "Review.",
        "revision_policy": "Version.", "comparability_policy": "Stable.", "transformation": "none",
        "trend_requirement": "none", "candidate_families": ["naive"], "horizon": 1,
        "horizon_unit": "days", "uncertainty_output_required": True,
        "diagnostic_requirements": ["residuals"], "limitations": ["non-causal"],
        "temporal_validation": {"initial_train_periods": 3, "step_size": 1, "horizon": 1,
                                "minimum_origins": 3,
                                "required_metrics": ["MAE", "RMSE", "bias", "sMAPE", "MASE",
                                                     "interval_coverage", "interval_width_sharpness"]},
    })
    dates = [date(2024, 1, 1) + timedelta(days=index) for index in range(8)]
    result = _forecast_result_data(dates, [1, 2, 4, 7, 11, 16, 22, 29], spec, "naive", 0.90)
    assert len(result["forecast_points"]) == 1
    assert result["forecast_points"][0]["calibration_residual_count"] == 5
    assert result["diagnostics"]["eligible_interval_point_count"] == 2
    assert result["metric_availability"]["interval_coverage"]["denominator_count"] == 2
