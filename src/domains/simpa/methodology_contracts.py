from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


SCHEMA_VERSION = "SIMPA-METHODOLOGY-CONTRACT-v1"
_DIRECT_OBSERVATION_FIELDS = {
    "geography_code",
    "geography_label",
    "indicator_code",
    "monitoring_cycle_id",
    "period_end",
    "period_start",
    "population_group",
    "quality_status",
    "value_numeric",
    "value_text",
}
_NATURAL_PERSON_FIELDS = {
    "citizen_id",
    "date_of_birth",
    "email",
    "first_name",
    "jmbg",
    "last_name",
    "natural_person_id",
    "person_id",
    "personal_id",
    "phone",
    "user_id",
}
_TEXT_FIELDS = {
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
}


class SimpaMethodologyContractV1(BaseModel):
    """Strict ISI-23A production contract for pass-through aggregate observations."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    schema_version: Literal["SIMPA-METHODOLOGY-CONTRACT-v1"] = SCHEMA_VERSION
    computation_type: Literal["direct_observation"] = "direct_observation"
    purpose: str
    interpretation: str
    unit: str
    scale: str
    required_source_fields: tuple[str, ...]
    eligible_aggregate_scope: str
    time_aggregation: str
    geographic_aggregation: str
    missing_data_rule: str
    suppression_privacy_rule: str
    quality_preconditions: str
    reference_dataset: str
    accepted_tolerance: float = Field(ge=0)
    limitations: str
    non_causal: Literal[True]

    @field_validator(
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
    )
    @classmethod
    def required_text_is_nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("required methodology contract text must be nonblank")
        return value.strip()

    @field_validator("accepted_tolerance", mode="before")
    @classmethod
    def tolerance_is_finite(cls, value: Any) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("accepted_tolerance must be numeric")
        value = float(value)
        if not math.isfinite(value):
            raise ValueError("accepted_tolerance must be finite")
        return value

    @field_validator("required_source_fields", mode="before")
    @classmethod
    def normalize_source_fields(cls, value: Any) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)) or not value:
            raise ValueError("required_source_fields must be a nonempty list")
        normalized: list[str] = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("source field names must be nonblank strings")
            field = item.strip().casefold()
            if field in normalized:
                raise ValueError("required_source_fields must be unique")
            normalized.append(field)
        return tuple(sorted(normalized))

    @model_validator(mode="after")
    def direct_observation_semantics(self) -> "SimpaMethodologyContractV1":
        fields = set(self.required_source_fields)
        if not {"indicator_code", "quality_status"} <= fields:
            raise ValueError("direct observation requires indicator_code and quality_status")
        if not fields.intersection({"value_numeric", "value_text"}):
            raise ValueError("direct observation requires at least one value channel")
        unknown = fields - _DIRECT_OBSERVATION_FIELDS
        if unknown:
            if unknown.intersection(_NATURAL_PERSON_FIELDS):
                raise ValueError("natural-person identifiers are not allowed in the default contract")
            raise ValueError("unsupported direct-observation source field")
        return self


def normalize_methodology_contract(
    value: SimpaMethodologyContractV1 | dict[str, Any], *, indicator_unit_hint: str = ""
) -> SimpaMethodologyContractV1:
    contract = (
        value if isinstance(value, SimpaMethodologyContractV1) else SimpaMethodologyContractV1.model_validate(value)
    )
    hint = indicator_unit_hint.strip()
    if hint and contract.unit.casefold() != hint.casefold():
        raise ValueError("methodology contract unit contradicts indicator unit_hint")
    return contract


def normalize_draft_methodology_contract(value: dict[str, Any]) -> dict[str, Any]:
    """Validate fields that are present without requiring a complete draft."""

    if not isinstance(value, dict):
        raise ValueError("draft methodology contract must be an object")
    allowed = set(SimpaMethodologyContractV1.model_fields)
    extra = set(value) - allowed
    if extra:
        raise ValueError("unsupported methodology contract field")
    normalized = dict(value)
    for field in _TEXT_FIELDS.intersection(normalized):
        item = normalized[field]
        if not isinstance(item, str) or not item.strip():
            raise ValueError("methodology contract text must be nonblank when supplied")
        normalized[field] = item.strip()
    if "schema_version" in normalized and normalized["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported methodology schema version")
    if "computation_type" in normalized and normalized["computation_type"] != "direct_observation":
        raise ValueError("unsupported methodology computation type")
    if "non_causal" in normalized and normalized["non_causal"] is not True:
        raise ValueError("non_causal must be true")
    if "accepted_tolerance" in normalized:
        tolerance = normalized["accepted_tolerance"]
        if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)):
            raise ValueError("accepted_tolerance must be numeric")
        tolerance = float(tolerance)
        if tolerance < 0 or not math.isfinite(tolerance):
            raise ValueError("accepted_tolerance must be finite and nonnegative")
        normalized["accepted_tolerance"] = tolerance
    if "required_source_fields" in normalized:
        fields = SimpaMethodologyContractV1.normalize_source_fields(normalized["required_source_fields"])
        unknown = set(fields) - _DIRECT_OBSERVATION_FIELDS
        if unknown:
            if unknown.intersection(_NATURAL_PERSON_FIELDS):
                raise ValueError("natural-person identifiers are not allowed in the default contract")
            raise ValueError("unsupported direct-observation source field")
        normalized["required_source_fields"] = list(fields)
    return normalized


def canonical_contract_json(value: SimpaMethodologyContractV1 | dict[str, Any]) -> str:
    contract = (
        value if isinstance(value, SimpaMethodologyContractV1) else SimpaMethodologyContractV1.model_validate(value)
    )
    return json.dumps(contract.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def contract_fingerprint(value: SimpaMethodologyContractV1 | dict[str, Any]) -> str:
    return hashlib.sha256(canonical_contract_json(value).encode("utf-8")).hexdigest()


__all__ = [
    "SCHEMA_VERSION",
    "SimpaMethodologyContractV1",
    "canonical_contract_json",
    "contract_fingerprint",
    "normalize_draft_methodology_contract",
    "normalize_methodology_contract",
]
