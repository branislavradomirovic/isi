from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.platform.data.models import DataSource, DataSourceVersion
from src.platform.workspaces.models import Workspace
from src.domains.simpa.models import (
    SimpaDataMapping, SimpaDimension, SimpaIndicatorDefinition, SimpaIndicatorObservation,
    SimpaLocalActor, SimpaLocalSystemProfile, SimpaMonitoringCycle, SimpaSourceType,
)


class SimpaDomainError(RuntimeError):
    pass


def validate_simpa_scope(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID) -> Workspace:
    workspace = session.scalar(select(Workspace).where(
        Workspace.id == workspace_id,
        Workspace.organization_id == organization_id,
        Workspace.product_code == "SIMPA",
        Workspace.status == "active",
    ))
    if workspace is None:
        raise SimpaDomainError("simpa_workspace_not_accessible")
    return workspace


def catalog(session: Session) -> dict:
    dimensions = session.scalars(select(SimpaDimension).where(SimpaDimension.active.is_(True)).order_by(SimpaDimension.sort_order)).all()
    source_types = session.scalars(select(SimpaSourceType).where(SimpaSourceType.active.is_(True)).order_by(SimpaSourceType.code)).all()
    indicators = session.scalars(select(SimpaIndicatorDefinition).where(SimpaIndicatorDefinition.active.is_(True)).order_by(SimpaIndicatorDefinition.dimension_code, SimpaIndicatorDefinition.code)).all()
    return {
        "dimensions": [{"code": x.code, "name_sr": x.name_sr} for x in dimensions],
        "source_types": [{"code": x.code, "name_sr": x.name_sr} for x in source_types],
        "indicators": [{
            "code": x.code, "name_sr": x.name_sr, "dimension_code": x.dimension_code,
            "unit_hint": x.unit_hint, "methodology_status": x.methodology_status,
        } for x in indicators],
    }


def foundation_summary(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID) -> dict:
    validate_simpa_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    profile = session.scalar(select(SimpaLocalSystemProfile).where(
        SimpaLocalSystemProfile.organization_id == organization_id, SimpaLocalSystemProfile.workspace_id == workspace_id
    ))
    def count(model, *criteria):
        return int(session.scalar(select(func.count()).select_from(model).where(*criteria)) or 0)
    actor_count = count(SimpaLocalActor, SimpaLocalActor.organization_id == organization_id, SimpaLocalActor.workspace_id == workspace_id, SimpaLocalActor.active.is_(True))
    cycle_count = count(SimpaMonitoringCycle, SimpaMonitoringCycle.organization_id == organization_id, SimpaMonitoringCycle.workspace_id == workspace_id)
    mapping_count = count(SimpaDataMapping, SimpaDataMapping.organization_id == organization_id, SimpaDataMapping.workspace_id == workspace_id, SimpaDataMapping.status != "retired")
    observation_count = count(SimpaIndicatorObservation, SimpaIndicatorObservation.organization_id == organization_id, SimpaIndicatorObservation.workspace_id == workspace_id)
    validated = count(SimpaIndicatorObservation, SimpaIndicatorObservation.organization_id == organization_id, SimpaIndicatorObservation.workspace_id == workspace_id, SimpaIndicatorObservation.quality_status == "validated")
    conceptual_count = count(SimpaIndicatorDefinition, SimpaIndicatorDefinition.active.is_(True), SimpaIndicatorDefinition.methodology_status == "conceptual")
    return {
        "organization_id": organization_id, "workspace_id": workspace_id, "product_code": "SIMPA",
        "profile": None if profile is None else {"id": str(profile.id), "jurisdiction_name": profile.jurisdiction_name, "jurisdiction_code": profile.jurisdiction_code, "reference_year": profile.reference_year, "notes": profile.notes},
        "actor_count": actor_count, "cycle_count": cycle_count, "mapping_count": mapping_count,
        "observation_count": observation_count, "validated_observation_count": validated,
        "conceptual_indicator_count": conceptual_count,
        "configured": profile is not None and actor_count > 0,
    }


def upsert_profile(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, jurisdiction_name: str, jurisdiction_code: str, reference_year: int | None, notes: str, actor_id: uuid.UUID | None) -> SimpaLocalSystemProfile:
    validate_simpa_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    row = session.scalar(select(SimpaLocalSystemProfile).where(SimpaLocalSystemProfile.workspace_id == workspace_id))
    if row is None:
        row = SimpaLocalSystemProfile(organization_id=organization_id, workspace_id=workspace_id, jurisdiction_name=jurisdiction_name.strip(), created_by_membership_id=actor_id)
        session.add(row)
    row.jurisdiction_name = jurisdiction_name.strip()
    row.jurisdiction_code = jurisdiction_code.strip()
    row.reference_year = reference_year
    row.notes = notes.strip()
    session.flush()
    return row


def list_actors(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID) -> list[SimpaLocalActor]:
    validate_simpa_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    return list(session.scalars(select(SimpaLocalActor).where(SimpaLocalActor.organization_id == organization_id, SimpaLocalActor.workspace_id == workspace_id, SimpaLocalActor.active.is_(True)).order_by(SimpaLocalActor.actor_type, SimpaLocalActor.name)).all())


