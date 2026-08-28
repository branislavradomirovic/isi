from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.platform.data.models import DataSource, DataSourceVersion
from src.platform.workspaces.models import Workspace
from src.domains.ordo.models import (
    OrdoAsset,
    OrdoDataMapping,
    OrdoDestinationProfile,
    OrdoDimension,
    OrdoIndicatorDefinition,
    OrdoIndicatorObservation,
    OrdoMonitoringCycle,
    OrdoPillar,
    OrdoSourceType,
    OrdoStakeholder,
)


class OrdoDomainError(RuntimeError):
    pass


def validate_ordo_scope(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID) -> Workspace:
    workspace = session.scalar(select(Workspace).where(
        Workspace.id == workspace_id,
        Workspace.organization_id == organization_id,
        Workspace.product_code == "ORDO",
        Workspace.status == "active",
    ))
    if workspace is None:
        raise OrdoDomainError("ordo_workspace_not_accessible")
    return workspace


def catalog(session: Session) -> dict:
    pillars = session.scalars(select(OrdoPillar).where(OrdoPillar.active.is_(True)).order_by(OrdoPillar.sort_order)).all()
    dimensions = session.scalars(select(OrdoDimension).where(OrdoDimension.active.is_(True)).order_by(OrdoDimension.sort_order)).all()
    source_types = session.scalars(select(OrdoSourceType).where(OrdoSourceType.active.is_(True)).order_by(OrdoSourceType.code)).all()
    indicators = session.scalars(select(OrdoIndicatorDefinition).where(OrdoIndicatorDefinition.active.is_(True)).order_by(OrdoIndicatorDefinition.dimension_code, OrdoIndicatorDefinition.code)).all()
    return {
        "pillars": [{"code": x.code, "name_sr": x.name_sr} for x in pillars],
        "dimensions": [{"code": x.code, "name_sr": x.name_sr} for x in dimensions],
        "source_types": [{"code": x.code, "name_sr": x.name_sr} for x in source_types],
        "indicators": [{"code": x.code, "name_sr": x.name_sr, "dimension_code": x.dimension_code, "pillar_code": x.pillar_code, "unit_hint": x.unit_hint, "methodology_status": x.methodology_status} for x in indicators],
    }


def _count(session: Session, model, *criteria) -> int:
    return int(session.scalar(select(func.count()).select_from(model).where(*criteria)) or 0)


def foundation_summary(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID) -> dict:
    validate_ordo_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    profile = session.scalar(select(OrdoDestinationProfile).where(OrdoDestinationProfile.organization_id == organization_id, OrdoDestinationProfile.workspace_id == workspace_id))
    asset_count = _count(session, OrdoAsset, OrdoAsset.organization_id == organization_id, OrdoAsset.workspace_id == workspace_id, OrdoAsset.active.is_(True))
    stakeholder_count = _count(session, OrdoStakeholder, OrdoStakeholder.organization_id == organization_id, OrdoStakeholder.workspace_id == workspace_id, OrdoStakeholder.active.is_(True))
    cycle_count = _count(session, OrdoMonitoringCycle, OrdoMonitoringCycle.organization_id == organization_id, OrdoMonitoringCycle.workspace_id == workspace_id)
    mapping_count = _count(session, OrdoDataMapping, OrdoDataMapping.organization_id == organization_id, OrdoDataMapping.workspace_id == workspace_id, OrdoDataMapping.status != "retired")
    observation_count = _count(session, OrdoIndicatorObservation, OrdoIndicatorObservation.organization_id == organization_id, OrdoIndicatorObservation.workspace_id == workspace_id)
    validated = _count(session, OrdoIndicatorObservation, OrdoIndicatorObservation.organization_id == organization_id, OrdoIndicatorObservation.workspace_id == workspace_id, OrdoIndicatorObservation.quality_status == "validated")
    conceptual_count = _count(session, OrdoIndicatorDefinition, OrdoIndicatorDefinition.active.is_(True), OrdoIndicatorDefinition.methodology_status == "conceptual")
    return {
        "organization_id": organization_id,
        "workspace_id": workspace_id,
        "product_code": "ORDO",
        "profile": None if profile is None else {"id": str(profile.id), "destination_name": profile.destination_name, "destination_code": profile.destination_code, "destination_type": profile.destination_type, "reference_year": profile.reference_year, "notes": profile.notes},
        "asset_count": asset_count,
        "stakeholder_count": stakeholder_count,
        "cycle_count": cycle_count,
        "mapping_count": mapping_count,
        "observation_count": observation_count,
        "validated_observation_count": validated,
        "conceptual_indicator_count": conceptual_count,
        "configured": profile is not None and (asset_count > 0 or stakeholder_count > 0),
    }


