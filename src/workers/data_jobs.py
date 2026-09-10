from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.database import build_session_factory
from src.platform.data.ingestion import IngestionError, inspect_payload
from src.platform.data.models import DataSourceVersion, IngestionJob
from src.platform.data.service import replace_quality_results
from src.platform.data.storage import StorageError, build_storage
from src.platform.observability.telemetry import record_ingestion, record_worker_execution


def _utcnow():
    return datetime.now(timezone.utc)


def process_ingestion_job(session: Session, *, job_id: uuid.UUID) -> None:
    job = session.get(IngestionJob, job_id)
    if job is None:
        raise ValueError("ingestion_job_missing")
    version = session.get(DataSourceVersion, job.version_id)
    if version is None:
        raise ValueError("data_source_version_missing")
    storage = build_storage()
    settings = get_settings()
    job.status = "running"
    job.progress = 10
    job.attempts += 1
    job.started_at = _utcnow()
    job.error_code = ""
    job.error_message = ""
    version.ingest_status = "running"
    session.flush()
    try:
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
    except (IngestionError, StorageError, ValueError) as exc:
        version.ingest_status = "failed"
        job.status = "failed"
        job.progress = 100
        job.error_code = str(exc)[:120] or exc.__class__.__name__
        job.error_message = str(exc)[:2000]
        job.finished_at = _utcnow()
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
