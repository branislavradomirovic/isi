from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from src.core.database import Base
from src.platform import models as platform_models  # noqa: F401
from src.platform.access.catalog import PermissionCode, ProductCode, RoleCode
from src.platform.access.models import Permission, Product, Role
from src.platform.access.service import bootstrap_reference_catalog


def build_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_core_table_contract_is_registered() -> None:
    session = build_session()
    tables = set(inspect(session.bind).get_table_names())
    assert {
        "core_users",
        "core_organizations",
        "core_memberships",
        "core_products",
        "core_organization_entitlements",
        "core_membership_product_access",
        "core_roles",
        "core_permissions",
        "core_role_permissions",
        "core_role_assignments",
        "core_workspaces",
    }.issubset(tables)


def test_reference_catalog_bootstrap_is_idempotent() -> None:
    session = build_session()
    bootstrap_reference_catalog(session)
    bootstrap_reference_catalog(session)

    assert {row.code for row in session.query(Product).all()} == {ProductCode.SIMPA.value, ProductCode.ORDO.value}
    assert {row.code for row in session.query(Role).all()} == {role.value for role in RoleCode}
    assert {row.code for row in session.query(Permission).all()} == {permission.value for permission in PermissionCode}
