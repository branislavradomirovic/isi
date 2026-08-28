from __future__ import annotations

import uuid

from redis import Redis
from rq import Queue

from src.core.config import get_settings
from src.core.database import build_session_factory
from src.platform.ai.models import AIJob
from src.workers.ai_jobs import run_ai_job


class AIQueueError(RuntimeError):
    pass


def dispatch_ai_job(job_id: uuid.UUID) -> None:
    settings = get_settings()
    backend = str(getattr(settings, "ai_job_backend", "inline"))
    if backend == "inline":
        run_ai_job(str(job_id))
        return
    if backend != "rq":
        raise AIQueueError(f"unsupported ai job backend: {backend}")
    try:
        redis = Redis.from_url(settings.redis_url)
        queue = Queue("isi-ai", connection=redis)
        rq_job = queue.enqueue("src.workers.ai_jobs.run_ai_job", str(job_id), job_timeout=900)
    except Exception as exc:
        raise AIQueueError("unable_to_enqueue_ai_job") from exc
    factory = build_session_factory()
    with factory() as session:
        job = session.get(AIJob, job_id)
        if job is not None:
            job.rq_job_id = rq_job.id
            session.commit()
