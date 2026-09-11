from __future__ import annotations

from datetime import timedelta
from inspect import getsource

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.api.administration_routes import (
    _error,
    _orgwide,
    _scope,
    _step_up,
    patch_organization,
    post_workspace,
    post_workspace_status,
)
from src.api.dependencies import AuthContext
from src.core.database import Base
from src.platform import models as platform_models  # noqa: F401
from src.platform.access.catalog import ProductCode, RoleCode
from src.platform.access.models import OrganizationEntitlement, Role, RoleAssignment
from src.platform.access.service import bootstrap_reference_catalog, can_access_product, grant_product_access
from src.platform.administration.service import AdministrationError, list_member_sessions, revoke_member_session
from src.platform.auth.models import AuthSession
from src.platform.auth.service import create_session, provision_user, utcnow
from src.platform.identity.models import Membership, Organization
from src.platform.security.assurance import (
    AssuranceDecisionReason,
    AssuranceMethod,
    AssuranceRequirement,
    PrivilegedOperation,
    evaluate_privileged_operation,
)


@pytest.fixture()
def db():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        bootstrap_reference_catalog(session)
        yield session


def _member(db, label, org):
    user = provision_user(db, email=f"{label}@example.invalid", display_name=label, password="Synthetic-access-password-2026", email_verified=True)
    membership = Membership(user_id=user.id, organization_id=org.id, status="active")
    db.add(membership)
    db.flush()
    return user, membership


def _grant(db, membership, org, product="SIMPA", role="organization_admin", scope="*"):
    if db.scalar(select(OrganizationEntitlement).where(OrganizationEntitlement.organization_id == org.id, OrganizationEntitlement.product_code == product)) is None:
        db.add(OrganizationEntitlement(organization_id=org.id, product_code=product, is_active=True))
        db.flush()
    grant_product_access(db, membership, product)
    role_model = db.scalar(select(Role).where(Role.code == role))
    db.add(RoleAssignment(membership_id=membership.id, role_id=role_model.id, product_code=scope))
    db.flush()


def test_authorization_precedes_assurance_and_product_boundaries_remain_independent(db):
    org = Organization(slug="matrix", name="Matrix")
    db.add(org); db.flush()
    user, membership = _member(db, "matrix-user", org)
    _grant(db, membership, org, product="SIMPA", role="viewer", scope="SIMPA")
    issued = create_session(db, user)
    context = AuthContext(token=issued.token, auth_session=db.get(AuthSession, issued.session_id), user=user)
    assert can_access_product(db, user.id, org.id, ProductCode.SIMPA) is True
    assert can_access_product(db, user.id, org.id, ProductCode.ORDO) is False
    with pytest.raises(HTTPException) as permission_denied:
        _scope(db, context, organization_id=org.id, product_code="SIMPA", permission_code="members.manage")
    assert permission_denied.value.detail == "administration_permission_denied"
    with pytest.raises(HTTPException):
        _scope(db, context, organization_id=org.id, product_code="ORDO", permission_code="members.manage")
    with pytest.raises(HTTPException):
        _orgwide(db, context, org.id, "members.manage")


def test_step_up_denies_missing_stale_mfa_only_password_and_invalid_sessions(db):
    org = Organization(slug="step-matrix", name="Step Matrix")
    db.add(org); db.flush()
    user, membership = _member(db, "step-admin", org)
    _grant(db, membership, org)
    issued = create_session(db, user, password_verified=True)
    model = db.get(AuthSession, issued.session_id)
    context = AuthContext(token=issued.token, auth_session=model, user=user)
    _step_up(db, context, operation=PrivilegedOperation.ROLE_ASSIGNMENT_CHANGE, organization_id=org.id, product_code="SIMPA")
    with pytest.raises(HTTPException):
        _step_up(db, context, operation=PrivilegedOperation.ORGANIZATION_ENTITLEMENT_CHANGE, organization_id=org.id, product_code="SIMPA")
    model.password_verified_at = utcnow() - timedelta(hours=1)
    with pytest.raises(HTTPException):
        _step_up(db, context, operation=PrivilegedOperation.ROLE_ASSIGNMENT_CHANGE, organization_id=org.id, product_code="SIMPA")
    model.password_verified_at = utcnow()
    model.revoked_at = utcnow()
    with pytest.raises(HTTPException):
        _step_up(db, context, operation=PrivilegedOperation.ROLE_ASSIGNMENT_CHANGE, organization_id=org.id, product_code="SIMPA")