def create_actor(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, actor_type: str, name: str, external_code: str, actor_id: uuid.UUID | None) -> SimpaLocalActor:
    validate_simpa_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    row = SimpaLocalActor(organization_id=organization_id, workspace_id=workspace_id, actor_type=actor_type, name=name.strip(), external_code=external_code.strip(), created_by_membership_id=actor_id)
    session.add(row); session.flush(); return row


def list_cycles(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID) -> list[SimpaMonitoringCycle]:
    validate_simpa_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    return list(session.scalars(select(SimpaMonitoringCycle).where(SimpaMonitoringCycle.organization_id == organization_id, SimpaMonitoringCycle.workspace_id == workspace_id).order_by(SimpaMonitoringCycle.period_start.desc())).all())


def create_cycle(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, code: str, title: str, period_start, period_end, status: str, actor_id: uuid.UUID | None) -> SimpaMonitoringCycle:
    validate_simpa_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    if period_end < period_start: raise SimpaDomainError("period_end_before_start")
    row = SimpaMonitoringCycle(organization_id=organization_id, workspace_id=workspace_id, code=code.strip(), title=title.strip(), period_start=period_start, period_end=period_end, status=status, created_by_membership_id=actor_id)
    session.add(row); session.flush(); return row


def create_mapping(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, data_source_id: uuid.UUID, source_type_code: str, mapping_schema: dict, status: str, notes: str, actor_id: uuid.UUID | None) -> SimpaDataMapping:
    validate_simpa_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    source = session.scalar(select(DataSource).where(DataSource.id == data_source_id, DataSource.organization_id == organization_id, DataSource.workspace_id == workspace_id, DataSource.product_code == "SIMPA", DataSource.status == "active"))
    if source is None: raise SimpaDomainError("data_source_not_accessible")
    source_type = session.scalar(select(SimpaSourceType).where(SimpaSourceType.code == source_type_code, SimpaSourceType.active.is_(True)))
    if source_type is None: raise SimpaDomainError("source_type_unknown")
    row = session.scalar(select(SimpaDataMapping).where(SimpaDataMapping.workspace_id == workspace_id, SimpaDataMapping.data_source_id == data_source_id))
    if row is None:
        row = SimpaDataMapping(organization_id=organization_id, workspace_id=workspace_id, data_source_id=data_source_id, source_type_code=source_type_code, created_by_membership_id=actor_id)
        session.add(row)
    row.source_type_code = source_type_code; row.mapping_schema = mapping_schema; row.status = status; row.notes = notes.strip(); session.flush(); return row


def list_mappings(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID) -> list[SimpaDataMapping]:
    validate_simpa_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    return list(session.scalars(select(SimpaDataMapping).where(SimpaDataMapping.organization_id == organization_id, SimpaDataMapping.workspace_id == workspace_id, SimpaDataMapping.status != "retired").order_by(SimpaDataMapping.created_at.desc())).all())


def create_observation(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, indicator_code: str, monitoring_cycle_id: uuid.UUID | None, source_version_id: uuid.UUID | None, period_start, period_end, geography_code: str, geography_label: str, population_group: str, value_numeric: float | None, value_text: str, quality_status: str, provenance_note: str, actor_id: uuid.UUID | None) -> SimpaIndicatorObservation:
    validate_simpa_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    indicator = session.scalar(select(SimpaIndicatorDefinition).where(SimpaIndicatorDefinition.code == indicator_code, SimpaIndicatorDefinition.active.is_(True)))
    if indicator is None: raise SimpaDomainError("indicator_unknown")
    if monitoring_cycle_id is not None:
        cycle = session.scalar(select(SimpaMonitoringCycle).where(SimpaMonitoringCycle.id == monitoring_cycle_id, SimpaMonitoringCycle.organization_id == organization_id, SimpaMonitoringCycle.workspace_id == workspace_id))
        if cycle is None: raise SimpaDomainError("monitoring_cycle_not_accessible")
    if source_version_id is not None:
        version = session.scalar(select(DataSourceVersion).where(DataSourceVersion.id == source_version_id, DataSourceVersion.organization_id == organization_id, DataSourceVersion.workspace_id == workspace_id, DataSourceVersion.product_code == "SIMPA"))
        if version is None: raise SimpaDomainError("source_version_not_accessible")
    if value_numeric is None and not value_text.strip(): raise SimpaDomainError("observation_value_required")
    row = SimpaIndicatorObservation(organization_id=organization_id, workspace_id=workspace_id, indicator_id=indicator.id, monitoring_cycle_id=monitoring_cycle_id, source_version_id=source_version_id, period_start=period_start, period_end=period_end, geography_code=geography_code.strip(), geography_label=geography_label.strip(), population_group=population_group.strip(), value_numeric=value_numeric, value_text=value_text.strip(), quality_status=quality_status, provenance_note=provenance_note.strip(), created_by_membership_id=actor_id)
    session.add(row); session.flush(); return row


def list_observations(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, limit: int = 100) -> list[tuple[SimpaIndicatorObservation, SimpaIndicatorDefinition]]:
    validate_simpa_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    return list(session.execute(select(SimpaIndicatorObservation, SimpaIndicatorDefinition).join(SimpaIndicatorDefinition, SimpaIndicatorDefinition.id == SimpaIndicatorObservation.indicator_id).where(SimpaIndicatorObservation.organization_id == organization_id, SimpaIndicatorObservation.workspace_id == workspace_id).order_by(SimpaIndicatorObservation.created_at.desc()).limit(limit)).all())
