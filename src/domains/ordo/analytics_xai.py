from __future__ import annotations

from collections.abc import Mapping
from typing import Any


FORECAST_REASON_EXPLANATIONS = {
    "": "No NOT_ESTIMATED reason applies to this persisted ESTIMATED result.",
    "EXECUTABLE_FAMILY_NOT_DEFINED_24C": (
        "The requested family is recorded by the validated specification, but 24C does not define "
        "execution for it. No fallback family was selected."
    ),
    "TRANSFORMATION_EXECUTION_NOT_DEFINED_24C": (
        "The validated specification requests a transformation that the accepted 24C runtime does "
        "not execute. No untransformed substitute was produced."
    ),
    "SERIES_EVIDENCE_NOT_FOUND": "No governed validated series matched the exact persisted series identity.",
    "DUPLICATE_TIME_INDEX": "More than one governed value exists for a required time index.",
    "INVALID_SERIES_VALUE": "At least one selected time or target value violates the validated series contract.",
    "IRREGULAR_OR_MISSING_PERIODS": "The selected chronological series is incomplete or irregular for its validated frequency.",
    "INSUFFICIENT_HISTORY": "The governed series does not contain the minimum validated history.",
    "INSUFFICIENT_ROLLING_ORIGINS": "The validated rolling-origin plan cannot produce enough historical origins.",
    "SEASONAL_PERIOD_REQUIRED": "The requested seasonal-naive family has no validated seasonal period.",
    "SEASONAL_HISTORY_INSUFFICIENT": "The governed history is too short for the validated seasonal period.",
    "INSUFFICIENT_INTERVAL_CALIBRATION": "Too few earlier residuals exist to construct every required empirical interval.",
    "REQUIRED_BACKTEST_METRIC_UNAVAILABLE": "A metric required by the validated temporal plan is unavailable, so no estimate was produced.",
}

FORECAST_UNSUPPORTED = {
    "causal_effect": "unavailable_without_separately_approved_causal_design",
    "feature_importance": "unavailable_for_naive_and_seasonal_naive_forecast_contract",
    "generic_confidence_score": "unavailable",
    "prediction_or_ranking": "unavailable",
    "automatic_recommendation": "unavailable",
}

SCENARIO_REASON_EXPLANATIONS = {
    "NO_APPROVED_RESPONSE_MODEL": (
        "Impact was deliberately not estimated because no separately approved response/impact model exists."
    ),
    "LEGACY_NOT_EVALUATED": (
        "This is historical compatibility state. It records that impact was not evaluated in the legacy row; "
        "it is not evidence of a later scenario or forecast execution."
    ),
}


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, (list, tuple)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def build_forecast_xai(result: Mapping[str, Any]) -> dict[str, Any]:
    """Interpret one persisted forecast result without fitting, inference or value synthesis."""
    status = str(result.get("result_status") or "")
    reason_code = str(result.get("reason_code") or "")
    estimated = status == "ESTIMATED"
    points = _list_of_mappings(result.get("forecast_points")) if estimated else []
    backtests = _list_of_mappings(result.get("backtest_records")) if estimated else []
    reason_interpretation = FORECAST_REASON_EXPLANATIONS.get(
        reason_code,
        "The persisted reason code is not recognized by this presentation version; preserve it exactly and request methodology review.",
    )
    return {
        "result_status": status,
        "status_interpretation": (
            "ESTIMATED means the accepted deterministic runtime persisted output for the exact validated specification and governed input."
            if estimated
            else "NOT_ESTIMATED is a successful bounded domain outcome. It is not zero, an empty forecast or a hidden estimate."
        ),
        "reason_code": reason_code,
        "reason_interpretation": reason_interpretation,
        "model_identity": {
            "requested_family": result.get("requested_family"),
            "executed_family": result.get("executed_family") if estimated else None,
            "engine_key": result.get("engine_key"),
            "engine_version": result.get("engine_version"),
            "automatic_model_selection": result.get("automatic_model_selection"),
            "interpretation": (
                "The requested family is explicit. The executed family is present only for an ESTIMATED run. "
                "automatic_model_selection=false means there was no automatic selection, fallback or winner choice."
            ),
        },
        "interval": {
            "method": result.get("interval_method"),
            "level": result.get("interval_level"),
            "interpretation": (
                "The stored interval method and configured level describe the accepted uncertainty-output contract. "
                "They are not a generic probability that this forecast is correct and are not a confidence score."
            ),
        },
        "coverage": {
            "observation_window": _mapping(result.get("observation_window")),
            "training_window": _mapping(result.get("training_window")),
            "horizon": result.get("horizon"),
        },
        "rolling_origin_plan": _mapping(result.get("rolling_origin_plan")),
        "backtest_records": backtests,
        "aggregate_backtest_metrics": _mapping(result.get("aggregate_backtest_metrics")) if estimated else {},
        "metric_availability": _mapping(result.get("metric_availability")),
        "backtest_interpretation": (
            "Rolling-origin metrics and interval coverage are historical backtest diagnostics over earlier observations. "
            "They do not prove future performance and this layer defines no invented pass/fail or quality threshold."
        ),
        "diagnostics": _mapping(result.get("diagnostics")),
        "diagnostics_interpretation": (
            "Diagnostics are displayed exactly as persisted. Their presence or value is not converted into an unstored pass/fail label."
        ),
        "warnings": _list(result.get("warnings")),
        "forecast_points": points,
        "provenance": {
            "forecast_run_id": result.get("id"),
            "schema_version": result.get("schema_version"),
            "analytics_run_id": result.get("analytics_run_id"),
            "time_series_spec_id": result.get("time_series_spec_id"),
            "time_series_spec_version": result.get("time_series_spec_version"),
            "time_series_spec_fingerprint": result.get("time_series_spec_fingerprint"),
            "target_indicator_id": result.get("target_indicator_id"),
            "target_methodology_id": result.get("target_methodology_id"),
            "target_methodology_version": result.get("target_methodology_version"),
            "methodology_fingerprint": result.get("methodology_fingerprint"),
            "input_snapshot_sha256": result.get("input_snapshot_sha256"),
            "series_identity": _mapping(result.get("series_identity")),
            "request_fingerprint": result.get("request_fingerprint"),
            "result_fingerprint": result.get("result_fingerprint"),
        },
        "safety": {
            "non_causal": result.get("non_causal"),
            "automatic_model_selection": result.get("automatic_model_selection"),
            "automatic_policy_recommendation": result.get("automatic_policy_recommendation"),
            "interpretation": (
                "non_causal=true forbids causal interpretation. automatic_policy_recommendation=false means the run does not choose an action."
            ),
        },
        "unsupported": dict(FORECAST_UNSUPPORTED),
    }


