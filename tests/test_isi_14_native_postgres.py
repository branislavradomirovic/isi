import os

import pytest
from sqlalchemy import inspect

from src.core.database import build_engine


@pytest.mark.skipif(os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1", reason="native PostgreSQL acceptance only")
def test_isi_14_native_security_schema():
    inspector = inspect(build_engine())
    tables = set(inspector.get_table_names())
    assert {"core_security_rate_limits", "core_security_events"}.issubset(tables)
    session_columns = {column["name"] for column in inspector.get_columns("core_auth_sessions")}
    assert {"remote_ip_hash", "user_agent_hash", "revoked_reason"}.issubset(session_columns)
