from __future__ import annotations

import time
import uuid

from src.core.database import build_session_factory
from src.platform.ai.models import AIModel, AIPrompt, AIPromptVersion
from src.platform.ai.service import execute_ai_job
from src.platform.observability.telemetry import record_ai_execution, record_worker_execution


def run_ai_job(job_id: str) -> None:
    started = time.perf_counter()
    factory = build_session_factory()
    try:
        with factory() as session:
            from src.platform.extraction.service import worker_guard
            from src.platform.ai.models import AIJob

            key = uuid.UUID(job_id)
            if worker_guard(session, key):
                job = execute_ai_job(session, job_id=key)
                worker_guard(session, key, after=True)
            else:
                job = session.get(AIJob, key)
            if job is None:
                raise ValueError("ai_job_missing")
            model = session.get(AIModel, job.model_id)
            prompt_version = session.get(AIPromptVersion, job.prompt_version_id)
            prompt = session.get(AIPrompt, prompt_version.prompt_id) if prompt_version is not None else None
            session.commit()
            duration_ms = max((time.perf_counter() - started) * 1000.0, 0.0)
            record_ai_execution(
                provider=job.provider_name or (model.provider_name if model is not None else "unknown"),
                model_key=model.model_key if model is not None else "unknown",
                prompt_key=prompt.prompt_key if prompt is not None else "unknown",
                product_code=job.product_code,
                outcome=job.status,
                duration_ms=duration_ms,
            )
            record_worker_execution(job_kind="ai", outcome=job.status, duration_ms=duration_ms)
    except Exception:
        record_worker_execution(
            job_kind="ai",
            outcome="exception",
            duration_ms=max((time.perf_counter() - started) * 1000.0, 0.0),
        )
        raise