def build_scenario_xai(assessment: Mapping[str, Any]) -> dict[str, Any]:
    """Interpret persisted scenario-assessment truth while keeping it distinct from forecast output."""
    assessment_detail = _mapping(assessment.get("assessment"))
    scenario_contract = _mapping(assessment_detail.get("scenario_contract"))
    impact = str(assessment.get("impact") or assessment.get("impact_estimation_status") or "")
    reason_code = str(assessment.get("impact_estimation_reason_code") or "")
    forecast_performed = assessment.get("forecast_performed")
    legacy = impact == "LEGACY_NOT_EVALUATED" or reason_code == "LEGACY_NOT_EVALUATED"
    reason_interpretation = SCENARIO_REASON_EXPLANATIONS.get(
        "LEGACY_NOT_EVALUATED" if legacy else reason_code,
        "The persisted reason code is not recognized by this presentation version; preserve it exactly for review.",
    )
    numeric = assessment.get("impact_estimate_numeric") if impact == "ESTIMATED" else None
    return {
        "scenario_is_forecast": False,
        "scenario_interpretation": (
            "A scenario contains user-authored assumptions and measures. Those inputs are not evidence and this assessment is not a forecast."
        ),
        "forecast_performed": forecast_performed,
        "forecast_boundary": (
            "forecast_performed=false is authoritative: no forecast was performed for this scenario assessment."
            if forecast_performed is False
            else "This presentation does not reinterpret the persisted forecast_performed value."
        ),
        "impact": impact,
        "impact_estimation_reason_code": reason_code,
        "reason_interpretation": reason_interpretation,
        "impact_estimate_numeric": numeric,
        "impact_estimate_unit": assessment.get("impact_estimate_unit") if numeric is not None else None,
        "impact_model_reference": assessment.get("impact_model_reference") if numeric is not None else None,
        "legacy_compatibility": legacy,
        "assessment": assessment_detail,
        "provenance": {
            "assessment_id": assessment.get("id"),
            "scenario_id": assessment.get("scenario_id"),
            "analytics_run_id": assessment.get("analytics_run_id"),
            "input_snapshot_sha256": assessment.get("input_snapshot_sha256") or scenario_contract.get("input_snapshot_sha256"),
            "scenario_contract_version": assessment.get("scenario_contract_version") or scenario_contract.get("scenario_contract_version"),
            "methodology_key": assessment.get("methodology_key") or scenario_contract.get("methodology_key"),
            "methodology_version": assessment.get("methodology_version") or scenario_contract.get("methodology_version"),
            "input_reference_identities": _list_of_mappings(
                assessment.get("input_reference_identities") or scenario_contract.get("input_reference_identities")
            ),
        },
        "human_review_state": assessment.get("human_review_state") or assessment.get("status"),
        "limitations": _list(
            assessment.get("limitations")
            or scenario_contract.get("limitations")
            or assessment_detail.get("limitations")
        ),
        "unsupported": {
            "causal_effect": "unavailable_without_separately_approved_response_model",
            "generic_confidence_score": "unavailable",
            "feature_importance": "unavailable",
            "ranking": "unavailable",
            "automatic_recommendation": "unavailable",
        },
    }


__all__ = [
    "FORECAST_REASON_EXPLANATIONS",
    "FORECAST_UNSUPPORTED",
    "SCENARIO_REASON_EXPLANATIONS",
    "build_forecast_xai",
    "build_scenario_xai",
]
