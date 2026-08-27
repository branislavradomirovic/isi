from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.database import build_session_factory
from src.platform.data.ingestion import IngestionError, inspect_payload
from src.platform.data.models import DataSourceVersion, IngestionJob
from src.platform.data.service import replace_quality_results
from src.platform.data.storage import StorageError, build_storage


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
    factory = build_session_factory()
    with factory() as session:
        process_ingestion_job(session, job_id=uuid.UUID(job_id))
        session.commit()
