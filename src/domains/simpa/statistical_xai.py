from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any


FAMILY_EXPLANATIONS = {
    "ols": {
        "title": "OLS / linear association",
        "coefficient": (
            "The coefficient is an aggregate conditional association in target units for a one-unit "
            "increase in the feature, holding the other included features fixed."
        ),
        "metrics": "R-squared, adjusted R-squared, RMSE and MAE are descriptive fit/error summaries, not proof of causality.",
    },
    "poisson_glm": {
        "title": "Poisson GLM / count association",
        "coefficient": (
            "The coefficient is on the log expected-count scale. The raw coefficient is not a direct count difference "
            "and must not be presented as a causal rate ratio without an approved interpretation contract."
        ),
        "metrics": "Deviance, Pearson chi-square, dispersion, log-likelihood and AIC are model diagnostics/comparison summaries; this version defines no universal pass/fail threshold.",
    },
    "binomial_logit": {
        "title": "Binomial/Logit / aggregate system-state association",
        "coefficient": (
            "The coefficient is on the aggregate log-odds scale for the contract-defined positive system state. "
            "It is not a percentage-point effect, citizen probability, classification threshold or causal effect."
        ),
        "metrics": "GLM fit summaries and the Brier error summary describe the fitted aggregate model; they do not create a decision threshold or a calibrated-confidence claim.",
    },
    "fractional_logit": {
        "title": "Fractional Logit / proportion-rate association",
        "coefficient": (
            "The coefficient is on the logit-link scale for the conditional mean of an aggregate proportion/rate. "
            "It is not a direct percentage-point effect and is not a causal effect."
        ),
        "metrics": "GLM fit summaries and squared probability error describe the fitted aggregate mean model; this contract does not certify predictive calibration or policy significance.",
    },
}

UNSUPPORTED_STATES = {
    "causal_effect": "unavailable_without_separately_approved_causal_design",
    "generic_confidence_score": "unavailable",
    "feature_importance": "unavailable_for_current_classical_regression_contract",
    "prediction_threshold": "unavailable",
    "automatic_policy_recommendation": "unavailable",
}


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _coefficient_rows(detail: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in detail.get("coefficients") or []:
        row = dict(raw)
        p_value = _finite_number(row.get("p_value"))
        row["p_value"] = p_value
        row["p_value_status"] = "available" if p_value is not None else "unavailable_legacy_result"
        rows.append(row)
    return rows


def _calibration_interpretation(detail: Mapping[str, Any], family: str) -> str:
    calibration = detail.get("calibration") or {"status": "not_applicable"}
    status = str(calibration.get("status") or "not_applicable")
    if status == "not_applicable":
        return (
            "Calibration is explicitly not applicable in the stored result for this model family. "
            "The UI must not replace this with an invented confidence/calibration score."
        )
    if family == "binomial_logit":
        return (
            "The stored Brier score and mean observed/predicted values are aggregate probability-error summaries. "
            "They are not proof that probabilities are calibrated for a decision threshold."
        )
    if family == "fractional_logit":
        return (
            "The stored squared probability error and mean observed/predicted values summarize aggregate rate/proportion error. "
            "They are not a certified generic confidence score."
        )
    return "Only the calibration fields actually stored by the statistical engine are authoritative."


def build_statistical_xai(result: Mapping[str, Any]) -> dict[str, Any]:
    detail = result.get("result_detail") or {}
    family = str(detail.get("model_family") or "")
    semantic = str(detail.get("target_semantic") or "")
    family_info = FAMILY_EXPLANATIONS.get(
        family,
        {
            "title": "Unsupported model family",
            "coefficient": "No family-specific coefficient interpretation is available.",
            "metrics": "No family-specific metric interpretation is available.",
        },
    )
    selected_count = detail.get("selected_count")
    sample_size = detail.get("sample_size", result.get("sample_size"))
    dropped = detail.get("dropped_missing_count", result.get("dropped_missing_count"))
    production_eligible = bool(result.get("production_eligible"))
    contract_status = result.get("statistical_contract_status") or detail.get("reproducibility_trace", {}).get(
        "statistical_contract_status"
    )
    provenance = dict(detail.get("reproducibility_trace") or {})
    provenance.update(
        {
            "result_fingerprint": result.get("result_fingerprint"),
            "engine_schema_version": result.get("engine_schema_version") or detail.get("engine_schema_version"),
            "statsmodels_version": result.get("statsmodels_version") or detail.get("statsmodels_version"),
        }
    )
    return {
        "model_identity": {
            "target_semantic": semantic,
            "model_family": family,
            "model_label": family_info["title"],
            "confidence_level": detail.get("confidence_level"),
            "covariance_type": detail.get("covariance_type"),
            "engine_schema_version": provenance.get("engine_schema_version"),
            "statsmodels_version": provenance.get("statsmodels_version"),
        },
        "coefficient_interpretation": family_info["coefficient"],
        "coefficients": _coefficient_rows(detail),
        "p_value_interpretation": (
            "A model-produced p-value, when present, is conditional association inference under the stored model/covariance specification. "
            "It is not causality, practical significance, policy significance or a generic confidence score; the v1 contract does not encode a multiplicity adjustment."
        ),
        "metrics": dict(detail.get("metrics") or {}),
        "metrics_interpretation": family_info["metrics"],
        "diagnostics": dict(detail.get("diagnostics") or {}),
        "diagnostics_interpretation": (
            "Diagnostics are the raw supported engine outputs. The current v1 contract defines no universal diagnostic pass/fail threshold; interpretation requires the approved methodology and human review."
        ),
        "calibration": dict(detail.get("calibration") or {"status": "not_applicable"}),
        "calibration_interpretation": _calibration_interpretation(detail, family),
        "missing_data_interpretation": (
            f"Complete-case handling selected {selected_count} candidate records, used {sample_size}, and dropped {dropped} records with a missing target or required feature. Numerical zero is preserved and is not treated as missing."
        ),
        "production_eligibility": {
            "value": production_eligible,
            "contract_status": contract_status,
            "interpretation": (
                "production_eligible=true means the executed statistical contract was in the human-approved VALIDATED lifecycle state at execution. "
                "It is not champion certification, performance certification or an automatic policy approval."
            ),
        },
        "provenance": provenance,
        "unsupported": dict(UNSUPPORTED_STATES),
        "non_causal_notice": detail.get(
            "semantic_notice",
            "Statistical association or feature contribution does not by itself establish causal effect.",
        ),
        "limitations": detail.get("limitations") or "",
    }


__all__ = ["FAMILY_EXPLANATIONS", "UNSUPPORTED_STATES", "build_statistical_xai"]
