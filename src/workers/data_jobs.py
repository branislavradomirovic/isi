from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.database import build_session_factory
from src.platform.data.ingestion import IngestionError, inspect_payload
from src.platform.data.models import (
    DataAuditEvent,
    DataConnectorContractVersion,
    DataIngestionRun,
    DataSource,
    DataSourceSchemaMappingVersion,
    DataSourceVersion,
    IngestionJob,
)
from src.platform.data.service import replace_quality_results
from src.platform.data.storage import StorageError, build_storage
from src.platform.observability.telemetry import record_ingestion, record_worker_execution


def _utcnow():
    return datetime.now(timezone.utc)


def _run_audit(
    session: Session,
    *,
    run: DataIngestionRun,
    event_type: str,
    error_code: str = "",
) -> None:
    detail = (
        f"run_no={run.run_no}; connector_contract_version_id={run.connector_contract_version_id}; "
        f"schema_mapping_version_id={run.schema_mapping_version_id}; "
        f"source_version_id={run.source_version_id}; inspection_job_id={run.inspection_job_id}; "
        f"status={run.status}; request_fingerprint={run.request_fingerprint}"
    )
    if error_code:
        detail = f"{detail}; error_code={error_code}"
    session.add(
        DataAuditEvent(
            organization_id=run.organization_id,
            workspace_id=run.workspace_id,
            product_code=run.product_code,
            actor_membership_id=None,
            event_type=event_type,
            entity_type="data_ingestion_run",
            entity_id=run.id,
            detail=detail,
        )
    )


def _linked_run_integrity_valid(
    session: Session,
    *,
    run: DataIngestionRun,
    job: IngestionJob,
    version: DataSourceVersion,
) -> bool:
    source = session.scalar(
        select(DataSource).where(
            DataSource.id == run.source_id,
            DataSource.organization_id == run.organization_id,
            DataSource.workspace_id == run.workspace_id,
            DataSource.product_code == run.product_code,
        )
    )
    if source is None:
        return False
    scope = (source.organization_id, source.workspace_id, source.product_code)
    if (
        run.status != "QUEUED"
        or run.inspection_job_id != job.id
        or run.source_version_id != job.version_id
        or version.id != run.source_version_id
        or version.source_id != source.id
        or job.job_type != "inspect"
        or (run.organization_id, run.workspace_id, run.product_code) != scope
        or (version.organization_id, version.workspace_id, version.product_code) != scope
        or (job.organization_id, job.workspace_id, job.product_code) != scope
    ):
        return False
    connector = session.scalar(
        select(DataConnectorContractVersion).where(
            DataConnectorContractVersion.id == run.connector_contract_version_id,
            DataConnectorContractVersion.source_id == source.id,
            DataConnectorContractVersion.organization_id == source.organization_id,
            DataConnectorContractVersion.workspace_id == source.workspace_id,
            DataConnectorContractVersion.product_code == source.product_code,
        )
    )
    mapping = session.scalar(
        select(DataSourceSchemaMappingVersion).where(
            DataSourceSchemaMappingVersion.id == run.schema_mapping_version_id,
            DataSourceSchemaMappingVersion.source_id == source.id,
            DataSourceSchemaMappingVersion.organization_id == source.organization_id,
            DataSourceSchemaMappingVersion.workspace_id == source.workspace_id,
            DataSourceSchemaMappingVersion.product_code == source.product_code,
        )
    )
    return bool(
        connector is not None
        and mapping is not None
        and run.connector_contract_version_id == connector.id
        and run.schema_mapping_version_id == mapping.id
        and mapping.connector_contract_version_id == connector.id
    )


def _fail_linked_integrity(
    session: Session,
    *,
    run: DataIngestionRun,
    job: IngestionJob,
    version: DataSourceVersion | None,
) -> None:
    now = _utcnow()
    error_code = "ingestion_run_execution_integrity_failed"
    error_message = "ingestion run provenance integrity check failed"
    job.status = "failed"
    job.progress = 100
    job.attempts += 1
    job.started_at = now
    job.finished_at = now
    job.error_code = error_code
    job.error_message = error_message
    if version is not None:
        version.ingest_status = "failed"
    run.status = "FAILED"
    run.attempts = job.attempts
    run.started_at = now
    run.finished_at = now
    run.error_code = error_code
    run.error_message = error_message
    _run_audit(
        session,
        run=run,
        event_type="data.ingestion_run.worker_failed",
        error_code=error_code,
    )
    session.flush()


