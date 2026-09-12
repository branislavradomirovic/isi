from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from src.platform.data.governance import AIUsePolicy, DataClassification, GovernanceState, PrivacyCategory


class UploadCreateRequest(BaseModel):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    source_name: str = Field(min_length=1, max_length=300)
    filename: str = Field(min_length=1, max_length=500)
    content_type: str = Field(default="application/octet-stream", max_length=200)
    content_base64: str = Field(min_length=1)


class VersionCreateRequest(BaseModel):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    filename: str = Field(min_length=1, max_length=500)
    content_type: str = Field(default="application/octet-stream", max_length=200)
    content_base64: str = Field(min_length=1)


class ScopeQuery(BaseModel):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str


class QualityResultResponse(BaseModel):
    check_code: str
    status: str
    message: str
    metric_name: str = ""
    metric_value: str = ""


class VersionResponse(BaseModel):
    id: uuid.UUID
    version_no: int
    original_filename: str
    extension: str
    content_type: str
    size_bytes: int
    sha256: str
    ingest_status: str
    detected_format: str
    row_count: int | None
    column_count: int | None
    sheet_count: int | None
    schema_fingerprint: str
    created_at: datetime
    quality: list[QualityResultResponse] = Field(default_factory=list)


class SourceSummaryResponse(BaseModel):
    id: uuid.UUID
    name: str
    source_kind: str
    product_code: str
    workspace_id: uuid.UUID
    status: str
    created_at: datetime
    latest_version: VersionResponse | None = None


class SourceDetailResponse(SourceSummaryResponse):
    versions: list[VersionResponse]


class IngestionJobResponse(BaseModel):
    id: uuid.UUID
    version_id: uuid.UUID
    job_type: str
    status: str
    backend: str
    progress: int
    attempts: int
    error_code: str
    error_message: str
    queued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class UploadResponse(BaseModel):
    source: SourceSummaryResponse
    version: VersionResponse
    job: IngestionJobResponse
    storage_reused: bool


class SourceGovernanceResponse(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    classification: DataClassification
    privacy_category: PrivacyCategory
    processing_purpose: str
    data_owner_ref: str
    data_steward_membership_id: uuid.UUID | None
    retention_policy_id: uuid.UUID | None
    ai_use_policy: AIUsePolicy
    export_policy: str
    governance_state: GovernanceState
    classification_rationale: str
    revision: int
    created_by_membership_id: uuid.UUID | None
    updated_by_membership_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class SourceGovernanceUpdate(BaseModel):
    expected_revision: int = Field(ge=1)
    classification: DataClassification | None = None
    privacy_category: PrivacyCategory | None = None
    processing_purpose: str | None = Field(default=None, max_length=1000)
    data_owner_ref: str | None = Field(default=None, max_length=300)
    data_steward_membership_id: uuid.UUID | None = None
    retention_policy_id: uuid.UUID | None = None
    ai_use_policy: AIUsePolicy | None = None
    export_policy: str | None = Field(default=None, max_length=32)
    governance_state: GovernanceState | None = None
    classification_rationale: str | None = Field(default=None, max_length=1000)


class RetentionPolicyCreate(BaseModel):
    policy_code: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    version_no: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=240)
    status: str = Field(default="active", pattern=r"^(active|retired)$")
    retention_days: int | None = Field(default=None, ge=0)
    no_auto_delete: bool = True
    manual_review_required: bool = True
    archive_before_purge: bool = True
    tombstone_retention_days: int | None = Field(default=None, ge=0)
    reference_text: str = Field(default="", max_length=1000)


class RetentionPolicyResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    policy_code: str
    version_no: int
    name: str
    status: str
    retention_days: int | None
    no_auto_delete: bool
    manual_review_required: bool
    archive_before_purge: bool
    tombstone_retention_days: int | None
    reference_text: str
    created_by_membership_id: uuid.UUID | None
    created_at: datetime


class RetentionStateResponse(BaseModel):
    id: uuid.UUID
    version_id: uuid.UUID
    source_id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    retention_start_at: datetime | None
    retention_due_at: datetime | None
    hold_active: bool
    hold_reason_ref: str
    purge_requested_at: datetime | None
    purge_requested_by_membership_id: uuid.UUID | None
    purge_approved_at: datetime | None
    purge_approved_by_membership_id: uuid.UUID | None
    purge_executed_at: datetime | None
    purge_executed_by_membership_id: uuid.UUID | None
    purge_result: str
    tombstone_checksum: str
    created_at: datetime
    updated_at: datetime
