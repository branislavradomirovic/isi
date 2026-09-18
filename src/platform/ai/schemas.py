from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ProductCodeValue = Literal["SIMPA", "ORDO"]
SensitivityValue = Literal["public", "internal", "sensitive"]


class AIScope(BaseModel):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: ProductCodeValue


class AICapabilityResponse(BaseModel):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: ProductCodeValue
    provider_default: str
    ollama_base_url: str
    development_stub_enabled: bool
    pgvector_available: bool
    pgvector_enabled: bool
    native_vector_table: bool
    human_accountability: str


class AIModelResponse(BaseModel):
    id: uuid.UUID
    model_key: str
    provider_type: str
    provider_name: str
    model_name: str
    purpose: str
    product_scope: str
    local_provider: bool
    enabled: bool
    development_only: bool = False


class AIPromptVersionResponse(BaseModel):
    id: uuid.UUID
    version_no: int
    checksum: str
    status: str
    output_schema: dict[str, Any] | None = None


class AIPromptResponse(BaseModel):
    id: uuid.UUID
    prompt_key: str
    product_scope: str
    title: str
    purpose: str
    active_version: AIPromptVersionResponse | None = None


class AIJobCreateRequest(AIScope):
    input_text: str = Field(min_length=1, max_length=20000)
    prompt_key: str = "foundation.diagnostic"
    model_key: str | None = None
    policy_key: str | None = None
    sensitivity: SensitivityValue = "internal"


class AIJobResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: ProductCodeValue
    status: str
    job_type: str
    sensitivity: str
    effective_provider_policy: str
    request_sha256: str
    output_text: str
    structured_output: dict[str, Any] | None
    provider_name: str
    model_name: str
    attempts: int
    latency_ms: int | None
    input_tokens: int | None
    output_tokens: int | None
    error_code: str
    error_message: str
    human_review_status: str
    prompt_key: str
    prompt_version: int
    policy_key: str
    model_key: str


class AIEmbeddingCreateRequest(AIScope):
    namespace: str
    source_type: str = Field(min_length=1, max_length=80)
    source_id: str = Field(min_length=1, max_length=220)
    chunk_index: int = Field(default=0, ge=0)
    text: str = Field(min_length=1, max_length=20000)
    model_key: str | None = None
    sensitivity: SensitivityValue = "internal"


class AIEmbeddingResponse(BaseModel):
    id: uuid.UUID
    namespace: str
    source_type: str
    source_id: str
    chunk_index: int
    content_sha256: str
    dimensions: int
    model_key: str
    provider_name: str
    model_name: str
    native_pgvector_written: bool


class AIModelRegistrationCreateRequest(AIScope):
    capability_key: str = Field(min_length=1, max_length=180)
    product_scope: Literal["SHARED", "SIMPA", "ORDO"]
    model_family: Literal["statistical_ml", "embedding", "llm", "vlm"]
    model_key: str = Field(min_length=1, max_length=220)
    runtime_model_id: uuid.UUID | None = None
    provider_name: str | None = Field(default=None, max_length=120)
    runtime_name: str | None = Field(default=None, max_length=300)
    version: str = Field(min_length=1, max_length=160)
    revision: str | None = Field(default=None, max_length=160)
    artifact_uri: str | None = Field(default=None, max_length=500)
    artifact_checksum: str | None = Field(default=None, min_length=64, max_length=64)
    provenance: dict[str, Any] = Field(default_factory=dict)
    lifecycle_state: Literal["candidate", "challenger", "champion"] = "candidate"


class AIModelRegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    capability_key: str
    product_scope: str
    model_family: str
    model_key: str
    runtime_model_id: uuid.UUID | None
    provider_name: str | None
    runtime_name: str | None
    version: str
    revision: str | None
    artifact_uri: str | None
    artifact_checksum: str | None
    provenance: dict[str, Any]
    registry_fingerprint: str
    lifecycle_state: str
    enabled: bool
    created_by_membership_id: uuid.UUID | None
    created_at: Any
    retired_at: Any | None