def upsert_profile(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, destination_name: str, destination_code: str, destination_type: str, reference_year: int | None, notes: str, actor_id: uuid.UUID | None) -> OrdoDestinationProfile:
    validate_ordo_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    row = session.scalar(select(OrdoDestinationProfile).where(OrdoDestinationProfile.workspace_id == workspace_id))
    if row is None:
        row = OrdoDestinationProfile(organization_id=organization_id, workspace_id=workspace_id, destination_name=destination_name.strip(), created_by_membership_id=actor_id)
        session.add(row)
    row.destination_name = destination_name.strip()
    row.destination_code = destination_code.strip()
    row.destination_type = destination_type.strip()
    row.reference_year = reference_year
    row.notes = notes.strip()
    session.flush()
    return row


def list_assets(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID) -> list[OrdoAsset]:
    validate_ordo_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    return list(session.scalars(select(OrdoAsset).where(OrdoAsset.organization_id == organization_id, OrdoAsset.workspace_id == workspace_id, OrdoAsset.active.is_(True)).order_by(OrdoAsset.asset_type, OrdoAsset.name)).all())


def create_asset(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, asset_type: str, name: str, external_code: str, location_label: str, description: str, actor_id: uuid.UUID | None) -> OrdoAsset:
    validate_ordo_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    row = OrdoAsset(organization_id=organization_id, workspace_id=workspace_id, asset_type=asset_type, name=name.strip(), external_code=external_code.strip(), location_label=location_label.strip(), description=description.strip(), created_by_membership_id=actor_id)
    session.add(row); session.flush(); return row


def list_stakeholders(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID) -> list[OrdoStakeholder]:
    validate_ordo_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    return list(session.scalars(select(OrdoStakeholder).where(OrdoStakeholder.organization_id == organization_id, OrdoStakeholder.workspace_id == workspace_id, OrdoStakeholder.active.is_(True)).order_by(OrdoStakeholder.stakeholder_type, OrdoStakeholder.name)).all())


def create_stakeholder(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, stakeholder_type: str, name: str, external_code: str, actor_id: uuid.UUID | None) -> OrdoStakeholder:
    validate_ordo_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    row = OrdoStakeholder(organization_id=organization_id, workspace_id=workspace_id, stakeholder_type=stakeholder_type, name=name.strip(), external_code=external_code.strip(), created_by_membership_id=actor_id)
    session.add(row); session.flush(); return row


def list_cycles(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID) -> list[OrdoMonitoringCycle]:
    validate_ordo_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    return list(session.scalars(select(OrdoMonitoringCycle).where(OrdoMonitoringCycle.organization_id == organization_id, OrdoMonitoringCycle.workspace_id == workspace_id).order_by(OrdoMonitoringCycle.period_start.desc())).all())


def create_cycle(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, code: str, title: str, period_start, period_end, status: str, actor_id: uuid.UUID | None) -> OrdoMonitoringCycle:
    validate_ordo_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    row = OrdoMonitoringCycle(organization_id=organization_id, workspace_id=workspace_id, code=code.strip(), title=title.strip(), period_start=period_start, period_end=period_end, status=status, created_by_membership_id=actor_id)
    session.add(row); session.flush(); return row


