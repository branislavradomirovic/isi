import os

import pytest
from sqlalchemy import create_engine, inspect, text


@pytest.mark.skipif("postgresql" not in os.getenv("DATABASE_URL", ""), reason="native PostgreSQL DATABASE_URL not configured")
def test_isi_05_native_postgres_shared_tables_exist_without_new_migration():
    engine = create_engine(os.environ["DATABASE_URL"])
    inspector = inspect(engine)
    names = set(inspector.get_table_names())
    required = {
        "core_users",
        "core_organizations",
        "core_memberships",
        "core_products",
        "core_organization_entitlements",
        "core_membership_product_access",
        "core_role_assignments",
        "core_workspaces",
        "core_auth_sessions",
    }
    assert required <= names
    with engine.connect() as conn:
        assert conn.execute(text("select 1")).scalar_one() == 1
