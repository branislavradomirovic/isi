from __future__ import annotations

import uuid

from redis import Redis
from rq import Queue

from src.core.config import get_settings
from src.core.database import build_session_factory
from src.platform.data.models import IngestionJob
from src.platform.observability.telemetry import record_queue_dispatch
from src.workers.data_jobs import run_ingestion_job


class DataQueueError(RuntimeError):
    pass


def dispatch_job(job_id: uuid.UUID) -> None:
    settings = get_settings()
    backend = str(getattr(settings, "data_job_backend", "inline"))
    if backend == "inline":
        try:
            run_ingestion_job(str(job_id))
        except Exception:
            record_queue_dispatch(job_kind="ingestion", backend=backend, outcome="failed")
            raise
        record_queue_dispatch(job_kind="ingestion", backend=backend, outcome="accepted")
        return
    if backend != "rq":
        record_queue_dispatch(job_kind="ingestion", backend=backend, outcome="rejected")
        raise DataQueueError(f"unsupported data job backend: {backend}")
    try:
        redis = Redis.from_url(settings.redis_url)
        queue = Queue("isi-data", connection=redis)
        rq_job = queue.enqueue("src.workers.data_jobs.run_ingestion_job", str(job_id), job_timeout=900)
    except Exception as exc:
        record_queue_dispatch(job_kind="ingestion", backend=backend, outcome="failed")
        raise DataQueueError("unable to enqueue data job") from exc
    record_queue_dispatch(job_kind="ingestion", backend=backend, outcome="accepted")
    factory = build_session_factory()
    with factory() as session:
        job = session.get(IngestionJob, job_id)
        if job is not None:
            job.rq_job_id = rq_job.id
            session.commit()
