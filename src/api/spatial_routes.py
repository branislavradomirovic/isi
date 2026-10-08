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


@router.get("/{product_code}/targets")
def targets(
    product_code: Product,
    organization_id: UUID,
    workspace_id: UUID,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    from src.platform.spatial.service import authorize

    try:
        authorize(
            db,
            user_id=context.user.id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
            permission="data.read",
        )
        if product_code == "SIMPA":
            from src.domains.simpa.spatial_adapter import targets as domain_targets
        else:
            from src.domains.ordo.spatial_adapter import targets as domain_targets
        return domain_targets(db, organization_id=organization_id, workspace_id=workspace_id)
    except GeometryError as exc:
        raise fail(db, exc) from None


@router.get("/{product_code}/geometries/{geometry_id}/export")
def export(
    product_code: Product,
    geometry_id: UUID,
    organization_id: UUID,
    workspace_id: UUID,
    at_date: date,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    from src.platform.spatial.service import export_geometry

    try:
        payload = export_geometry(
            db,
            user_id=context.user.id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
            geometry_id=geometry_id,
            at_date=at_date,
        )
        db.commit()
        return payload
    except (GeometryError, StorageError) as exc:
        raise fail(db, exc) from None


@router.get("/{product_code}/geometries/{geometry_id}/results")
def results(
    product_code: Product,
    geometry_id: UUID,
    organization_id: UUID,
    workspace_id: UUID,
    at_date: date,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    from src.platform.spatial.service import authorize, scoped_row

    try:
        authorize(
            db,
            user_id=context.user.id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
            permission="analysis.read",
        )
        get_geometry(
            db,
            user_id=context.user.id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
            geometry_id=geometry_id,
            at_date=at_date,
        )
        if product_code == "SIMPA":
            return {"status": "UNAVAILABLE", "reason": "simpa_result_geography_binding_not_approved", "results": []}
        row = scoped_row(
            db,
            geometry_id=geometry_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
        )
        from src.domains.ordo.spatial_adapter import linked_results

        return linked_results(db, organization_id=organization_id, workspace_id=workspace_id, geometry_row=row)
    except (GeometryError, StorageError) as exc:
        raise fail(db, exc) from None


# Existing ORDO identity authoring, separate from reviewed geometry registration.
from pydantic import BaseModel, ConfigDict, Field, model_validator  # noqa: E402


class UnitCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    organization_id: UUID
    workspace_id: UUID
    spatial_unit_key: str = Field(min_length=1, max_length=160)
    spatial_unit_type: Literal["national", "macro_region", "region", "local_government", "custom"]
    name: str = Field(min_length=1, max_length=300)
    boundary_source: str = Field(min_length=1, max_length=300)
    boundary_version: str = Field(min_length=1, max_length=120)
    geometry_id: str = Field(min_length=1, max_length=300)
    crs: Literal["OGC:CRS84", "EPSG:4326"]
    artifact_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    valid_from: date
    valid_to: date | None = None

    @model_validator(mode="after")
    def valid(self):
        from urllib.parse import urlsplit

        url = urlsplit(self.boundary_source)
        if (
            url.scheme != "https"
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
            or (self.valid_to is not None and self.valid_to < self.valid_from)
        ):
            raise ValueError("spatial_unit_source_or_validity_invalid")
        return self


class UnitReview(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    state: Literal["proposed", "validated", "retired"]
    note: str = Field(min_length=1, max_length=1000)


def unit_metadata(row):
    names = (
        "id",
        "spatial_unit_key",
        "spatial_unit_type",
        "name",
        "boundary_source",
        "boundary_version",
        "geometry_id",
        "crs",
        "artifact_sha256",
        "valid_from",
        "valid_to",
        "lifecycle_status",
        "created_by_membership_id",
        "proposed_by_membership_id",
        "proposed_at",
        "validated_by_membership_id",
        "validated_at",
        "retired_by_membership_id",
        "retired_at",
    )
    return {k: str(v) if isinstance(v, (date, UUID)) else v for k in names if (v := getattr(row, k)) is not None}


@router.get("/ORDO/units")
def units(
    organization_id: UUID,
    workspace_id: UUID,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    from src.platform.spatial.service import authorize
    from src.domains.ordo.models import OrdoSpatialUnit
    from sqlalchemy import select

    try:
        authorize(
            db,
            user_id=context.user.id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code="ORDO",
            permission="data.read",
        )
        rows = db.scalars(
            select(OrdoSpatialUnit)
            .where(OrdoSpatialUnit.organization_id == organization_id, OrdoSpatialUnit.workspace_id == workspace_id)
            .order_by(OrdoSpatialUnit.id)
            .limit(101)
        ).all()
        return {"items": [unit_metadata(x) for x in rows[:100]], "truncated": len(rows) > 100}
    except GeometryError as exc:
        raise fail(db, exc) from None


@router.post("/ORDO/units", status_code=201)
def unit_create(payload: UnitCreate, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    from src.platform.spatial.service import authorize
    from src.domains.ordo.service import create_spatial_unit, OrdoDomainError

    try:
        actor = authorize(
            db,
            user_id=context.user.id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code="ORDO",
            permission="data.governance.manage",
        )
        row = create_spatial_unit(
            db,
            **payload.model_dump(),
            actor_id=actor,
            provenance={"source_verification": "DECLARED", "schema": "ISI-29C-UNIT-v1"},
        )
        db.commit()
        return unit_metadata(row)
    except (GeometryError, OrdoDomainError, IntegrityError) as exc:
        raise fail(db, exc) from None


@router.post("/ORDO/units/{unit_id}/review")
def unit_review(
    unit_id: UUID,
    payload: UnitReview,
    organization_id: UUID,
    workspace_id: UUID,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    from src.platform.spatial.service import authorize
    from src.domains.ordo.service import transition_spatial_unit, OrdoDomainError

    try:
        actor = authorize(
            db,
            user_id=context.user.id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code="ORDO",
            permission="data.validate" if payload.state == "validated" else "data.governance.manage",
        )
        from sqlalchemy import select
        from src.domains.ordo.models import OrdoSpatialUnit

        locked = db.scalar(
            select(OrdoSpatialUnit)
            .where(
                OrdoSpatialUnit.id == unit_id,
                OrdoSpatialUnit.organization_id == organization_id,
                OrdoSpatialUnit.workspace_id == workspace_id,
            )
            .with_for_update()
        )
        if locked is None:
            raise GeometryAccessError("geometry_not_accessible")
        row = transition_spatial_unit(
            db,
            spatial_unit_id=unit_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            target_status=payload.state,
            note=payload.note,
            actor_id=actor,
        )
        db.commit()
        return unit_metadata(row)
    except (GeometryError, OrdoDomainError, IntegrityError) as exc:
        raise fail(db, exc) from None
