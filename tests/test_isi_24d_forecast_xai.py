from __future__ import annotations

import copy
import inspect

from src.domains.ordo.analytics_xai import build_forecast_xai, build_scenario_xai


def _forecast(status: str = "ESTIMATED") -> dict:
    estimated = status == "ESTIMATED"
    return {
        "id": "forecast-1",
        "analytics_run_id": "run-1",
        "time_series_spec_id": "spec-1",
        "time_series_spec_version": 3,
        "time_series_spec_fingerprint": "a" * 64,
        "target_indicator_id": "indicator-1",
        "target_methodology_id": "method-1",
        "target_methodology_version": 4,
        "methodology_fingerprint": "b" * 64,
        "input_snapshot_sha256": "c" * 64,
        "schema_version": "ORDO-FORECAST-RUN-v1",
        "series_identity": {"destination": "A"},
        "request_fingerprint": "d" * 64,
        "requested_family": "naive",
        "executed_family": "naive" if estimated else None,
        "engine_key": "ordo_forecast_engine",
        "engine_version": "1",
        "interval_method": "rolling_origin_empirical_residual_quantile_v1",
        "interval_level": 0.90,
        "result_status": status,
        "reason_code": "" if estimated else "INSUFFICIENT_HISTORY",
        "observation_window": {"start": "2024-01-01", "end": "2024-12-01"},
        "training_window": {"start": "2024-01-01", "end": "2024-12-01", "period_count": 12},
        "horizon": 1,
        "rolling_origin_plan": {"minimum_origins": 3, "required_metrics": ["MAE"]},
        "backtest_records": [{"origin": 1, "metrics": {"MAE": 1.0}}] if estimated else [],
        "aggregate_backtest_metrics": {"MAE": 1.0} if estimated else {},
        "metric_availability": {"MAE": {"available": estimated, "denominator_count": 3 if estimated else 0}},
        "diagnostics": {"rolling_origin_count": 3} if estimated else {},
        "warnings": ["stored warning"] if estimated else [],
        "forecast_points": [
            {"horizon_step": 1, "time": "2025-01-01", "point": 10.0, "lower": 8.0, "upper": 12.0}
        ] if estimated else [],
        "result_fingerprint": "e" * 64,
        "non_causal": True,
        "automatic_model_selection": False,
        "automatic_policy_recommendation": False,
    }


def test_forecast_xai_is_pure_deterministic_and_uses_persisted_values_only():
    value = _forecast()
    before = copy.deepcopy(value)
    first = build_forecast_xai(value)
    second = build_forecast_xai(value)
    assert first == second
    assert value == before
    assert first["forecast_points"] == value["forecast_points"]
    assert first["aggregate_backtest_metrics"] == value["aggregate_backtest_metrics"]
    assert first["diagnostics"] == value["diagnostics"]
    assert first["warnings"] == value["warnings"]
    source = inspect.getsource(build_forecast_xai)
    for forbidden in ("Session", "requests.", "streamlit", "random", "fit(", "predict("):
        assert forbidden not in source


def test_estimated_forecast_explains_family_intervals_backtest_and_exact_provenance():
    value = _forecast()
    xai = build_forecast_xai(value)
    assert xai["result_status"] == "ESTIMATED"
    assert xai["model_identity"]["requested_family"] == "naive"
    assert xai["model_identity"]["executed_family"] == "naive"
    assert "no automatic selection" in xai["model_identity"]["interpretation"].casefold()
    assert "not a generic probability" in xai["interval"]["interpretation"].casefold()
    assert "historical backtest" in xai["backtest_interpretation"].casefold()
    assert "do not prove future performance" in xai["backtest_interpretation"].casefold()
    for key in (
        "time_series_spec_id", "time_series_spec_version", "time_series_spec_fingerprint",
        "target_methodology_id", "target_methodology_version", "methodology_fingerprint",
        "input_snapshot_sha256", "series_identity", "request_fingerprint", "result_fingerprint",
    ):
        assert xai["provenance"][key] == value[key]
    assert xai["unsupported"]["causal_effect"].startswith("unavailable")
    assert xai["unsupported"]["feature_importance"].startswith("unavailable")
    assert xai["unsupported"]["generic_confidence_score"] == "unavailable"
    assert xai["unsupported"]["prediction_or_ranking"] == "unavailable"
    assert xai["unsupported"]["automatic_recommendation"] == "unavailable"


