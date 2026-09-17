from __future__ import annotations

import uuid
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrdoAnalyticsScope(BaseModel):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID


class AnalyticsRunCreateRequest(OrdoAnalyticsScope):
    analytical_artifact_type: Literal["snapshot", "feature_version"]
    analytical_artifact_id: uuid.UUID
    monitoring_cycle_id: uuid.UUID | None = None


class MethodologyCreateRequest(OrdoAnalyticsScope):
    indicator_code: str = Field(min_length=1, max_length=140)
    computation_type: Literal["direct_observation"] = "direct_observation"
    methodology_note: str = Field(min_length=1, max_length=5000)
    source_requirements: dict = Field(default_factory=dict)


class MethodologyValidateRequest(OrdoAnalyticsScope):
    validation_note: str = Field(min_length=8, max_length=5000)


class MethodologyProposeRequest(OrdoAnalyticsScope):
    pass


class MethodologyRetireRequest(OrdoAnalyticsScope):
    retirement_note: str = Field(min_length=1, max_length=5000)


class IndicatorComputeRequest(OrdoAnalyticsScope):
    indicator_code: str = Field(min_length=1, max_length=140)
    monitoring_cycle_id: uuid.UUID | None = None
    analytics_run_id: uuid.UUID


class DevelopmentGoalCreateRequest(OrdoAnalyticsScope):
    code: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=3, max_length=400)
    description: str = Field(default="", max_length=8000)
    focus_area: Literal[
        "competitiveness",
        "sustainability",
        "inclusion",
        "employment",
        "quality_of_life",
        "destination_development",
        "custom",
    ] = "destination_development"
    target_horizon: date | None = None
    status: Literal["draft", "active", "closed"] = "draft"


class ScenarioCreateRequest(OrdoAnalyticsScope):
    goal_id: uuid.UUID
    name: str = Field(min_length=3, max_length=300)
    description: str = Field(default="", max_length=8000)
    assumptions: list[str] = Field(default_factory=list, max_length=50)
    measures: list[str] = Field(default_factory=list, max_length=50)


class ScenarioStatusRequest(OrdoAnalyticsScope):
    status: Literal["draft", "review_ready", "accepted", "rejected"]


class ScenarioAssessmentCreateRequest(OrdoAnalyticsScope):
    scenario_id: uuid.UUID
    analytics_run_id: uuid.UUID


class ScenarioAssessmentReviewRequest(OrdoAnalyticsScope):
    decision: Literal["reviewed", "rejected"]
    reviewer_note: str = Field(default="", max_length=5000)


class ForecastExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    time_series_spec_id: uuid.UUID
    requested_family: Literal["naive", "seasonal_naive", "ets", "sarima", "sarimax", "count_time_series"]
    series_identity: dict[str, str | int | float | bool | None]
    interval_level: Literal[0.80, 0.90, 0.95]

    @field_validator("series_identity")
    @classmethod
    def validate_series_identity(cls, value):
        if any(not isinstance(key, str) or not key.strip() for key in value):
            raise ValueError("series_identity keys must be nonblank strings")
        return value


class TimeSeriesSpecCreateRequest(OrdoAnalyticsScope):
    """Customer-controlled fields for an authoritative server-bound specification."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    analytics_run_id: uuid.UUID
    series_key: str = Field(min_length=1, max_length=140)
    target_indicator_code: str = Field(min_length=1, max_length=140)
    target_semantic: Literal["continuous", "count", "proportion_rate"]
    time_index_field: str = Field(min_length=1, max_length=140)
    frequency: Literal["daily", "weekly", "monthly", "quarterly", "annual"]
    series_key_fields: tuple[str, ...]
    observation_window_start: date
    observation_window_end: date
    observation_as_of: date
    minimum_history_periods: int = Field(ge=2)
    maximum_missing_ratio: float = Field(ge=0, le=1)
    missing_data_rule: Literal["fail", "exclude_periods", "explicit_gap"]
    outlier_policy: str = Field(min_length=1, max_length=1000)
    revision_policy: str = Field(min_length=1, max_length=1000)
    comparability_policy: str = Field(min_length=1, max_length=1000)
    transformation: Literal["none", "log1p", "difference", "seasonal_difference"] = "none"
    trend_requirement: Literal["none", "allowed", "required"]
    seasonality_period: int | None = Field(default=None, ge=2)
    candidate_families: tuple[
        Literal["naive", "seasonal_naive", "ets", "sarima", "sarimax", "count_time_series"], ...
    ]
    horizon: int = Field(ge=1)
    horizon_unit: Literal["days", "weeks", "months", "quarters", "years"]
    diagnostic_requirements: tuple[str, ...]
    limitations: tuple[str, ...]
    initial_train_periods: int = Field(ge=2)
    step_size: int = Field(ge=1)
    minimum_origins: int = Field(ge=2)
    required_metrics: tuple[str, ...]


class TimeSeriesSpecScopeRequest(OrdoAnalyticsScope):
    model_config = ConfigDict(extra="forbid")


class TimeSeriesSpecValidateRequest(TimeSeriesSpecScopeRequest):
    validation_note: str = Field(min_length=1, max_length=5000)
    validation_evidence_reference: str = Field(min_length=1, max_length=5000)


class TimeSeriesSpecRetireRequest(TimeSeriesSpecScopeRequest):
    retirement_note: str = Field(min_length=1, max_length=5000)


class SynthesisCreateRequest(OrdoAnalyticsScope):
    analytics_run_id: uuid.UUID
    scenario_id: uuid.UUID | None = None
    synthesis_type: Literal["monitoring", "scenario_review"] = "monitoring"
    model_key: str | None = None


class SynthesisReviewRequest(OrdoAnalyticsScope):
    decision: Literal["accepted", "rejected"]
    reviewer_note: str = Field(default="", max_length=5000)

class ScenarioContractMetadata(BaseModel):
    scenario_contract_version: Literal["ORDO-SCENARIO-CONTRACT-v1"] = "ORDO-SCENARIO-CONTRACT-v1"
    methodology_key: Literal["ordo_evidence_readiness_v1"] = "ordo_evidence_readiness_v1"
    methodology_version: Literal["1"] = "1"
    input_reference_identities: list[dict[str, Any]] = Field(default_factory=list)
    input_snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    limitations: list[str] = Field(default_factory=list)
    uncertainty_semantics: Literal["not_applicable_scenario_not_forecast"] = "not_applicable_scenario_not_forecast"
    human_review_state: Literal["pending", "reviewed", "rejected"] = "pending"
    scenario_is_forecast: Literal[False] = False
    causal_claim: Literal[False] = False
    automatic_policy_recommendation: Literal[False] = False
