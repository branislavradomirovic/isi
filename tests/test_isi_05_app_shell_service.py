from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.core.database import Base
from src.platform import models as platform_models  # noqa: F401
from src.platform.access.models import OrganizationEntitlement, Role, RoleAssignment
from src.platform.access.service import bootstrap_reference_catalog, grant_product_access
from src.platform.app_context.service import AppContextError
from src.platform.app_shell.service import resolve_app_shell
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace


def _db():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def _seed(session: Session, *, products=("SIMPA",), role_code="analyst"):
    bootstrap_reference_catalog(session)
    user = User(email="shell@example.com", display_name="Shell User", is_active=True, is_platform_admin=False)
    org = Organization(slug="shell-org", name="Shell Org", status="active")
    session.add_all([user, org])
    session.flush()
    membership = Membership(user_id=user.id, organization_id=org.id, status="active")
    session.add(membership)
    session.flush()
    role = session.scalar(select(Role).where(Role.code == role_code))
    assert role is not None
    workspaces = {}
    for code in products:
        session.add(OrganizationEntitlement(organization_id=org.id, product_code=code, is_active=True))
        session.flush()
        grant_product_access(session, membership, code)
        session.add(RoleAssignment(membership_id=membership.id, role_id=role.id, product_code=code))
        workspace = Workspace(
            organization_id=org.id,
            product_code=code,
            slug=f"{code.lower()}-main",
            name=f"{code} Main",
            status="active",
            created_by_membership_id=membership.id,
        )
        session.add(workspace)
        workspaces[code] = workspace
    session.commit()
    return user, org, workspaces


def test_shell_revalidates_selection_and_builds_permission_navigation():
    with _db() as session:
        user, org, workspaces = _seed(session, products=("SIMPA",), role_code="analyst")
        shell = resolve_app_shell(
            session,
            user_id=user.id,
            organization_id=org.id,
            product_code="SIMPA",
            workspace_id=workspaces["SIMPA"].id,
        )
        enabled = {item.code for item in shell.navigation if item.enabled}
        assert "overview" in enabled
        assert "data" in enabled
        assert "analysis" in enabled
        assert "reports" in enabled
        assert "administration" not in enabled
        assert shell.workspace_state == "selected"
        assert not shell.switcher.product_switching


def test_dual_product_shell_exposes_product_switching_only_with_entitlement():
    with _db() as session:
        user, org, workspaces = _seed(session, products=("SIMPA", "ORDO"), role_code="viewer")
        shell = resolve_app_shell(
            session,
            user_id=user.id,
            organization_id=org.id,
            product_code="ORDO",
            workspace_id=workspaces["ORDO"].id,
        )
        assert shell.switcher.product_switching
        assert shell.product.code == "ORDO"


def test_shell_rejects_foreign_workspace():
    with _db() as session:
        user, org, workspaces = _seed(session, products=("SIMPA",))
        other = Organization(slug="other-org", name="Other Org", status="active")
        session.add(other)
        session.flush()
        foreign = Workspace(
            organization_id=other.id,
            product_code="SIMPA",
            slug="foreign",
            name="Foreign",
            status="active",
        )
        session.add(foreign)
        session.commit()

        try:
            resolve_app_shell(
                session,
                user_id=user.id,
                organization_id=org.id,
                product_code="SIMPA",
                workspace_id=foreign.id,
            )
        except AppContextError as exc:
            assert "workspace_not_accessible" in str(exc)
        else:
            raise AssertionError("foreign workspace was accepted")
