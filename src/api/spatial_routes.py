from __future__ import annotations
from datetime import date
from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from src.api.dependencies import AuthContext, get_auth_context, get_db
from src.platform.data.storage import StorageError
from src.platform.spatial.contracts import GeometryCreate, GeometryReview, GeometryError
from src.platform.spatial.service import (
    GeometryAccessError,
    GeometryConflict,
    create_geometry,
    get_geometry,
    list_geometry,
    metadata,
    review_geometry,
)

router = APIRouter(prefix="/api/v1/spatial", tags=["spatial"])
Product = Literal["SIMPA", "ORDO"]


def fail(db, exc):
    db.rollback()
    if isinstance(exc, GeometryAccessError):
        return HTTPException(404 if str(exc) == "geometry_not_accessible" else 403, str(exc))
    if isinstance(exc, (GeometryConflict, StaleDataError, IntegrityError)):
        return HTTPException(409, "geometry_conflict")
    if isinstance(exc, StorageError):
        return HTTPException(503, "geometry_storage_unavailable")
    return HTTPException(400, str(exc))


@router.post("/{product_code}/geometries", status_code=201)
def create(
    product_code: Product,
    payload: GeometryCreate,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    try:
        row = create_geometry(db, user_id=context.user.id, product_code=product_code, payload=payload)
        db.commit()
        return metadata(row)
    except (GeometryError, StorageError, IntegrityError) as exc:
        raise fail(db, exc) from None


@router.get("/{product_code}/geometries")
def listing(
    product_code: Product,
    organization_id: UUID,
    workspace_id: UUID,
    limit: int = Query(100, ge=1, le=100),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    try:
        return [
            metadata(row)
            for row in list_geometry(
                db,
                user_id=context.user.id,
                organization_id=organization_id,
                workspace_id=workspace_id,
                product_code=product_code,
                limit=limit,
            )
        ]
    except GeometryError as exc:
        raise fail(db, exc) from None


@router.post("/{product_code}/geometries/{geometry_id}/review")
def review(
    product_code: Product,
    geometry_id: UUID,
    payload: GeometryReview,
    organization_id: UUID,
    workspace_id: UUID,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    try:
        row = review_geometry(
            db,
            user_id=context.user.id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
            geometry_id=geometry_id,
            payload=payload,
        )
        db.commit()
        return metadata(row)
    except (GeometryError, StorageError, StaleDataError, IntegrityError) as exc:
        raise fail(db, exc) from None


@router.get("/{product_code}/geometries/{geometry_id}")
def detail(
    product_code: Product,
    geometry_id: UUID,
    organization_id: UUID,
    workspace_id: UUID,
    at_date: date,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    try:
        return get_geometry(
            db,
            user_id=context.user.id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
            geometry_id=geometry_id,
            at_date=at_date,
        )
    except (GeometryError, StorageError) as exc:
        raise fail(db, exc) from None
