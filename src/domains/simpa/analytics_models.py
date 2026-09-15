from __future__ import annotations

import uuid

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class SimpaIndicatorMethodology(Base):
    __tablename__ = "simpa_indicator_methodologies"
    __table_args__ = (
        UniqueConstraint("indicator_id", "version_no", name="uq_simpa_indicator_methodology_version"),
        CheckConstraint(
            "status IN ('draft','proposed','validated','retired')", name="ck_simpa_indicator_methodology_status"
        ),
        CheckConstraint(
            "computation_type IN ('direct_observation')", name="ck_simpa_indicator_methodology_computation"
        ),
        CheckConstraint(
            "contract_fingerprint = '' OR length(contract_fingerprint) = 64",
            name="ck_simpa_methodology_contract_fingerprint",
        ),
        CheckConstraint(
            "reference_check_status IN ('not_run','passed','failed','legacy_unknown')",
            name="ck_simpa_methodology_reference_status",
        ),
        CheckConstraint(
            "(reference_check_status IN ('not_run','legacy_unknown') AND reference_check_fingerprint = '') OR (reference_check_status IN ('passed','failed') AND length(reference_check_fingerprint) = 64)",
            name="ck_simpa_methodology_reference_fingerprint",
        ),
        CheckConstraint(
            "reference_evidence_mode IN ('legacy_unknown','legacy_inline','suite_v1')",
            name="ck_simpa_methodology_reference_evidence_mode",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    indicator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("simpa_indicator_definitions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    computation_type: Mapped[str] = mapped_column(
        String(40), nullable=False, default="direct_observation", server_default="direct_observation"
    )
    computation_spec: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    contract_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    source_requirements: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    methodology_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    validation_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    proposed_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    proposed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reference_check_status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="not_run", server_default="legacy_unknown"
    )
    reference_check_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    reference_check_detail: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    reference_evidence_mode: Mapped[str] = mapped_column(
        String(24), nullable=False, default="suite_v1", server_default="suite_v1"
    )
    approved_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retired_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    retired_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retirement_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SimpaMethodologyReferenceSuite(Base):
    __tablename__ = "simpa_methodology_reference_suites"
    __table_args__ = (
        UniqueConstraint("methodology_id", "version_no", name="uq_simpa_reference_suite_version"),
        UniqueConstraint("methodology_id", "suite_fingerprint", name="uq_simpa_reference_suite_fingerprint"),
        CheckConstraint("version_no >= 1", name="ck_simpa_reference_suite_version"),
        CheckConstraint("case_count >= 1", name="ck_simpa_reference_suite_case_count"),
        CheckConstraint("schema_version = 'SIMPA-REFERENCE-SUITE-v1'", name="ck_simpa_reference_suite_schema_version"),
        CheckConstraint(
            "length(methodology_contract_fingerprint) = 64", name="ck_simpa_reference_suite_contract_fingerprint"
        ),
        CheckConstraint("length(reference_dataset) > 0", name="ck_simpa_reference_suite_dataset"),
        CheckConstraint("length(reference_dataset_version) > 0", name="ck_simpa_reference_suite_dataset_version"),
        CheckConstraint("length(suite_fingerprint) = 64", name="ck_simpa_reference_suite_fingerprint"),
        CheckConstraint("status IN ('not_run','passed','failed')", name="ck_simpa_reference_suite_status"),
        CheckConstraint(
            "(status = 'not_run' AND result_fingerprint = '' AND length(CAST(result_detail AS TEXT)) = 2 AND executed_by_membership_id IS NULL AND executed_at IS NULL) OR (status IN ('passed','failed') AND length(result_fingerprint) = 64 AND length(CAST(result_detail AS TEXT)) > 2 AND executed_at IS NOT NULL)",
            name="ck_simpa_reference_suite_terminal",
        ),
        Index("ix_simpa_reference_suite_methodology_status", "methodology_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    methodology_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("simpa_indicator_methodologies.id", ondelete="CASCADE"), nullable=False
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_version: Mapped[str] = mapped_column(
        String(40), nullable=False, default="SIMPA-REFERENCE-SUITE-v1", server_default="SIMPA-REFERENCE-SUITE-v1"
    )
    methodology_contract_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_dataset: Mapped[str] = mapped_column(Text, nullable=False)
    reference_dataset_version: Mapped[str] = mapped_column(String(255), nullable=False)
    suite_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    case_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="not_run", server_default="not_run")
    result_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    result_detail: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    executed_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    executed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SimpaMethodologyReferenceCase(Base):
    __tablename__ = "simpa_methodology_reference_cases"
    __table_args__ = (
        UniqueConstraint("suite_id", "case_key", name="uq_simpa_reference_case_key"),
        UniqueConstraint("suite_id", "case_index", name="uq_simpa_reference_case_index"),
        CheckConstraint("length(case_key) > 0", name="ck_simpa_reference_case_key"),
        CheckConstraint("case_index >= 0", name="ck_simpa_reference_case_index"),
        CheckConstraint("length(case_fingerprint) = 64", name="ck_simpa_reference_case_fingerprint"),
        CheckConstraint("status IN ('not_run','passed','failed')", name="ck_simpa_reference_case_status"),
        CheckConstraint(
            "(status = 'not_run' AND result_fingerprint = '' AND length(CAST(result_detail AS TEXT)) = 2) OR (status IN ('passed','failed') AND length(result_fingerprint) = 64 AND length(CAST(result_detail AS TEXT)) > 2)",
            name="ck_simpa_reference_case_terminal",
        ),
        Index("ix_simpa_reference_case_suite", "suite_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    suite_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("simpa_methodology_reference_suites.id", ondelete="CASCADE"), nullable=False
    )
    case_key: Mapped[str] = mapped_column(String(255), nullable=False)
    case_index: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_record: Mapped[dict] = mapped_column(JSON, nullable=False)
    expected_result: Mapped[dict] = mapped_column(JSON, nullable=False)
    case_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="not_run", server_default="not_run")
    result_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    result_detail: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SimpaAnalyticsRun(Base):
    __tablename__ = "simpa_analytics_runs"
    __table_args__ = (
        CheckConstraint("status IN ('completed','failed')", name="ck_simpa_analytics_run_status"),
        CheckConstraint(
            "evidence_quality_score >= 0 AND evidence_quality_score <= 1", name="ck_simpa_analytics_run_quality_score"
        ),
        CheckConstraint(
            "validated_observation_ratio >= 0 AND validated_observation_ratio <= 1",
            name="ck_simpa_analytics_run_validated_ratio",
        ),
        CheckConstraint(
            "provenance_coverage >= 0 AND provenance_coverage <= 1", name="ck_simpa_analytics_run_provenance"
        ),
        CheckConstraint(
            "indicator_coverage >= 0 AND indicator_coverage <= 1", name="ck_simpa_analytics_run_indicator_coverage"
        ),
        CheckConstraint(
            "analytical_artifact_type IN ('LEGACY_OBSERVATION','ANALYTICAL_SNAPSHOT','ANALYTICAL_FEATURE_VERSION')",
            name="ck_simpa_run_artifact_type",
        ),
        CheckConstraint(
            "(analytical_artifact_type = 'LEGACY_OBSERVATION' AND analytical_snapshot_id IS NULL AND analytical_feature_version_id IS NULL) OR (analytical_artifact_type = 'ANALYTICAL_SNAPSHOT' AND analytical_snapshot_id IS NOT NULL AND analytical_feature_version_id IS NULL) OR (analytical_artifact_type = 'ANALYTICAL_FEATURE_VERSION' AND analytical_snapshot_id IS NULL AND analytical_feature_version_id IS NOT NULL)",
            name="ck_simpa_run_artifact_binding",
        ),
        CheckConstraint(
            "analytical_artifact_type = 'LEGACY_OBSERVATION' OR (dataset_contract_version_id IS NOT NULL AND length(analytical_artifact_fingerprint) = 64 AND length(dataset_contract_fingerprint) = 64 AND analytical_quality_state IN ('ACCEPTED_CLEAN','ACCEPTED_WITH_WARNING'))",
            name="ck_simpa_run_governed_identity",
        ),
        Index("ix_simpa_run_analytical_snapshot", "analytical_snapshot_id"),
        Index("ix_simpa_run_analytical_feature", "analytical_feature_version_id"),
        Index("ix_simpa_run_dataset_contract", "dataset_contract_version_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    monitoring_cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("simpa_monitoring_cycles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    analytical_artifact_type: Mapped[str] = mapped_column(
        String(40), nullable=False, default="LEGACY_OBSERVATION", server_default="LEGACY_OBSERVATION"
    )
    analytical_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_analytical_dataset_snapshots.id", ondelete="RESTRICT"), nullable=True
    )
    analytical_feature_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_analytical_feature_versions.id", ondelete="RESTRICT"), nullable=True
    )
    analytical_artifact_fingerprint: Mapped[str] = mapped_column(
        String(64), nullable=False, default="", server_default=""
    )
    dataset_contract_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_analytical_dataset_contract_versions.id", ondelete="RESTRICT"), nullable=True
    )
    dataset_contract_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    analytical_quality_state: Mapped[str] = mapped_column(
        String(32), nullable=False, default="LEGACY_UNKNOWN", server_default="LEGACY_UNKNOWN"
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="completed", server_default="completed")
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    evidence_quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    validated_observation_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    provenance_coverage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    indicator_coverage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SimpaIndicatorResult(Base):
    __tablename__ = "simpa_indicator_results"
    __table_args__ = (
        CheckConstraint("status IN ('computed','reviewed','rejected')", name="ck_simpa_indicator_result_status"),
        CheckConstraint("quality_score >= 0 AND quality_score <= 1", name="ck_simpa_indicator_result_quality"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    analytics_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("simpa_analytics_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    indicator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("simpa_indicator_definitions.id"), nullable=False, index=True
    )
    methodology_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("simpa_indicator_methodologies.id"), nullable=False, index=True
    )
    value_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_text: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    unit: Mapped[str] = mapped_column(String(80), nullable=False, default="", server_default="")
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    source_observation_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    computation_trace: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="computed", server_default="computed")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SimpaAISynthesis(Base):
    __tablename__ = "simpa_ai_syntheses"
    __table_args__ = (
        CheckConstraint("review_status IN ('pending','accepted','rejected')", name="ck_simpa_ai_synthesis_review"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    analytics_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("simpa_analytics_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ai_job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_ai_jobs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    source_snapshot_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    review_status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending", server_default="pending")
    reviewer_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    reviewed_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
