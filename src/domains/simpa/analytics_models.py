from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class SimpaIndicatorMethodology(Base):
    __tablename__ = "simpa_indicator_methodologies"
    __table_args__ = (
        UniqueConstraint("indicator_id", "version_no", name="uq_simpa_indicator_methodology_version"),
        CheckConstraint("status IN ('draft','validated','retired')", name="ck_simpa_indicator_methodology_status"),
        CheckConstraint("computation_type IN ('direct_observation')", name="ck_simpa_indicator_methodology_computation"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    indicator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("simpa_indicator_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    computation_type: Mapped[str] = mapped_column(String(40), nullable=False, default="direct_observation", server_default="direct_observation")
    computation_spec: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    source_requirements: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    methodology_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    validation_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    approved_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class SimpaAnalyticsRun(Base):
    __tablename__ = "simpa_analytics_runs"
    __table_args__ = (
        CheckConstraint("status IN ('completed','failed')", name="ck_simpa_analytics_run_status"),
        CheckConstraint("evidence_quality_score >= 0 AND evidence_quality_score <= 1", name="ck_simpa_analytics_run_quality_score"),
        CheckConstraint("validated_observation_ratio >= 0 AND validated_observation_ratio <= 1", name="ck_simpa_analytics_run_validated_ratio"),
        CheckConstraint("provenance_coverage >= 0 AND provenance_coverage <= 1", name="ck_simpa_analytics_run_provenance"),
        CheckConstraint("indicator_coverage >= 0 AND indicator_coverage <= 1", name="ck_simpa_analytics_run_indicator_coverage"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    monitoring_cycle_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("simpa_monitoring_cycles.id", ondelete="SET NULL"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="completed", server_default="completed")
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    evidence_quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    validated_observation_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    provenance_coverage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    indicator_coverage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SimpaIndicatorResult(Base):
    __tablename__ = "simpa_indicator_results"
    __table_args__ = (
        CheckConstraint("status IN ('computed','reviewed','rejected')", name="ck_simpa_indicator_result_status"),
        CheckConstraint("quality_score >= 0 AND quality_score <= 1", name="ck_simpa_indicator_result_quality"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    analytics_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("simpa_analytics_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    indicator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("simpa_indicator_definitions.id"), nullable=False, index=True)
    methodology_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("simpa_indicator_methodologies.id"), nullable=False, index=True)
    value_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_text: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    unit: Mapped[str] = mapped_column(String(80), nullable=False, default="", server_default="")
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    source_observation_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    computation_trace: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="computed", server_default="computed")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SimpaAISynthesis(Base):
    __tablename__ = "simpa_ai_syntheses"
    __table_args__ = (
        CheckConstraint("review_status IN ('pending','accepted','rejected')", name="ck_simpa_ai_synthesis_review"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    analytics_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("simpa_analytics_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    ai_job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_ai_jobs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    source_snapshot_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    review_status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending", server_default="pending")
    reviewer_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    reviewed_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
