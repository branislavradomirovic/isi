from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class SimpaDimension(Base):
    __tablename__ = "simpa_dimensions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name_sr: Mapped[str] = mapped_column(String(260), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SimpaSourceType(Base):
    __tablename__ = "simpa_source_types"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name_sr: Mapped[str] = mapped_column(String(260), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SimpaIndicatorDefinition(Base):
    __tablename__ = "simpa_indicator_definitions"
    __table_args__ = (
        UniqueConstraint("code", name="uq_simpa_indicator_definitions_code"),
        CheckConstraint(
            "methodology_status IN ('conceptual', 'draft', 'proposed', 'validated', 'retired')",
            name="ck_simpa_indicator_methodology_status",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(140), nullable=False)
    name_sr: Mapped[str] = mapped_column(String(400), nullable=False)
    dimension_code: Mapped[str] = mapped_column(ForeignKey("simpa_dimensions.code"), nullable=False, index=True)
    unit_hint: Mapped[str] = mapped_column(String(80), nullable=False, default="", server_default="")
    methodology_status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="conceptual", server_default="conceptual"
    )
    methodology_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SimpaLocalSystemProfile(Base):
    __tablename__ = "simpa_local_system_profiles"
    __table_args__ = (UniqueConstraint("workspace_id", name="uq_simpa_local_system_profiles_workspace"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    jurisdiction_name: Mapped[str] = mapped_column(String(300), nullable=False)
    jurisdiction_code: Mapped[str] = mapped_column(String(80), nullable=False, default="", server_default="")
    reference_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SimpaLocalActor(Base):
    __tablename__ = "simpa_local_actors"
    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_simpa_local_actors_workspace_name"),
        CheckConstraint(
            "actor_type IN ('local_government','social_work_center','social_service_provider','education','health','employment','housing','civil_society','other')",
            name="ck_simpa_local_actors_type",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_type: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    external_code: Mapped[str] = mapped_column(String(120), nullable=False, default="", server_default="")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SimpaMonitoringCycle(Base):
    __tablename__ = "simpa_monitoring_cycles"
    __table_args__ = (
        UniqueConstraint("workspace_id", "code", name="uq_simpa_monitoring_cycles_workspace_code"),
        CheckConstraint("status IN ('planned','open','closed')", name="ck_simpa_monitoring_cycles_status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    period_start: Mapped[object] = mapped_column(Date, nullable=False)
    period_end: Mapped[object] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="planned", server_default="planned")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SimpaDataMapping(Base):
    __tablename__ = "simpa_data_mappings"
    __table_args__ = (
        UniqueConstraint("workspace_id", "data_source_id", name="uq_simpa_data_mappings_workspace_source"),
        CheckConstraint("status IN ('draft','validated','retired')", name="ck_simpa_data_mappings_status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data_source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_data_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type_code: Mapped[str] = mapped_column(ForeignKey("simpa_source_types.code"), nullable=False, index=True)
    mapping_schema: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SimpaIndicatorObservation(Base):
    __tablename__ = "simpa_indicator_observations"
    __table_args__ = (
        CheckConstraint(
            "quality_status IN ('draft','validated','rejected')", name="ck_simpa_indicator_observations_quality"
        ),
        CheckConstraint("value_numeric IS NOT NULL OR value_text <> ''", name="ck_simpa_indicator_observations_value"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    indicator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("simpa_indicator_definitions.id"), nullable=False, index=True
    )
    monitoring_cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("simpa_monitoring_cycles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_data_source_versions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    period_start: Mapped[object | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[object | None] = mapped_column(Date, nullable=True)
    geography_code: Mapped[str] = mapped_column(String(120), nullable=False, default="", server_default="")
    geography_label: Mapped[str] = mapped_column(String(300), nullable=False, default="", server_default="")
    population_group: Mapped[str] = mapped_column(String(220), nullable=False, default="", server_default="")
    value_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_text: Mapped[str] = mapped_column(String(500), nullable=False, default="", server_default="")
    quality_status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    provenance_note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


__all__ = [
    "SimpaDimension",
    "SimpaSourceType",
    "SimpaIndicatorDefinition",
    "SimpaLocalSystemProfile",
    "SimpaLocalActor",
    "SimpaMonitoringCycle",
    "SimpaDataMapping",
    "SimpaIndicatorObservation",
]
