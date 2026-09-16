from __future__ import annotations

import hashlib
import json
import uuid
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


STATISTICAL_MODEL_CONTRACT_SCHEMA_VERSION = "ORDO-STATISTICAL-MODEL-CONTRACT-v1"
CROSS_SECTIONAL_FAMILIES = {
    "continuous": {"linear_regression", "robust_regression"},
    "count": {"poisson_glm", "negative_binomial_glm"},
    "proportion_rate": {"fractional_logit", "beta_regression"},
}
PANEL_FAMILIES = {"fixed_effects", "mixed_effects", "hierarchical"}
RESPONSE_FAMILIES = {
    "continuous": {"gaussian"},
    "count": {"poisson", "negative_binomial"},
    "proportion_rate": {"fractional", "beta"},
}


class OrdoStatisticalFeatureSpecV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    feature_key: str = Field(min_length=1, max_length=140)
    role: Literal["predictor", "control", "offset", "exposure"]
    source_field: str = Field(min_length=1, max_length=140)
    version_identity: str = Field(min_length=1, max_length=300)
    transformation: Literal["none", "log1p", "standardize", "categorical"] = "none"
    missing_rule: Literal["complete_case", "exclude", "missing_indicator"] = "complete_case"

    @field_validator("feature_key", "source_field", mode="before")
    @classmethod
    def normalize_key(cls, value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("feature keys must be nonblank")
        return value.strip().casefold()


class OrdoStatisticalModelContractV1(BaseModel):
    """Frozen model specification only; it carries no fitting or result semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True, allow_inf_nan=False)

    schema_version: Literal["ORDO-STATISTICAL-MODEL-CONTRACT-v1"] = STATISTICAL_MODEL_CONTRACT_SCHEMA_VERSION
    analysis_key: str = Field(min_length=1, max_length=140)
    purpose: str = Field(min_length=1, max_length=5000)
    target_indicator_code: str = Field(min_length=1, max_length=140)
    target_methodology_id: uuid.UUID
    target_methodology_version: int = Field(ge=1)
    target_methodology_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_semantic: Literal["continuous", "count", "proportion_rate"]
    analysis_structure: Literal["cross_sectional", "panel"]
    model_family: Literal[
        "linear_regression", "robust_regression", "poisson_glm", "negative_binomial_glm",
        "fractional_logit", "beta_regression", "fixed_effects", "mixed_effects", "hierarchical",
    ]
    response_family: Literal["gaussian", "poisson", "negative_binomial", "fractional", "beta"]
    features: tuple[OrdoStatisticalFeatureSpecV1, ...]
    analysis_window_start: date
    analysis_window_end: date
    analysis_as_of: date
    assumptions: tuple[str, ...]
    required_diagnostics: tuple[str, ...]
    limitations: tuple[str, ...]
    non_causal: Literal[True] = True
    automatic_policy_recommendation: Literal[False] = False

    @field_validator("analysis_key", "target_indicator_code", mode="before")
    @classmethod
    def normalize_key(cls, value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("contract keys must be nonblank")
        return value.strip().casefold()

    @field_validator("features")
    @classmethod
    def unique_features(cls, value: tuple[OrdoStatisticalFeatureSpecV1, ...]):
        if not value or len({item.feature_key for item in value}) != len(value):
            raise ValueError("features must be nonempty and uniquely keyed")
        return tuple(sorted(value, key=lambda item: item.feature_key))

    @field_validator("assumptions", "required_diagnostics", "limitations", mode="before")
    @classmethod
    def nonempty_text_list(cls, value: Any) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)) or not value:
            raise ValueError("contract text lists must be nonempty")
        normalized = tuple(str(item).strip() for item in value)
        if any(not item for item in normalized):
            raise ValueError("contract text entries must be nonblank")
        return normalized

    @model_validator(mode="after")
    def compatible_semantics(self):
        allowed = CROSS_SECTIONAL_FAMILIES[self.target_semantic]
        if self.analysis_structure == "cross_sectional" and self.model_family not in allowed:
            raise ValueError("unsupported target semantic and cross-sectional family pair")
        if self.analysis_structure == "panel" and self.model_family not in PANEL_FAMILIES:
            raise ValueError("unsupported panel family")
        if self.response_family not in RESPONSE_FAMILIES[self.target_semantic]:
            raise ValueError("unsupported target semantic and response-family pair")
        if not (self.analysis_window_start <= self.analysis_window_end <= self.analysis_as_of):
            raise ValueError("analysis window must end on or before as-of")
        return self


def normalize_statistical_model_contract(value: OrdoStatisticalModelContractV1 | dict[str, Any]):
    return value if isinstance(value, OrdoStatisticalModelContractV1) else OrdoStatisticalModelContractV1.model_validate(value)


def canonical_contract_json(value: OrdoStatisticalModelContractV1 | dict[str, Any]) -> str:
    contract = normalize_statistical_model_contract(value)
    return json.dumps(contract.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def contract_fingerprint(value: OrdoStatisticalModelContractV1 | dict[str, Any]) -> str:
    return hashlib.sha256(canonical_contract_json(value).encode("utf-8")).hexdigest()


__all__ = ["OrdoStatisticalFeatureSpecV1", "OrdoStatisticalModelContractV1", "canonical_contract_json", "contract_fingerprint", "normalize_statistical_model_contract"]
