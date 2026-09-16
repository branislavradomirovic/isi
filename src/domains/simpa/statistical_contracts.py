from __future__ import annotations

import hashlib
import json
import math
import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


STATISTICAL_MODEL_CONTRACT_SCHEMA_VERSION = "SIMPA-STATISTICAL-MODEL-CONTRACT-v1"

TARGET_SEMANTIC_FAMILIES = {
    "continuous": "ols",
    "count": "poisson_glm",
    "binary_system_state": "binomial_logit",
    "proportion_rate": "fractional_logit",
}

FORBIDDEN_FEATURE_FIELDS = {
    "indicator_code",
    "quality_status",
    "value_numeric",
    "value_text",
    "monitoring_cycle_id",
}


class SimpaStatisticalModelContractV1(BaseModel):
    """Global, immutable SIMPA statistical-methodology specification."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True, allow_inf_nan=False)

    schema_version: Literal["SIMPA-STATISTICAL-MODEL-CONTRACT-v1"] = (
        STATISTICAL_MODEL_CONTRACT_SCHEMA_VERSION
    )
    analysis_key: str = Field(min_length=1, max_length=140)
    target_indicator_code: str = Field(min_length=1, max_length=140)
    target_methodology_id: uuid.UUID
    target_methodology_version: int = Field(ge=1)
    target_methodology_contract_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_field: Literal["value_numeric"] = "value_numeric"
    target_semantic: Literal["continuous", "count", "binary_system_state", "proportion_rate"]
    model_family: Literal["ols", "poisson_glm", "binomial_logit", "fractional_logit"]
    feature_fields: tuple[str, ...]
    confidence_level: float
    covariance_type: Literal["nonrobust", "HC3"]
    missing_data_rule: Literal["complete_case"] = "complete_case"
    feature_scaling: Literal["none"] = "none"
    include_intercept: Literal[True] = True
    aggregate_only: Literal[True] = True
    non_causal: Literal[True] = True
    purpose: str = Field(min_length=1, max_length=5000)
    limitations: str = Field(min_length=1, max_length=5000)
    positive_outcome_definition: str | None = Field(default=None, max_length=1000)

    @field_validator("analysis_key", "target_indicator_code", mode="before")
    @classmethod
    def normalize_key(cls, value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("statistical contract key must be nonblank")
        return value.strip().casefold()

    @field_validator("purpose", "limitations", mode="before")
    @classmethod
    def normalize_required_text(cls, value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("statistical contract text must be nonblank")
        return value.strip()

    @field_validator("positive_outcome_definition", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError("positive outcome definition must be nonblank when supplied")
        return value.strip()

    @field_validator("confidence_level", mode="before")
    @classmethod
    def confidence_is_finite(cls, value: Any) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("confidence_level must be numeric")
        number = float(value)
        if not math.isfinite(number) or not 0 < number < 1:
            raise ValueError("confidence_level must be finite and strictly between zero and one")
        return number

    @field_validator("feature_fields", mode="before")
    @classmethod
    def normalize_features(cls, value: Any) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)) or not value:
            raise ValueError("feature_fields must be a nonempty list")
        normalized: list[str] = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("feature field names must be nonblank strings")
            field = item.strip().casefold()
            if field in FORBIDDEN_FEATURE_FIELDS:
                raise ValueError("canonical direct-observation fields cannot be model features")
            if field in normalized:
                raise ValueError("feature_fields must be unique")
            normalized.append(field)
        return tuple(sorted(normalized))

    @model_validator(mode="after")
    def validate_semantics(self) -> "SimpaStatisticalModelContractV1":
        if TARGET_SEMANTIC_FAMILIES[self.target_semantic] != self.model_family:
            raise ValueError("unsupported target semantic and model family pair")
        if self.target_semantic == "binary_system_state":
            if self.positive_outcome_definition is None:
                raise ValueError("binary system-state contracts require a positive outcome definition")
        elif self.positive_outcome_definition is not None:
            raise ValueError("positive outcome definitions are allowed only for binary system-state contracts")
        return self


def normalize_statistical_model_contract(
    value: SimpaStatisticalModelContractV1 | dict[str, Any],
) -> SimpaStatisticalModelContractV1:
    return (
        value
        if isinstance(value, SimpaStatisticalModelContractV1)
        else SimpaStatisticalModelContractV1.model_validate(value)
    )


def canonical_contract_json(value: SimpaStatisticalModelContractV1 | dict[str, Any]) -> str:
    contract = normalize_statistical_model_contract(value)
    return json.dumps(
        contract.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def contract_fingerprint(value: SimpaStatisticalModelContractV1 | dict[str, Any]) -> str:
    return hashlib.sha256(canonical_contract_json(value).encode("utf-8")).hexdigest()


__all__ = [
    "FORBIDDEN_FEATURE_FIELDS",
    "STATISTICAL_MODEL_CONTRACT_SCHEMA_VERSION",
    "TARGET_SEMANTIC_FAMILIES",
    "SimpaStatisticalModelContractV1",
    "canonical_contract_json",
    "contract_fingerprint",
    "normalize_statistical_model_contract",
]
