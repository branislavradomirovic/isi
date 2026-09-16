from __future__ import annotations

import uuid

import pytest

from src.domains.simpa import statistical_models
from src.domains.simpa.statistical_models import (
    StatisticalModelError,
    result_fingerprint,
    run_statistical_model,
)


FIELDS = [
    {"field_key": "x", "logical_type": "NUMBER", "required": False},
    {"field_key": "z", "logical_type": "NUMBER", "required": False},
]


def _contract(semantic="continuous", family="ols", **changes):
    value = {
        "schema_version": "SIMPA-STATISTICAL-MODEL-CONTRACT-v1",
        "analysis_key": "association",
        "target_indicator_code": "target",
        "target_methodology_id": str(uuid.uuid4()),
        "target_methodology_version": 1,
        "target_methodology_contract_fingerprint": "a" * 64,
        "target_field": "value_numeric",
        "target_semantic": semantic,
        "model_family": family,
        "feature_fields": ["x"],
        "confidence_level": 0.95,
        "covariance_type": "nonrobust",
        "missing_data_rule": "complete_case",
        "feature_scaling": "none",
        "include_intercept": True,
        "aggregate_only": True,
        "non_causal": True,
        "purpose": "Aggregate association baseline.",
        "limitations": "Observational and non-causal.",
        "positive_outcome_definition": (
            "Aggregate system outcome is present." if semantic == "binary_system_state" else None
        ),
    }
    value.update(changes)
    return value


@pytest.mark.parametrize(
    ("semantic", "family", "target"),
    [
        ("continuous", "ols", [1.1, 2.4, 2.0, 4.2, 3.8, 5.5, 5.1, 6.4]),
        ("count", "poisson_glm", [0, 1, 1, 2, 1, 3, 2, 4]),
        ("binary_system_state", "binomial_logit", [0, 1, 0, 1, 1, 0, 1, 0]),
        ("proportion_rate", "fractional_logit", [0.05, 0.3, 0.2, 0.55, 0.45, 0.8, 0.7, 0.9]),
    ],
)
def test_four_deterministic_baselines_expose_uncertainty_diagnostics_and_calibration(semantic, family, target):
    records = [{"value_numeric": value, "x": index} for index, value in enumerate(target)]
    contract = _contract(semantic, family)
    first = run_statistical_model(contract, records, FIELDS)
    second = run_statistical_model(contract, records, FIELDS)
    assert first == second
    assert len(first["coefficients"]) == 2
    assert all(
        {"term", "estimate", "standard_error", "confidence_interval_low", "confidence_interval_high"}
        <= set(row)
        for row in first["coefficients"]
    )
    assert first["sample_size"] == len(records)
    assert first["non_causal"] is True
    assert "causal effect" in first["semantic_notice"]
    assert len(result_fingerprint(first)) == 64
    if family == "ols":
        assert {"r_squared", "adjusted_r_squared", "rmse", "mae"} <= set(first["metrics"])
        assert first["calibration"] == {"status": "not_applicable"}
    else:
        assert {"deviance", "pearson_chi_square", "dispersion", "log_likelihood", "aic"} <= set(
            first["metrics"]
        )
        assert first["diagnostics"]["converged"] is True
        assert "negative_binomial" not in str(first).casefold()
        if family in {"binomial_logit", "fractional_logit"}:
            assert first["calibration"]["status"] == "applicable"
            score_key = "brier_score" if family == "binomial_logit" else "squared_probability_error"
            assert {score_key, "mean_observed", "mean_predicted"} <= set(first["calibration"])
            assert "predicted_class" not in str(first)
            assert "threshold" not in str(first).casefold()


def test_complete_case_preserves_zero_and_reports_selected_used_and_dropped():
    records = [
        {"value_numeric": 0, "x": 0},
        {"value_numeric": 1, "x": 1},
        {"value_numeric": 2, "x": ""},
        {"value_numeric": 3, "x": 2},
        {"value_numeric": 4, "x": 3},
    ]
    detail = run_statistical_model(_contract(), records, FIELDS)
    assert detail["selected_count"] == 5
    assert detail["sample_size"] == 4
    assert detail["dropped_missing_count"] == 1


@pytest.mark.parametrize("bad", [True, "bad", float("nan"), float("inf")])
def test_invalid_numeric_values_are_rejected_not_zero_filled(bad):
    records = [
        {"value_numeric": 1, "x": 0},
        {"value_numeric": 2, "x": 1},
        {"value_numeric": 3, "x": 2},
        {"value_numeric": 4, "x": bad},
    ]
    with pytest.raises(StatisticalModelError, match="input_numeric_invalid"):
        run_statistical_model(_contract(), records, FIELDS)


def test_numeric_field_rank_variation_and_estimability_fail_closed():
    records = [{"value_numeric": value, "x": 1} for value in (1, 2, 3, 4)]
    with pytest.raises(StatisticalModelError, match="rank_deficient_design"):
        run_statistical_model(_contract(), records, FIELDS)
    with pytest.raises(StatisticalModelError, match="target_not_estimable"):
        run_statistical_model(_contract(), [{"value_numeric": 1, "x": index} for index in range(4)], FIELDS)
    with pytest.raises(StatisticalModelError, match="feature_field_contract_invalid"):
        run_statistical_model(_contract(), [{"value_numeric": index, "x": index} for index in range(4)], [])
    with pytest.raises(StatisticalModelError, match="positive_residual_degrees_of_freedom_required"):
        run_statistical_model(
            _contract(),
            [{"value_numeric": 1, "x": 0}, {"value_numeric": 2, "x": 1}],
            FIELDS,
        )


def test_target_semantics_and_perfect_separation_fail_closed():
    with pytest.raises(StatisticalModelError, match="count_target_invalid"):
        run_statistical_model(
            _contract("count", "poisson_glm"),
            [{"value_numeric": value, "x": index} for index, value in enumerate([0, 1.5, 2, 3])],
            FIELDS,
        )
    separated = [{"value_numeric": int(index > 2), "x": index} for index in range(6)]
    with pytest.raises(StatisticalModelError, match="perfect_separation|numerical_failure"):
        run_statistical_model(_contract("binary_system_state", "binomial_logit"), separated, FIELDS)


def test_glm_non_convergence_is_a_closed_stable_error(monkeypatch):
    monkeypatch.setattr(statistical_models, "GLM_MAX_ITERATIONS", 0)
    records = [
        {"value_numeric": value, "x": index}
        for index, value in enumerate([0, 1, 1, 2, 1, 3, 2, 4])
    ]
    with pytest.raises(StatisticalModelError, match="non_convergence"):
        run_statistical_model(_contract("count", "poisson_glm"), records, FIELDS)
