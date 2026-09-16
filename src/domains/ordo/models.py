from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class OrdoPillar(Base):
    __tablename__ = "ordo_pillars"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name_sr: Mapped[str] = mapped_column(String(260), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OrdoDimension(Base):
    __tablename__ = "ordo_dimensions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name_sr: Mapped[str] = mapped_column(String(260), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OrdoSourceType(Base):
    __tablename__ = "ordo_source_types"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name_sr: Mapped[str] = mapped_column(String(260), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OrdoIndicatorDefinition(Base):
    __tablename__ = "ordo_indicator_definitions"
    __table_args__ = (
        UniqueConstraint("code", name="uq_ordo_indicator_definitions_code"),
        CheckConstraint("methodology_status IN ('conceptual','validated','retired')", name="ck_ordo_indicator_methodology_status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(140), nullable=False)
    name_sr: Mapped[str] = mapped_column(String(400), nullable=False)
    dimension_code: Mapped[str] = mapped_column(ForeignKey("ordo_dimensions.code"), nullable=False, index=True)
    pillar_code: Mapped[str] = mapped_column(ForeignKey("ordo_pillars.code"), nullable=False, index=True)
    unit_hint: Mapped[str] = mapped_column(String(80), nullable=False, default="", server_default="")
    methodology_status: Mapped[str] = mapped_column(String(24), nullable=False, default="conceptual", server_default="conceptual")
    methodology_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class OrdoDestinationProfile(Base):
    __tablename__ = "ordo_destination_profiles"
    __table_args__ = (UniqueConstraint("workspace_id", name="uq_ordo_destination_profiles_workspace"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    destination_name: Mapped[str] = mapped_column(String(300), nullable=False)
    destination_code: Mapped[str] = mapped_column(String(80), nullable=False, default="", server_default="")
    destination_type: Mapped[str] = mapped_column(String(80), nullable=False, default="", server_default="")
    reference_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class OrdoAsset(Base):
    __tablename__ = "ordo_assets"
    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_ordo_assets_workspace_name"),
        CheckConstraint("asset_type IN ('natural_resource','cultural_heritage','attraction','experience','infrastructure','mobility','accommodation','gastronomy','event','knowledge','entrepreneurship','community','other')", name="ck_ordo_assets_type"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    external_code: Mapped[str] = mapped_column(String(120), nullable=False, default="", server_default="")
    location_label: Mapped[str] = mapped_column(String(300), nullable=False, default="", server_default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OrdoStakeholder(Base):
    __tablename__ = "ordo_stakeholders"
    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_ordo_stakeholders_workspace_name"),
        CheckConstraint("stakeholder_type IN ('local_government','tourism_organization','heritage_institution','protected_area_manager','business','entrepreneur','education_research','infrastructure_operator','civil_society','community','other')", name="ck_ordo_stakeholders_type"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    stakeholder_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    external_code: Mapped[str] = mapped_column(String(120), nullable=False, default="", server_default="")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OrdoMonitoringCycle(Base):
    __tablename__ = "ordo_monitoring_cycles"
    __table_args__ = (
        UniqueConstraint("workspace_id", "code", name="uq_ordo_monitoring_cycles_workspace_code"),
        CheckConstraint("status IN ('planned','open','closed')", name="ck_ordo_monitoring_cycles_status"),
        CheckConstraint("period_end >= period_start", name="ck_ordo_monitoring_cycles_period"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    period_start: Mapped[object] = mapped_column(Date, nullable=False)
    period_end: Mapped[object] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="planned", server_default="planned")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OrdoDataMapping(Base):
    __tablename__ = "ordo_data_mappings"
    __table_args__ = (
        UniqueConstraint("workspace_id", "data_source_id", name="uq_ordo_data_mappings_workspace_source"),
        CheckConstraint("status IN ('draft','validated','retired')", name="ck_ordo_data_mappings_status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    data_source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type_code: Mapped[str] = mapped_column(ForeignKey("ordo_source_types.code"), nullable=False, index=True)
    mapping_schema: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class OrdoIndicatorObservation(Base):
    __tablename__ = "ordo_indicator_observations"
    __table_args__ = (
        CheckConstraint("quality_status IN ('draft','validated','rejected')", name="ck_ordo_indicator_observations_quality"),
        CheckConstraint("value_numeric IS NOT NULL OR value_text <> ''", name="ck_ordo_indicator_observations_value"),
        CheckConstraint("period_end IS NULL OR period_start IS NULL OR period_end >= period_start", name="ck_ordo_indicator_observations_period"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    indicator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ordo_indicator_definitions.id"), nullable=False, index=True)
    monitoring_cycle_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ordo_monitoring_cycles.id", ondelete="SET NULL"), nullable=True, index=True)
    source_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_data_source_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    period_start: Mapped[object | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[object | None] = mapped_column(Date, nullable=True)
    geography_code: Mapped[str] = mapped_column(String(120), nullable=False, default="", server_default="")
    geography_label: Mapped[str] = mapped_column(String(300), nullable=False, default="", server_default="")
    value_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_text: Mapped[str] = mapped_column(String(500), nullable=False, default="", server_default="")
    quality_status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    provenance_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

class OrdoReferenceEvidence(Base):
    __tablename__ = "ordo_reference_evidence"
    __table_args__ = (
        UniqueConstraint("workspace_id", "evidence_key", name="uq_ordo_reference_evidence_workspace_key"),
        CheckConstraint("lifecycle_status IN ('draft','proposed','validated','retired')", name="ck_ordo_reference_evidence_lifecycle"),
        CheckConstraint("valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from", name="ck_ordo_reference_evidence_validity"),
        CheckConstraint("artifact_sha256 = '' OR length(artifact_sha256) = 64", name="ck_ordo_reference_evidence_artifact_sha"),
        CheckConstraint("content_sha256 = '' OR length(content_sha256) = 64", name="ck_ordo_reference_evidence_content_sha"),
        Index("ix_ordo_reference_evidence_scope_lifecycle", "organization_id", "workspace_id", "lifecycle_status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_key: Mapped[str] = mapped_column(String(160), nullable=False)
    indicator_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ordo_indicator_definitions.id", ondelete="SET NULL"), nullable=True, index=True)
    source_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_data_source_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    source_identity: Mapped[str] = mapped_column(String(300), nullable=False, default="", server_default="")
    source_version: Mapped[str] = mapped_column(String(160), nullable=False, default="", server_default="")
    external_identity: Mapped[str] = mapped_column(String(300), nullable=False, default="", server_default="")
    artifact_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    valid_from: Mapped[object | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[object | None] = mapped_column(Date, nullable=True)
    lifecycle_status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    provenance_lineage: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    lifecycle_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    proposed_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    proposed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validated_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    validated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retired_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    retired_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class OrdoSpatialUnit(Base):
    __tablename__ = "ordo_spatial_units"
    __table_args__ = (
        UniqueConstraint("workspace_id", "spatial_unit_key", "boundary_version", name="uq_ordo_spatial_unit_boundary_version"),
        CheckConstraint("spatial_unit_type IN ('national','macro_region','region','local_government','custom')", name="ck_ordo_spatial_unit_type"),
        CheckConstraint("lifecycle_status IN ('draft','proposed','validated','retired')", name="ck_ordo_spatial_unit_lifecycle"),
        CheckConstraint("valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from", name="ck_ordo_spatial_unit_validity"),
        CheckConstraint("artifact_sha256 = '' OR length(artifact_sha256) = 64", name="ck_ordo_spatial_unit_artifact_sha"),
        Index("ix_ordo_spatial_unit_scope_lifecycle", "organization_id", "workspace_id", "lifecycle_status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    spatial_unit_key: Mapped[str] = mapped_column(String(160), nullable=False)
    spatial_unit_type: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    boundary_source: Mapped[str] = mapped_column(String(300), nullable=False, default="", server_default="")
    boundary_version: Mapped[str] = mapped_column(String(160), nullable=False, default="", server_default="")
    geometry_id: Mapped[str] = mapped_column(String(300), nullable=False, default="", server_default="")
    crs: Mapped[str] = mapped_column(String(80), nullable=False, default="", server_default="")
    artifact_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    valid_from: Mapped[object | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[object | None] = mapped_column(Date, nullable=True)
    provenance: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    lifecycle_status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    lifecycle_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    proposed_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    proposed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validated_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    validated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retired_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    retired_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
