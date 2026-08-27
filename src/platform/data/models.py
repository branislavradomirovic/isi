from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
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
