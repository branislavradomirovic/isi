from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.platform.data.governance import (
    AIUsePolicy,
    AnalyticalAIAction,
    AnalyticalSnapshotState,
    AnonymizationStatus,
    ContentState,
    DataClassification,
    ExportPolicy,
    GovernanceState,
    PrivacyCategory,
    PurgeStatus,
)


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
    content_state: ContentState
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
    export_policy: ExportPolicy
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
    export_policy: ExportPolicy | None = None
    governance_state: GovernanceState | None = None
    classification_rationale: str | None = Field(default=None, max_length=1000)
    verified_anonymization_record_id: uuid.UUID | None = None


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
    hold_placed_at: datetime | None
    hold_placed_by_membership_id: uuid.UUID | None
    hold_released_at: datetime | None
    hold_released_by_membership_id: uuid.UUID | None
    purge_status: PurgeStatus
    revision: int
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


class RetentionMutationRequest(BaseModel):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    expected_revision: int = Field(ge=1)


class HoldPlaceRequest(RetentionMutationRequest):
    reason_reference: str = Field(min_length=1, max_length=500)


class AnonymizationProposalCreate(BaseModel):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    input_version_id: uuid.UUID
    output_version_id: uuid.UUID
    method_code: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    method_version: str = Field(min_length=1, max_length=120)
    method_reference: str = Field(min_length=1, max_length=500)
    parameter_reference: str = Field(default="", max_length=1000)
    evidence_checksum: str = Field(default="", max_length=64)
    evidence_reference: str = Field(min_length=1, max_length=1000)
    classification_after: DataClassification
    privacy_category_after: PrivacyCategory


class AnonymizationReviewRequest(BaseModel):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    decision: AnonymizationStatus
    review_reference: str = Field(min_length=1, max_length=1000)
    review_reason: str = Field(default="", max_length=1000)


class AnonymizationRecordResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    input_version_id: uuid.UUID
    output_version_id: uuid.UUID
    method_code: str
    method_version: str
    method_reference: str
    parameter_reference: str
    evidence_checksum: str
    evidence_reference: str
    classification_before: DataClassification
    classification_after: DataClassification
    privacy_category_before: PrivacyCategory
    privacy_category_after: PrivacyCategory
    status: AnonymizationStatus
    proposed_by_membership_id: uuid.UUID | None
    proposed_at: datetime
    reviewed_by_membership_id: uuid.UUID | None
    reviewed_at: datetime | None
    review_reference: str
    review_reason: str


class ExportRequest(BaseModel):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    purpose_reference: str = Field(min_length=1, max_length=1000)


class _AnalyticalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AnalyticalDatasetCreate(_AnalyticalRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str = Field(pattern=r"^(SIMPA|ORDO)$")
    code: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    name: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=1000)
    methodology_reference: str = Field(min_length=1, max_length=500)
    methodology_version: str = Field(min_length=1, max_length=120)


class AnalyticalDatasetResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    code: str
    name: str
    description: str
    methodology_reference: str
    methodology_version: str
    revision: int
    created_by_membership_id: uuid.UUID | None
    updated_by_membership_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class AnalyticalSnapshotCreate(_AnalyticalRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str = Field(pattern=r"^(SIMPA|ORDO)$")
    source_version_ids: list[uuid.UUID] = Field(min_length=1)
    methodology_reference: str = Field(min_length=1, max_length=500)
    methodology_version: str = Field(min_length=1, max_length=120)
    build_reference: str = Field(default="", max_length=500)


class AnalyticalTransitionRequest(_AnalyticalRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str = Field(pattern=r"^(SIMPA|ORDO)$")
    expected_revision: int = Field(ge=1)
    target_state: AnalyticalSnapshotState


class FeatureTransitionRequest(_AnalyticalRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str = Field(pattern=r"^(SIMPA|ORDO)$")
    expected_revision: int = Field(ge=1)
    target_state: GovernanceState


class SourceLineageResponse(BaseModel):
    source_id: uuid.UUID
    source_version_id: uuid.UUID
    source_version_no: int
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    classification: DataClassification
    privacy_category: PrivacyCategory
    ai_use_policy: AIUsePolicy
    source_fingerprint: str


class AnalyticalSnapshotResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    version_no: int
    methodology_reference: str
    methodology_version: str
    build_reference: str
    classification: DataClassification
    privacy_category: PrivacyCategory
    ai_use_policy: AIUsePolicy
    state: AnalyticalSnapshotState
    fingerprint: str
    revision: int
    invalidated: bool
    invalidation_reason: str
    invalidated_at: datetime | None
    invalidated_by_membership_id: uuid.UUID | None
    frozen_at: datetime | None
    created_by_membership_id: uuid.UUID | None
    updated_by_membership_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    source_versions: list[SourceLineageResponse] = Field(default_factory=list)


class AnalyticalFeatureCreate(_AnalyticalRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str = Field(pattern=r"^(SIMPA|ORDO)$")
    code: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    name: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=1000)
    methodology_reference: str = Field(min_length=1, max_length=500)
    methodology_version: str = Field(min_length=1, max_length=120)


class AnalyticalFeatureResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    code: str
    name: str
    description: str
    methodology_reference: str
    methodology_version: str
    revision: int
    created_by_membership_id: uuid.UUID | None
    updated_by_membership_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class AnalyticalFeatureVersionCreate(_AnalyticalRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str = Field(pattern=r"^(SIMPA|ORDO)$")
    snapshot_ids: list[uuid.UUID] = Field(min_length=1)
    methodology_reference: str = Field(min_length=1, max_length=500)
    methodology_version: str = Field(min_length=1, max_length=120)


class SnapshotInputResponse(BaseModel):
    snapshot_id: uuid.UUID
    snapshot_version_no: int
    snapshot_fingerprint: str
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str


class AnalyticalFeatureVersionResponse(BaseModel):
    id: uuid.UUID
    feature_id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    version_no: int
    methodology_reference: str
    methodology_version: str
    classification: DataClassification
    privacy_category: PrivacyCategory
    ai_use_policy: AIUsePolicy
    state: GovernanceState
    fingerprint: str
    revision: int
    invalidated: bool
    invalidation_reason: str
    invalidated_at: datetime | None
    invalidated_by_membership_id: uuid.UUID | None
    frozen_at: datetime | None
    created_by_membership_id: uuid.UUID | None
    updated_by_membership_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    snapshot_inputs: list[SnapshotInputResponse] = Field(default_factory=list)


class AnalyticalLineageResponse(BaseModel):
    dataset: AnalyticalDatasetResponse
    snapshot: AnalyticalSnapshotResponse
    dependent_feature_versions: list[AnalyticalFeatureVersionResponse] = Field(default_factory=list)


class AnalyticalAIEligibilityRequest(_AnalyticalRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str = Field(pattern=r"^(SIMPA|ORDO)$")
    artifact_type: str = Field(pattern=r"^(snapshot|feature_version)$")
    artifact_id: uuid.UUID
    action: AnalyticalAIAction
    namespace: str = Field(min_length=1, max_length=160)


class AnalyticalAIEligibilityResponse(BaseModel):
    allowed: bool
    requested_action: AnalyticalAIAction
    reason_code: str
    requires_separate_approval: bool
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    artifact_type: str
    artifact_id: uuid.UUID
    artifact_version: int
    lifecycle_state: str
    classification: DataClassification
    privacy_category: PrivacyCategory
    ai_use_policy: AIUsePolicy
    namespace: str
    human_review_required: bool
    provenance_fingerprint: str
