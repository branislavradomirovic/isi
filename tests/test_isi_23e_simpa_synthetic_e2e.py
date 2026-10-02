from __future__ import annotations

import math
import uuid
from pathlib import Path

import pytest

from src.domains.simpa.statistical_models import run_statistical_model
from src.domains.simpa.statistical_xai import build_statistical_xai


ROOT = Path(__file__).resolve().parents[1]
FIELDS = [{"field_key": "x", "logical_type": "NUMBER", "required": False}]


def _contract(semantic: str, family: str) -> dict:
    return {
        "schema_version": "SIMPA-STATISTICAL-MODEL-CONTRACT-v1",
        "analysis_key": f"closeout-{family}",
        "target_indicator_code": "SYNTHETIC.TARGET",
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
        "purpose": "Synthetic aggregate-only closeout association check.",
        "limitations": "Synthetic and non-causal.",
        "positive_outcome_definition": "Aggregate positive system state." if semantic == "binary_system_state" else None,
    }


def _wrap(detail: dict) -> dict:
    return {
        "result_detail": detail,
        "sample_size": detail["sample_size"],
        "dropped_missing_count": detail["dropped_missing_count"],
        "statistical_contract_status": "validated",
        "production_eligible": True,
        "result_fingerprint": "f" * 64,
        "input_content_fingerprint": "e" * 64,
        "engine_schema_version": detail["engine_schema_version"],
        "statsmodels_version": detail["statsmodels_version"],
    }


@pytest.mark.parametrize(
    ("semantic", "family", "target"),
    [
        ("continuous", "ols", [0.0, 1.1, 2.4, 2.0, 4.2, 3.8, 5.5, 5.1, 6.4]),
        ("count", "poisson_glm", [0, 1, 1, 2, 1, 3, 2, 4, 3]),
        ("binary_system_state", "binomial_logit", [0, 1, 0, 1, 1, 0, 1, 0, 1]),
        ("proportion_rate", "fractional_logit", [0.05, 0.3, 0.2, 0.55, 0.45, 0.8, 0.7, 0.9, 0.65]),
    ],
)
def test_synthetic_contract_engine_xai_flow_for_all_accepted_families(semantic, family, target):
    records = [{"value_numeric": value, "x": index} for index, value in enumerate(target)]
    if family == "ols":
        records.insert(3, {"value_numeric": 3.0, "x": ""})
    detail = run_statistical_model(_contract(semantic, family), records, FIELDS)
    assert detail["model_family"] == family
    assert detail["target_semantic"] == semantic
    assert detail["sample_size"] > 0
    assert detail["selected_count"] == len(records)
    if family == "ols":
        assert detail["dropped_missing_count"] == 1
        assert detail["sample_size"] == len(records) - 1
    for coefficient in detail["coefficients"]:
        assert math.isfinite(coefficient["estimate"])
        assert math.isfinite(coefficient["standard_error"])
        assert math.isfinite(coefficient["confidence_interval_low"])
        assert math.isfinite(coefficient["confidence_interval_high"])
        assert coefficient["confidence_interval_low"] <= coefficient["confidence_interval_high"]
        assert 0.0 <= coefficient["p_value"] <= 1.0

    xai = build_statistical_xai(_wrap(detail))
    assert xai["model_identity"]["model_family"] == family
    assert all(row["p_value_status"] == "available" for row in xai["coefficients"])
    assert "not causality" in xai["p_value_interpretation"].casefold()
    assert "no universal" in xai["diagnostics_interpretation"].casefold()
    assert xai["unsupported"]["generic_confidence_score"] == "unavailable"
    assert xai["unsupported"]["feature_importance"].startswith("unavailable")
    assert xai["unsupported"]["prediction_threshold"] == "unavailable"
    assert xai["unsupported"]["automatic_policy_recommendation"] == "unavailable"
    assert "causal" in xai["non_causal_notice"].casefold()
    if family in {"ols", "poisson_glm"}:
        assert xai["calibration"]["status"] == "not_applicable"
    else:
        assert xai["calibration"]["status"] == "applicable"
        if family == "binomial_logit":
            assert "not proof" in xai["calibration_interpretation"].casefold()
        else:
            assert family == "fractional_logit"
            assert "generic confidence score" in xai["calibration_interpretation"].casefold()


def test_synthetic_flow_preserves_simpa_help_and_follows_current_global_matrix_authority():
    matrix = (ROOT / "docs/help/ISI-HELP-COVERAGE-MATRIX.md").read_text(encoding="utf-8")
    guide = (ROOT / "docs/help/SIMPA-USER-GUIDE.md").read_text(encoding="utf-8")
    for row in ("INV-A10", "INV-A11", "INV-A18"):
        line = next(item for item in matrix.splitlines() if item.startswith(f"| {row} |"))
        assert "| VERIFIED |" in line
    inv_a21 = next(item for item in matrix.splitlines() if item.startswith("| INV-A21 |"))
    assert "| VERIFIED |" in inv_a21
    assert "test_isi_27a_shared_help_contract.py" in inv_a21
    for phrase in (
        "OLS",
        "Poisson",
        "Binomial",
        "Fractional",
        "p-value",
        "non-causal",
    ):
        assert phrase.casefold() in guide.casefold()
