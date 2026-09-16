from __future__ import annotations

import math
import uuid

import pytest

from src.domains.simpa.statistical_models import run_statistical_model
from src.domains.simpa.statistical_xai import build_statistical_xai


FIELDS = [{"field_key": "x", "logical_type": "NUMBER", "required": False}]


def _contract(semantic: str, family: str) -> dict:
    return {
        "schema_version": "SIMPA-STATISTICAL-MODEL-CONTRACT-v1",
        "analysis_key": "xai-association",
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
        "positive_outcome_definition": "Aggregate positive system state." if semantic == "binary_system_state" else None,
    }


def _wrap(detail: dict, *, eligible: bool = True) -> dict:
    return {
        "result_detail": detail,
        "sample_size": detail["sample_size"],
        "dropped_missing_count": detail["dropped_missing_count"],
        "statistical_contract_status": "validated" if eligible else "proposed",
        "production_eligible": eligible,
        "result_fingerprint": "f" * 64,
        "engine_schema_version": detail["engine_schema_version"],
        "statsmodels_version": detail["statsmodels_version"],
    }


@pytest.mark.parametrize(
    ("semantic", "family", "target"),
    [
        ("continuous", "ols", [1.1, 2.4, 2.0, 4.2, 3.8, 5.5, 5.1, 6.4]),
        ("count", "poisson_glm", [0, 1, 1, 2, 1, 3, 2, 4]),
        ("binary_system_state", "binomial_logit", [0, 1, 0, 1, 1, 0, 1, 0]),
        ("proportion_rate", "fractional_logit", [0.05, 0.3, 0.2, 0.55, 0.45, 0.8, 0.7, 0.9]),
    ],
)
def test_new_results_expose_model_produced_pvalues_and_family_faithful_xai(semantic, family, target):
    detail = run_statistical_model(
        _contract(semantic, family),
        [{"value_numeric": value, "x": index} for index, value in enumerate(target)],
        FIELDS,
    )
    for row in detail["coefficients"]:
        assert "p_value" in row
        assert math.isfinite(row["p_value"])
        assert 0.0 <= row["p_value"] <= 1.0
    xai = build_statistical_xai(_wrap(detail))
    assert xai["model_identity"]["model_family"] == family
    assert all(row["p_value_status"] == "available" for row in xai["coefficients"])
    assert "not causality" in xai["p_value_interpretation"].casefold()
    assert "no universal" in xai["diagnostics_interpretation"].casefold()
    assert xai["unsupported"]["generic_confidence_score"] == "unavailable"
    assert xai["unsupported"]["prediction_threshold"] == "unavailable"
    assert "causal" in xai["non_causal_notice"].casefold()


def test_legacy_immutable_result_does_not_reconstruct_missing_pvalue():
    detail = run_statistical_model(
        _contract("continuous", "ols"),
        [{"value_numeric": value, "x": index} for index, value in enumerate([1.1, 2.4, 2.0, 4.2, 3.8, 5.5])],
        FIELDS,
    )
    for row in detail["coefficients"]:
        row.pop("p_value")
    xai = build_statistical_xai(_wrap(detail, eligible=False))
    assert all(row["p_value"] is None for row in xai["coefficients"])
    assert all(row["p_value_status"] == "unavailable_legacy_result" for row in xai["coefficients"])
    assert xai["production_eligibility"]["value"] is False


def test_complete_case_xai_reports_selected_used_dropped_and_preserves_zero():
    detail = run_statistical_model(
        _contract("continuous", "ols"),
        [
            {"value_numeric": 0, "x": 0},
            {"value_numeric": 1, "x": 1},
            {"value_numeric": 2, "x": ""},
            {"value_numeric": 3, "x": 2},
            {"value_numeric": 4, "x": 3},
        ],
        FIELDS,
    )
    xai = build_statistical_xai(_wrap(detail))
    assert detail["selected_count"] == 5
    assert detail["sample_size"] == 4
    assert detail["dropped_missing_count"] == 1
    assert "selected 5" in xai["missing_data_interpretation"]
    assert "used 4" in xai["missing_data_interpretation"]
    assert "dropped 1" in xai["missing_data_interpretation"]
    assert "zero is preserved" in xai["missing_data_interpretation"].casefold()


def test_calibration_semantics_never_invent_generic_confidence():
    ols = run_statistical_model(
        _contract("continuous", "ols"),
        [{"value_numeric": value, "x": index} for index, value in enumerate([1.1, 2.4, 2.0, 4.2, 3.8, 5.5])],
        FIELDS,
    )
    assert build_statistical_xai(_wrap(ols))["calibration"]["status"] == "not_applicable"
    binary = run_statistical_model(
        _contract("binary_system_state", "binomial_logit"),
        [{"value_numeric": value, "x": index} for index, value in enumerate([0, 1, 0, 1, 1, 0, 1, 0])],
        FIELDS,
    )
    xai = build_statistical_xai(_wrap(binary))
    assert xai["calibration"]["status"] == "applicable"
    assert "not proof" in xai["calibration_interpretation"].casefold()
    assert xai["unsupported"]["generic_confidence_score"] == "unavailable"