def process_ingestion_job(session: Session, *, job_id: uuid.UUID) -> None:
    job = session.scalar(
        select(IngestionJob).where(IngestionJob.id == job_id).with_for_update()
    )
    if job is None:
        raise ValueError("ingestion_job_missing")
    if job.status != "queued":
        return
    run = session.scalar(
        select(DataIngestionRun)
        .where(DataIngestionRun.inspection_job_id == job.id)
        .with_for_update()
    )
    version = session.scalar(
        select(DataSourceVersion)
        .where(DataSourceVersion.id == job.version_id)
        .with_for_update()
    )
    if version is None:
        if run is not None:
            _fail_linked_integrity(session, run=run, job=job, version=None)
            return
        raise ValueError("data_source_version_missing")
    if run is not None and not _linked_run_integrity_valid(
        session,
        run=run,
        job=job,
        version=version,
    ):
        _fail_linked_integrity(session, run=run, job=job, version=version)
        return

    settings = get_settings()
    job.status = "running"
    job.progress = 10
    job.attempts += 1
    job.started_at = _utcnow()
    job.error_code = ""
    job.error_message = ""
    version.ingest_status = "running"
    if run is not None:
        run.status = "RUNNING"
        run.attempts = job.attempts
        run.started_at = job.started_at
        run.finished_at = None
        run.error_code = ""
        run.error_message = ""
        _run_audit(
            session,
            run=run,
            event_type="data.ingestion_run.worker_started",
        )
    session.flush()
    try:
        storage = build_storage()
        payload = storage.get_bytes(version.storage_key)
        profile = inspect_payload(
            payload,
            filename=version.original_filename,
            max_uncompressed_bytes=int(getattr(settings, "data_max_xlsx_uncompressed_bytes", 67108864)),
        )
        job.progress = 80
        version.detected_format = profile.detected_format
        version.row_count = profile.row_count
        version.column_count = profile.column_count
        version.sheet_count = profile.sheet_count
        version.schema_fingerprint = profile.schema_fingerprint
        replace_quality_results(session, version.id, profile.quality)
        version.ingest_status = "succeeded"
        job.status = "succeeded"
        job.progress = 100
        job.finished_at = _utcnow()
        if run is not None:
            run.status = "SUCCEEDED"
            run.attempts = job.attempts
            run.finished_at = job.finished_at
            run.error_code = ""
            run.error_message = ""
            _run_audit(
                session,
                run=run,
                event_type="data.ingestion_run.worker_succeeded",
            )
    except (IngestionError, StorageError, ValueError) as exc:
        version.ingest_status = "failed"
        job.status = "failed"
        job.progress = 100
        job.error_code = str(exc)[:120] or exc.__class__.__name__
        job.error_message = str(exc)[:2000]
        job.finished_at = _utcnow()
        if run is not None:
            run.status = "FAILED"
            run.attempts = job.attempts
            run.finished_at = job.finished_at
            run.error_code = job.error_code
            run.error_message = job.error_message
            _run_audit(
                session,
                run=run,
                event_type="data.ingestion_run.worker_failed",
                error_code=job.error_code,
            )
    session.flush()


def run_ingestion_job(job_id: str) -> None:
    started = time.perf_counter()
    factory = build_session_factory()
    try:
        with factory() as session:
            parsed_job_id = uuid.UUID(job_id)
            process_ingestion_job(session, job_id=parsed_job_id)
            job = session.get(IngestionJob, parsed_job_id)
            version = session.get(DataSourceVersion, job.version_id) if job is not None else None
            session.commit()
            duration_ms = max((time.perf_counter() - started) * 1000.0, 0.0)
            outcome = job.status if job is not None else "missing"
            record_worker_execution(job_kind="ingestion", outcome=outcome, duration_ms=duration_ms)
            record_ingestion(
                detected_format=(version.detected_format if version is not None else "unknown") or "unknown",
                outcome=outcome,
                row_count=int(version.row_count or 0) if version is not None else 0,
                column_count=int(version.column_count or 0) if version is not None else 0,
                duration_ms=duration_ms,
            )
    except Exception:
        duration_ms = max((time.perf_counter() - started) * 1000.0, 0.0)
        record_worker_execution(job_kind="ingestion", outcome="exception", duration_ms=duration_ms)
        record_ingestion(
            detected_format="unknown",
            outcome="exception",
            row_count=0,
            column_count=0,
            duration_ms=duration_ms,
        )
        raise
