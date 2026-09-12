from inspect import getsource
from pathlib import Path
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api import data_routes
from src.api.app import app
from src.api.dependencies import get_db
from src.core.database import Base
from src.platform.access.models import OrganizationEntitlement, Role, RoleAssignment
from src.platform.access.service import bootstrap_reference_catalog, grant_product_access
from src.platform.auth.models import AuthSession
from src.platform.auth.service import create_session, provision_user, utcnow
from src.platform.data.schemas import SourceGovernanceUpdate
from src.platform.data.service import create_source_upload, update_source_governance
from src.platform.data.storage import LocalFilesystemStorage
from src.platform.identity.models import Membership, Organization
from src.platform.security.assurance import PrivilegedOperation
from src.platform.workspaces.models import Workspace


def test_governance_privacy_routes_are_authenticated_and_permission_scoped():
    source = Path("src/api/data_routes.py").read_text()
    required_routes = (
        '/sources/{source_id}/governance',
        '/retention-policies',
        '/versions/{version_id}/retention',
        '/versions/{version_id}/hold',
        '/versions/{version_id}/purge/request',
        '/versions/{version_id}/purge/approve',
        '/versions/{version_id}/purge/execute',
        '/anonymization-records',
        '/versions/{version_id}/export',
    )
    for route in required_routes:
        assert route in source
    assert source.count("Depends(get_auth_context)") >= len(required_routes)
    assert 'permission_code="data.governance.manage"' in source
    assert 'permission_code="data.export"' in source


def test_every_new_capability_rejects_unauthenticated_requests():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    def override_db():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    identifier = str(uuid.uuid4())
    scope = {"organization_id": identifier, "workspace_id": identifier, "product_code": "SIMPA"}
    requests = (
        ("get", f"/api/v1/data/sources/{identifier}/governance", {"params": scope}),
        ("get", "/api/v1/data/retention-policies", {"params": scope}),
        ("get", f"/api/v1/data/versions/{identifier}/retention", {"params": scope}),
        ("post", f"/api/v1/data/versions/{identifier}/hold", {"json": {**scope, "expected_revision": 1, "reason_reference": "case"}}),
        ("post", f"/api/v1/data/versions/{identifier}/purge/request", {"json": {**scope, "expected_revision": 1}}),
        ("post", "/api/v1/data/anonymization-records", {"json": {**scope, "input_version_id": identifier,
            "output_version_id": str(uuid.uuid4()), "method_code": "METHOD", "method_version": "1",
            "method_reference": "method:v1",
            "evidence_reference": "evidence:1", "classification_after": "PUBLIC",
            "privacy_category_after": "NONE_DECLARED"}}),
        ("post", f"/api/v1/data/versions/{identifier}/export", {"json": {**scope, "purpose_reference": "case"}}),
    )
    try:
        with TestClient(app) as client:
            for method, path, kwargs in requests:
                assert getattr(client, method)(path, **kwargs).status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_export_route_enforces_analyst_boundary_then_mfa(tmp_path, monkeypatch):
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        with factory() as db:
            yield db

    storage = LocalFilesystemStorage(tmp_path)
    monkeypatch.setattr(data_routes, "build_storage", lambda: storage)
    app.dependency_overrides[get_db] = override_db
    with factory() as db:
        bootstrap_reference_catalog(db)
        user = provision_user(db, email="isi21b-api@example.invalid", display_name="ISI-21B",
                              password="Synthetic-ISI21B-password-2026", email_verified=True)
        org = Organization(slug="isi21b-api", name="ISI-21B API")
        db.add(org); db.flush()
        member = Membership(user_id=user.id, organization_id=org.id, status="active")
        db.add(member); db.flush()
        db.add(OrganizationEntitlement(organization_id=org.id, product_code="SIMPA", is_active=True)); db.flush()
        grant_product_access(db, member, "SIMPA")
        analyst = db.scalar(select(Role).where(Role.code == "analyst"))
        db.add(RoleAssignment(membership_id=member.id, role_id=analyst.id, product_code="SIMPA"))
        workspace = Workspace(organization_id=org.id, product_code="SIMPA", slug="main", name="Main", status="active")
        db.add(workspace); db.flush()
        source, version, _job, _ = create_source_upload(
            db, storage, organization_id=org.id, workspace_id=workspace.id, product_code="SIMPA",
            source_name="API export", filename="api.csv", content_type="text/csv", payload=b"api-export\n",
            actor_id=member.id, backend="inline")
        update_source_governance(
            db, source_id=source.id, organization_id=org.id, workspace_id=workspace.id, product_code="SIMPA",
            update=SourceGovernanceUpdate(
                expected_revision=1, classification="INTERNAL", privacy_category="AGGREGATE_NON_PERSONAL",
                processing_purpose="test", data_owner_ref="owner", export_policy="GOVERNED_EXPORT_ALLOWED",
                governance_state="GOVERNED"), actor_id=member.id)
        issued = create_session(db, user)
        db.commit()
        ids = str(org.id), str(workspace.id), str(version.id)

    headers = {"Authorization": f"Bearer {issued.token}"}
    payload = {"organization_id": ids[0], "workspace_id": ids[1], "product_code": "SIMPA", "purpose_reference": "case:api"}
    try:
        with TestClient(app) as client:
            allowed = client.post(f"/api/v1/data/versions/{ids[2]}/export", headers=headers, json=payload)
            assert allowed.status_code == 200 and allowed.content == b"api-export\n"
            assert allowed.headers["x-data-export-manifest-id"]

            with factory() as db:
                update_source_governance(
                    db, source_id=source.id, organization_id=org.id, workspace_id=workspace.id, product_code="SIMPA",
                    update=SourceGovernanceUpdate(expected_revision=2, classification="CONFIDENTIAL",
                                                  privacy_category="PERSONAL_DATA"), actor_id=member.id)
                db.commit()
            analyst_denied = client.post(f"/api/v1/data/versions/{ids[2]}/export", headers=headers, json=payload)
            assert analyst_denied.json()["detail"] == "sensitive_export_governance_permission_required"

            with factory() as db:
                manager = db.scalar(select(Role).where(Role.code == "data_manager"))
                db.add(RoleAssignment(membership_id=member.id, role_id=manager.id, product_code="SIMPA")); db.commit()
            step_up = client.post(f"/api/v1/data/versions/{ids[2]}/export", headers=headers, json=payload)
            assert step_up.json()["detail"] == "step_up_authentication_required"

            with factory() as db:
                auth_session = db.get(AuthSession, issued.session_id)
                auth_session.mfa_verified_at = utcnow()
                db.commit()
            mfa_allowed = client.post(f"/api/v1/data/versions/{ids[2]}/export", headers=headers, json=payload)
            assert mfa_allowed.status_code == 200 and mfa_allowed.content == b"api-export\n"
    finally:
        app.dependency_overrides.clear()


