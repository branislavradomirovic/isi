from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.dependencies import AuthContext, get_auth_context, get_db
from src.core.config import get_settings
from src.platform.access.service import has_permission
from src.platform.app_context.service import AppContextError, resolve_selection
from src.platform.data.models import DataSourceVersion, IngestionJob
from src.platform.data.queue import DataQueueError, dispatch_job
from src.platform.data.schemas import (
    IngestionJobResponse,
    ScopeQuery,
    SourceDetailResponse,
    SourceSummaryResponse,
    UploadCreateRequest,
    UploadResponse,
    VersionCreateRequest,
)
from src.platform.data.service import (
    DataPlatformError,
    actor_membership_id,
    create_source_upload,
    create_source_version,
    create_validation_job,
    decode_upload,
    get_scoped_source,
    job_response,
    list_sources,
    source_detail,
    source_summary,
)
from src.platform.data.storage import build_storage


router = APIRouter(prefix="/api/v1/data", tags=["data"])


def _require_scope(
    db: Session,
    context: AuthContext,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    permission_code: str,
) -> None:
    try:
        resolve_selection(
            db,
            user_id=context.user.id,
            organization_id=organization_id,
            product_code=product_code,
            workspace_id=workspace_id,
        )
    except AppContextError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="data scope not accessible") from None
    if not has_permission(db, context.user.id, organization_id, permission_code, product_code):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="data permission denied")


def _platform_error(exc: DataPlatformError) -> HTTPException:
    code = str(exc)
    if code in {"source_not_accessible", "workspace_scope_mismatch"}:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=code)
    if code in {"upload_too_large"}:
        return HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=code)
    if code in {"source_name_exists"}:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=code)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=code)


def _dispatch_or_503(job_id: uuid.UUID) -> None:
    try:
        dispatch_job(job_id)
    except DataQueueError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="data job queue unavailable") from exc


@router.get("/sources", response_model=list[SourceSummaryResponse])
def get_sources(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        permission_code="data.read",
    )
    try:
        return list_sources(db, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    except DataPlatformError as exc:
        raise _platform_error(exc) from None


@router.post("/sources", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
def post_source(
    payload: UploadCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
        permission_code="data.upload",
    )
    settings = get_settings()
    try:
        raw = decode_upload(payload.content_base64, max_bytes=int(getattr(settings, "data_max_upload_bytes", 16777216)))
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        source, version, job, reused = create_source_upload(
            db,
            build_storage(),
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
            source_name=payload.source_name,
            filename=payload.filename,
            content_type=payload.content_type,
            payload=raw,
            actor_id=actor_id,
            backend=getattr(settings, "data_job_backend", "inline"),
        )
        db.commit()
        job_id = job.id
        _dispatch_or_503(job_id)
        db.expire_all()
        source = get_scoped_source(
            db,
            source_id=source.id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
        )
        version = db.get(DataSourceVersion, version.id)
        job = db.get(IngestionJob, job_id)
        return UploadResponse(
            source=source_summary(db, source),
            version=source_detail(db, source).versions[0] if version is not None else source_summary(db, source).latest_version,
            job=job_response(job),
            storage_reused=reused,
        )
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.get("/sources/{source_id}", response_model=SourceDetailResponse)
def get_source(
    source_id: uuid.UUID,
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        permission_code="data.read",
    )
    try:
        source = get_scoped_source(
            db,
            source_id=source_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
        )
        return source_detail(db, source)
    except DataPlatformError as exc:
        raise _platform_error(exc) from None


@router.post("/sources/{source_id}/versions", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
def post_source_version(
    source_id: uuid.UUID,
    payload: VersionCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
        permission_code="data.upload",
    )
    settings = get_settings()
    try:
        raw = decode_upload(payload.content_base64, max_bytes=int(getattr(settings, "data_max_upload_bytes", 16777216)))
        source = get_scoped_source(
            db,
            source_id=source_id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
        )
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        version, job, reused = create_source_version(
            db,
            build_storage(),
            source=source,
            filename=payload.filename,
            content_type=payload.content_type,
            payload=raw,
            actor_id=actor_id,
            backend=getattr(settings, "data_job_backend", "inline"),
        )
        db.commit()
        _dispatch_or_503(job.id)
        db.expire_all()
        source = get_scoped_source(
            db,
            source_id=source_id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
        )
        latest = source_detail(db, source).versions[0]
        refreshed_job = db.get(IngestionJob, job.id)
        return UploadResponse(source=source_summary(db, source), version=latest, job=job_response(refreshed_job), storage_reused=reused)
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.post("/versions/{version_id}/validate", response_model=IngestionJobResponse, status_code=status.HTTP_202_ACCEPTED)
def validate_version(
    version_id: uuid.UUID,
    payload: ScopeQuery,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
        permission_code="data.validate",
    )
    version = db.scalar(
        select(DataSourceVersion).where(
            DataSourceVersion.id == version_id,
            DataSourceVersion.organization_id == payload.organization_id,
            DataSourceVersion.workspace_id == payload.workspace_id,
            DataSourceVersion.product_code == payload.product_code,
        )
    )
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="version_not_accessible")
    settings = get_settings()
    actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
    job = create_validation_job(db, version=version, actor_id=actor_id, backend=getattr(settings, "data_job_backend", "inline"))
    db.commit()
    _dispatch_or_503(job.id)
    db.expire_all()
    return job_response(db.get(IngestionJob, job.id))


@router.get("/jobs/{job_id}", response_model=IngestionJobResponse)
def get_job(
    job_id: uuid.UUID,
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        permission_code="data.read",
    )
    job = db.scalar(
        select(IngestionJob).where(
            IngestionJob.id == job_id,
            IngestionJob.organization_id == organization_id,
            IngestionJob.workspace_id == workspace_id,
            IngestionJob.product_code == product_code,
        )
    )
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job_not_accessible")
    return job_response(job)