class AIGovernanceScopeRequest(AIScope):
    pass


class AIFallbackCreateRequest(AIScope):
    source_registration_id: uuid.UUID
    target_registration_id: uuid.UUID
    priority: int = Field(ge=1)
    trigger_codes: list[str] = Field(default_factory=list)
    semantically_equivalent: bool = False
    requires_human_review: bool = True
    provenance: str = Field(default="", max_length=2000)


class AIFallbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_registration_id: uuid.UUID
    target_registration_id: uuid.UUID
    priority: int
    trigger_codes: list[str]
    semantically_equivalent: bool
    requires_human_review: bool
    fingerprint: str
    provenance: str
    created_by_membership_id: uuid.UUID | None
    created_at: Any


class AIPromptRollbackCreateRequest(AIScope):
    source_prompt_version_id: uuid.UUID
    target_prompt_version_id: uuid.UUID
    provenance: str = Field(min_length=1, max_length=2000)


class AIPromptRollbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_prompt_version_id: uuid.UUID
    target_prompt_version_id: uuid.UUID
    source_checksum: str
    target_checksum: str
    fingerprint: str
    provenance: str
    created_by_membership_id: uuid.UUID | None
    created_at: Any


class AIEvaluationDatasetCreateRequest(AIScope):
    manifest: dict[str, Any]


class AIEvaluationDatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dataset_key: str
    version: str
    product_code: str
    schema_version: str
    capability_coverage: list[str]
    cases_sha256: str
    case_count: int
    source_provenance: str
    sensitivity: str
    frozen: bool
    frozen_at: Any
    approval_state: str
    owner: str
    foundation_only_not_production_promotion_evidence: bool
    dataset_fingerprint: str
    created_at: Any


class AIEvaluationRunCreateRequest(AIScope):
    dataset_id: uuid.UUID
    model_registration_id: uuid.UUID
    baseline_registration_id: uuid.UUID | None = None
    prompt_version_id: uuid.UUID | None = None
    policy_profile_id: uuid.UUID | None = None
    input_fingerprint: str = Field(min_length=64, max_length=64)
    environment_fingerprint: str = Field(min_length=64, max_length=64)
    provenance: dict[str, Any] = Field(default_factory=dict)


class AIEvaluationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    dataset_id: uuid.UUID
    model_registration_id: uuid.UUID
    baseline_registration_id: uuid.UUID | None
    prompt_version_id: uuid.UUID | None
    policy_profile_id: uuid.UUID | None
    input_fingerprint: str
    environment_fingerprint: str
    provenance: dict[str, Any]
    status: str
    result_fingerprint: str | None
    failure_reason: str
    created_by_membership_id: uuid.UUID | None
    created_at: Any
    started_at: Any | None
    completed_at: Any | None


class AIEvaluationResultCreateRequest(AIScope):
    result_type: Literal["metric", "safety", "reliability", "provenance", "evidence"]
    result_key: str = Field(min_length=1, max_length=180)
    payload: dict[str, Any]


class AIEvaluationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    evaluation_run_id: uuid.UUID
    sequence_no: int
    result_type: str
    result_key: str
    payload: dict[str, Any]
    fingerprint: str
    created_by_membership_id: uuid.UUID | None
    created_at: Any


class AIEvaluationTerminalRequest(AIScope):
    failure_reason: str = Field(default="", max_length=180)


class AIEvaluationReviewCreateRequest(AIScope):
    decision: Literal["pending", "approved", "changes_requested", "rejected"]
    notes: str = Field(default="", max_length=5000)
    evidence_reference: str = Field(default="", max_length=500)


class AIEvaluationReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    evaluation_run_id: uuid.UUID
    reviewer_membership_id: uuid.UUID
    decision: str
    is_final: bool
    notes: str
    evidence_reference: str
    fingerprint: str
    reviewed_at: Any
