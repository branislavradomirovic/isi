import os

import pytest
from sqlalchemy import inspect

from src.core.database import build_engine


@pytest.mark.skipif(os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1", reason="native PostgreSQL acceptance only")
def test_isi_13_native_tables_exist():
    inspector = inspect(build_engine())
    tables = set(inspector.get_table_names())
    assert {"core_invitation_product_grants", "core_invitation_role_grants", "core_admin_audit_events"}.issubset(tables)
    audit_columns = {column["name"] for column in inspector.get_columns("core_admin_audit_events")}
    assert {"organization_id", "actor_user_id", "action", "target_type", "target_id", "before_state", "after_state", "created_at"}.issubset(audit_columns)
