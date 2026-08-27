from __future__ import annotations

import uuid

from redis import Redis
from rq import Queue

from src.core.config import get_settings
from src.core.database import build_session_factory
from src.platform.data.models import IngestionJob
from src.workers.data_jobs import run_ingestion_job


class DataQueueError(RuntimeError):
    pass


def dispatch_job(job_id: uuid.UUID) -> None:
    settings = get_settings()
    backend = getattr(settings, "data_job_backend", "inline")
    if backend == "inline":
        run_ingestion_job(str(job_id))
        return
    if backend != "rq":
        raise DataQueueError(f"unsupported data job backend: {backend}")
    try:
        redis = Redis.from_url(settings.redis_url)
        queue = Queue("isi-data", connection=redis)
        rq_job = queue.enqueue("src.workers.data_jobs.run_ingestion_job", str(job_id), job_timeout=900)
    except Exception as exc:
        raise DataQueueError("unable to enqueue data job") from exc
    factory = build_session_factory()
    with factory() as session:
        job = session.get(IngestionJob, job_id)
        if job is not None:
            job.rq_job_id = rq_job.id
            session.commit()
