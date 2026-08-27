import os

import pytest
from sqlalchemy import inspect

from src.core.database import build_engine


@pytest.mark.skipif(os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1", reason="native PostgreSQL acceptance only")
def test_native_postgres_has_shared_data_tables():
    inspector = inspect(build_engine())
    names = set(inspector.get_table_names())
    assert {
        "core_data_sources",
        "core_data_source_versions",
        "core_ingestion_jobs",
        "core_data_quality_results",
        "core_data_audit_events",
    } <= names