def test_authorization_precedes_assurance_and_uses_exact_operations():
    export = getsource(data_routes.post_version_export)
    assert export.index('permission_code="data.export"') < export.index("inspect_export(")
    assert export.index("validate_export_policy(") < export.index('"data.governance.manage"')
    assert export.index('"data.governance.manage"') < export.index("PrivilegedOperation.SENSITIVE_EXPORT_ADMINISTRATION")
    mutation = getsource(data_routes._retention_mutation)
    assert mutation.index('permission_code="data.governance.manage"') < mutation.index("PrivilegedOperation.DESTRUCTIVE_ADMINISTRATION")
    assert PrivilegedOperation.DESTRUCTIVE_ADMINISTRATION.value == "administration.destructive"
    assert PrivilegedOperation.SENSITIVE_EXPORT_ADMINISTRATION.value == "administration.sensitive_export"


def test_foreign_ids_are_not_oracles_and_errors_are_bounded():
    scope = getsource(data_routes._require_scope)
    assert "resolve_selection" in scope
    assert "data_scope_not_accessible" in scope
    mapping = getsource(data_routes._platform_error)
    assert '"version_not_accessible"' in mapping
    assert "HTTP_404_NOT_FOUND" in mapping
    assert "retention_revision_conflict" in mapping
    assert "HTTP_409_CONFLICT" in mapping
    assert "storage_operation_failed" in mapping
    assert "HTTP_503_SERVICE_UNAVAILABLE" in mapping


def test_mutating_routes_rollback_and_export_never_exposes_storage_key():
    source = Path("src/api/data_routes.py").read_text()
    assert source.count("db.rollback()") >= 6
    export = getsource(data_routes.post_version_export)
    assert "db.rollback()" in export
    assert '"X-Data-Export-Manifest-ID"' in export
    assert "storage_key" not in export
    assert "authorization" not in export.casefold()
