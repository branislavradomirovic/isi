from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.core.database import Base
from src.platform import models as platform_models  # noqa: F401
from src.platform.access.catalog import PermissionCode, ProductCode, RoleCode
from src.platform.access.models import OrganizationEntitlement, Role, RoleAssignment
from src.platform.access.service import bootstrap_reference_catalog, grant_product_access
from src.platform.app_context.service import AppContextError, resolve_app_context, resolve_selection
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace


@pytest.fixture()
def db():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        bootstrap_reference_catalog(session)
        yield session


def seed_access(db: Session, *, email: str, org_slug: str, products: tuple[str, ...], role_code: str = "analyst"):
    user = User(email=email, display_name=email, is_active=True, is_platform_admin=False)
    org = Organization(slug=org_slug, name=org_slug.replace("-", " ").title(), status="active")
    db.add_all([user, org])
    db.flush()
    membership = Membership(user_id=user.id, organization_id=org.id, status="active")
    db.add(membership)
    db.flush()
    role = db.scalar(select(Role).where(Role.code == role_code))
    assert role is not None
    for product_code in products:
        db.add(OrganizationEntitlement(organization_id=org.id, product_code=product_code, is_active=True))
        db.flush()
        grant_product_access(db, membership, product_code)
        db.add(RoleAssignment(membership_id=membership.id, role_id=role.id, product_code=product_code))
        db.add(
            Workspace(
                organization_id=org.id,
                product_code=product_code,
                slug=f"{org_slug}-{product_code.lower()}",
                name=f"{product_code} Main",
                status="active",
                created_by_membership_id=membership.id,
            )
        )
    db.commit()
    return user, org, membership


def test_simpa_only_user_routes_directly_to_simpa_workspace(db):
    user, org, _membership = seed_access(db, email="simpa@example.com", org_slug="simpa-org", products=("SIMPA",))
    context = resolve_app_context(db, user.id)
    assert context.initial_route.mode == "workspace"
    assert context.initial_route.organization_id == org.id
    assert context.initial_route.product_code == "SIMPA"
    assert len(context.organizations) == 1
    assert [product.code for product in context.organizations[0].products] == ["SIMPA"]


def test_ordo_only_user_routes_directly_to_ordo_workspace(db):
    user, _org, _membership = seed_access(db, email="ordo@example.com", org_slug="ordo-org", products=("ORDO",))
    context = resolve_app_context(db, user.id)
    assert context.initial_route.mode == "workspace"
    assert context.initial_route.product_code == "ORDO"


def test_dual_product_user_requires_selector_and_has_switchable_products(db):
    user, _org, _membership = seed_access(
        db,
        email="dual@example.com",
        org_slug="dual-org",
        products=("SIMPA", "ORDO"),
    )
    context = resolve_app_context(db, user.id)
    assert context.initial_route.mode == "selector"
    assert {product.code for product in context.organizations[0].products} == {"SIMPA", "ORDO"}


def test_multiple_organizations_require_selector_even_with_one_product_each(db):
    user, _org1, _membership1 = seed_access(db, email="multi@example.com", org_slug="first-org", products=("SIMPA",))
    org2 = Organization(slug="second-org", name="Second Org", status="active")
    db.add(org2)
    db.flush()
    membership2 = Membership(user_id=user.id, organization_id=org2.id, status="active")
    db.add(membership2)
    db.flush()
    db.add(OrganizationEntitlement(organization_id=org2.id, product_code="ORDO", is_active=True))
    db.flush()
    grant_product_access(db, membership2, "ORDO")
    db.add(Workspace(organization_id=org2.id, product_code="ORDO", slug="second-ordo", name="ORDO Second", status="active"))
    db.commit()
    context = resolve_app_context(db, user.id)
    assert context.initial_route.mode == "selector"
    assert len(context.organizations) == 2


def test_role_and_permission_codes_are_product_scoped(db):
    user, _org, _membership = seed_access(db, email="analyst@example.com", org_slug="analyst-org", products=("SIMPA",))
    context = resolve_app_context(db, user.id)
    product = context.organizations[0].products[0]
    assert RoleCode.ANALYST.value in product.role_codes
    assert PermissionCode.ANALYSIS_RUN.value in product.permission_codes
    assert PermissionCode.MEMBERS_MANAGE.value not in product.permission_codes


def test_suspended_membership_is_excluded(db):
    user, _org, membership = seed_access(db, email="suspended@example.com", org_slug="suspended-org", products=("SIMPA",))
    membership.status = "suspended"
    db.commit()
    context = resolve_app_context(db, user.id)
    assert context.organizations == []
    assert context.initial_route.mode == "no_access"


def test_selection_rejects_cross_tenant_workspace(db):
    user, org, _membership = seed_access(db, email="select@example.com", org_slug="select-org", products=("SIMPA",))
    _other_user, _other_org, _other_membership = seed_access(db, email="other@example.com", org_slug="other-org", products=("SIMPA",))
    other_workspace = db.scalar(select(Workspace).where(Workspace.organization_id != org.id))
    assert other_workspace is not None
    with pytest.raises(AppContextError, match="workspace_not_accessible"):
        resolve_selection(
            db,
            user_id=user.id,
            organization_id=org.id,
            product_code="SIMPA",
            workspace_id=other_workspace.id,
        )


def test_platform_admin_can_resolve_active_organizations_without_memberships(db):
    org = Organization(slug="admin-org", name="Admin Org", status="active")
    admin = User(email="admin@example.com", display_name="Admin", is_active=True, is_platform_admin=True)
    db.add_all([org, admin])
    db.commit()
    context = resolve_app_context(db, admin.id)
    assert len(context.organizations) == 1
    assert {product.code for product in context.organizations[0].products} == {ProductCode.SIMPA, ProductCode.ORDO}
    assert context.organizations[0].membership_id is None
