from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class OrdoIndicatorMethodology(Base):
    __tablename__ = "ordo_indicator_methodologies"
    __table_args__ = (
        UniqueConstraint("indicator_id", "version_no", name="uq_ordo_indicator_methodology_version"),
        CheckConstraint("status IN ('draft','proposed','validated','retired')", name="ck_ordo_indicator_methodology_status"),
        CheckConstraint("computation_type IN ('direct_observation')", name="ck_ordo_indicator_methodology_computation"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    indicator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_indicator_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    computation_type: Mapped[str] = mapped_column(String(40), nullable=False, default="direct_observation", server_default="direct_observation")
    computation_spec: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    source_requirements: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    methodology_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    validation_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    proposed_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    proposed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retired_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    retired_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retirement_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class OrdoAnalyticsRun(Base):
    __tablename__ = "ordo_analytics_runs"
    __table_args__ = (
        CheckConstraint("status IN ('completed','failed')", name="ck_ordo_analytics_run_status"),
        CheckConstraint("evidence_quality_score >= 0 AND evidence_quality_score <= 1", name="ck_ordo_analytics_run_quality_score"),
        CheckConstraint("validated_observation_ratio >= 0 AND validated_observation_ratio <= 1", name="ck_ordo_analytics_run_validated_ratio"),
        CheckConstraint("provenance_coverage >= 0 AND provenance_coverage <= 1", name="ck_ordo_analytics_run_provenance"),
        CheckConstraint("indicator_coverage >= 0 AND indicator_coverage <= 1", name="ck_ordo_analytics_run_indicator_coverage"),
        CheckConstraint("dimension_coverage >= 0 AND dimension_coverage <= 1", name="ck_ordo_analytics_run_dimension_coverage"),
        CheckConstraint("pillar_coverage >= 0 AND pillar_coverage <= 1", name="ck_ordo_analytics_run_pillar_coverage"),
        CheckConstraint("analytical_artifact_type IN ('LEGACY_OBSERVATION','ANALYTICAL_SNAPSHOT','ANALYTICAL_FEATURE_VERSION')", name="ck_ordo_run_artifact_type"),
        CheckConstraint("(analytical_artifact_type = 'LEGACY_OBSERVATION' AND analytical_snapshot_id IS NULL AND analytical_feature_version_id IS NULL) OR (analytical_artifact_type = 'ANALYTICAL_SNAPSHOT' AND analytical_snapshot_id IS NOT NULL AND analytical_feature_version_id IS NULL) OR (analytical_artifact_type = 'ANALYTICAL_FEATURE_VERSION' AND analytical_snapshot_id IS NULL AND analytical_feature_version_id IS NOT NULL)", name="ck_ordo_run_artifact_binding"),
        CheckConstraint("analytical_artifact_type = 'LEGACY_OBSERVATION' OR (dataset_contract_version_id IS NOT NULL AND length(analytical_artifact_fingerprint) = 64 AND length(dataset_contract_fingerprint) = 64 AND analytical_quality_state IN ('ACCEPTED_CLEAN','ACCEPTED_WITH_WARNING'))", name="ck_ordo_run_governed_identity"),
        Index("ix_ordo_run_analytical_snapshot", "analytical_snapshot_id"),
        Index("ix_ordo_run_analytical_feature", "analytical_feature_version_id"),
        Index("ix_ordo_run_dataset_contract", "dataset_contract_version_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    monitoring_cycle_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ordo_monitoring_cycles.id", ondelete="SET NULL"), nullable=True, index=True)
    analytical_artifact_type: Mapped[str] = mapped_column(String(40), nullable=False, default="LEGACY_OBSERVATION", server_default="LEGACY_OBSERVATION")
    analytical_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_analytical_dataset_snapshots.id", ondelete="RESTRICT"), nullable=True)
    analytical_feature_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_analytical_feature_versions.id", ondelete="RESTRICT"), nullable=True)
    analytical_artifact_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    dataset_contract_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_analytical_dataset_contract_versions.id", ondelete="RESTRICT"), nullable=True)
    dataset_contract_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    analytical_quality_state: Mapped[str] = mapped_column(String(32), nullable=False, default="LEGACY_UNKNOWN", server_default="LEGACY_UNKNOWN")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="completed", server_default="completed")
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    evidence_quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    validated_observation_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    provenance_coverage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    indicator_coverage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    dimension_coverage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    pillar_coverage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OrdoIndicatorResult(Base):
    __tablename__ = "ordo_indicator_results"
    __table_args__ = (
        CheckConstraint("status IN ('computed','reviewed','rejected')", name="ck_ordo_indicator_result_status"),
        CheckConstraint("quality_score >= 0 AND quality_score <= 1", name="ck_ordo_indicator_result_quality"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    analytics_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ordo_analytics_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    indicator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_indicator_definitions.id"), nullable=False, index=True)
    methodology_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_indicator_methodologies.id"), nullable=False, index=True)
    value_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_text: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    unit: Mapped[str] = mapped_column(String(80), nullable=False, default="", server_default="")
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    source_observation_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    computation_trace: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="computed", server_default="computed")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OrdoSpatialAggregationRun(Base):
    __tablename__ = "ordo_spatial_aggregation_runs"
    __table_args__ = (
        CheckConstraint("schema_version = 'ORDO-SPATIAL-AGGREGATION-v1'", name="ck_ordo_spatial_run_schema"),
        CheckConstraint("aggregation_rule IN ('count','sum','mean','min','max')", name="ck_ordo_spatial_run_rule"),
        CheckConstraint("input_record_count >= 0 AND matched_record_count >= 0 AND dropped_missing_numeric_count >= 0", name="ck_ordo_spatial_run_counts"),
        CheckConstraint("spatial_join_performed = false AND weighted = false AND forecast_performed = false AND causal_claim = false AND automatic_policy_recommendation = false", name="ck_ordo_spatial_run_locked_semantics"),
        CheckConstraint("length(methodology_fingerprint) = 64 AND length(input_snapshot_sha256) = 64 AND length(run_fingerprint) = 64", name="ck_ordo_spatial_run_fingerprints"),
        UniqueConstraint("analytics_run_id", "indicator_id", "target_spatial_unit_id", "methodology_id", name="uq_ordo_spatial_run_identity"),
        Index("ix_ordo_spatial_run_scope_created", "organization_id", "workspace_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False)
    analytics_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_analytics_runs.id", ondelete="RESTRICT"), nullable=False)
    indicator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_indicator_definitions.id", ondelete="RESTRICT"), nullable=False)
    methodology_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_indicator_methodologies.id", ondelete="RESTRICT"), nullable=False)
    methodology_version: Mapped[int] = mapped_column(Integer, nullable=False)
    methodology_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    target_spatial_unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_spatial_units.id", ondelete="RESTRICT"), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False, default="ORDO-SPATIAL-AGGREGATION-v1", server_default="ORDO-SPATIAL-AGGREGATION-v1")
    aggregation_rule: Mapped[str] = mapped_column(String(16), nullable=False)
    boundary_version: Mapped[str] = mapped_column(String(160), nullable=False)
    crs: Mapped[str] = mapped_column(String(80), nullable=False)
    spatial_unit_type: Mapped[str] = mapped_column(String(40), nullable=False)
    input_snapshot_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    input_record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    matched_record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    dropped_missing_numeric_count: Mapped[int] = mapped_column(Integer, nullable=False)
    aggregate_numeric_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(80), nullable=False, default="", server_default="")
    computation_trace: Mapped[dict] = mapped_column(JSON, nullable=False)
    run_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    weighted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    spatial_join_performed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    forecast_performed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    causal_claim: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    automatic_policy_recommendation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OrdoStatisticalModelContract(Base):
    __tablename__ = "ordo_statistical_model_contracts"
    __table_args__ = (
        UniqueConstraint("workspace_id", "analysis_key", "version_no", name="uq_ordo_statistical_contract_version"),
        CheckConstraint("status IN ('draft','proposed','validated','retired')", name="ck_ordo_statistical_contract_status"),
        CheckConstraint("schema_version = 'ORDO-STATISTICAL-MODEL-CONTRACT-v1'", name="ck_ordo_statistical_contract_schema"),
        CheckConstraint("version_no >= 1 AND target_methodology_version >= 1", name="ck_ordo_statistical_contract_versions"),
        CheckConstraint("length(methodology_fingerprint) = 64 AND length(input_snapshot_sha256) = 64 AND length(contract_fingerprint) = 64", name="ck_ordo_statistical_contract_fingerprints"),
        CheckConstraint("status != 'validated' OR (length(validation_note) > 0 AND length(validation_evidence_reference) > 0 AND approved_by_membership_id IS NOT NULL AND approved_at IS NOT NULL)", name="ck_ordo_statistical_contract_validation_trace"),
        Index("ix_ordo_statistical_contract_scope_status", "organization_id", "workspace_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False)
    analytics_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_analytics_runs.id", ondelete="RESTRICT"), nullable=False)
    target_indicator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_indicator_definitions.id", ondelete="RESTRICT"), nullable=False)
    target_methodology_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_indicator_methodologies.id", ondelete="RESTRICT"), nullable=False)
    target_methodology_version: Mapped[int] = mapped_column(Integer, nullable=False)
    methodology_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    input_snapshot_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    analysis_key: Mapped[str] = mapped_column(String(140), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    target_semantic: Mapped[str] = mapped_column(String(40), nullable=False)
    analysis_structure: Mapped[str] = mapped_column(String(32), nullable=False)
    model_family: Mapped[str] = mapped_column(String(40), nullable=False)
    response_family: Mapped[str] = mapped_column(String(40), nullable=False)
    contract_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    contract_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    proposed_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    proposed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validation_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    validation_evidence_reference: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    retired_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    retired_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retirement_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OrdoTimeSeriesSpec(Base):
    __tablename__ = "ordo_time_series_specs"
    __table_args__ = (
        UniqueConstraint("workspace_id", "series_key", "version_no", name="uq_ordo_time_series_spec_version"),
        CheckConstraint("status IN ('draft','proposed','validated','retired')", name="ck_ordo_time_series_spec_status"),
        CheckConstraint("schema_version = 'ORDO-TIME-SERIES-SPEC-v1'", name="ck_ordo_time_series_spec_schema"),
        CheckConstraint("version_no >= 1 AND target_methodology_version >= 1", name="ck_ordo_time_series_spec_versions"),
        CheckConstraint("length(methodology_fingerprint) = 64 AND length(input_snapshot_sha256) = 64 AND length(contract_fingerprint) = 64", name="ck_ordo_time_series_spec_fingerprints"),
        CheckConstraint("forecast_execution = false AND automatic_model_selection = false AND non_causal = true", name="ck_ordo_time_series_spec_locked_semantics"),
        CheckConstraint("status != 'validated' OR (length(validation_note) > 0 AND length(validation_evidence_reference) > 0 AND approved_by_membership_id IS NOT NULL AND approved_at IS NOT NULL)", name="ck_ordo_time_series_spec_validation_trace"),
        Index("ix_ordo_time_series_spec_scope_status", "organization_id", "workspace_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False)
    analytics_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_analytics_runs.id", ondelete="RESTRICT"), nullable=False)
    target_indicator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_indicator_definitions.id", ondelete="RESTRICT"), nullable=False)
    target_methodology_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_indicator_methodologies.id", ondelete="RESTRICT"), nullable=False)
    target_methodology_version: Mapped[int] = mapped_column(Integer, nullable=False)
    methodology_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    input_snapshot_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    series_key: Mapped[str] = mapped_column(String(140), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    target_semantic: Mapped[str] = mapped_column(String(40), nullable=False)
    frequency: Mapped[str] = mapped_column(String(24), nullable=False)
    transformation: Mapped[str] = mapped_column(String(32), nullable=False)
    contract_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    contract_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    forecast_execution: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    automatic_model_selection: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    non_causal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    proposed_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    proposed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validation_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    validation_evidence_reference: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    retired_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    retired_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retirement_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OrdoForecastRun(Base):
    __tablename__ = "ordo_forecast_runs"
    __table_args__ = (
        CheckConstraint("schema_version = 'ORDO-FORECAST-RUN-v1'", name="ck_ordo_forecast_run_schema"),
        CheckConstraint("result_status IN ('ESTIMATED','NOT_ESTIMATED')", name="ck_ordo_forecast_run_status"),
        CheckConstraint("requested_family IN ('naive','seasonal_naive','ets','sarima','sarimax','count_time_series')", name="ck_ordo_forecast_run_requested_family"),
        CheckConstraint("executed_family IS NULL OR executed_family IN ('naive','seasonal_naive')", name="ck_ordo_forecast_run_executed_family"),
        CheckConstraint("interval_level IN (0.80,0.90,0.95)", name="ck_ordo_forecast_run_interval_level"),
        CheckConstraint("horizon >= 1", name="ck_ordo_forecast_run_horizon"),
        CheckConstraint("length(time_series_spec_fingerprint) = 64 AND length(methodology_fingerprint) = 64 AND length(input_snapshot_sha256) = 64 AND length(request_fingerprint) = 64 AND length(result_fingerprint) = 64", name="ck_ordo_forecast_run_fingerprints"),
        CheckConstraint("non_causal = true AND automatic_model_selection = false AND automatic_policy_recommendation = false", name="ck_ordo_forecast_run_locked_semantics"),
        CheckConstraint("(result_status = 'ESTIMATED' AND executed_family IS NOT NULL AND reason_code = '' AND json_array_length(forecast_points) = horizon AND json_array_length(backtest_records) > 0) OR (result_status = 'NOT_ESTIMATED' AND executed_family IS NULL AND length(reason_code) > 0 AND json_array_length(forecast_points) = 0 AND json_array_length(backtest_records) = 0)", name="ck_ordo_forecast_run_result_state"),
        Index("ix_ordo_forecast_run_scope_created", "organization_id", "workspace_id", "created_at"),
        Index("ix_ordo_forecast_run_request_fingerprint", "request_fingerprint"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False)
    analytics_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_analytics_runs.id", ondelete="RESTRICT"), nullable=False)
    time_series_spec_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_time_series_specs.id", ondelete="RESTRICT"), nullable=False)
    time_series_spec_version: Mapped[int] = mapped_column(Integer, nullable=False)
    time_series_spec_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    target_indicator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_indicator_definitions.id", ondelete="RESTRICT"), nullable=False)
    target_methodology_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_indicator_methodologies.id", ondelete="RESTRICT"), nullable=False)
    target_methodology_version: Mapped[int] = mapped_column(Integer, nullable=False)
    methodology_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    input_snapshot_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False, default="ORDO-FORECAST-RUN-v1", server_default="ORDO-FORECAST-RUN-v1")
    series_identity: Mapped[dict] = mapped_column(JSON, nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    requested_family: Mapped[str] = mapped_column(String(32), nullable=False)
    executed_family: Mapped[str | None] = mapped_column(String(32), nullable=True)
    engine_key: Mapped[str] = mapped_column(String(80), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    interval_method: Mapped[str] = mapped_column(String(80), nullable=False)
    interval_level: Mapped[float] = mapped_column(Float, nullable=False)
    result_status: Mapped[str] = mapped_column(String(24), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(80), nullable=False, default="", server_default="")
    observation_window: Mapped[dict] = mapped_column(JSON, nullable=False)
    training_window: Mapped[dict] = mapped_column(JSON, nullable=False)
    horizon: Mapped[int] = mapped_column(Integer, nullable=False)
    rolling_origin_plan: Mapped[dict] = mapped_column(JSON, nullable=False)
    backtest_records: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    aggregate_backtest_metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    metric_availability: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    diagnostics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    warnings: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    forecast_points: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    result_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    non_causal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    automatic_model_selection: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    automatic_policy_recommendation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OrdoDevelopmentGoal(Base):
    __tablename__ = "ordo_development_goals"
    __table_args__ = (
        UniqueConstraint("workspace_id", "code", name="uq_ordo_development_goals_workspace_code"),
        CheckConstraint("status IN ('draft','active','closed')", name="ck_ordo_development_goal_status"),
        CheckConstraint("focus_area IN ('competitiveness','sustainability','inclusion','employment','quality_of_life','destination_development','custom')", name="ck_ordo_development_goal_focus"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(400), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    focus_area: Mapped[str] = mapped_column(String(40), nullable=False, default="destination_development", server_default="destination_development")
    target_horizon: Mapped[object | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class OrdoScenario(Base):
    __tablename__ = "ordo_scenarios"
    __table_args__ = (
        UniqueConstraint("workspace_id", "goal_id", "name", name="uq_ordo_scenarios_workspace_goal_name"),
        CheckConstraint("status IN ('draft','review_ready','accepted','rejected')", name="ck_ordo_scenario_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_development_goals.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    assumptions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    measures: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class OrdoScenarioAssessment(Base):
    __tablename__ = "ordo_scenario_assessments"
    __table_args__ = (
        CheckConstraint("status IN ('evidence_only','reviewed','rejected')", name="ck_ordo_scenario_assessment_status"),
        CheckConstraint("forecast_performed = false", name="ck_ordo_scenario_assessment_no_forecast"),
        CheckConstraint("input_snapshot_sha256 = '' OR length(input_snapshot_sha256) = 64", name="ck_ordo_scenario_assessment_snapshot_sha"),
        CheckConstraint("human_review_state IN ('pending','reviewed','rejected')", name="ck_ordo_scenario_assessment_human_review"),
        CheckConstraint("uncertainty_semantics = 'not_applicable_scenario_not_forecast'", name="ck_ordo_scenario_assessment_uncertainty"),
        CheckConstraint("impact_estimation_status IN ('LEGACY_NOT_EVALUATED','NOT_ESTIMATED','ESTIMATED')", name="ck_ordo_scenario_assessment_impact_status"),
        CheckConstraint("impact_estimation_status != 'NOT_ESTIMATED' OR (impact_estimation_reason_code = 'NO_APPROVED_RESPONSE_MODEL' AND impact_estimate_numeric IS NULL AND impact_model_reference = '')", name="ck_ordo_scenario_assessment_not_estimated_impact"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    scenario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    analytics_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_analytics_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    assessment: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    scenario_contract_version: Mapped[str] = mapped_column(String(64), nullable=False, default="ORDO-SCENARIO-CONTRACT-v1", server_default="ORDO-SCENARIO-CONTRACT-v1")
    methodology_key: Mapped[str] = mapped_column(String(160), nullable=False, default="ordo_evidence_readiness_v1", server_default="ordo_evidence_readiness_v1")
    methodology_version: Mapped[str] = mapped_column(String(80), nullable=False, default="1", server_default="1")
    input_reference_identities: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    input_snapshot_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    limitations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    uncertainty_semantics: Mapped[str] = mapped_column(String(80), nullable=False, default="not_applicable_scenario_not_forecast", server_default="not_applicable_scenario_not_forecast")
    human_review_state: Mapped[str] = mapped_column(String(24), nullable=False, default="pending", server_default="pending")
    forecast_performed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    impact_estimation_status: Mapped[str] = mapped_column(String(32), nullable=False, default="NOT_ESTIMATED", server_default="NOT_ESTIMATED")
    impact_estimation_reason_code: Mapped[str] = mapped_column(String(80), nullable=False, default="NO_APPROVED_RESPONSE_MODEL", server_default="NO_APPROVED_RESPONSE_MODEL")
    impact_estimate_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    impact_estimate_unit: Mapped[str] = mapped_column(String(80), nullable=False, default="", server_default="")
    impact_model_reference: Mapped[str] = mapped_column(String(400), nullable=False, default="", server_default="")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="evidence_only", server_default="evidence_only")
    reviewer_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    reviewed_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OrdoAISynthesis(Base):
    __tablename__ = "ordo_ai_syntheses"
    __table_args__ = (
        CheckConstraint("synthesis_type IN ('monitoring','scenario_review')", name="ck_ordo_ai_synthesis_type"),
        CheckConstraint("review_status IN ('pending','accepted','rejected')", name="ck_ordo_ai_synthesis_review"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    analytics_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_analytics_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    scenario_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ordo_scenarios.id", ondelete="SET NULL"), nullable=True, index=True)
    ai_job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_ai_jobs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    synthesis_type: Mapped[str] = mapped_column(String(32), nullable=False, default="monitoring", server_default="monitoring")
    source_snapshot_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    review_status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending", server_default="pending")
    reviewer_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    reviewed_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
