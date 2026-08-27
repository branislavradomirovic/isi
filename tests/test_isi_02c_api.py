from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.api.dependencies import get_db
from src.core.database import Base
from src.platform import models as platform_models  # noqa: F401
from src.platform.access.models import OrganizationEntitlement
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


def teardown_client():
    app.dependency_overrides.clear()


def test_context_endpoint_and_selection_enforce_tenant_and_product_access():
    client, SessionLocal = make_client()
    try:
        with SessionLocal() as db:
            bootstrap_reference_catalog(db)
            user = provision_user(
                db,
                email="context-api@example.com",
                display_name="Context API",
                password="Context-API-password-2026",
                email_verified=True,
            )
            org = Organization(slug="context-api-org", name="Context API Org", status="active")
            other_org = Organization(slug="other-api-org", name="Other API Org", status="active")
            db.add_all([org, other_org])
            db.flush()
            membership = Membership(user_id=user.id, organization_id=org.id, status="active")
            db.add(membership)
            db.flush()
            db.add(OrganizationEntitlement(organization_id=org.id, product_code="SIMPA", is_active=True))
            db.flush()
            grant_product_access(db, membership, "SIMPA")
            workspace = Workspace(organization_id=org.id, product_code="SIMPA", slug="main", name="Main", status="active")
            foreign_workspace = Workspace(
                organization_id=other_org.id,
                product_code="SIMPA",
                slug="foreign",
                name="Foreign",
                status="active",
            )
            db.add_all([workspace, foreign_workspace])
            token = create_session(db, user).token
            db.commit()
            org_id = str(org.id)
            workspace_id = str(workspace.id)
            foreign_workspace_id = str(foreign_workspace.id)

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/app-context", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["initial_route"]["mode"] == "workspace"
        assert body["initial_route"]["product_code"] == "SIMPA"

        accepted = client.post(
            "/api/v1/app-context/select",
            headers=headers,
            json={"organization_id": org_id, "product_code": "SIMPA", "workspace_id": workspace_id},
        )
        assert accepted.status_code == 200
        assert accepted.json()["workspace"]["id"] == workspace_id

        rejected = client.post(
            "/api/v1/app-context/select",
            headers=headers,
            json={"organization_id": org_id, "product_code": "SIMPA", "workspace_id": foreign_workspace_id},
        )
        assert rejected.status_code == 403
    finally:
        teardown_client()


def test_context_endpoint_requires_authentication():
    client, _SessionLocal = make_client()
    try:
        assert client.get("/api/v1/app-context").status_code == 401
    finally:
        teardown_client()
