from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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


IngestionIdempotencyKey = Annotated[
    str,
    Field(
        min_length=1,
        max_length=200,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$",
    ),
]


class _IngestionRunMutationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class IngestionRunCreate(_IngestionRunMutationRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]
    connector_contract_version_id: uuid.UUID
    schema_mapping_version_id: uuid.UUID
    idempotency_key: IngestionIdempotencyKey
    filename: str = Field(min_length=1, max_length=500)
    content_type: str = Field(default="application/octet-stream", max_length=200)
    content_base64: str = Field(min_length=1)
    cursor_after: str = Field(default="", max_length=1000)
    source_observed_at: datetime | None = None

    @field_validator("filename")
    @classmethod
    def filename_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("filename must not be blank")
        return value

    @field_validator("cursor_after")
    @classmethod
    def cursor_must_be_opaque_and_trimmed(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("cursor must not have leading or trailing whitespace")
        if any(ord(character) < 32 or ord(character) == 127 for character in value):
            raise ValueError("cursor must not contain control characters")
        return value


class IngestionRunRetryRequest(_IngestionRunMutationRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]


class IngestionRunResponse(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    run_no: int
    connector_contract_version_id: uuid.UUID
    schema_mapping_version_id: uuid.UUID
    record_governance_policy_version_id: uuid.UUID | None
    operational_policy_version_id: uuid.UUID | None
    execution_mode: Literal["INCREMENTAL", "BACKFILL", "REPLAY"]
    window_start_cursor: str
    window_end_cursor: str
    replay_of_run_id: uuid.UUID | None
    source_observed_at: datetime | None
    forward_cursor_committed: bool
    source_version_id: uuid.UUID
    inspection_job_id: uuid.UUID
    request_fingerprint: str
    payload_sha256: str
    cursor_before: str
    cursor_after: str
    status: Literal["QUEUED", "RUNNING", "SUCCEEDED", "FAILED"]
    attempts: int
    error_code: str
    error_message: str
    queued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


class IngestionRunCreateResponse(BaseModel):
    run: IngestionRunResponse
    reused: bool


OperationalIdentifier = Annotated[
    str,
    Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"),
]


class _IngestionOperationsMutationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class IngestionFreshnessContract(_IngestionOperationsMutationRequest):
    warning_after_seconds: int = Field(ge=0)
    reject_after_seconds: int = Field(ge=0)
    missing_evidence_action: Literal["WARN", "REJECT"]

    @field_validator("reject_after_seconds")
    @classmethod
    def reject_must_not_precede_warning(cls, value: int, info):
        warning = info.data.get("warning_after_seconds")
        if warning is not None and value < warning:
            raise ValueError("reject_after_seconds must be >= warning_after_seconds")
        return value


class IngestionQualityContract(_IngestionOperationsMutationRequest):
    required_check_codes: list[OperationalIdentifier] = Field(default_factory=list, max_length=200)
    warning_quarantine_ratio: float = Field(ge=0, le=1)
    reject_quarantine_ratio: float = Field(ge=0, le=1)
    missing_required_check_action: Literal["WARN", "REJECT"]

    @field_validator("required_check_codes")
    @classmethod
    def required_checks_are_unique(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value]
        if len(normalized) != len(set(normalized)):
            raise ValueError("required_check_codes must be unique")
        return sorted(normalized)

    @field_validator("reject_quarantine_ratio")
    @classmethod
    def reject_ratio_must_not_precede_warning(cls, value: float, info):
        warning = info.data.get("warning_quarantine_ratio")
        if warning is not None and value < warning:
            raise ValueError("reject_quarantine_ratio must be >= warning_quarantine_ratio")
        return value


class IngestionBackfillContract(_IngestionOperationsMutationRequest):
    backfill_allowed: bool
    replay_allowed: bool
    require_explicit_window: Literal[True] = True
    cursor_mutation_allowed: Literal[False] = False


class IngestionDeadLetterContract(_IngestionOperationsMutationRequest):
    max_retry_attempts: int = Field(ge=1)
    terminal_error_codes: list[OperationalIdentifier] = Field(default_factory=list, max_length=200)
    rejected_evaluation_to_dead_letter: bool

    @field_validator("terminal_error_codes")
    @classmethod
    def terminal_codes_are_unique(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value]
        if len(normalized) != len(set(normalized)):
            raise ValueError("terminal_error_codes must be unique")
        return sorted(normalized)


class IngestionOperationalPolicyVersionCreate(_IngestionOperationsMutationRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]
    connector_contract_version_id: uuid.UUID
    schema_mapping_version_id: uuid.UUID
    record_governance_policy_version_id: uuid.UUID
    freshness_contract: IngestionFreshnessContract
    quality_contract: IngestionQualityContract
    backfill_contract: IngestionBackfillContract
    dead_letter_contract: IngestionDeadLetterContract


class IngestionOperationalPolicyActivationRequest(_IngestionOperationsMutationRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]


class IngestionOperationalPolicyVersionResponse(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    connector_contract_version_id: uuid.UUID
    schema_mapping_version_id: uuid.UUID
    record_governance_policy_version_id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]
    version_no: int
    contract_format_version: Literal[1]
    freshness_contract: IngestionFreshnessContract
    quality_contract: IngestionQualityContract
    backfill_contract: IngestionBackfillContract
    dead_letter_contract: IngestionDeadLetterContract
    fingerprint: str
    lifecycle_state: Literal["DRAFT", "ACTIVE", "RETIRED"]
    created_by_membership_id: uuid.UUID | None
    activated_by_membership_id: uuid.UUID | None
    retired_by_membership_id: uuid.UUID | None
    created_at: datetime
    activated_at: datetime | None
    retired_at: datetime | None


class IngestionBackfillCreate(_IngestionOperationsMutationRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]
    connector_contract_version_id: uuid.UUID
    schema_mapping_version_id: uuid.UUID
    idempotency_key: IngestionIdempotencyKey
    filename: str = Field(min_length=1, max_length=500)
    content_type: str = Field(default="application/octet-stream", max_length=200)
    content_base64: str = Field(min_length=1)
    source_observed_at: datetime | None = None
    window_start_cursor: str = Field(min_length=1, max_length=1000)
    window_end_cursor: str = Field(min_length=1, max_length=1000)

    @field_validator("filename", "window_start_cursor", "window_end_cursor")
    @classmethod
    def nonblank_trimmed_value(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("value must be nonblank and trimmed")
        if any(ord(character) < 32 or ord(character) == 127 for character in value):
            raise ValueError("value must not contain control characters")
        return value


class IngestionReplayCreate(_IngestionOperationsMutationRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]
    idempotency_key: IngestionIdempotencyKey


class IngestionEvaluationResponse(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    ingestion_run_id: uuid.UUID
    operational_policy_version_id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]
    freshness_status: Literal["FRESH", "STALE_WARNING", "STALE_REJECTED", "UNKNOWN", "NOT_APPLICABLE"]
    quality_status: Literal["PASS", "WARNING", "REJECTED", "UNKNOWN"]
    decision: Literal["ACCEPTED", "ACCEPTED_WITH_WARNING", "REJECTED", "DEAD_LETTERED"]
    freshness_details: dict[str, Any]
    quality_details: dict[str, Any]
    record_metrics: dict[str, Any]
    evidence_fingerprint: str
    evaluated_at: datetime


class IngestionDeadLetterRequeueRequest(_IngestionOperationsMutationRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]
    idempotency_key: IngestionIdempotencyKey


class IngestionDeadLetterResolveRequest(_IngestionOperationsMutationRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]
    status: Literal["RESOLVED", "DISCARDED"] = "RESOLVED"
    resolution_note: str = Field(min_length=1, max_length=1000)

    @field_validator("resolution_note")
    @classmethod
    def note_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("resolution_note must not be blank")
        return value


class IngestionDeadLetterResponse(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    ingestion_run_id: uuid.UUID
    evaluation_id: uuid.UUID | None
    operational_policy_version_id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]
    reason_code: str
    error_category: str
    details: dict[str, Any]
    status: Literal["OPEN", "REQUEUED", "RESOLVED", "DISCARDED"]
    created_at: datetime
    resolved_at: datetime | None
    resolver_membership_id: uuid.UUID | None
    resolution_note: str
    replacement_run_id: uuid.UUID | None


class GovernedIngestionOutputResponse(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    source_version_id: uuid.UUID
    ingestion_run_id: uuid.UUID
    evaluation_id: uuid.UUID
    connector_contract_version_id: uuid.UUID
    schema_mapping_version_id: uuid.UUID
    record_governance_policy_version_id: uuid.UUID
    operational_policy_version_id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]
    contract_version: Literal[1]
    record_count: int
    current_record_count: int
    duplicate_record_count: int
    quarantined_record_count: int
    superseded_record_count: int
    output_fingerprint: str
    created_at: datetime


ConnectorIdentifier = Annotated[
    str,
    Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$"),
]


class _ConnectorMutationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConnectorContractVersionCreate(_ConnectorMutationRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]
    connector_kind: ConnectorIdentifier
    transport: ConnectorIdentifier
    configuration: dict[str, Any] = Field(default_factory=dict)
    credential_reference: str = Field(default="", max_length=500)
    capabilities: list[ConnectorIdentifier] = Field(default_factory=list, max_length=200)


class ConnectorContractActivationRequest(_ConnectorMutationRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]


class ConnectorContractVersionResponse(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    version_no: int
    connector_kind: str
    transport: str
    configuration: dict[str, Any]
    credential_reference: str
    capabilities: list[str]
    fingerprint: str
    lifecycle_state: Literal["DRAFT", "ACTIVE", "RETIRED"]
    created_by_membership_id: uuid.UUID | None
    activated_by_membership_id: uuid.UUID | None
    retired_by_membership_id: uuid.UUID | None
    created_at: datetime
    activated_at: datetime | None
    retired_at: datetime | None


SourceFieldName = Annotated[str, Field(min_length=1, max_length=500)]
MissingValueToken = Annotated[str, Field(max_length=500)]


class SourceSchemaField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ordinal: int = Field(ge=1)
    source_field: SourceFieldName
    logical_type: Literal["STRING", "INTEGER", "NUMBER", "BOOLEAN", "DATE", "DATETIME", "JSON"]
    required: bool
    nullable: bool
    missing_values: list[MissingValueToken] = Field(default_factory=list, max_length=200)


class SourceFieldMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_field: SourceFieldName
    disposition: Literal["MAP", "IGNORE"]
    field_key: str | None = Field(default=None, max_length=120)


class _SourceSchemaMappingMutationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceSchemaMappingVersionCreate(_SourceSchemaMappingMutationRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]
    connector_contract_version_id: uuid.UUID
    schema_kind: Literal["TABULAR", "RECORD"]
    source_schema: list[SourceSchemaField] = Field(min_length=1, max_length=500)
    field_mapping: list[SourceFieldMapping] = Field(min_length=1, max_length=500)
    missing_value_policy: Literal["PRESERVE_MISSING"] = "PRESERVE_MISSING"
    unexpected_field_policy: Literal["REJECT", "IGNORE"] = "REJECT"


class SourceSchemaMappingActivationRequest(_SourceSchemaMappingMutationRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]


class SourceSchemaMappingVersionResponse(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    connector_contract_version_id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    version_no: int
    contract_format_version: Literal[1]
    schema_kind: Literal["TABULAR", "RECORD"]
    source_schema: list[SourceSchemaField]
    field_mapping: list[SourceFieldMapping]
    missing_value_policy: Literal["PRESERVE_MISSING"]
    unexpected_field_policy: Literal["REJECT", "IGNORE"]
    fingerprint: str
    lifecycle_state: Literal["DRAFT", "ACTIVE", "RETIRED"]
    created_by_membership_id: uuid.UUID | None
    activated_by_membership_id: uuid.UUID | None
    retired_by_membership_id: uuid.UUID | None
    created_at: datetime
    activated_at: datetime | None
    retired_at: datetime | None


class _RecordGovernanceMutationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RecordGovernancePolicyVersionCreate(_RecordGovernanceMutationRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]
    connector_contract_version_id: uuid.UUID
    schema_mapping_version_id: uuid.UUID
    identity_field_keys: list[str] = Field(min_length=1, max_length=500)
    missing_identity_policy: Literal["QUARANTINE"] = "QUARANTINE"
    exact_duplicate_policy: Literal["LINK_EXISTING"] = "LINK_EXISTING"
    conflict_policy: Literal["QUARANTINE"] = "QUARANTINE"


class RecordGovernancePolicyActivationRequest(_RecordGovernanceMutationRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]


class RecordGovernancePolicyVersionResponse(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    connector_contract_version_id: uuid.UUID
    schema_mapping_version_id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]
    version_no: int
    contract_format_version: Literal[1]
    identity_field_keys: list[str]
    missing_identity_policy: Literal["QUARANTINE"]
    exact_duplicate_policy: Literal["LINK_EXISTING"]
    conflict_policy: Literal["QUARANTINE"]
    fingerprint: str
    lifecycle_state: Literal["DRAFT", "ACTIVE", "RETIRED"]
    created_by_membership_id: uuid.UUID | None
    activated_by_membership_id: uuid.UUID | None
    retired_by_membership_id: uuid.UUID | None
    created_at: datetime
    activated_at: datetime | None
    retired_at: datetime | None


class RecordQuarantineListItem(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    source_version_id: uuid.UUID
    ingestion_run_id: uuid.UUID
    connector_contract_version_id: uuid.UUID
    schema_mapping_version_id: uuid.UUID
    record_governance_policy_version_id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]
    source_record_ordinal: int
    source_locator: str
    entity_id: uuid.UUID | None
    identity_fingerprint: str
    content_fingerprint: str
    disposition: Literal["QUARANTINED"]
    duplicate_of_record_id: uuid.UUID | None
    conflict_with_record_id: uuid.UUID | None
    quarantine_reason: str | None
    created_at: datetime
    updated_at: datetime


class RecordQuarantineDetailResponse(RecordQuarantineListItem):
    normalized_record: dict[str, Any]
    current_accepted_record_id: uuid.UUID | None
    current_accepted_record: dict[str, Any] | None


class RecordResolutionCreate(_RecordGovernanceMutationRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]
    decision: Literal["REJECT_INCOMING", "ACCEPT_INCOMING"]
    resolution_reference: str = Field(min_length=1, max_length=1000)
    reason: str | None = Field(default=None, max_length=1000)
    # Omitted by historical callers; explicit null pins the absence of a current record.
    expected_current_accepted_record_id: uuid.UUID | None = None

    @field_validator("resolution_reference")
    @classmethod
    def resolution_reference_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("resolution_reference must not be blank")
        return value


class RecordResolutionResponse(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]
    entity_id: uuid.UUID
    quarantined_record_id: uuid.UUID
    existing_accepted_record_id: uuid.UUID | None
    decision: Literal["REJECT_INCOMING", "ACCEPT_INCOMING"]
    resolution_reference: str
    reason: str | None
    resolved_by_membership_id: uuid.UUID | None
    resolved_at: datetime


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


class AnalyticalDatasetFieldContract(_AnalyticalRequest):
    field_key: str = Field(min_length=1, max_length=240, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    logical_type: Literal["STRING", "INTEGER", "NUMBER", "BOOLEAN", "DATE", "DATETIME", "JSON"]
    required: bool
    semantic_role: Literal["KEY", "DIMENSION", "MEASURE", "ATTRIBUTE"]


class AnalyticalDatasetContractVersionCreate(_AnalyticalRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]
    field_contract: list[AnalyticalDatasetFieldContract] = Field(min_length=1)
    temporal_mode: Literal["STATIC", "POINT_IN_TIME", "PERIOD"]
    temporal_key_fields: list[str] = Field(default_factory=list)
    granularity_key_fields: list[str] = Field(min_length=1)
    missing_value_policy: Literal["PRESERVE_MISSING"] = "PRESERVE_MISSING"

    @model_validator(mode="after")
    def validate_contract_semantics(self):
        field_keys = [field.field_key for field in self.field_contract]
        if len(field_keys) != len(set(field_keys)):
            raise ValueError("analytical_contract_field_keys_duplicate")
        if len(self.temporal_key_fields) != len(set(self.temporal_key_fields)):
            raise ValueError("analytical_contract_temporal_keys_duplicate")
        if len(self.granularity_key_fields) != len(set(self.granularity_key_fields)):
            raise ValueError("analytical_contract_granularity_keys_duplicate")
        declared = set(field_keys)
        if not set(self.temporal_key_fields).issubset(declared):
            raise ValueError("analytical_contract_temporal_key_missing")
        if not set(self.granularity_key_fields).issubset(declared):
            raise ValueError("analytical_contract_granularity_key_missing")
        if self.temporal_mode == "STATIC" and self.temporal_key_fields:
            raise ValueError("analytical_contract_static_temporal_keys_forbidden")
        if self.temporal_mode == "POINT_IN_TIME" and len(self.temporal_key_fields) != 1:
            raise ValueError("analytical_contract_point_temporal_key_required")
        if self.temporal_mode == "PERIOD" and len(self.temporal_key_fields) != 2:
            raise ValueError("analytical_contract_period_temporal_keys_required")
        by_key = {field.field_key: field for field in self.field_contract}
        if any(not by_key[key].required for key in self.granularity_key_fields):
            raise ValueError("analytical_contract_granularity_key_must_be_required")
        if any(by_key[key].semantic_role != "KEY" for key in self.granularity_key_fields):
            raise ValueError("analytical_contract_granularity_key_role_invalid")
        if any(not by_key[key].required or by_key[key].logical_type not in {"DATE", "DATETIME"}
               for key in self.temporal_key_fields):
            raise ValueError("analytical_contract_temporal_key_type_invalid")
        return self


class AnalyticalDatasetContractVersionResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    version_no: int
    contract_format_version: int
    field_contract: list[AnalyticalDatasetFieldContract]
    temporal_mode: str
    temporal_key_fields: list[str]
    granularity_key_fields: list[str]
    missing_value_policy: str
    fingerprint: str
    lifecycle_state: str
    created_by_membership_id: uuid.UUID | None
    activated_by_membership_id: uuid.UUID | None
    retired_by_membership_id: uuid.UUID | None
    created_at: datetime
    activated_at: datetime | None
    retired_at: datetime | None


class AnalyticalDatasetContractActivationRequest(_AnalyticalRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: Literal["SIMPA", "ORDO"]


class AnalyticalSnapshotCreate(_AnalyticalRequest):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str = Field(pattern=r"^(SIMPA|ORDO)$")
    dataset_contract_version_id: uuid.UUID
    governed_output_ids: list[uuid.UUID] = Field(min_length=1)
    methodology_reference: str = Field(min_length=1, max_length=500)
    methodology_version: str = Field(min_length=1, max_length=120)
    build_reference: str = Field(min_length=1, max_length=500)


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


class GovernedOutputLineageResponse(BaseModel):
    governed_output_id: uuid.UUID
    governed_output_fingerprint: str
    source_id: uuid.UUID
    source_version_id: uuid.UUID
    ingestion_run_id: uuid.UUID
    evaluation_id: uuid.UUID
    evaluation_fingerprint: str
    evaluation_decision: str
    classification: DataClassification
    privacy_category: PrivacyCategory
    ai_use_policy: AIUsePolicy
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str


class SnapshotRecordMembershipResponse(BaseModel):
    governed_output_id: uuid.UUID
    normalized_record_id: uuid.UUID
    source_id: uuid.UUID
    source_version_id: uuid.UUID
    ingestion_run_id: uuid.UUID
    source_record_ordinal: int
    source_locator: str
    identity_fingerprint: str
    content_fingerprint: str
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str


class AnalyticalSnapshotResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    version_no: int
    dataset_contract_version_id: uuid.UUID | None
    dataset_contract_fingerprint: str
    lineage_mode: str
    temporal_mode: str
    temporal_key_fields: list[str]
    granularity_key_fields: list[str]
    missing_value_policy: str
    analytical_quality_state: str
    record_count: int
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
    governed_outputs: list[GovernedOutputLineageResponse] = Field(default_factory=list)
    record_membership: list[SnapshotRecordMembershipResponse] = Field(default_factory=list)


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
    snapshot_lineage_mode: str
    dataset_contract_version_id: uuid.UUID | None
    dataset_contract_fingerprint: str
    analytical_quality_state: str
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
