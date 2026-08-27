from __future__ import annotations

import base64
import binascii
import uuid
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from src.platform.data.models import DataAuditEvent, DataQualityResult, DataSource, DataSourceVersion, IngestionJob
from src.platform.data.schemas import (
    IngestionJobResponse,
    QualityResultResponse,
    SourceDetailResponse,
    SourceSummaryResponse,
    UploadResponse,
    VersionResponse,
)
from src.platform.data.storage import StorageBackend, digest_bytes, scoped_storage_key
from src.platform.identity.models import Membership
from src.platform.workspaces.models import Workspace


class DataPlatformError(ValueError):
    pass


DATASET_EXTENSIONS = {"csv", "json", "xlsx"}
DOCUMENT_EXTENSIONS = {"pdf", "docx", "txt"}
ALLOWED_EXTENSIONS = DATASET_EXTENSIONS | DOCUMENT_EXTENSIONS


def actor_membership_id(session: Session, *, user_id: uuid.UUID, organization_id: uuid.UUID) -> uuid.UUID | None:
    membership = session.scalar(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.organization_id == organization_id,
            Membership.status == "active",
        )
    )
    return membership.id if membership is not None else None


def validate_scope(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> Workspace:
    if product_code not in {"SIMPA", "ORDO"}:
        raise DataPlatformError("unsupported_product")
    workspace = session.scalar(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.organization_id == organization_id,
            Workspace.product_code == product_code,
            Workspace.status == "active",
        )
    )
    if workspace is None:
        raise DataPlatformError("workspace_scope_mismatch")
    return workspace


def decode_upload(content_base64: str, *, max_bytes: int) -> bytes:
    try:
        payload = base64.b64decode(content_base64.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error) as exc:
        raise DataPlatformError("invalid_base64") from exc
    if not payload:
        raise DataPlatformError("empty_upload")
    if len(payload) > max_bytes:
        raise DataPlatformError("upload_too_large")
    return payload


def safe_filename(filename: str) -> tuple[str, str]:
    name = Path(filename.replace("\\", "/")).name.strip()
    if not name or name in {".", ".."}:
        raise DataPlatformError("invalid_filename")
    ext = Path(name).suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise DataPlatformError("unsupported_format")
    return name[:500], ext


def _audit(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    actor_id: uuid.UUID | None,
    event_type: str,
    entity_type: str,
    entity_id: uuid.UUID,
    detail: str,
) -> None:
    session.add(
        DataAuditEvent(
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
            actor_membership_id=actor_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            detail=detail[:4000],
        )
    )


def _version_response(session: Session, version: DataSourceVersion) -> VersionResponse:
    quality_rows = session.scalars(
        select(DataQualityResult)
        .where(DataQualityResult.version_id == version.id)
        .order_by(DataQualityResult.check_code, DataQualityResult.id)
    ).all()
    return VersionResponse(
        id=version.id,
        version_no=version.version_no,
        original_filename=version.original_filename,
        extension=version.extension,
        content_type=version.content_type,
        size_bytes=version.size_bytes,
        sha256=version.sha256,
        ingest_status=version.ingest_status,
        detected_format=version.detected_format,
        row_count=version.row_count,
        column_count=version.column_count,
        sheet_count=version.sheet_count,
        schema_fingerprint=version.schema_fingerprint,
        created_at=version.created_at,
        quality=[
            QualityResultResponse(
                check_code=row.check_code,
                status=row.status,
                message=row.message,
                metric_name=row.metric_name,
                metric_value=row.metric_value,
            )
            for row in quality_rows
        ],
    )


def _latest_version(session: Session, source_id: uuid.UUID) -> DataSourceVersion | None:
    return session.scalar(
        select(DataSourceVersion)
        .where(DataSourceVersion.source_id == source_id)
        .order_by(DataSourceVersion.version_no.desc())
        .limit(1)
    )


def source_summary(session: Session, source: DataSource) -> SourceSummaryResponse:
    latest = _latest_version(session, source.id)
    return SourceSummaryResponse(
        id=source.id,
        name=source.name,
        source_kind=source.source_kind,
        product_code=source.product_code,
        workspace_id=source.workspace_id,
        status=source.status,
        created_at=source.created_at,
        latest_version=_version_response(session, latest) if latest else None,
    )


def source_detail(session: Session, source: DataSource) -> SourceDetailResponse:
    versions = session.scalars(
        select(DataSourceVersion)
        .where(DataSourceVersion.source_id == source.id)
        .order_by(DataSourceVersion.version_no.desc())
    ).all()
    latest = versions[0] if versions else None
    return SourceDetailResponse(
        id=source.id,
        name=source.name,
        source_kind=source.source_kind,
        product_code=source.product_code,
        workspace_id=source.workspace_id,
        status=source.status,
        created_at=source.created_at,
        latest_version=_version_response(session, latest) if latest else None,
        versions=[_version_response(session, version) for version in versions],
    )


