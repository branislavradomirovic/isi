from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field


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


class MethodologyValidateRequest(SimpaAnalyticsScope):
    validation_note: str = Field(min_length=8, max_length=5000)


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
