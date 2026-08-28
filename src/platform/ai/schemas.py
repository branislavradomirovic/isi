from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


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
