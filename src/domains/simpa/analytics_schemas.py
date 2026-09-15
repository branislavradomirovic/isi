from __future__ import annotations

import math
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SimpaAnalyticsScope(BaseModel):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID


class AnalyticsRunCreateRequest(SimpaAnalyticsScope):
    analytical_artifact_type: Literal["snapshot", "feature_version"]
    analytical_artifact_id: uuid.UUID
    monitoring_cycle_id: uuid.UUID | None = None


class MethodologyCreateRequest(SimpaAnalyticsScope):
    indicator_code: str = Field(min_length=1, max_length=140)
    computation_type: Literal["direct_observation"] = "direct_observation"
    methodology_note: str = Field(min_length=1, max_length=5000)
    source_requirements: dict = Field(default_factory=dict)
    computation_spec: dict = Field(default_factory=dict)


class MethodologyProposeRequest(SimpaAnalyticsScope):
    pass


class MethodologyValidateRequest(SimpaAnalyticsScope):
    validation_note: str = Field(min_length=8, max_length=5000)


class MethodologyRetireRequest(SimpaAnalyticsScope):
    retirement_note: str = Field(min_length=1, max_length=5000)


class DirectObservationReferenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)

    indicator_code: str = Field(min_length=1, max_length=140)
    quality_status: Literal["validated", "draft", "rejected"]
    value_numeric: float | int | str | None = None
    value_text: str | None = None

    @field_validator("value_numeric", mode="before")
    @classmethod
    def numeric_is_not_boolean(cls, value):
        if isinstance(value, bool):
            raise ValueError("numeric value must not be boolean")
        if value is not None:
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                raise ValueError("numeric value must be finite") from None
            if not math.isfinite(numeric):
                raise ValueError("numeric value must be finite")
        return value

    @model_validator(mode="after")
    def has_value(self) -> "DirectObservationReferenceRecord":
        numeric = self.value_numeric is not None
        textual = bool((self.value_text or "").strip())
        if not numeric and not textual:
            raise ValueError("reference record requires at least one value channel")
        return self


class DirectObservationExpectedResult(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)

    value_numeric: float | int | str | None = None
    value_text: str | None = None

    @field_validator("value_numeric", mode="before")
    @classmethod
    def numeric_is_not_boolean(cls, value):
        if isinstance(value, bool):
            raise ValueError("numeric value must not be boolean")
        if value is not None:
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                raise ValueError("numeric value must be finite") from None
            if not math.isfinite(numeric):
                raise ValueError("numeric value must be finite")
        return value

    @model_validator(mode="after")
    def has_one_value(self) -> "DirectObservationExpectedResult":
        numeric = self.value_numeric is not None
        textual = bool((self.value_text or "").strip())
        if numeric == textual:
            raise ValueError("expected result requires exactly one value channel")
        return self


class MethodologyReferenceCheckRequest(SimpaAnalyticsScope):
    reference_record: DirectObservationReferenceRecord
    expected_result: DirectObservationExpectedResult


class MethodologyReferenceCaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    case_key: str = Field(min_length=1, max_length=255)
    reference_record: DirectObservationReferenceRecord
    expected_result: DirectObservationExpectedResult


class MethodologyReferenceSuiteCreateRequest(SimpaAnalyticsScope):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    reference_dataset_version: str = Field(min_length=1, max_length=255)
    cases: list[MethodologyReferenceCaseCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_case_keys(self) -> "MethodologyReferenceSuiteCreateRequest":
        keys = [case.case_key for case in self.cases]
        if len(keys) != len(set(keys)):
            raise ValueError("reference suite case keys must be unique")
        return self


class MethodologyReferenceSuiteRunRequest(SimpaAnalyticsScope):
    model_config = ConfigDict(extra="forbid")


class IndicatorComputeRequest(SimpaAnalyticsScope):
    indicator_code: str = Field(min_length=1, max_length=140)
    monitoring_cycle_id: uuid.UUID | None = None
    analytics_run_id: uuid.UUID


class SynthesisCreateRequest(SimpaAnalyticsScope):
    analytics_run_id: uuid.UUID
    sensitivity: Literal["internal", "sensitive"] = "sensitive"
    model_key: str | None = None


class SynthesisReviewRequest(SimpaAnalyticsScope):
    decision: Literal["accepted", "rejected"]
    reviewer_note: str = Field(default="", max_length=5000)