def list_mappings(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID) -> list[OrdoDataMapping]:
    validate_ordo_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    return list(session.scalars(select(OrdoDataMapping).where(OrdoDataMapping.organization_id == organization_id, OrdoDataMapping.workspace_id == workspace_id).order_by(OrdoDataMapping.created_at.desc())).all())


def create_mapping(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, data_source_id: uuid.UUID, source_type_code: str, mapping_schema: dict, status: str, notes: str, actor_id: uuid.UUID | None) -> OrdoDataMapping:
    validate_ordo_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    source_type = session.scalar(select(OrdoSourceType).where(OrdoSourceType.code == source_type_code, OrdoSourceType.active.is_(True)))
    if source_type is None: raise OrdoDomainError("source_type_unknown")
    source = session.scalar(select(DataSource).where(DataSource.id == data_source_id, DataSource.organization_id == organization_id, DataSource.workspace_id == workspace_id, DataSource.product_code == "ORDO"))
    if source is None: raise OrdoDomainError("data_source_not_accessible")
    row = OrdoDataMapping(organization_id=organization_id, workspace_id=workspace_id, data_source_id=data_source_id, source_type_code=source_type_code, mapping_schema=mapping_schema, status=status, notes=notes.strip(), created_by_membership_id=actor_id)
    session.add(row); session.flush(); return row


def list_observations(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, limit: int = 100):
    validate_ordo_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    stmt = select(OrdoIndicatorObservation, OrdoIndicatorDefinition).join(OrdoIndicatorDefinition, OrdoIndicatorDefinition.id == OrdoIndicatorObservation.indicator_id).where(OrdoIndicatorObservation.organization_id == organization_id, OrdoIndicatorObservation.workspace_id == workspace_id).order_by(OrdoIndicatorObservation.created_at.desc()).limit(limit)
    return list(session.execute(stmt).all())


def create_observation(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, indicator_code: str, monitoring_cycle_id: uuid.UUID | None, source_version_id: uuid.UUID | None, period_start, period_end, geography_code: str, geography_label: str, value_numeric: float | None, value_text: str, quality_status: str, provenance_note: str, actor_id: uuid.UUID | None) -> OrdoIndicatorObservation:
    validate_ordo_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    indicator = session.scalar(select(OrdoIndicatorDefinition).where(OrdoIndicatorDefinition.code == indicator_code, OrdoIndicatorDefinition.active.is_(True)))
    if indicator is None: raise OrdoDomainError("indicator_unknown")
    if monitoring_cycle_id is not None:
        cycle = session.scalar(select(OrdoMonitoringCycle).where(OrdoMonitoringCycle.id == monitoring_cycle_id, OrdoMonitoringCycle.organization_id == organization_id, OrdoMonitoringCycle.workspace_id == workspace_id))
        if cycle is None: raise OrdoDomainError("monitoring_cycle_not_accessible")
    if source_version_id is not None:
        version = session.scalar(select(DataSourceVersion).join(DataSource, DataSource.id == DataSourceVersion.data_source_id).where(DataSourceVersion.id == source_version_id, DataSource.organization_id == organization_id, DataSource.workspace_id == workspace_id, DataSource.product_code == "ORDO"))
        if version is None: raise OrdoDomainError("source_version_not_accessible")
    row = OrdoIndicatorObservation(organization_id=organization_id, workspace_id=workspace_id, indicator_id=indicator.id, monitoring_cycle_id=monitoring_cycle_id, source_version_id=source_version_id, period_start=period_start, period_end=period_end, geography_code=geography_code.strip(), geography_label=geography_label.strip(), value_numeric=value_numeric, value_text=value_text.strip(), quality_status=quality_status, provenance_note=provenance_note.strip(), created_by_membership_id=actor_id)
    session.add(row); session.flush(); return row
