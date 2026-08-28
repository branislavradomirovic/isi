from __future__ import annotations

import uuid

from src.core.database import build_session_factory
from src.platform.ai.service import execute_ai_job


def run_ai_job(job_id: str) -> None:
    factory = build_session_factory()
    with factory() as session:
        execute_ai_job(session, job_id=uuid.UUID(job_id))
        session.commit()
