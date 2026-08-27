from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.core.database import Base
from src.platform import models as platform_models  # noqa: F401
from src.platform.access.catalog import PermissionCode, ProductCode, RoleCode
from src.platform.access.models import OrganizationEntitlement, Role, RoleAssignment
from src.platform.access.service import (
    AccessInvariantError,
    bootstrap_reference_catalog,
    can_access_product,
    grant_product_access,
    has_permission,
)
from src.platform.identity.models import Membership, Organization, User


def session_with_catalog() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    bootstrap_reference_catalog(session)
    return session


def create_user_org_membership(session: Session, suffix: str) -> tuple[User, Organization, Membership]:
    user = User(email=f"{suffix}@example.test", display_name=suffix)
    org = Organization(slug=f"org-{suffix}", name=f"Organization {suffix}")
    session.add_all([user, org])
    session.flush()
    membership = Membership(user_id=user.id, organization_id=org.id, status="active")
    session.add(membership)
    session.commit()
    return user, org, membership


def entitle(session: Session, org: Organization, product: ProductCode) -> None:
    session.add(OrganizationEntitlement(organization_id=org.id, product_code=product.value, is_active=True))
    session.commit()


def assign_role(session: Session, membership: Membership, role_code: RoleCode, product_scope: str) -> None:
    role = session.scalar(select(Role).where(Role.code == role_code.value))
    assert role is not None
    session.add(RoleAssignment(membership_id=membership.id, role_id=role.id, product_code=product_scope))
    session.commit()


def test_simpa_only_member_cannot_access_ordo() -> None:
    session = session_with_catalog()
    user, org, membership = create_user_org_membership(session, "simpa")
    entitle(session, org, ProductCode.SIMPA)
    grant_product_access(session, membership, ProductCode.SIMPA)
    session.commit()

    assert can_access_product(session, user.id, org.id, ProductCode.SIMPA) is True
    assert can_access_product(session, user.id, org.id, ProductCode.ORDO) is False


def test_ordo_only_member_cannot_access_simpa() -> None:
    session = session_with_catalog()
    user, org, membership = create_user_org_membership(session, "ordo")
    entitle(session, org, ProductCode.ORDO)
    grant_product_access(session, membership, ProductCode.ORDO)
    session.commit()

    assert can_access_product(session, user.id, org.id, ProductCode.ORDO) is True
    assert can_access_product(session, user.id, org.id, ProductCode.SIMPA) is False


def test_dual_product_member_can_access_both() -> None:
    session = session_with_catalog()
    user, org, membership = create_user_org_membership(session, "dual")
    for product in ProductCode:
        entitle(session, org, product)
        grant_product_access(session, membership, product)
    session.commit()

    assert can_access_product(session, user.id, org.id, ProductCode.SIMPA) is True
    assert can_access_product(session, user.id, org.id, ProductCode.ORDO) is True


def test_tenant_isolation_denies_other_organization() -> None:
    session = session_with_catalog()
    user, org_a, membership = create_user_org_membership(session, "tenant-a")
    _, org_b, _ = create_user_org_membership(session, "tenant-b")
    entitle(session, org_a, ProductCode.SIMPA)
    entitle(session, org_b, ProductCode.SIMPA)
    grant_product_access(session, membership, ProductCode.SIMPA)
    session.commit()

    assert can_access_product(session, user.id, org_a.id, ProductCode.SIMPA) is True
    assert can_access_product(session, user.id, org_b.id, ProductCode.SIMPA) is False


def test_grant_product_access_requires_org_entitlement() -> None:
    session = session_with_catalog()
    _, _, membership = create_user_org_membership(session, "no-entitlement")

    try:
        grant_product_access(session, membership, ProductCode.SIMPA)
    except AccessInvariantError:
        pass
    else:
        raise AssertionError("expected AccessInvariantError")


def test_role_permission_matrix_and_product_scope() -> None:
    session = session_with_catalog()
    user, org, membership = create_user_org_membership(session, "roles")
    for product in ProductCode:
        entitle(session, org, product)
        grant_product_access(session, membership, product)
    assign_role(session, membership, RoleCode.ANALYST, ProductCode.SIMPA.value)

    assert has_permission(session, user.id, org.id, PermissionCode.ANALYSIS_RUN, ProductCode.SIMPA) is True
    assert has_permission(session, user.id, org.id, PermissionCode.MEMBERS_MANAGE, ProductCode.SIMPA) is False
    assert has_permission(session, user.id, org.id, PermissionCode.ANALYSIS_RUN, ProductCode.ORDO) is False


def test_org_admin_star_scope_and_viewer_deny() -> None:
    session = session_with_catalog()
    admin, org, admin_membership = create_user_org_membership(session, "admin")
    viewer, _, viewer_membership = create_user_org_membership(session, "viewer-temp")
    viewer_membership.organization_id = org.id
    session.commit()

    entitle(session, org, ProductCode.SIMPA)
    grant_product_access(session, admin_membership, ProductCode.SIMPA)
    grant_product_access(session, viewer_membership, ProductCode.SIMPA)
    assign_role(session, admin_membership, RoleCode.ORGANIZATION_ADMIN, "*")
    assign_role(session, viewer_membership, RoleCode.VIEWER, ProductCode.SIMPA.value)

    assert has_permission(session, admin.id, org.id, PermissionCode.MEMBERS_MANAGE, ProductCode.SIMPA) is True
    assert has_permission(session, viewer.id, org.id, PermissionCode.ANALYSIS_RUN, ProductCode.SIMPA) is False


def test_disabled_user_and_suspended_membership_are_denied() -> None:
    session = session_with_catalog()
    user, org, membership = create_user_org_membership(session, "disabled")
    entitle(session, org, ProductCode.SIMPA)
    grant_product_access(session, membership, ProductCode.SIMPA)
    session.commit()

    user.is_active = False
    session.commit()
    assert can_access_product(session, user.id, org.id, ProductCode.SIMPA) is False

    user.is_active = True
    membership.status = "suspended"
    session.commit()
    assert can_access_product(session, user.id, org.id, ProductCode.SIMPA) is False