@pytest.mark.parametrize(
    "operation",
    [
        PrivilegedOperation.WORKSPACE_ADMINISTRATION_CHANGE,
        PrivilegedOperation.ORGANIZATION_PROFILE_CHANGE,
    ],
)
def test_existing_administration_changes_accept_only_fresh_password_or_mfa(db, operation):
    org = Organization(slug=f"assurance-{operation.name.lower()}", name="Assurance")
    db.add(org); db.flush()
    user, _membership = _member(db, operation.name.lower(), org)
    issued = create_session(db, user)
    model = db.get(AuthSession, issued.session_id)
    now = utcnow()

    missing = evaluate_privileged_operation(model, operation, now=now)
    assert missing.allowed is False
    assert missing.reason is AssuranceDecisionReason.ASSURANCE_MISSING
    assert missing.required_assurance is AssuranceRequirement.PASSWORD_OR_MFA

    model.password_verified_at = now - timedelta(hours=1)
    stale = evaluate_privileged_operation(model, operation, now=now)
    assert stale.allowed is False
    assert stale.reason is AssuranceDecisionReason.ASSURANCE_STALE

    model.password_verified_at = now
    fresh = evaluate_privileged_operation(model, operation, now=now)
    assert fresh.allowed is True
    assert fresh.satisfied_by is AssuranceMethod.PASSWORD

    destructive = evaluate_privileged_operation(
        model,
        PrivilegedOperation.DESTRUCTIVE_ADMINISTRATION,
        now=now,
    )
    assert destructive.allowed is False
    assert destructive.reason is AssuranceDecisionReason.ASSURANCE_INSUFFICIENT
    assert destructive.required_assurance is AssuranceRequirement.MFA


def test_existing_administration_routes_use_specific_non_destructive_operations():
    workspace_create_source = getsource(post_workspace)
    workspace_status_source = getsource(post_workspace_status)
    organization_profile_source = getsource(patch_organization)

    assert "PrivilegedOperation.WORKSPACE_ADMINISTRATION_CHANGE" in workspace_create_source
    assert "PrivilegedOperation.WORKSPACE_ADMINISTRATION_CHANGE" in workspace_status_source
    assert "PrivilegedOperation.ORGANIZATION_PROFILE_CHANGE" in organization_profile_source
    for route_source in (workspace_create_source, workspace_status_source, organization_profile_source):
        assert "PrivilegedOperation.DESTRUCTIVE_ADMINISTRATION" not in route_source
        assert route_source.index("_scope(") < route_source.index("_step_up(")
    assert organization_profile_source.index("_orgwide(") < organization_profile_source.index("_step_up(")


def test_admin_target_session_actions_fail_closed_for_multi_organization_target(db):
    org_a = Organization(slug="org-a", name="A")
    org_b = Organization(slug="org-b", name="B")
    db.add_all([org_a, org_b]); db.flush()
    admin, admin_membership = _member(db, "admin-target", org_a)
    target, target_membership = _member(db, "target-a", org_a)
    foreign, foreign_membership = _member(db, "target-b", org_b)
    multi_target, multi_target_membership_a = _member(db, "target-multi", org_a)
    multi_target_membership_b = Membership(
        user_id=multi_target.id,
        organization_id=org_b.id,
        status="active",
    )
    db.add(multi_target_membership_b)
    db.flush()
    admin_session = create_session(db, admin, password_verified=True)
    target_session = create_session(db, target)
    foreign_session = create_session(db, foreign)
    multi_target_session = create_session(db, multi_target)

    with pytest.raises(AdministrationError) as multi_org_inventory:
        list_member_sessions(
            db,
            organization_id=org_a.id,
            membership_id=multi_target_membership_a.id,
            actor_user_id=admin.id,
            current_session_id=admin_session.session_id,
        )
    assert multi_org_inventory.value.code == "global_session_multi_organization_target_not_supported"

    with pytest.raises(AdministrationError) as multi_org_revocation:
        revoke_member_session(
            db,
            organization_id=org_a.id,
            membership_id=multi_target_membership_a.id,
            target_session_id=multi_target_session.session_id,
            actor_user_id=admin.id,
        )
    assert multi_org_revocation.value.code == "global_session_multi_organization_target_not_supported"
    assert db.get(AuthSession, multi_target_session.session_id).revoked_at is None

    conflict = _error(AdministrationError("global_session_multi_organization_target_not_supported"))
    assert conflict.status_code == 409
    assert conflict.detail == "global_session_multi_organization_target_not_supported"

    inventory = list_member_sessions(db, organization_id=org_a.id, membership_id=target_membership.id, actor_user_id=admin.id, current_session_id=admin_session.session_id)
    assert [item.session_id for item in inventory] == [target_session.session_id]
    assert revoke_member_session(db, organization_id=org_a.id, membership_id=target_membership.id, target_session_id=target_session.session_id, actor_user_id=admin.id)
    assert revoke_member_session(db, organization_id=org_a.id, membership_id=target_membership.id, target_session_id=target_session.session_id, actor_user_id=admin.id)
    with pytest.raises(AdministrationError) as cross_org:
        revoke_member_session(db, organization_id=org_a.id, membership_id=foreign_membership.id, target_session_id=foreign_session.session_id, actor_user_id=admin.id)
    assert cross_org.value.code == "membership_not_accessible"
    assert foreign_session.session_id not in {item.session_id for item in inventory}


def test_org_role_never_sets_platform_admin_and_last_admin_guard_remains_present(db):
    org = Organization(slug="role-boundary", name="Role Boundary")
    db.add(org); db.flush()
    user, membership = _member(db, "org-admin-only", org)
    _grant(db, membership, org)
    assert user.is_platform_admin is False
    from src.platform.administration.service import set_membership_status
    with pytest.raises(AdministrationError) as protected:
        set_membership_status(db, organization_id=org.id, membership_id=membership.id, status="suspended", actor_user_id=user.id, product_code="SIMPA")
    assert protected.value.code == "last_organization_admin_required"
