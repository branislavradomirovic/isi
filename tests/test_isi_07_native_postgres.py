import os

import pytest
from sqlalchemy import inspect, text

from src.core.database import build_engine


@pytest.mark.skipif(os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1", reason="native PostgreSQL acceptance only")
def test_native_postgres_has_shared_ai_tables_and_vector_capability_is_consistent():
    engine = build_engine()
    inspector = inspect(engine)
    names = set(inspector.get_table_names())
    assert {
        "core_ai_models",
        "core_ai_prompts",
        "core_ai_prompt_versions",
        "core_ai_policy_profiles",
        "core_ai_jobs",
        "core_ai_job_attempts",
        "core_ai_audit_events",
        "core_ai_embeddings",
    } <= names
    with engine.connect() as connection:
        enabled = bool(connection.execute(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='vector')")).scalar())
        native = "core_ai_embedding_vectors" in names
    assert native is enabled
