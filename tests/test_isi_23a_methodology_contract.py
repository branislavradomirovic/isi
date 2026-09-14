from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.domains.simpa.methodology_contracts import (
    SimpaMethodologyContractV1,
    canonical_contract_json,
    contract_fingerprint,
    normalize_draft_methodology_contract,
    normalize_methodology_contract,
)


def test_service_enforces_contract_immutability_after_proposal():
    from pathlib import Path

    service = Path("src/domains/simpa/analytics_service.py").read_text()
    assert 'if row.status != "draft":' in service
    assert 'raise SimpaAnalyticsError("methodology_contract_immutable")' in service


def _contract() -> dict:
    return {
        "schema_version": "SIMPA-METHODOLOGY-CONTRACT-v1",
        "computation_type": "direct_observation",
        "purpose": "Pass through governed aggregate evidence.",
        "interpretation": "A descriptive observed value.",
        "unit": "count",
        "scale": "Local-system aggregate.",
        "required_source_fields": ["value_numeric", "quality_status", "indicator_code"],
        "eligible_aggregate_scope": "Authorized organization/local system.",
        "time_aggregation": "Governed reporting period.",
        "geographic_aggregation": "Approved aggregate geography.",
        "missing_data_rule": "Preserve missing; never convert it to zero.",
        "suppression_privacy_rule": "Suppress disallowed granular evidence.",
        "quality_preconditions": "Validated source evidence only.",
        "reference_dataset": "Compact ISI-23A reference fixture.",
        "accepted_tolerance": 0.01,
        "limitations": "Descriptive, aggregate and non-causal.",
        "non_causal": True,
    }


def test_strict_v1_contract_normalizes_fields_and_has_stable_fingerprint():
    first = _contract()
    second = dict(reversed(list(first.items())))
    second["required_source_fields"] = [" INDICATOR_CODE ", "VALUE_NUMERIC", "quality_status"]
    parsed = SimpaMethodologyContractV1.model_validate(first)
    assert parsed.required_source_fields == ("indicator_code", "quality_status", "value_numeric")
    assert canonical_contract_json(first) == canonical_contract_json(second)
    assert contract_fingerprint(first) == contract_fingerprint(second)
    assert len(contract_fingerprint(first)) == 64


def test_draft_may_be_incomplete_but_not_semantically_invalid():
    assert normalize_draft_methodology_contract(
        {"purpose": "Draft purpose", "required_source_fields": [" VALUE_TEXT "]}
    ) == {"purpose": "Draft purpose", "required_source_fields": ["value_text"]}
    for invalid in (
        {"formula": "x + y"},
        {"non_causal": False},
        {"accepted_tolerance": -1},
        {"required_source_fields": ["person_id"]},
    ):
        with pytest.raises(ValueError):
            normalize_draft_methodology_contract(invalid)


@pytest.mark.parametrize(
    "field",
    [
        "purpose",
        "interpretation",
        "unit",
        "scale",
        "eligible_aggregate_scope",
        "time_aggregation",
        "geographic_aggregation",
        "missing_data_rule",
        "suppression_privacy_rule",
        "quality_preconditions",
        "reference_dataset",
        "limitations",
    ],
)
def test_required_text_is_nonblank(field):
    value = _contract()
    value[field] = "  "
    with pytest.raises(ValidationError):
        SimpaMethodologyContractV1.model_validate(value)


def test_non_causal_source_semantics_and_tolerance_are_fail_closed():
    for mutation in (
        {"non_causal": False},
        {"accepted_tolerance": -0.1},
        {"required_source_fields": ["indicator_code", "value_numeric"]},
        {"required_source_fields": ["indicator_code", "quality_status"]},
        {"required_source_fields": ["indicator_code", "quality_status", "person_id", "value_text"]},
        {"required_source_fields": ["indicator_code", "quality_status", "value_text", "value_text"]},
    ):
        value = _contract()
        value.update(mutation)
        with pytest.raises(ValidationError):
            SimpaMethodologyContractV1.model_validate(value)


def test_unit_mismatch_is_explicit():
    with pytest.raises(ValueError, match="unit_hint"):
        normalize_methodology_contract(_contract(), indicator_unit_hint="percent")


@pytest.mark.parametrize("forbidden", ["formula", "weight", "threshold", "risk_band", "lisi"])
def test_formula_weight_threshold_risk_and_lisi_fields_are_forbidden(forbidden):
    value = _contract()
    value[forbidden] = "not authorized"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        SimpaMethodologyContractV1.model_validate(value)
