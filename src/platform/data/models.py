from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class DataSource(Base):
    __tablename__ = "core_data_sources"
    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_core_data_sources_workspace_name"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_data_sources_product"),
        CheckConstraint("source_kind IN ('dataset', 'document')", name="ck_core_data_sources_kind"),
        CheckConstraint("status IN ('active', 'archived')", name="ck_core_data_sources_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    source_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active", server_default="active")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class DataSourceVersion(Base):
    __tablename__ = "core_data_source_versions"
    __table_args__ = (
        UniqueConstraint("source_id", "version_no", name="uq_core_data_source_versions_source_version"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_data_source_versions_product"),
        CheckConstraint(
            "ingest_status IN ('uploaded', 'queued', 'running', 'succeeded', 'failed')",
            name="ck_core_data_source_versions_ingest_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False, index=True)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    extension: Mapped[str] = mapped_column(String(32), nullable=False)
    content_type: Mapped[str] = mapped_column(String(200), nullable=False, default="application/octet-stream", server_default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_key: Mapped[str] = mapped_column(String(1200), nullable=False)
    ingest_status: Mapped[str] = mapped_column(String(24), nullable=False, default="uploaded", server_default="uploaded")
    detected_format: Mapped[str] = mapped_column(String(32), nullable=False, default="", server_default="")
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sheet_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    schema_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DataRetentionPolicy(Base):
    __tablename__ = "core_data_retention_policies"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "policy_code",
            "version_no",
            name="uq_core_data_retention_policies_workspace_code_version",
        ),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_data_retention_policies_product"),
        CheckConstraint("version_no >= 1", name="ck_core_data_retention_policies_version"),
        CheckConstraint("status IN ('active', 'retired')", name="ck_core_data_retention_policies_status"),
        CheckConstraint("retention_days IS NULL OR retention_days >= 0", name="ck_core_data_retention_policies_days"),
        CheckConstraint(
            "tombstone_retention_days IS NULL OR tombstone_retention_days >= 0",
            name="ck_core_data_retention_policies_tombstone_days",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False, index=True)
    policy_code: Mapped[str] = mapped_column(String(120), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active", server_default="active")
    retention_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    no_auto_delete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    manual_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    archive_before_purge: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    tombstone_retention_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reference_text: Mapped[str] = mapped_column(String(1000), nullable=False, default="", server_default="")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DataSourceGovernanceProfile(Base):
    __tablename__ = "core_data_source_governance_profiles"
    __table_args__ = (
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_data_source_governance_profiles_product"),
        CheckConstraint(
            "classification IN ('UNCLASSIFIED', 'PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED')",
            name="ck_core_data_source_governance_profiles_classification",
        ),
        CheckConstraint(
            "privacy_category IN ('NONE_DECLARED', 'AGGREGATE_NON_PERSONAL', 'PSEUDONYMOUS_OR_LINKABLE', "
            "'PERSONAL_DATA', 'SENSITIVE_PERSONAL_DATA', 'UNKNOWN')",
            name="ck_core_data_source_governance_profiles_privacy",
        ),
        CheckConstraint(
            "ai_use_policy IN ('PROHIBITED', 'LOCAL_ANALYSIS_ONLY', 'RAG_RETRIEVAL_ALLOWED', "
            "'MODEL_EVALUATION_ALLOWED', 'MODEL_TRAINING_REQUIRES_SEPARATE_APPROVAL')",
            name="ck_core_data_source_governance_profiles_ai_use",
        ),
        CheckConstraint("export_policy = 'PROHIBITED'", name="ck_core_data_source_governance_profiles_export"),
        CheckConstraint(
            "governance_state IN ('DRAFT', 'GOVERNED', 'FROZEN', 'RETIRED')",
            name="ck_core_data_source_governance_profiles_state",
        ),
        CheckConstraint("revision >= 1", name="ck_core_data_source_governance_profiles_revision"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_sources.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False, index=True)
    classification: Mapped[str] = mapped_column(String(32), nullable=False, default="UNCLASSIFIED", server_default="UNCLASSIFIED")
    privacy_category: Mapped[str] = mapped_column(String(40), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    processing_purpose: Mapped[str] = mapped_column(String(1000), nullable=False, default="", server_default="")
    data_owner_ref: Mapped[str] = mapped_column(String(300), nullable=False, default="", server_default="")
    data_steward_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    retention_policy_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_data_retention_policies.id", ondelete="SET NULL"), nullable=True)
    ai_use_policy: Mapped[str] = mapped_column(String(64), nullable=False, default="PROHIBITED", server_default="PROHIBITED")
    export_policy: Mapped[str] = mapped_column(String(32), nullable=False, default="PROHIBITED", server_default="PROHIBITED")
    governance_state: Mapped[str] = mapped_column(String(24), nullable=False, default="DRAFT", server_default="DRAFT")
    classification_rationale: Mapped[str] = mapped_column(String(1000), nullable=False, default="", server_default="")
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    updated_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class DataRetentionState(Base):
    __tablename__ = "core_data_retention_states"
    __table_args__ = (
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_data_retention_states_product"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_source_versions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False, index=True)
    retention_start_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retention_due_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hold_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    hold_reason_ref: Mapped[str] = mapped_column(String(500), nullable=False, default="", server_default="")
    purge_requested_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    purge_requested_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    purge_approved_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    purge_approved_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    purge_executed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    purge_executed_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    purge_result: Mapped[str] = mapped_column(String(500), nullable=False, default="", server_default="")
    tombstone_checksum: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class IngestionJob(Base):
    __tablename__ = "core_ingestion_jobs"
    __table_args__ = (
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_ingestion_jobs_product"),
        CheckConstraint("job_type IN ('inspect', 'validate')", name="ck_core_ingestion_jobs_type"),
        CheckConstraint("status IN ('queued', 'running', 'succeeded', 'failed')", name="ck_core_ingestion_jobs_status"),
        CheckConstraint("backend IN ('inline', 'rq')", name="ck_core_ingestion_jobs_backend"),
        CheckConstraint("progress >= 0 AND progress <= 100", name="ck_core_ingestion_jobs_progress"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_source_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False, index=True)
    job_type: Mapped[str] = mapped_column(String(24), nullable=False, default="inspect", server_default="inspect")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="queued", server_default="queued")
    backend: Mapped[str] = mapped_column(String(16), nullable=False, default="inline", server_default="inline")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    rq_job_id: Mapped[str] = mapped_column(String(160), nullable=False, default="", server_default="")
    error_code: Mapped[str] = mapped_column(String(120), nullable=False, default="", server_default="")
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    queued_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class DataQualityResult(Base):
    __tablename__ = "core_data_quality_results"
    __table_args__ = (
        CheckConstraint("status IN ('pass', 'warn', 'fail')", name="ck_core_data_quality_results_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_source_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    check_code: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    metric_name: Mapped[str] = mapped_column(String(120), nullable=False, default="", server_default="")
    metric_value: Mapped[str] = mapped_column(String(300), nullable=False, default="", server_default="")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DataAuditEvent(Base):
    __tablename__ = "core_data_audit_events"
    __table_args__ = (
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_data_audit_events_product"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False, index=True)
    actor_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
