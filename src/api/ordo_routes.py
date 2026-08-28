from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api.dependencies import AuthContext, get_auth_context, get_db
from src.platform.access.service import has_permission
from src.platform.app_context.service import AppContextError, resolve_selection
from src.platform.data.service import actor_membership_id
from src.domains.ordo.schemas import AssetCreateRequest, CycleCreateRequest, DestinationProfileUpsertRequest, MappingCreateRequest, ObservationCreateRequest, StakeholderCreateRequest
from src.domains.ordo.service import OrdoDomainError, catalog, create_asset, create_cycle, create_mapping, create_observation, create_stakeholder, foundation_summary, list_assets, list_cycles, list_mappings, list_observations, list_stakeholders, upsert_profile

router = APIRouter(prefix="/api/v1/ordo", tags=["ordo"])


def _require_scope(db: Session, context: AuthContext, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, permission_code: str) -> None:
    try:
        resolve_selection(db, user_id=context.user.id, organization_id=organization_id, product_code="ORDO", workspace_id=workspace_id)
    except AppContextError:
        raise HTTPException(status_code=403, detail="ordo_scope_not_accessible") from None
    if not has_permission(db, context.user.id, organization_id, permission_code, "ORDO"):
        raise HTTPException(status_code=403, detail="ordo_permission_denied")


def _error(exc: OrdoDomainError) -> HTTPException:
    code = str(exc)
    if code.endswith("not_accessible"): return HTTPException(status_code=404, detail=code)
    if code in {"source_type_unknown", "indicator_unknown"}: return HTTPException(status_code=400, detail=code)
    return HTTPException(status_code=400, detail=code)


@router.get("/catalog")
def get_catalog(organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="indicator.read")
    return catalog(db)


@router.get("/foundation")
def get_foundation(organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="indicator.read")
    try: return foundation_summary(db, organization_id=organization_id, workspace_id=workspace_id)
    except OrdoDomainError as exc: raise _error(exc) from None


@router.put("/profile")
def put_profile(payload: DestinationProfileUpsertRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="workspace.manage")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = upsert_profile(db, actor_id=actor_id, **payload.model_dump()); db.commit(); db.refresh(row)
        return {"id": str(row.id), "destination_name": row.destination_name, "destination_code": row.destination_code, "destination_type": row.destination_type, "reference_year": row.reference_year, "notes": row.notes}
    except OrdoDomainError as exc: db.rollback(); raise _error(exc) from None


@router.get("/assets")
def get_assets(organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="indicator.read")
    try: return [{"id": str(x.id), "asset_type": x.asset_type, "name": x.name, "external_code": x.external_code, "location_label": x.location_label, "description": x.description} for x in list_assets(db, organization_id=organization_id, workspace_id=workspace_id)]
    except OrdoDomainError as exc: raise _error(exc) from None


@router.post("/assets", status_code=status.HTTP_201_CREATED)
def post_asset(payload: AssetCreateRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="workspace.manage")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = create_asset(db, actor_id=actor_id, **payload.model_dump()); db.commit(); db.refresh(row)
        return {"id": str(row.id), "asset_type": row.asset_type, "name": row.name, "location_label": row.location_label}
    except OrdoDomainError as exc: db.rollback(); raise _error(exc) from None
    except IntegrityError: db.rollback(); raise HTTPException(status_code=409, detail="ordo_asset_exists") from None


@router.get("/stakeholders")
def get_stakeholders(organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="indicator.read")
    try: return [{"id": str(x.id), "stakeholder_type": x.stakeholder_type, "name": x.name, "external_code": x.external_code} for x in list_stakeholders(db, organization_id=organization_id, workspace_id=workspace_id)]
    except OrdoDomainError as exc: raise _error(exc) from None


@router.post("/stakeholders", status_code=status.HTTP_201_CREATED)
def post_stakeholder(payload: StakeholderCreateRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="workspace.manage")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = create_stakeholder(db, actor_id=actor_id, **payload.model_dump()); db.commit(); db.refresh(row)
        return {"id": str(row.id), "stakeholder_type": row.stakeholder_type, "name": row.name, "external_code": row.external_code}
    except OrdoDomainError as exc: db.rollback(); raise _error(exc) from None
    except IntegrityError: db.rollback(); raise HTTPException(status_code=409, detail="ordo_stakeholder_exists") from None


@router.get("/cycles")
def get_cycles(organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="indicator.read")
    try: return [{"id": str(x.id), "code": x.code, "title": x.title, "period_start": x.period_start, "period_end": x.period_end, "status": x.status} for x in list_cycles(db, organization_id=organization_id, workspace_id=workspace_id)]
    except OrdoDomainError as exc: raise _error(exc) from None


@router.post("/cycles", status_code=status.HTTP_201_CREATED)
def post_cycle(payload: CycleCreateRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="indicator.manage")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = create_cycle(db, actor_id=actor_id, **payload.model_dump()); db.commit(); db.refresh(row)
        return {"id": str(row.id), "code": row.code, "title": row.title, "period_start": row.period_start, "period_end": row.period_end, "status": row.status}
    except OrdoDomainError as exc: db.rollback(); raise _error(exc) from None
    except IntegrityError: db.rollback(); raise HTTPException(status_code=409, detail="ordo_cycle_exists") from None


@router.get("/mappings")
def get_mappings(organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="indicator.read")
    try: return [{"id": str(x.id), "data_source_id": str(x.data_source_id), "source_type_code": x.source_type_code, "status": x.status, "mapping_schema": x.mapping_schema, "notes": x.notes} for x in list_mappings(db, organization_id=organization_id, workspace_id=workspace_id)]
    except OrdoDomainError as exc: raise _error(exc) from None


@router.post("/mappings", status_code=status.HTTP_201_CREATED)
def post_mapping(payload: MappingCreateRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="indicator.manage")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = create_mapping(db, actor_id=actor_id, **payload.model_dump()); db.commit(); db.refresh(row)
        return {"id": str(row.id), "data_source_id": str(row.data_source_id), "source_type_code": row.source_type_code, "status": row.status}
    except OrdoDomainError as exc: db.rollback(); raise _error(exc) from None


@router.get("/observations")
def get_observations(organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), limit: int = Query(100, ge=1, le=500), context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="indicator.read")
    try:
        rows = list_observations(db, organization_id=organization_id, workspace_id=workspace_id, limit=limit)
        return [{"id": str(obs.id), "indicator_code": ind.code, "indicator_name_sr": ind.name_sr, "value_numeric": obs.value_numeric, "value_text": obs.value_text, "quality_status": obs.quality_status, "geography_label": obs.geography_label, "provenance_note": obs.provenance_note, "created_at": obs.created_at} for obs, ind in rows]
    except OrdoDomainError as exc: raise _error(exc) from None


@router.post("/observations", status_code=status.HTTP_201_CREATED)
def post_observation(payload: ObservationCreateRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="indicator.manage")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = create_observation(db, actor_id=actor_id, **payload.model_dump()); db.commit(); db.refresh(row)
        return {"id": str(row.id), "quality_status": row.quality_status, "created_at": row.created_at}
    except OrdoDomainError as exc: db.rollback(); raise _error(exc) from None