def test_not_estimated_never_exposes_fabricated_points_intervals_or_metrics():
    value = _forecast("NOT_ESTIMATED")
    value["forecast_points"] = [{"point": 999, "lower": 0, "upper": 1000}]
    value["backtest_records"] = [{"invented": True}]
    value["aggregate_backtest_metrics"] = {"MAE": 999}
    xai = build_forecast_xai(value)
    assert xai["result_status"] == "NOT_ESTIMATED"
    assert xai["forecast_points"] == []
    assert xai["backtest_records"] == []
    assert xai["aggregate_backtest_metrics"] == {}
    assert xai["model_identity"]["executed_family"] is None
    assert "not zero" in xai["status_interpretation"].casefold()
    assert "minimum validated history" in xai["reason_interpretation"].casefold()


def test_stable_reason_codes_remain_bounded_and_unknown_code_is_preserved():
    for code in (
        "EXECUTABLE_FAMILY_NOT_DEFINED_24C",
        "TRANSFORMATION_EXECUTION_NOT_DEFINED_24C",
        "SERIES_EVIDENCE_NOT_FOUND",
        "DUPLICATE_TIME_INDEX",
        "INVALID_SERIES_VALUE",
        "IRREGULAR_OR_MISSING_PERIODS",
        "INSUFFICIENT_HISTORY",
        "INSUFFICIENT_ROLLING_ORIGINS",
        "SEASONAL_PERIOD_REQUIRED",
        "SEASONAL_HISTORY_INSUFFICIENT",
        "INSUFFICIENT_INTERVAL_CALIBRATION",
        "REQUIRED_BACKTEST_METRIC_UNAVAILABLE",
    ):
        value = _forecast("NOT_ESTIMATED")
        value["reason_code"] = code
        xai = build_forecast_xai(value)
        assert xai["reason_code"] == code
        assert xai["reason_interpretation"]
        assert xai["forecast_points"] == []
    value["reason_code"] = "FUTURE_REASON"
    assert build_forecast_xai(value)["reason_code"] == "FUTURE_REASON"


def test_scenario_not_estimated_and_legacy_truth_are_preserved_without_invention():
    value = {
        "id": "assessment-1",
        "scenario_id": "scenario-1",
        "analytics_run_id": "run-1",
        "forecast_performed": False,
        "impact": "NOT_ESTIMATED",
        "impact_estimation_reason_code": "NO_APPROVED_RESPONSE_MODEL",
        "impact_estimate_numeric": None,
        "impact_estimate_unit": "",
        "impact_model_reference": "",
        "status": "evidence_only",
        "assessment": {
            "scenario_contract": {
                "scenario_contract_version": "ORDO-SCENARIO-CONTRACT-v1",
                "methodology_key": "ordo_evidence_readiness_v1",
                "methodology_version": "1",
                "input_snapshot_sha256": "f" * 64,
                "input_reference_identities": [{"kind": "snapshot", "id": "snapshot-1"}],
                "limitations": ["No approved response model."],
            }
        },
    }
    first = build_scenario_xai(value)
    assert first["scenario_is_forecast"] is False
    assert first["forecast_performed"] is False
    assert first["impact"] == "NOT_ESTIMATED"
    assert first["impact_estimate_numeric"] is None
    assert "deliberately not estimated" in first["reason_interpretation"].casefold()
    assert first["provenance"]["input_snapshot_sha256"] == "f" * 64
    assert first["provenance"]["input_reference_identities"] == [{"kind": "snapshot", "id": "snapshot-1"}]
    assert all(state.startswith("unavailable") for state in first["unsupported"].values())

    legacy = dict(value, impact="LEGACY_NOT_EVALUATED", impact_estimation_reason_code="LEGACY_NOT_EVALUATED")
    interpreted = build_scenario_xai(legacy)
    assert interpreted["legacy_compatibility"] is True
    assert interpreted["impact"] == "LEGACY_NOT_EVALUATED"
    assert "historical compatibility" in interpreted["reason_interpretation"].casefold()
    assert interpreted["impact_estimate_numeric"] is None
