from __future__ import annotations

import uuid
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field


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