def job_response(job: IngestionJob) -> IngestionJobResponse:
    return IngestionJobResponse(
        id=job.id,
        version_id=job.version_id,
        job_type=job.job_type,
        status=job.status,
        backend=job.backend,
        progress=job.progress,
        attempts=job.attempts,
        error_code=job.error_code,
        error_message=job.error_message,
        queued_at=job.queued_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


def list_sources(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> list[SourceSummaryResponse]:
    validate_scope(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    rows = session.scalars(
        select(DataSource)
        .where(
            DataSource.organization_id == organization_id,
            DataSource.workspace_id == workspace_id,
            DataSource.product_code == product_code,
            DataSource.status == "active",
        )
        .order_by(DataSource.created_at.desc(), DataSource.id)
    ).all()
    return [source_summary(session, row) for row in rows]


def get_scoped_source(
    session: Session,
    *,
    source_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> DataSource:
    validate_scope(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    source = session.scalar(
        select(DataSource).where(
            DataSource.id == source_id,
            DataSource.organization_id == organization_id,
            DataSource.workspace_id == workspace_id,
            DataSource.product_code == product_code,
            DataSource.status == "active",
        )
    )
    if source is None:
        raise DataPlatformError("source_not_accessible")
    return source


def _create_version(
    session: Session,
    storage: StorageBackend,
    *,
    source: DataSource,
    filename: str,
    content_type: str,
    payload: bytes,
    actor_id: uuid.UUID | None,
    backend: str,
) -> tuple[DataSourceVersion, IngestionJob, bool]:
    safe_name, extension = safe_filename(filename)
    sha256 = digest_bytes(payload)
    storage_key = scoped_storage_key(
        organization_id=str(source.organization_id),
        product_code=source.product_code,
        workspace_id=str(source.workspace_id),
        sha256=sha256,
        extension=extension,
    )
    stored_new = storage.put_bytes(storage_key, payload)
    next_no = (session.scalar(select(func.max(DataSourceVersion.version_no)).where(DataSourceVersion.source_id == source.id)) or 0) + 1
    version = DataSourceVersion(
        source_id=source.id,
        organization_id=source.organization_id,
        workspace_id=source.workspace_id,
        product_code=source.product_code,
        version_no=next_no,
        original_filename=safe_name,
        extension=extension,
        content_type=(content_type or "application/octet-stream")[:200],
        size_bytes=len(payload),
        sha256=sha256,
        storage_key=storage_key,
        ingest_status="queued",
        created_by_membership_id=actor_id,
    )
    session.add(version)
    session.flush()
    job = IngestionJob(
        version_id=version.id,
        organization_id=source.organization_id,
        workspace_id=source.workspace_id,
        product_code=source.product_code,
        job_type="inspect",
        status="queued",
        backend=backend,
        progress=0,
        created_by_membership_id=actor_id,
    )
    session.add(job)
    session.flush()
    _audit(
        session,
        organization_id=source.organization_id,
        workspace_id=source.workspace_id,
        product_code=source.product_code,
        actor_id=actor_id,
        event_type="data.version.uploaded",
        entity_type="data_source_version",
        entity_id=version.id,
        detail=f"filename={safe_name}; sha256={sha256}; storage_reused={str(not stored_new).lower()}",
    )
    return version, job, not stored_new


def create_source_upload(
    session: Session,
    storage: StorageBackend,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    source_name: str,
    filename: str,
    content_type: str,
    payload: bytes,
    actor_id: uuid.UUID | None,
    backend: str,
) -> tuple[DataSource, DataSourceVersion, IngestionJob, bool]:
    validate_scope(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    name = " ".join(source_name.split()).strip()
    if not name:
        raise DataPlatformError("source_name_required")
    existing = session.scalar(select(DataSource).where(DataSource.workspace_id == workspace_id, DataSource.name == name))
    if existing is not None:
        raise DataPlatformError("source_name_exists")
    _safe, ext = safe_filename(filename)
    source = DataSource(
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        name=name[:300],
        source_kind="dataset" if ext in DATASET_EXTENSIONS else "document",
        status="active",
        created_by_membership_id=actor_id,
    )
    session.add(source)
    session.flush()
    _audit(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        actor_id=actor_id,
        event_type="data.source.created",
        entity_type="data_source",
        entity_id=source.id,
        detail=f"name={source.name}; kind={source.source_kind}",
    )
    version, job, reused = _create_version(
        session,
        storage,
        source=source,
        filename=filename,
        content_type=content_type,
        payload=payload,
        actor_id=actor_id,
        backend=backend,
    )
    return source, version, job, reused


def create_source_version(
    session: Session,
    storage: StorageBackend,
    *,
    source: DataSource,
    filename: str,
    content_type: str,
    payload: bytes,
    actor_id: uuid.UUID | None,
    backend: str,
) -> tuple[DataSourceVersion, IngestionJob, bool]:
    return _create_version(
        session,
        storage,
        source=source,
        filename=filename,
        content_type=content_type,
        payload=payload,
        actor_id=actor_id,
        backend=backend,
    )


def create_validation_job(
    session: Session,
    *,
    version: DataSourceVersion,
    actor_id: uuid.UUID | None,
    backend: str,
) -> IngestionJob:
    job = IngestionJob(
        version_id=version.id,
        organization_id=version.organization_id,
        workspace_id=version.workspace_id,
        product_code=version.product_code,
        job_type="validate",
        status="queued",
        backend=backend,
        progress=0,
        created_by_membership_id=actor_id,
    )
    session.add(job)
    session.flush()
    version.ingest_status = "queued"
    _audit(
        session,
        organization_id=version.organization_id,
        workspace_id=version.workspace_id,
        product_code=version.product_code,
        actor_id=actor_id,
        event_type="data.validation.requested",
        entity_type="data_source_version",
        entity_id=version.id,
        detail=f"job_id={job.id}",
    )
    return job


def replace_quality_results(session: Session, version_id: uuid.UUID, checks) -> None:
    session.execute(delete(DataQualityResult).where(DataQualityResult.version_id == version_id))
    for check in checks:
        session.add(
            DataQualityResult(
                version_id=version_id,
                check_code=check.code,
                status=check.status,
                message=check.message,
                metric_name=check.metric_name,
                metric_value=check.metric_value,
            )
        )
