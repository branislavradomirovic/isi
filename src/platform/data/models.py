from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func, text
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


class DataConnectorContractVersion(Base):
    __tablename__ = "core_data_connector_contract_versions"
    __table_args__ = (
        UniqueConstraint("source_id", "version_no", name="uq_connector_contract_source_version"),
        CheckConstraint("version_no >= 1", name="ck_connector_contract_version_no"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_connector_contract_product"),
        CheckConstraint(
            "lifecycle_state IN ('DRAFT', 'ACTIVE', 'RETIRED')",
            name="ck_connector_contract_state",
        ),
        Index(
            "ix_connector_contract_scope",
            "organization_id",
            "workspace_id",
            "product_code",
        ),
        Index(
            "ix_connector_contract_source_state",
            "source_id",
            "lifecycle_state",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_sources.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False
    )
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    connector_kind: Mapped[str] = mapped_column(String(120), nullable=False)
    transport: Mapped[str] = mapped_column(String(120), nullable=False)
    configuration_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}", server_default="{}")
    credential_reference: Mapped[str] = mapped_column(String(500), nullable=False, default="", server_default="")
    capabilities_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]", server_default="[]")
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    lifecycle_state: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT", server_default="DRAFT")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    activated_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    retired_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    activated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retired_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DataSourceSchemaMappingVersion(Base):
    __tablename__ = "core_data_source_schema_mapping_versions"
    __table_args__ = (
        UniqueConstraint("source_id", "version_no", name="uq_schema_mapping_source_version"),
        CheckConstraint("version_no >= 1", name="ck_schema_mapping_version_no"),
        CheckConstraint("contract_format_version = 1", name="ck_schema_mapping_contract_format"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_schema_mapping_product"),
        CheckConstraint("schema_kind IN ('TABULAR', 'RECORD')", name="ck_schema_mapping_schema_kind"),
        CheckConstraint(
            "missing_value_policy = 'PRESERVE_MISSING'",
            name="ck_schema_mapping_missing_policy",
        ),
        CheckConstraint(
            "unexpected_field_policy IN ('REJECT', 'IGNORE')",
            name="ck_schema_mapping_unexpected_policy",
        ),
        CheckConstraint(
            "lifecycle_state IN ('DRAFT', 'ACTIVE', 'RETIRED')",
            name="ck_schema_mapping_lifecycle",
        ),
        Index(
            "ix_schema_mapping_scope",
            "organization_id",
            "workspace_id",
            "product_code",
        ),
        Index(
            "ix_schema_mapping_source_state",
            "source_id",
            "lifecycle_state",
        ),
        Index("ix_schema_mapping_connector", "connector_contract_version_id"),
        Index(
            "uq_schema_mapping_active_source",
            "source_id",
            unique=True,
            postgresql_where=text("lifecycle_state = 'ACTIVE'"),
            sqlite_where=text("lifecycle_state = 'ACTIVE'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_sources.id", ondelete="CASCADE"), nullable=False
    )
    connector_contract_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_connector_contract_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False
    )
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    contract_format_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    schema_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    source_schema_json: Mapped[str] = mapped_column(Text, nullable=False)
    field_mapping_json: Mapped[str] = mapped_column(Text, nullable=False)
    missing_value_policy: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PRESERVE_MISSING", server_default="PRESERVE_MISSING"
    )
    unexpected_field_policy: Mapped[str] = mapped_column(
        String(16), nullable=False, default="REJECT", server_default="REJECT"
    )
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    lifecycle_state: Mapped[str] = mapped_column(
        String(16), nullable=False, default="DRAFT", server_default="DRAFT"
    )
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    activated_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    retired_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    activated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retired_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DataRecordGovernancePolicyVersion(Base):
    __tablename__ = "core_data_record_governance_policy_versions"
    __table_args__ = (
        UniqueConstraint("source_id", "version_no", name="uq_rec_policy_source_version"),
        CheckConstraint("version_no >= 1", name="ck_rec_policy_version_no"),
        CheckConstraint("contract_format_version = 1", name="ck_rec_policy_format"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_rec_policy_product"),
        CheckConstraint("missing_identity_policy = 'QUARANTINE'", name="ck_rec_policy_missing"),
        CheckConstraint("exact_duplicate_policy = 'LINK_EXISTING'", name="ck_rec_policy_duplicate"),
        CheckConstraint("conflict_policy = 'QUARANTINE'", name="ck_rec_policy_conflict"),
        CheckConstraint(
            "lifecycle_state IN ('DRAFT', 'ACTIVE', 'RETIRED')",
            name="ck_rec_policy_lifecycle",
        ),
        Index("ix_rec_policy_scope", "organization_id", "workspace_id", "product_code"),
        Index(
            "ix_rec_policy_binding",
            "source_id",
            "connector_contract_version_id",
            "schema_mapping_version_id",
        ),
        Index("ix_rec_policy_source_state", "source_id", "lifecycle_state"),
        Index(
            "uq_rec_policy_active_source",
            "source_id",
            unique=True,
            postgresql_where=text("lifecycle_state = 'ACTIVE'"),
            sqlite_where=text("lifecycle_state = 'ACTIVE'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_sources.id", ondelete="RESTRICT"), nullable=False
    )
    connector_contract_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_connector_contract_versions.id", ondelete="RESTRICT"), nullable=False
    )
    schema_mapping_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_source_schema_mapping_versions.id", ondelete="RESTRICT"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False
    )
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    contract_format_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    identity_field_keys_json: Mapped[str] = mapped_column(Text, nullable=False)
    missing_identity_policy: Mapped[str] = mapped_column(
        String(24), nullable=False, default="QUARANTINE", server_default="QUARANTINE"
    )
    exact_duplicate_policy: Mapped[str] = mapped_column(
        String(24), nullable=False, default="LINK_EXISTING", server_default="LINK_EXISTING"
    )
    conflict_policy: Mapped[str] = mapped_column(
        String(24), nullable=False, default="QUARANTINE", server_default="QUARANTINE"
    )
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    lifecycle_state: Mapped[str] = mapped_column(
        String(16), nullable=False, default="DRAFT", server_default="DRAFT"
    )
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    activated_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    retired_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    activated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retired_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DataIngestionOperationalPolicyVersion(Base):
    __tablename__ = "core_data_ingestion_operational_policy_versions"
    __table_args__ = (
        UniqueConstraint("source_id", "version_no", name="uq_ing_op_policy_source_version"),
        CheckConstraint("version_no >= 1", name="ck_ing_op_policy_version_no"),
        CheckConstraint("contract_format_version = 1", name="ck_ing_op_policy_format"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_ing_op_policy_product"),
        CheckConstraint("lifecycle_state IN ('DRAFT', 'ACTIVE', 'RETIRED')", name="ck_ing_op_policy_lifecycle"),
        Index("ix_ing_op_policy_scope", "organization_id", "workspace_id", "product_code"),
        Index("ix_ing_op_policy_binding", "source_id", "connector_contract_version_id", "schema_mapping_version_id", "record_governance_policy_version_id"),
        Index("ix_ing_op_policy_source_state", "source_id", "lifecycle_state"),
        Index("uq_ing_op_policy_active_source", "source_id", unique=True,
              postgresql_where=text("lifecycle_state = 'ACTIVE'"),
              sqlite_where=text("lifecycle_state = 'ACTIVE'")),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_sources.id", ondelete="RESTRICT"), nullable=False)
    connector_contract_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_connector_contract_versions.id", ondelete="RESTRICT"), nullable=False)
    schema_mapping_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_source_schema_mapping_versions.id", ondelete="RESTRICT"), nullable=False)
    record_governance_policy_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_record_governance_policy_versions.id", ondelete="RESTRICT"), nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    contract_format_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    freshness_contract_json: Mapped[str] = mapped_column(Text, nullable=False)
    quality_contract_json: Mapped[str] = mapped_column(Text, nullable=False)
    backfill_contract_json: Mapped[str] = mapped_column(Text, nullable=False)
    dead_letter_contract_json: Mapped[str] = mapped_column(Text, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    lifecycle_state: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT", server_default="DRAFT")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    activated_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    retired_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    activated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retired_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DataSourceVersion(Base):
    __tablename__ = "core_data_source_versions"
    __table_args__ = (
        UniqueConstraint("source_id", "version_no", name="uq_core_data_source_versions_source_version"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_data_source_versions_product"),
        CheckConstraint(
            "ingest_status IN ('uploaded', 'queued', 'running', 'succeeded', 'failed')",
            name="ck_core_data_source_versions_ingest_status",
        ),
        CheckConstraint("content_state IN ('AVAILABLE', 'PURGED')", name="ck_core_data_source_versions_content_state"),
        Index(
            "ix_data_versions_scope_storage_content",
            "organization_id", "workspace_id", "product_code", "storage_key", "content_state",
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
    content_state: Mapped[str] = mapped_column(String(16), nullable=False, default="AVAILABLE", server_default="AVAILABLE")
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
        CheckConstraint(
            "export_policy IN ('PROHIBITED', 'GOVERNED_EXPORT_ALLOWED')",
            name="ck_core_data_source_governance_profiles_export",
        ),
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
        CheckConstraint("revision >= 1", name="ck_core_data_retention_states_revision"),
        CheckConstraint(
            "purge_status IN ('NONE', 'REQUESTED', 'APPROVED', 'EXECUTING', 'EXECUTED', 'FAILED')",
            name="ck_core_data_retention_states_purge_status",
        ),
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
    hold_placed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hold_placed_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    hold_released_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hold_released_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    purge_status: Mapped[str] = mapped_column(String(16), nullable=False, default="NONE", server_default="NONE")
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
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


class DataAnonymizationRecord(Base):
    __tablename__ = "core_data_anonymization_records"
    __table_args__ = (
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_data_anonymization_product"),
        CheckConstraint("status IN ('PROPOSED', 'VERIFIED', 'REJECTED')", name="ck_core_data_anonymization_status"),
        CheckConstraint("input_version_id <> output_version_id", name="ck_core_data_anonymization_versions"),
        CheckConstraint(
            "classification_before IN ('UNCLASSIFIED', 'PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED') "
            "AND classification_after IN ('UNCLASSIFIED', 'PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED')",
            name="ck_core_data_anonymization_classification",
        ),
        CheckConstraint(
            "privacy_category_before IN ('NONE_DECLARED', 'AGGREGATE_NON_PERSONAL', 'PSEUDONYMOUS_OR_LINKABLE', "
            "'PERSONAL_DATA', 'SENSITIVE_PERSONAL_DATA', 'UNKNOWN') AND privacy_category_after IN "
            "('NONE_DECLARED', 'AGGREGATE_NON_PERSONAL', 'PSEUDONYMOUS_OR_LINKABLE', 'PERSONAL_DATA', "
            "'SENSITIVE_PERSONAL_DATA', 'UNKNOWN')",
            name="ck_core_data_anonymization_privacy",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False, index=True)
    input_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_source_versions.id", ondelete="RESTRICT"), nullable=False, index=True)
    output_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_source_versions.id", ondelete="RESTRICT"), nullable=False, index=True)
    method_code: Mapped[str] = mapped_column(String(120), nullable=False)
    method_version: Mapped[str] = mapped_column(String(120), nullable=False)
    method_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    parameter_reference: Mapped[str] = mapped_column(String(1000), nullable=False, default="", server_default="")
    evidence_checksum: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    evidence_reference: Mapped[str] = mapped_column(String(1000), nullable=False)
    classification_before: Mapped[str] = mapped_column(String(32), nullable=False)
    classification_after: Mapped[str] = mapped_column(String(32), nullable=False)
    privacy_category_before: Mapped[str] = mapped_column(String(40), nullable=False)
    privacy_category_after: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PROPOSED", server_default="PROPOSED")
    proposed_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    proposed_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reviewed_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_reference: Mapped[str] = mapped_column(String(1000), nullable=False, default="", server_default="")
    review_reason: Mapped[str] = mapped_column(String(1000), nullable=False, default="", server_default="")


class DataGovernanceInvalidation(Base):
    __tablename__ = "core_data_governance_invalidations"
    __table_args__ = (
        UniqueConstraint("upstream_version_id", "reason", name="uq_core_data_governance_invalidation_version_reason"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_data_invalidation_product"),
        CheckConstraint("upstream_entity_type = 'source_version'", name="ck_core_data_invalidation_entity"),
        CheckConstraint("reason = 'PURGED'", name="ck_core_data_invalidation_reason"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False, index=True)
    upstream_entity_type: Mapped[str] = mapped_column(String(40), nullable=False, default="source_version", server_default="source_version")
    upstream_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_source_versions.id", ondelete="RESTRICT"), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(24), nullable=False, default="PURGED", server_default="PURGED")
    actor_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DataExportManifest(Base):
    __tablename__ = "core_data_export_manifests"
    __table_args__ = (
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_data_export_manifests_product"),
        CheckConstraint("outcome IN ('COMPLETED', 'DENIED', 'FAILED')", name="ck_core_data_export_manifests_outcome"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False, index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    source_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_source_versions.id", ondelete="RESTRICT"), nullable=False, index=True)
    actor_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    purpose_reference: Mapped[str] = mapped_column(String(1000), nullable=False)
    classification: Mapped[str] = mapped_column(String(32), nullable=False)
    privacy_category: Mapped[str] = mapped_column(String(40), nullable=False)
    governance_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    content_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    assurance_method: Mapped[str] = mapped_column(String(24), nullable=False, default="", server_default="")
    assurance_reference: Mapped[str] = mapped_column(String(200), nullable=False, default="", server_default="")
    result_code: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


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


class DataIngestionRun(Base):
    __tablename__ = "core_data_ingestion_runs"
    __table_args__ = (
        UniqueConstraint("source_id", "run_no", name="uq_ing_run_source_no"),
        UniqueConstraint("source_id", "idempotency_key", name="uq_ing_run_source_idem"),
        UniqueConstraint("source_id", "request_fingerprint", name="uq_ing_run_source_fp"),
        UniqueConstraint("source_version_id", name="uq_ing_run_source_version"),
        UniqueConstraint("inspection_job_id", name="uq_ing_run_inspection_job"),
        CheckConstraint("run_no >= 1", name="ck_ing_run_no"),
        CheckConstraint("attempts >= 0", name="ck_ing_run_attempts"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_ing_run_product"),
        CheckConstraint(
            "status IN ('QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED')",
            name="ck_ing_run_status",
        ),
        CheckConstraint("execution_mode IN ('INCREMENTAL', 'BACKFILL', 'REPLAY')", name="ck_ing_run_execution_mode"),
        Index(
            "ix_ing_run_scope",
            "organization_id",
            "workspace_id",
            "product_code",
        ),
        Index("ix_ing_run_source_status", "source_id", "status"),
        Index(
            "ix_ing_run_binding",
            "source_id",
            "connector_contract_version_id",
            "schema_mapping_version_id",
        ),
        Index(
            "uq_ing_run_live_source",
            "source_id",
            unique=True,
            postgresql_where=text("status IN ('QUEUED', 'RUNNING')"),
            sqlite_where=text("status IN ('QUEUED', 'RUNNING')"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_sources.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False
    )
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False)
    run_no: Mapped[int] = mapped_column(Integer, nullable=False)
    connector_contract_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_connector_contract_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    schema_mapping_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_source_schema_mapping_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    record_governance_policy_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_data_record_governance_policy_versions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    operational_policy_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_data_ingestion_operational_policy_versions.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    execution_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="INCREMENTAL", server_default="INCREMENTAL")
    window_start_cursor: Mapped[str] = mapped_column(String(1000), nullable=False, default="", server_default="")
    window_end_cursor: Mapped[str] = mapped_column(String(1000), nullable=False, default="", server_default="")
    replay_of_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_data_ingestion_runs.id", ondelete="RESTRICT"), nullable=True, index=True)
    source_observed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    forward_cursor_committed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    source_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_source_versions.id", ondelete="RESTRICT"), nullable=False
    )
    inspection_job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_ingestion_jobs.id", ondelete="RESTRICT"), nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    cursor_before: Mapped[str] = mapped_column(String(1000), nullable=False, default="", server_default="")
    cursor_after: Mapped[str] = mapped_column(String(1000), nullable=False, default="", server_default="")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="QUEUED", server_default="QUEUED")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_code: Mapped[str] = mapped_column(String(120), nullable=False, default="", server_default="")
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    queued_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class DataIngestionEvaluation(Base):
    __tablename__ = "core_data_ingestion_evaluations"
    __table_args__ = (
        UniqueConstraint("ingestion_run_id", name="uq_ing_eval_run"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_ing_eval_product"),
        CheckConstraint("freshness_status IN ('FRESH', 'STALE_WARNING', 'STALE_REJECTED', 'UNKNOWN', 'NOT_APPLICABLE')", name="ck_ing_eval_freshness"),
        CheckConstraint("quality_status IN ('PASS', 'WARNING', 'REJECTED', 'UNKNOWN')", name="ck_ing_eval_quality"),
        CheckConstraint("decision IN ('ACCEPTED', 'ACCEPTED_WITH_WARNING', 'REJECTED', 'DEAD_LETTERED')", name="ck_ing_eval_decision"),
        Index("ix_ing_eval_scope", "organization_id", "workspace_id", "product_code"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_sources.id", ondelete="RESTRICT"), nullable=False)
    ingestion_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_ingestion_runs.id", ondelete="RESTRICT"), nullable=False)
    operational_policy_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_ingestion_operational_policy_versions.id", ondelete="RESTRICT"), nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False)
    freshness_status: Mapped[str] = mapped_column(String(24), nullable=False)
    quality_status: Mapped[str] = mapped_column(String(16), nullable=False)
    decision: Mapped[str] = mapped_column(String(24), nullable=False)
    freshness_details_json: Mapped[str] = mapped_column(Text, nullable=False)
    quality_details_json: Mapped[str] = mapped_column(Text, nullable=False)
    record_metrics_json: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    evaluated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DataIngestionDeadLetter(Base):
    __tablename__ = "core_data_ingestion_dead_letters"
    __table_args__ = (
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_ing_dead_product"),
        CheckConstraint("status IN ('OPEN', 'REQUEUED', 'RESOLVED', 'DISCARDED')", name="ck_ing_dead_status"),
        Index("ix_ing_dead_scope", "organization_id", "workspace_id", "product_code"),
        Index("ix_ing_dead_run_reason", "ingestion_run_id", "reason_code"),
        Index("uq_ing_dead_open_run_reason", "ingestion_run_id", "reason_code", unique=True,
              postgresql_where=text("status = 'OPEN'"), sqlite_where=text("status = 'OPEN'")),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_sources.id", ondelete="RESTRICT"), nullable=False)
    ingestion_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_ingestion_runs.id", ondelete="RESTRICT"), nullable=False)
    evaluation_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_data_ingestion_evaluations.id", ondelete="RESTRICT"), nullable=True)
    operational_policy_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_ingestion_operational_policy_versions.id", ondelete="RESTRICT"), nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(120), nullable=False)
    error_category: Mapped[str] = mapped_column(String(120), nullable=False)
    details_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}", server_default="{}")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="OPEN", server_default="OPEN")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolver_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    resolution_note: Mapped[str] = mapped_column(String(1000), nullable=False, default="", server_default="")
    replacement_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_data_ingestion_runs.id", ondelete="RESTRICT"), nullable=True)


class DataGovernedIngestionOutput(Base):
    __tablename__ = "core_data_governed_ingestion_outputs"
    __table_args__ = (
        UniqueConstraint("ingestion_run_id", name="uq_gov_ing_output_run"),
        UniqueConstraint("evaluation_id", name="uq_gov_ing_output_evaluation"),
        CheckConstraint("contract_version = 1", name="ck_gov_ing_output_contract"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_gov_ing_output_product"),
        CheckConstraint("record_count >= 0 AND current_record_count >= 0 AND duplicate_record_count >= 0 AND quarantined_record_count >= 0 AND superseded_record_count >= 0", name="ck_gov_ing_output_counts"),
        Index("ix_gov_ing_output_scope", "organization_id", "workspace_id", "product_code"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_sources.id", ondelete="RESTRICT"), nullable=False)
    source_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_source_versions.id", ondelete="RESTRICT"), nullable=False)
    ingestion_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_ingestion_runs.id", ondelete="RESTRICT"), nullable=False)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_ingestion_evaluations.id", ondelete="RESTRICT"), nullable=False)
    connector_contract_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_connector_contract_versions.id", ondelete="RESTRICT"), nullable=False)
    schema_mapping_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_source_schema_mapping_versions.id", ondelete="RESTRICT"), nullable=False)
    record_governance_policy_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_record_governance_policy_versions.id", ondelete="RESTRICT"), nullable=False)
    operational_policy_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_ingestion_operational_policy_versions.id", ondelete="RESTRICT"), nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False)
    contract_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    current_record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    duplicate_record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    quarantined_record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    superseded_record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    output_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DataRecordEntity(Base):
    __tablename__ = "core_data_record_entities"
    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "record_governance_policy_version_id",
            "identity_fingerprint",
            name="uq_rec_entity_source_policy_identity",
        ),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_rec_entity_product"),
        CheckConstraint("state IN ('ACTIVE', 'QUARANTINED', 'EMPTY')", name="ck_rec_entity_state"),
        Index("ix_rec_entity_scope", "organization_id", "workspace_id", "product_code"),
        Index("ix_rec_entity_source_policy", "source_id", "record_governance_policy_version_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_sources.id", ondelete="RESTRICT"), nullable=False
    )
    record_governance_policy_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_record_governance_policy_versions.id", ondelete="RESTRICT"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False
    )
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False)
    identity_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE", server_default="ACTIVE")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class DataNormalizedRecord(Base):
    __tablename__ = "core_data_normalized_records"
    __table_args__ = (
        UniqueConstraint("ingestion_run_id", "source_record_ordinal", name="uq_norm_rec_run_ordinal"),
        CheckConstraint("source_record_ordinal >= 1", name="ck_norm_rec_ordinal"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_norm_rec_product"),
        CheckConstraint(
            "disposition IN ('ACCEPTED', 'DUPLICATE', 'QUARANTINED', 'REJECTED', 'SUPERSEDED', 'PURGED')",
            name="ck_norm_rec_disposition",
        ),
        Index("ix_norm_rec_scope", "organization_id", "workspace_id", "product_code"),
        Index("ix_norm_rec_source_version", "source_id", "source_version_id"),
        Index("ix_norm_rec_run", "ingestion_run_id"),
        Index("ix_norm_rec_entity", "entity_id"),
        Index(
            "ix_norm_rec_identity_fp",
            "source_id",
            "record_governance_policy_version_id",
            "identity_fingerprint",
        ),
        Index("ix_norm_rec_content_fp", "schema_mapping_version_id", "content_fingerprint"),
        Index(
            "uq_norm_rec_accepted_entity",
            "entity_id",
            unique=True,
            postgresql_where=text("entity_id IS NOT NULL AND disposition = 'ACCEPTED'"),
            sqlite_where=text("entity_id IS NOT NULL AND disposition = 'ACCEPTED'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_sources.id", ondelete="RESTRICT"), nullable=False
    )
    source_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_source_versions.id", ondelete="RESTRICT"), nullable=False
    )
    ingestion_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_ingestion_runs.id", ondelete="RESTRICT"), nullable=False
    )
    connector_contract_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_connector_contract_versions.id", ondelete="RESTRICT"), nullable=False
    )
    schema_mapping_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_source_schema_mapping_versions.id", ondelete="RESTRICT"), nullable=False
    )
    record_governance_policy_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_record_governance_policy_versions.id", ondelete="RESTRICT"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False
    )
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False)
    source_record_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    source_locator: Mapped[str] = mapped_column(String(1000), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_data_record_entities.id", ondelete="RESTRICT"), nullable=True
    )
    normalized_record_json: Mapped[str] = mapped_column(Text, nullable=False)
    identity_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    content_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    disposition: Mapped[str] = mapped_column(String(16), nullable=False)
    duplicate_of_record_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_data_normalized_records.id", ondelete="RESTRICT"), nullable=True
    )
    conflict_with_record_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_data_normalized_records.id", ondelete="RESTRICT"), nullable=True
    )
    quarantine_reason: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class DataRecordResolution(Base):
    __tablename__ = "core_data_record_resolutions"
    __table_args__ = (
        UniqueConstraint("quarantined_record_id", name="uq_rec_resolution_quarantine"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_rec_resolution_product"),
        CheckConstraint(
            "decision IN ('REJECT_INCOMING', 'ACCEPT_INCOMING')",
            name="ck_rec_resolution_decision",
        ),
        Index("ix_rec_resolution_scope", "organization_id", "workspace_id", "product_code"),
        Index("ix_rec_resolution_entity", "entity_id", "resolved_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_sources.id", ondelete="RESTRICT"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False
    )
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_record_entities.id", ondelete="RESTRICT"), nullable=False
    )
    quarantined_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_normalized_records.id", ondelete="RESTRICT"), nullable=False
    )
    existing_accepted_record_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_data_normalized_records.id", ondelete="RESTRICT"), nullable=True
    )
    decision: Mapped[str] = mapped_column(String(24), nullable=False)
    resolution_reference: Mapped[str] = mapped_column(String(1000), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    resolved_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    resolved_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


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


class AnalyticalDataset(Base):
    __tablename__ = "core_analytical_datasets"
    __table_args__ = (
        UniqueConstraint("workspace_id", "product_code", "code", name="uq_analytical_dataset_scope_code"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_analytical_dataset_product"),
        CheckConstraint("revision >= 1", name="ck_analytical_dataset_revision"),
        Index("ix_analytical_dataset_scope", "organization_id", "workspace_id", "product_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False)
    code: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False, default="", server_default="")
    methodology_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    methodology_version: Mapped[str] = mapped_column(String(120), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    updated_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class AnalyticalDatasetSnapshot(Base):
    __tablename__ = "core_analytical_dataset_snapshots"
    __table_args__ = (
        UniqueConstraint("dataset_id", "version_no", name="uq_analytical_snapshot_dataset_version"),
        CheckConstraint("version_no >= 1", name="ck_analytical_snapshot_version"),
        CheckConstraint("revision >= 1", name="ck_analytical_snapshot_revision"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_analytical_snapshot_product"),
        CheckConstraint("state IN ('DRAFT', 'VALIDATED', 'FROZEN', 'RETIRED')", name="ck_analytical_snapshot_state"),
        Index("ix_analytical_snapshot_scope", "organization_id", "workspace_id", "product_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_analytical_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    methodology_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    methodology_version: Mapped[str] = mapped_column(String(120), nullable=False)
    build_reference: Mapped[str] = mapped_column(String(500), nullable=False, default="", server_default="")
    classification: Mapped[str] = mapped_column(String(32), nullable=False)
    privacy_category: Mapped[str] = mapped_column(String(40), nullable=False)
    ai_use_policy: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="DRAFT", server_default="DRAFT")
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    invalidated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    invalidation_reason: Mapped[str] = mapped_column(String(120), nullable=False, default="", server_default="")
    invalidated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invalidated_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    frozen_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    updated_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class AnalyticalSnapshotSourceVersion(Base):
    __tablename__ = "core_analytical_snapshot_source_versions"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "source_version_id", name="uq_analytical_snapshot_source_edge"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_analytical_snapshot_source_product"),
        Index("ix_analytical_snapshot_source_lineage", "source_version_id", "snapshot_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_analytical_dataset_snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    source_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_source_versions.id", ondelete="RESTRICT"), nullable=False, index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_sources.id", ondelete="RESTRICT"), nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False)
    source_version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), nullable=False)
    privacy_category: Mapped[str] = mapped_column(String(40), nullable=False)
    ai_use_policy: Mapped[str] = mapped_column(String(64), nullable=False)
    source_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AnalyticalFeature(Base):
    __tablename__ = "core_analytical_features"
    __table_args__ = (
        UniqueConstraint("workspace_id", "product_code", "code", name="uq_analytical_feature_scope_code"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_analytical_feature_product"),
        CheckConstraint("revision >= 1", name="ck_analytical_feature_revision"),
        Index("ix_analytical_feature_scope", "organization_id", "workspace_id", "product_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False)
    code: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False, default="", server_default="")
    methodology_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    methodology_version: Mapped[str] = mapped_column(String(120), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    updated_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class AnalyticalFeatureVersion(Base):
    __tablename__ = "core_analytical_feature_versions"
    __table_args__ = (
        UniqueConstraint("feature_id", "version_no", name="uq_analytical_feature_version"),
        CheckConstraint("version_no >= 1", name="ck_analytical_feature_version_number"),
        CheckConstraint("revision >= 1", name="ck_analytical_feature_version_revision"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_analytical_feature_version_product"),
        CheckConstraint("state IN ('DRAFT', 'GOVERNED', 'FROZEN', 'RETIRED')", name="ck_analytical_feature_version_state"),
        Index("ix_analytical_feature_version_scope", "organization_id", "workspace_id", "product_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    feature_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_analytical_features.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    methodology_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    methodology_version: Mapped[str] = mapped_column(String(120), nullable=False)
    classification: Mapped[str] = mapped_column(String(32), nullable=False)
    privacy_category: Mapped[str] = mapped_column(String(40), nullable=False)
    ai_use_policy: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="DRAFT", server_default="DRAFT")
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    invalidated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    invalidation_reason: Mapped[str] = mapped_column(String(120), nullable=False, default="", server_default="")
    invalidated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invalidated_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    frozen_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    updated_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class AnalyticalFeatureSnapshotInput(Base):
    __tablename__ = "core_analytical_feature_snapshot_inputs"
    __table_args__ = (
        UniqueConstraint("feature_version_id", "snapshot_id", name="uq_analytical_feature_snapshot_edge"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_analytical_feature_snapshot_product"),
        Index("ix_analytical_feature_snapshot_lineage", "snapshot_id", "feature_version_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    feature_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_analytical_feature_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_analytical_dataset_snapshots.id", ondelete="RESTRICT"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False)
    snapshot_version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
