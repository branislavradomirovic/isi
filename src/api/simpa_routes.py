from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.api.dependencies import AuthContext, get_auth_context, get_db
from src.platform.access.service import has_permission
from src.platform.app_context.service import AppContextError, resolve_selection
from src.platform.data.service import actor_membership_id
from src.domains.simpa.schemas import ActorCreateRequest, CycleCreateRequest, MappingCreateRequest, ObservationCreateRequest, ProfileUpsertRequest
from src.domains.simpa.service import SimpaDomainError, catalog, create_actor, create_cycle, create_mapping, create_observation, foundation_summary, list_actors, list_cycles, list_mappings, list_observations, upsert_profile

router = APIRouter(prefix="/api/v1/simpa", tags=["simpa"])


def _require_scope(db: Session, context: AuthContext, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, permission_code: str) -> None:
    try:
        resolve_selection(db, user_id=context.user.id, organization_id=organization_id, product_code="SIMPA", workspace_id=workspace_id)
    except AppContextError:
        raise HTTPException(status_code=403, detail="simpa_scope_not_accessible") from None
    if not has_permission(db, context.user.id, organization_id, permission_code, "SIMPA"):
        raise HTTPException(status_code=403, detail="simpa_permission_denied")


def _error(exc: SimpaDomainError) -> HTTPException:
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
    except SimpaDomainError as exc: raise _error(exc) from None


@router.put("/profile")
def put_profile(payload: ProfileUpsertRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="workspace.manage")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = upsert_profile(db, actor_id=actor_id, **payload.model_dump())
        db.commit(); db.refresh(row)
        return {"id": str(row.id), "jurisdiction_name": row.jurisdiction_name, "jurisdiction_code": row.jurisdiction_code, "reference_year": row.reference_year, "notes": row.notes}
    except SimpaDomainError as exc: db.rollback(); raise _error(exc) from None


@router.get("/actors")
def get_actors(organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="indicator.read")
    try: return [{"id": str(x.id), "actor_type": x.actor_type, "name": x.name, "external_code": x.external_code} for x in list_actors(db, organization_id=organization_id, workspace_id=workspace_id)]
    except SimpaDomainError as exc: raise _error(exc) from None


@router.post("/actors", status_code=status.HTTP_201_CREATED)
def post_actor(payload: ActorCreateRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="workspace.manage")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = create_actor(db, actor_id=actor_id, **payload.model_dump()); db.commit(); db.refresh(row)
        return {"id": str(row.id), "actor_type": row.actor_type, "name": row.name, "external_code": row.external_code}
    except SimpaDomainError as exc:
        db.rollback(); raise _error(exc) from None
    except IntegrityError:
        db.rollback(); raise HTTPException(status_code=409, detail="simpa_actor_exists") from None


@router.get("/cycles")
def get_cycles(organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="indicator.read")
    try: return [{"id": str(x.id), "code": x.code, "title": x.title, "period_start": x.period_start, "period_end": x.period_end, "status": x.status} for x in list_cycles(db, organization_id=organization_id, workspace_id=workspace_id)]
    except SimpaDomainError as exc: raise _error(exc) from None


@router.post("/cycles", status_code=status.HTTP_201_CREATED)
def post_cycle(payload: CycleCreateRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="indicator.manage")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = create_cycle(db, actor_id=actor_id, **payload.model_dump()); db.commit(); db.refresh(row)
        return {"id": str(row.id), "code": row.code, "title": row.title, "period_start": row.period_start, "period_end": row.period_end, "status": row.status}
    except SimpaDomainError as exc: db.rollback(); raise _error(exc) from None
    except IntegrityError:
        db.rollback(); raise HTTPException(status_code=409, detail="simpa_cycle_exists") from None


@router.get("/mappings")
def get_mappings(organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="indicator.read")
    try: return [{"id": str(x.id), "data_source_id": str(x.data_source_id), "source_type_code": x.source_type_code, "status": x.status, "mapping_schema": x.mapping_schema, "notes": x.notes} for x in list_mappings(db, organization_id=organization_id, workspace_id=workspace_id)]
    except SimpaDomainError as exc: raise _error(exc) from None


@router.post("/mappings", status_code=status.HTTP_201_CREATED)
def post_mapping(payload: MappingCreateRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="indicator.manage")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = create_mapping(db, actor_id=actor_id, **payload.model_dump()); db.commit(); db.refresh(row)
        return {"id": str(row.id), "data_source_id": str(row.data_source_id), "source_type_code": row.source_type_code, "status": row.status}
    except SimpaDomainError as exc: db.rollback(); raise _error(exc) from None


@router.get("/observations")
def get_observations(organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), limit: int = Query(100, ge=1, le=500), context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="indicator.read")
    try:
        rows = list_observations(db, organization_id=organization_id, workspace_id=workspace_id, limit=limit)
        return [{"id": str(obs.id), "indicator_code": ind.code, "indicator_name_sr": ind.name_sr, "value_numeric": obs.value_numeric, "value_text": obs.value_text, "quality_status": obs.quality_status, "geography_label": obs.geography_label, "population_group": obs.population_group, "provenance_note": obs.provenance_note, "created_at": obs.created_at} for obs, ind in rows]
    except SimpaDomainError as exc: raise _error(exc) from None


@router.post("/observations", status_code=status.HTTP_201_CREATED)
def post_observation(payload: ObservationCreateRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="indicator.manage")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = create_observation(db, actor_id=actor_id, **payload.model_dump()); db.commit(); db.refresh(row)
        return {"id": str(row.id), "quality_status": row.quality_status, "created_at": row.created_at}
    except SimpaDomainError as exc: db.rollback(); raise _error(exc) from None
