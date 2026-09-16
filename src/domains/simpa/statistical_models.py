from __future__ import annotations

import hashlib
import json
import math
import warnings
from collections.abc import Mapping, Sequence
from numbers import Integral, Real
from typing import Any

import statsmodels
import statsmodels.api as sm

from src.domains.simpa.statistical_contracts import (
    SimpaStatisticalModelContractV1,
    normalize_statistical_model_contract,
)


STATISTICAL_MODEL_ENGINE_SCHEMA_VERSION = "SIMPA-STATISTICAL-MODEL-v1"
GLM_MAX_ITERATIONS = 100
GLM_CONVERGENCE_TOLERANCE = 1e-8
NON_CAUSAL_NOTICE = (
    "Statistical association or feature contribution does not by itself establish causal effect."
)


class StatisticalModelError(ValueError):
    pass


def _stable_number(value: Any) -> int | float:
    if isinstance(value, bool):
        raise StatisticalModelError("numerical_failure")
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, Real):
        number = float(value)
        if not math.isfinite(number):
            raise StatisticalModelError("numerical_failure")
        if number == 0:
            return 0.0
        return float(format(number, ".15g"))
    raise StatisticalModelError("numerical_failure")


def normalize_result(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, (Integral, Real)):
        return _stable_number(value)
    if isinstance(value, Mapping):
        return {str(key): normalize_result(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [normalize_result(item) for item in value]
    raise StatisticalModelError("result_contract_invalid")


def canonical_result_json(value: Mapping[str, Any]) -> str:
    normalized = normalize_result(dict(value))
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def result_fingerprint(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_result_json(value).encode("utf-8")).hexdigest()


def _matrix_rank(matrix: Sequence[Sequence[float]], tolerance: float = 1e-12) -> int:
    if not matrix:
        return 0
    work = [list(map(float, row)) for row in matrix]
    rows, columns = len(work), len(work[0])
    rank = 0
    for column in range(columns):
        pivot = max(range(rank, rows), key=lambda index: abs(work[index][column]), default=rank)
        if rank >= rows or abs(work[pivot][column]) <= tolerance:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        pivot_value = work[rank][column]
        work[rank] = [item / pivot_value for item in work[rank]]
        for row_index in range(rows):
            if row_index == rank:
                continue
            factor = work[row_index][column]
            if abs(factor) > tolerance:
                work[row_index] = [
                    current - factor * pivot_item
                    for current, pivot_item in zip(work[row_index], work[rank])
                ]
        rank += 1
        if rank == rows:
            break
    return rank


def _missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _number(value: Any) -> float:
    if isinstance(value, bool):
        raise StatisticalModelError("input_numeric_invalid")
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise StatisticalModelError("input_numeric_invalid") from None
    if not math.isfinite(number):
        raise StatisticalModelError("input_numeric_invalid")
    return number


def _prepare_input(
    contract: SimpaStatisticalModelContractV1,
    records: Sequence[Mapping[str, Any]],
    field_contract: Sequence[Mapping[str, Any]],
) -> tuple[list[float], list[list[float]], int]:
    field_types = {
        str(field.get("field_key", "")).strip().casefold(): field.get("logical_type")
        for field in field_contract
    }
    if any(field_types.get(field) != "NUMBER" for field in contract.feature_fields):
        raise StatisticalModelError("feature_field_contract_invalid")

    target: list[float] = []
    design: list[list[float]] = []
    dropped = 0
    for record in records:
        raw_values = [record.get(contract.target_field), *(record.get(field) for field in contract.feature_fields)]
        if any(_missing(value) for value in raw_values):
            dropped += 1
            continue
        values = [_number(value) for value in raw_values]
        target.append(values[0])
        design.append([1.0, *values[1:]])

    if not target or len(set(target)) < 2:
        raise StatisticalModelError("target_not_estimable")
    columns = len(contract.feature_fields) + 1
    if len(target) <= columns:
        raise StatisticalModelError("positive_residual_degrees_of_freedom_required")
    if _matrix_rank(design) != columns:
        raise StatisticalModelError("rank_deficient_design")
    return target, design, dropped


def _validate_target(contract: SimpaStatisticalModelContractV1, target: Sequence[float]) -> None:
    if contract.target_semantic == "count" and any(value < 0 or not value.is_integer() for value in target):
        raise StatisticalModelError("count_target_invalid")
    if contract.target_semantic == "binary_system_state" and set(target) != {0.0, 1.0}:
        raise StatisticalModelError("binary_target_invalid")
    if contract.target_semantic == "proportion_rate" and any(value < 0 or value > 1 for value in target):
        raise StatisticalModelError("proportion_target_invalid")


def _coefficient_rows(result: Any, terms: Sequence[str], confidence_level: float) -> list[dict[str, Any]]:
    intervals = result.conf_int(alpha=1.0 - confidence_level)
    rows = []
    for index, term in enumerate(terms):
        rows.append(
            {
                "term": term,
                "estimate": float(result.params[index]),
                "standard_error": float(result.bse[index]),
                "p_value": float(result.pvalues[index]),
                "confidence_interval_low": float(intervals[index][0]),
                "confidence_interval_high": float(intervals[index][1]),
            }
        )
    return rows


def _fit_ols(contract: SimpaStatisticalModelContractV1, target: list[float], design: list[list[float]]) -> Any:
    model = sm.OLS(target, design, hasconst=True)
    if contract.covariance_type == "nonrobust":
        return model.fit()
    return model.fit(cov_type=contract.covariance_type)


def _fit_glm(
    contract: SimpaStatisticalModelContractV1,
    target: list[float],
    design: list[list[float]],
) -> Any:
    family = sm.families.Poisson() if contract.model_family == "poisson_glm" else sm.families.Binomial()
    fit_kwargs: dict[str, Any] = {
        "maxiter": GLM_MAX_ITERATIONS,
        "tol": GLM_CONVERGENCE_TOLERANCE,
    }
    if contract.covariance_type != "nonrobust":
        fit_kwargs["cov_type"] = contract.covariance_type
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = sm.GLM(target, design, family=family).fit(**fit_kwargs)
    if any("perfect separation" in str(item.message).casefold() for item in caught):
        raise StatisticalModelError("perfect_separation")
    if any("overflow" in str(item.message).casefold() or "invalid value" in str(item.message).casefold() for item in caught):
        raise StatisticalModelError("numerical_failure")
    if not bool(getattr(result, "converged", False)):
        raise StatisticalModelError("non_convergence")
    return result


def run_statistical_model(
    contract_value: SimpaStatisticalModelContractV1 | dict[str, Any],
    records: Sequence[Mapping[str, Any]],
    field_contract: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Fit one deterministic aggregate baseline without formula evaluation or policy interpretation."""

    contract = normalize_statistical_model_contract(contract_value)
    selected_count = len(records)
    target, design, dropped = _prepare_input(contract, records, field_contract)
    _validate_target(contract, target)
    terms = ["intercept", *contract.feature_fields]

    try:
        result = (
            _fit_ols(contract, target, design)
            if contract.model_family == "ols"
            else _fit_glm(contract, target, design)
        )
        coefficients = _coefficient_rows(result, terms, contract.confidence_level)
        predicted = [float(value) for value in result.predict(design)]
        residuals = [actual - estimate for actual, estimate in zip(target, predicted)]
        if contract.model_family == "ols":
            metrics = {
                "r_squared": float(result.rsquared),
                "adjusted_r_squared": float(result.rsquared_adj),
                "rmse": math.sqrt(sum(value * value for value in residuals) / len(residuals)),
                "mae": sum(abs(value) for value in residuals) / len(residuals),
            }
            diagnostics = {
                "nobs": float(result.nobs),
                "df_model": float(result.df_model),
                "df_resid": float(result.df_resid),
                "condition_number": float(result.condition_number),
                "design_rank": _matrix_rank(design),
            }
            calibration: dict[str, Any] = {"status": "not_applicable"}
            numerical_controls: dict[str, Any] = {"fit_method": "statsmodels.OLS.fit"}
        else:
            df_resid = float(result.df_resid)
            metrics = {
                "deviance": float(result.deviance),
                "pearson_chi_square": float(result.pearson_chi2),
                "dispersion": float(result.pearson_chi2) / df_resid,
                "log_likelihood": float(result.llf),
                "aic": float(result.aic),
            }
            diagnostics = {
                "converged": bool(result.converged),
                "nobs": float(result.nobs),
                "df_model": float(result.df_model),
                "df_resid": df_resid,
                "design_rank": _matrix_rank(design),
            }
            if contract.model_family in {"binomial_logit", "fractional_logit"}:
                calibration_key = (
                    "brier_score"
                    if contract.model_family == "binomial_logit"
                    else "squared_probability_error"
                )
                calibration = {
                    "status": "applicable",
                    "measure": calibration_key,
                    calibration_key: sum(value * value for value in residuals) / len(residuals),
                    "mean_observed": sum(target) / len(target),
                    "mean_predicted": sum(predicted) / len(predicted),
                }
            else:
                calibration = {"status": "not_applicable"}
            numerical_controls = {
                "fit_method": "statsmodels.GLM.fit",
                "max_iterations": GLM_MAX_ITERATIONS,
                "convergence_tolerance": GLM_CONVERGENCE_TOLERANCE,
            }
    except StatisticalModelError:
        raise
    except Exception as exc:
        name = type(exc).__name__.casefold()
        message = str(exc).casefold()
        if "perfectseparation" in name or "perfect separation" in message:
            raise StatisticalModelError("perfect_separation") from None
        raise StatisticalModelError("numerical_failure") from exc

    detail = {
        "engine_schema_version": STATISTICAL_MODEL_ENGINE_SCHEMA_VERSION,
        "statsmodels_version": statsmodels.__version__,
        "target_semantic": contract.target_semantic,
        "model_family": contract.model_family,
        "target_field": contract.target_field,
        "feature_fields": list(contract.feature_fields),
        "selected_count": selected_count,
        "nobs": len(target),
        "sample_size": len(target),
        "dropped_missing_count": dropped,
        "coefficients": coefficients,
        "confidence_level": contract.confidence_level,
        "covariance_type": contract.covariance_type,
        "metrics": metrics,
        "diagnostics": diagnostics,
        "calibration": calibration,
        "numerical_controls": numerical_controls,
        "limitations": contract.limitations,
        "non_causal": True,
        "semantic_notice": NON_CAUSAL_NOTICE,
    }
    return normalize_result(detail)


__all__ = [
    "GLM_CONVERGENCE_TOLERANCE",
    "GLM_MAX_ITERATIONS",
    "NON_CAUSAL_NOTICE",
    "STATISTICAL_MODEL_ENGINE_SCHEMA_VERSION",
    "StatisticalModelError",
    "canonical_result_json",
    "normalize_result",
    "result_fingerprint",
    "run_statistical_model",
]
