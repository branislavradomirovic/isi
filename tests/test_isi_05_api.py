from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.api.dependencies import get_db
from src.core.database import Base
from src.platform import models as platform_models  # noqa: F401
from src.platform.access.models import OrganizationEntitlement, Role, RoleAssignment
from src.platform.access.service import bootstrap_reference_catalog, grant_product_access
from src.platform.auth.service import create_session, provision_user
from src.platform.identity.models import Membership, Organization
from src.platform.workspaces.models import Workspace


def make_client():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), SessionLocal


def teardown():
    app.dependency_overrides.clear()


def test_app_shell_requires_authentication():
    client, _ = make_client()
    try:
        response = client.get(
            "/api/v1/app-shell",
            params={"organization_id": "00000000-0000-0000-0000-000000000001", "product_code": "SIMPA"},
        )
        assert response.status_code == 401
    finally:
        teardown()


def test_app_shell_endpoint_enforces_product_and_workspace_access():
    client, SessionLocal = make_client()
    try:
        with SessionLocal() as db:
            bootstrap_reference_catalog(db)
            user = provision_user(
                db,
                email="shell-api@example.com",
                display_name="Shell API",
                password="Shell-API-password-2026",
                email_verified=True,
            )
            org = Organization(slug="shell-api-org", name="Shell API Org", status="active")
            other = Organization(slug="shell-api-other", name="Other", status="active")
            db.add_all([org, other])
            db.flush()
            membership = Membership(user_id=user.id, organization_id=org.id, status="active")
            db.add(membership)
            db.flush()
            db.add(OrganizationEntitlement(organization_id=org.id, product_code="SIMPA", is_active=True))
            db.flush()
            grant_product_access(db, membership, "SIMPA")
            role = db.scalar(select(Role).where(Role.code == "analyst"))
            assert role is not None
            db.add(RoleAssignment(membership_id=membership.id, role_id=role.id, product_code="SIMPA"))
            workspace = Workspace(organization_id=org.id, product_code="SIMPA", slug="main", name="Main", status="active")
            foreign = Workspace(organization_id=other.id, product_code="SIMPA", slug="foreign", name="Foreign", status="active")
            db.add_all([workspace, foreign])
            token = create_session(db, user).token
            db.commit()
            org_id = str(org.id)
            workspace_id = str(workspace.id)
            foreign_id = str(foreign.id)

        headers = {"Authorization": f"Bearer {token}"}
        ok = client.get(
            "/api/v1/app-shell",
            headers=headers,
            params={"organization_id": org_id, "product_code": "SIMPA", "workspace_id": workspace_id},
        )
        assert ok.status_code == 200
        assert ok.json()["product"]["code"] == "SIMPA"
        assert ok.json()["workspace"]["id"] == workspace_id

        denied = client.get(
            "/api/v1/app-shell",
            headers=headers,
            params={"organization_id": org_id, "product_code": "SIMPA", "workspace_id": foreign_id},
        )
        assert denied.status_code == 403

        product_denied = client.get(
            "/api/v1/app-shell",
            headers=headers,
            params={"organization_id": org_id, "product_code": "ORDO"},
        )
        assert product_denied.status_code == 403
    finally:
        teardown()
