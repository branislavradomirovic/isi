"""Authenticated documentary evidence transport, never echo source/provider errors."""

from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.api.dependencies import get_db, get_auth_context, AuthContext
from src.platform.extraction.contracts import Create, Review
from src.platform.extraction import service
from src.platform.spatial.service import GeometryAccessError
from src.platform.ai.queue import dispatch_ai_job
from src.platform.ai.models import AIJob

router = APIRouter(prefix="/api/v1/extraction", tags=["extraction"])
Product = Literal["SIMPA", "ORDO"]


def fail(db, exc):
    db.rollback()
    if isinstance(exc, GeometryAccessError):
        return HTTPException(403, "extraction_access_denied")
    if isinstance(exc, IntegrityError):
        return HTTPException(409, "extraction_conflict")
    return HTTPException(409, "extraction_unavailable_or_invalid")


@router.post("/{product_code}/requests", status_code=201)
def create(
    product_code: Product,
    payload: Create,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    try:
        row, new = service.create_request(db, user_id=context.user.id, product_code=product_code, payload=payload)
        db.commit()
    except (ValueError, RuntimeError, IntegrityError) as exc:
        raise fail(db, exc) from None
    if new:
        try:
            dispatch_ai_job(row.job_id)
        except Exception:
            # Bind persisted failure to existing queue evidence; retry is explicit new request.
            job = db.get(AIJob, row.job_id)
            if job.status == "queued":
                job.status = "failed"
                job.error_code = "extraction_dispatch_failed"
                job.error_message = "Queue dispatch unavailable."
                job.request_text = ""
                db.commit()
    db.expire_all()
    return service.metadata(db, row)


@router.get("/{product_code}/requests")
def listing(
    product_code: Product,
    organization_id: UUID,
    workspace_id: UUID,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    try:
        return service.listing(
            db,
            user_id=context.user.id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
        )
    except (ValueError, RuntimeError) as exc:
        raise fail(db, exc) from None


@router.get("/{product_code}/requests/{request_id}")
def detail(
    product_code: Product,
    request_id: UUID,
    organization_id: UUID,
    workspace_id: UUID,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    try:
        return service.detail(
            db,
            user_id=context.user.id,
            request_id=request_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
        )
    except (ValueError, RuntimeError) as exc:
        raise fail(db, exc) from None


@router.post("/{product_code}/requests/{request_id}/review")
def review(
    product_code: Product,
    request_id: UUID,
    payload: Review,
    organization_id: UUID,
    workspace_id: UUID,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    try:
        result = service.review_request(
            db,
            user_id=context.user.id,
            request_id=request_id,
            payload=payload,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
        )
        db.commit()
        return result
    except (ValueError, RuntimeError, IntegrityError) as exc:
        raise fail(db, exc) from None


@router.post("/{product_code}/requests/{request_id}/cancel")
def cancel(
    product_code: Product,
    request_id: UUID,
    organization_id: UUID,
    workspace_id: UUID,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    try:
        result = service.cancel(
            db,
            user_id=context.user.id,
            request_id=request_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
        )
        db.commit()
        return result
    except (ValueError, RuntimeError, IntegrityError) as exc:
        raise fail(db, exc) from None


@router.get("/{product_code}/claims")
def claims(
    product_code: Product,
    organization_id: UUID,
    workspace_id: UUID,
    geometry_id: UUID | None = None,
    period: str | None = Query(None, max_length=100),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    try:
        return service.retrieve(
            db,
            user_id=context.user.id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
            geometry_id=geometry_id,
            period=period,
        )
    except (ValueError, RuntimeError) as exc:
        raise fail(db, exc) from None
