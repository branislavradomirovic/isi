"""Scoped customer lifecycle for existing ORDO metadata specifications."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api.dependencies import AuthContext, get_auth_context, get_db
from src.api.ordo_analytics_routes import _require_scope, _error
from src.domains.ordo import statistical_authoring as service
from src.domains.ordo.analytics_models import OrdoStatisticalModelContract
from src.domains.ordo.analytics_service import OrdoAnalyticsError
from src.platform.ai.service import actor_membership_id

router = APIRouter(prefix="/api/v1/ordo/analytics/statistical-model-contracts", tags=["ordo-analytics"])


def authorize(db, context, organization_id, workspace_id, permission):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code=permission)


@router.get("")
def list_contracts(
    organization_id: UUID = Query(...),
    workspace_id: UUID = Query(...),
    offset: int = Query(default=0, ge=0, le=100000),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    authorize(db, context, organization_id, workspace_id, "analysis.read")
    rows = db.scalars(
        select(OrdoStatisticalModelContract)
        .where(
            OrdoStatisticalModelContract.organization_id == organization_id,
            OrdoStatisticalModelContract.workspace_id == workspace_id,
        )
        .order_by(OrdoStatisticalModelContract.created_at.desc(), OrdoStatisticalModelContract.id)
        .offset(offset)
        .limit(101)
    ).all()
    return dict(items=[service.metadata(row) for row in rows[:100]], truncated=len(rows) > 100, offset=offset)


@router.get("/{record_id}")
def detail(
    record_id: UUID,
    organization_id: UUID = Query(...),
    workspace_id: UUID = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    authorize(db, context, organization_id, workspace_id, "analysis.read")
    try:
        return service.metadata(
            service.get(db, organization_id=organization_id, workspace_id=workspace_id, record_id=record_id)
        )
    except OrdoAnalyticsError as exc:
        raise _error(exc) from None


def mutate(db, context, body, callback):
    authorize(db, context, body.organization_id, body.workspace_id, "indicator.manage")
    actor = actor_membership_id(db, user_id=context.user.id, organization_id=body.organization_id)
    if actor is None:
        raise HTTPException(status_code=403, detail="ordo_analytics_scope_not_accessible")
    try:
        row = callback(actor)
        db.commit()
        return service.metadata(row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="statistical_version_conflict_refresh_required") from None
    except (OrdoAnalyticsError, ValueError) as exc:
        db.rollback()
        raise _error(exc) from None


@router.post("", status_code=201)
def create(
    body: service.StatisticalCreate, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)
):
    return mutate(db, context, body, lambda actor: service.create(db, body=body, actor_id=actor))


@router.post("/{record_id}/{action}")
def change(
    record_id: UUID,
    action: Literal["propose", "validate", "retire"],
    body: service.StatisticalTransition,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    return mutate(
        db,
        context,
        body,
        lambda actor: service.transition(db, record_id=record_id, body=body, action=action, actor_id=actor),
    )
