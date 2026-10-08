"""Exact interventional linear SHAP from an existing OLS result; never fits."""

from __future__ import annotations

import math
import hashlib
from pathlib import Path
from collections.abc import Mapping, Sequence
from typing import Any

from src.domains.simpa.statistical_contracts import normalize_statistical_model_contract
from src.domains.simpa.statistical_models import (
    _prepare_input,
    normalize_result,
    result_fingerprint,
    STATISTICAL_MODEL_ENGINE_SCHEMA_VERSION,
)

SCHEMA = "SIMPA-LINEAR-SHAP-v1"
METHOD = "EXACT_INTERVENTIONAL_LINEAR_TRAINING_COHORT"
TOLERANCE = 1e-8
MAX_RECORDS = 512
MAX_FEATURES = 24


class AttributionError(ValueError):
    pass


def number(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise AttributionError("attribution_numeric_invalid")
    return float(value)


def close(actual, expected):
    if not math.isclose(number(actual), number(expected), rel_tol=TOLERANCE, abs_tol=TOLERANCE):
        raise AttributionError("attribution_prediction_parity_failed")


def _explain(contract_value, detail: Mapping, records: Sequence[Mapping], field_contract, *, unit: str) -> dict:
    contract = normalize_statistical_model_contract(contract_value)
    if contract.model_family != "ols" or contract.target_semantic != "continuous":
        raise AttributionError("attribution_model_unsupported")
    if not records or len(records) > MAX_RECORDS or len(contract.feature_fields) > MAX_FEATURES:
        raise AttributionError("attribution_capacity_exceeded")
    if not isinstance(unit, str) or not unit.strip() or len(unit) > 160:
        raise AttributionError("attribution_unit_unavailable")
    if any(
        detail.get(k) != v
        for k, v in {
            "engine_schema_version": STATISTICAL_MODEL_ENGINE_SCHEMA_VERSION,
            "model_family": "ols",
            "target_semantic": "continuous",
            "target_field": "value_numeric",
            "feature_fields": list(contract.feature_fields),
            "non_causal": True,
            "confidence_level": contract.confidence_level,
            "covariance_type": contract.covariance_type,
        }.items()
    ):
        raise AttributionError("attribution_result_contract_mismatch")
    target, design, dropped = _prepare_input(contract, records, field_contract)
    if any(
        detail.get(k) != v
        for k, v in {
            "selected_count": len(records),
            "sample_size": len(target),
            "nobs": len(target),
            "dropped_missing_count": dropped,
        }.items()
    ):
        raise AttributionError("attribution_sample_mismatch")
    terms = ["intercept", *contract.feature_fields]
    coefficients = detail.get("coefficients")
    if not isinstance(coefficients, list) or [x.get("term") for x in coefficients] != terms:
        raise AttributionError("attribution_feature_order_mismatch")
    beta = [number(row.get("estimate")) for row in coefficients]
    output = [math.fsum(b * x for b, x in zip(beta, row)) for row in design]
    residuals = [y - p for y, p in zip(target, output)]
    n = len(target)
    mean_target = math.fsum(target) / n
    sse = math.fsum(r * r for r in residuals)
    sst = math.fsum((y - mean_target) ** 2 for y in target)
    r2 = 1 - sse / sst
    calculated = {
        "rmse": math.sqrt(sse / n),
        "mae": math.fsum(abs(r) for r in residuals) / n,
        "r_squared": r2,
        "adjusted_r_squared": 1 - (1 - r2) * (n - 1) / (n - len(beta)),
    }
    metrics = detail.get("metrics") or {}
    for key, value in calculated.items():
        close(value, metrics.get(key))
    background = [math.fsum(row[j + 1] for row in design) / n for j in range(len(beta) - 1)]
    base = math.fsum([beta[0], *(b * m for b, m in zip(beta[1:], background))])
    matrix, samples = [], []
    for i, (row, predicted) in enumerate(zip(design, output)):
        contributions = [b * (x - m) for b, x, m in zip(beta[1:], row[1:], background)]
        reconstructed = math.fsum([base, *contributions])
        close(reconstructed, predicted)
        matrix.append(contributions)
        samples.append(
            {
                "sample": i + 1,
                "values": row[1:],
                "prediction": predicted,
                "additivity_error": abs(reconstructed - predicted),
            }
        )
    artifact = normalize_result(
        {
            "schema": SCHEMA,
            "attribution_implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "input_reconstruction_sha256": hashlib.sha256(
                Path(__file__).with_name("statistical_models.py").read_bytes()
            ).hexdigest(),
            "original_fit_code_sha": "NOT_RECORDED_LEGACY_RESULT",
            "seed": "NOT_APPLICABLE_DETERMINISTIC_CLOSED_FORM",
            "method": METHOD,
            "output_scale": "identity",
            "unit": unit,
            "features": list(contract.feature_fields),
            "background_policy": "EXACT_COMPLETE_CASE_TRAINING_COHORT",
            "background_means": background,
            "background_count": n,
            "background_fingerprint": result_fingerprint({"features": list(contract.feature_fields), "design": design}),
            "baseline": base,
            "matrix": matrix,
            "samples": samples,
            "global_mean_absolute": [math.fsum(abs(row[j]) for row in matrix) / n for j in range(len(background))],
            "selected_count": len(records),
            "dropped_missing_count": dropped,
            "tolerance": TOLERANCE,
            "non_causal": True,
            "in_sample_only": True,
            "limitations": "Interventional SHAP ignores feature correlations; attribution depends on the recorded background. In-sample model explanation, not causal effect, future forecast, LLM truth or policy significance.",
        }
    )
    # Stable serialization must preserve the same numerical additivity contract.
    for sample, contributions in zip(artifact["samples"], artifact["matrix"]):
        close(math.fsum([artifact["baseline"], *contributions]), sample["prediction"])
        sample["additivity_error"] = normalize_result(
            abs(math.fsum([artifact["baseline"], *contributions]) - sample["prediction"])
        )
    return artifact


def explain(contract_value, detail, records, field_contract, *, unit):
    try:
        return _explain(contract_value, detail, records, field_contract, unit=unit)
    except (KeyError, TypeError, OverflowError, ZeroDivisionError, AttributeError):
        raise AttributionError("attribution_payload_invalid") from None
