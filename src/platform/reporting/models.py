from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Report(Base):
    __tablename__ = "core_reports"
    __table_args__ = (
        CheckConstraint("product_code IN ('SIMPA','ORDO')", name="ck_core_reports_product"),
        CheckConstraint("status IN ('active','archived')", name="ck_core_reports_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False, index=True)
    report_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active", server_default="active")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class ReportVersion(Base):
    __tablename__ = "core_report_versions"
    __table_args__ = (
        UniqueConstraint("report_id", "version_no", name="uq_core_report_versions_report_version"),
        CheckConstraint(
            "status IN ('draft','in_review','approved','rejected','published','superseded')",
            name="ck_core_report_versions_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft", index=True)
    content: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    source_manifest: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    source_manifest_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    submitted_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReportReview(Base):
    __tablename__ = "core_report_reviews"
    __table_args__ = (
        CheckConstraint("decision IN ('approved','rejected')", name="ck_core_report_reviews_decision"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    report_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_report_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True, index=True)
    decision: Mapped[str] = mapped_column(String(24), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ReportExport(Base):
    __tablename__ = "core_report_exports"
    __table_args__ = (
        CheckConstraint("format IN ('json','markdown','html')", name="ck_core_report_exports_format"),
        UniqueConstraint("report_version_id", "format", "sha256", name="uq_core_report_exports_version_format_sha"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    report_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_report_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    format: Mapped[str] = mapped_column(String(24), nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    generated_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
