from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from src.domains.simpa.statistical_contracts import (
    STATISTICAL_MODEL_CONTRACT_SCHEMA_VERSION,
    SimpaStatisticalModelContractV1,
    contract_fingerprint,
)


def _contract(**changes):
    value = {
        "schema_version": STATISTICAL_MODEL_CONTRACT_SCHEMA_VERSION,
        "analysis_key": " Aggregate Association ",
        "target_indicator_code": "SIMPA.TEST",
        "target_methodology_id": uuid.uuid4(),
        "target_methodology_version": 2,
        "target_methodology_contract_fingerprint": "a" * 64,
        "target_field": "value_numeric",
        "target_semantic": "continuous",
        "model_family": "ols",
        "feature_fields": [" Capacity ", "coverage"],
        "confidence_level": 0.95,
        "covariance_type": "HC3",
        "missing_data_rule": "complete_case",
        "feature_scaling": "none",
        "include_intercept": True,
        "aggregate_only": True,
        "non_causal": True,
        "purpose": "Estimate aggregate statistical association.",
        "limitations": "Observational and non-causal.",
        "positive_outcome_definition": None,
    }
    value.update(changes)
    return value


@pytest.mark.parametrize(
    ("semantic", "family"),
    [
        ("continuous", "ols"),
        ("count", "poisson_glm"),
        ("binary_system_state", "binomial_logit"),
        ("proportion_rate", "fractional_logit"),
    ],
)
def test_exact_semantic_family_mapping(semantic, family):
    changes = {"target_semantic": semantic, "model_family": family}
    if semantic == "binary_system_state":
        changes["positive_outcome_definition"] = "Aggregate system state is present."
    assert SimpaStatisticalModelContractV1.model_validate(_contract(**changes)).model_family == family


def test_unsupported_pair_extra_policy_fields_and_forbidden_features_fail_closed():
    with pytest.raises(ValidationError, match="unsupported target semantic"):
        SimpaStatisticalModelContractV1.model_validate(_contract(model_family="poisson_glm"))
    for forbidden in ("formula", "weights", "threshold", "predicted_class_threshold", "lisi"):
        with pytest.raises(ValidationError):
            SimpaStatisticalModelContractV1.model_validate(_contract(**{forbidden: "forbidden"}))
    for feature in ("indicator_code", "quality_status", "value_numeric", "value_text", "monitoring_cycle_id"):
        with pytest.raises(ValidationError, match="cannot be model features"):
            SimpaStatisticalModelContractV1.model_validate(_contract(feature_fields=[feature]))


def test_binary_definition_is_required_and_nonbinary_cannot_smuggle_class_semantics():
    with pytest.raises(ValidationError, match="positive outcome definition"):
        SimpaStatisticalModelContractV1.model_validate(
            _contract(target_semantic="binary_system_state", model_family="binomial_logit")
        )
    with pytest.raises(ValidationError, match="only for binary"):
        SimpaStatisticalModelContractV1.model_validate(
            _contract(positive_outcome_definition="A categorical label")
        )


def test_canonical_normalization_and_fingerprint_exclude_database_identity_and_timestamps():
    methodology_id = uuid.uuid4()
    first = SimpaStatisticalModelContractV1.model_validate(
        _contract(target_methodology_id=methodology_id, feature_fields=["coverage", " capacity "])
    )
    second = SimpaStatisticalModelContractV1.model_validate(
        _contract(target_methodology_id=methodology_id, feature_fields=["CAPACITY", "coverage"])
    )
    assert first.analysis_key == "aggregate association"
    assert first.feature_fields == ("capacity", "coverage")
    assert contract_fingerprint(first) == contract_fingerprint(second)
    assert len(contract_fingerprint(first)) == 64


@pytest.mark.parametrize("confidence", [0, 1, float("nan"), float("inf"), True])
def test_confidence_must_be_explicit_finite_and_strict(confidence):
    with pytest.raises(ValidationError):
        SimpaStatisticalModelContractV1.model_validate(_contract(confidence_level=confidence))
