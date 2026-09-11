from __future__ import annotations

import ast
import uuid
from datetime import timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.core.database import Base
from src.platform import models as platform_models  # noqa: F401
from src.platform.auth.models import AuthSession, MfaChallenge
from src.platform.auth.service import (
    AuthError,
    create_mfa_factor,
    create_session,
    issue_mfa_challenge,
    provision_user,
    refresh_password_assurance,
    revoke_mfa_challenge,
    utcnow,
    verify_mfa_challenge,
    verify_mfa_challenge_for_session,
)
from src.platform.security.assurance import (
    ASSURANCE_FRESHNESS_SECONDS,
    PRIVILEGED_OPERATION_CATALOG,
    AssuranceDecisionReason,
    AssuranceMethod,
    AssuranceRequirement,
    PrivilegedOperation,
    evaluate_privileged_operation,
)


TEST_PASSWORD = "Synthetic-assurance-password-2026"


@pytest.fixture()
def db():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _user(db: Session, label: str = "assurance"):
    return provision_user(
        db,
        email=f"{label}-{uuid.uuid4().hex}@example.invalid",
        display_name=f"{label.title()} User",
        password=TEST_PASSWORD,
        email_verified=True,
    )


def _assert_error(code: str, operation) -> None:
    with pytest.raises(AuthError) as raised:
        operation()
    assert raised.value.code == code


def _aware(value):
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _active_factor(db: Session, user, *, now):
    factor = create_mfa_factor(db, user, method="synthetic.test")
    enrollment = issue_mfa_challenge(
        db,
        user_id=user.id,
        factor_id=factor.id,
        purpose="enrollment",
        verifier="synthetic-enrollment-proof",
        now=now,
    )
    result = verify_mfa_challenge(
        db,
        user_id=user.id,
        challenge_id=enrollment.challenge_id,
        verifier="synthetic-enrollment-proof",
        now=now,
    )
    assert result.succeeded
    return factor


def test_create_session_requires_explicit_password_verified_signal(db):
    user = _user(db)
    default_issued = create_session(db, user)
    default_model = db.get(AuthSession, default_issued.session_id)
    assert default_model is not None
    assert default_model.password_verified_at is None
    assert default_model.mfa_verified_at is None

    before = utcnow()
    verified_issued = create_session(db, user, password_verified=True)
    after = utcnow()
    verified_model = db.get(AuthSession, verified_issued.session_id)
    assert verified_model is not None
    assert verified_model.password_verified_at is not None
    assert before <= _aware(verified_model.password_verified_at) <= after
    assert verified_model.mfa_verified_at is None

    decision = evaluate_privileged_operation(
        default_model,
        PrivilegedOperation.ROLE_ASSIGNMENT_CHANGE,
        now=utcnow(),
    )
    assert decision.allowed is False
    assert decision.reason is AssuranceDecisionReason.ASSURANCE_MISSING


def test_auth_routes_only_login_marks_password_verified():
    route_path = Path("src/api/auth_routes.py")
    module = ast.parse(route_path.read_text(encoding="utf-8"), filename=str(route_path))
    route_functions = {
        node.name: node
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    def create_session_calls(function_name: str) -> list[ast.Call]:
        return [
            node
            for node in ast.walk(route_functions[function_name])
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "create_session"
        ]

    login_calls = create_session_calls("login")
    invite_calls = create_session_calls("accept_invite")
    assert len(login_calls) == 1
    assert len(invite_calls) == 1

    login_keyword = next(
        keyword for keyword in login_calls[0].keywords if keyword.arg == "password_verified"
    )
    assert isinstance(login_keyword.value, ast.Constant)
    assert login_keyword.value.value is True
    assert all(keyword.arg != "password_verified" for keyword in invite_calls[0].keywords)


def test_password_refresh_is_bound_to_one_active_user_session(db):
    user = _user(db)
    first = create_session(db, user)
    second = create_session(db, user)
    first_model = db.get(AuthSession, first.session_id)
    second_model = db.get(AuthSession, second.session_id)
    first_model.password_verified_at = None
    second_original = second_model.password_verified_at
    checked_at = utcnow()

    refreshed = refresh_password_assurance(
        db,
        user_id=user.id,
        session_id=first.session_id,
        password=TEST_PASSWORD,
        now=checked_at,
    )
    assert refreshed.password_verified_at == checked_at
    assert second_model.password_verified_at == second_original

    refreshed.password_verified_at = None
    _assert_error(
        "invalid_password",
        lambda: refresh_password_assurance(
            db,
            user_id=user.id,
            session_id=first.session_id,
            password="Synthetic-wrong-password-2026",
            now=checked_at,
        ),
    )
    assert refreshed.password_verified_at is None

    other = _user(db, "other")
    _assert_error(
        "invalid_auth_session",
        lambda: refresh_password_assurance(
            db,
            user_id=other.id,
            session_id=first.session_id,
            password=TEST_PASSWORD,
            now=checked_at,
        ),
    )


@pytest.mark.parametrize("state", ["revoked", "expired", "inactive"])
def test_password_refresh_rejects_inactive_session_or_user(db, state):
    user = _user(db, state)
    issued = create_session(db, user)
    model = db.get(AuthSession, issued.session_id)
    model.password_verified_at = None
    now = utcnow()
    if state == "revoked":
        model.revoked_at = now
        expected = "auth_session_revoked"
    elif state == "expired":
        model.expires_at = now - timedelta(seconds=1)
        expected = "auth_session_expired"
    else:
        user.is_active = False
        expected = "inactive_user"

    _assert_error(
        expected,
        lambda: refresh_password_assurance(
            db,
            user_id=user.id,
            session_id=issued.session_id,
            password=TEST_PASSWORD,
            now=now,
        ),
    )
    assert model.password_verified_at is None


def test_central_policy_enforces_freshness_and_mfa_requirement(db):
    user = _user(db)
    issued = create_session(db, user)
    model = db.get(AuthSession, issued.session_id)
    now = utcnow()
    model.expires_at = now + timedelta(hours=1)
    model.password_verified_at = now

    password_policy = evaluate_privileged_operation(
        model,
        PrivilegedOperation.ROLE_ASSIGNMENT_CHANGE,
        now=now,
    )
    assert password_policy.allowed
    assert password_policy.satisfied_by is AssuranceMethod.PASSWORD

    mfa_policy = evaluate_privileged_operation(
        model,
        PrivilegedOperation.PLATFORM_ADMIN_GRANT,
        now=now,
    )
    assert not mfa_policy.allowed
    assert mfa_policy.reason is AssuranceDecisionReason.ASSURANCE_INSUFFICIENT
    assert mfa_policy.required_assurance is AssuranceRequirement.MFA

    model.password_verified_at = now - timedelta(seconds=ASSURANCE_FRESHNESS_SECONDS + 1)
    stale = evaluate_privileged_operation(model, PrivilegedOperation.ROLE_ASSIGNMENT_CHANGE, now=now)
    assert not stale.allowed
    assert stale.reason is AssuranceDecisionReason.ASSURANCE_STALE

    model.mfa_verified_at = now
    elevated = evaluate_privileged_operation(model, PrivilegedOperation.PLATFORM_ADMIN_GRANT, now=now)
    assert elevated.allowed
    assert elevated.satisfied_by is AssuranceMethod.MFA
    model.mfa_verified_at = now - timedelta(seconds=ASSURANCE_FRESHNESS_SECONDS + 1)
    assert not evaluate_privileged_operation(model, PrivilegedOperation.PLATFORM_ADMIN_GRANT, now=now).allowed


def test_policy_fails_closed_for_unknown_revoked_and_expired_sessions(db):
    user = _user(db)
    issued = create_session(db, user)
    model = db.get(AuthSession, issued.session_id)
    now = utcnow()
    model.expires_at = now + timedelta(hours=1)
    model.mfa_verified_at = now

    unknown = evaluate_privileged_operation(model, "unregistered.operation", now=now)
    assert not unknown.allowed
    assert unknown.reason is AssuranceDecisionReason.UNKNOWN_OPERATION
    model.revoked_at = now
    assert evaluate_privileged_operation(
        model, PrivilegedOperation.SECURITY_CONTROL_CHANGE, now=now
    ).reason is AssuranceDecisionReason.SESSION_REVOKED
    model.revoked_at = None
    model.expires_at = now
    assert evaluate_privileged_operation(
        model, PrivilegedOperation.SECURITY_CONTROL_CHANGE, now=now
    ).reason is AssuranceDecisionReason.SESSION_EXPIRED


def test_authentication_challenge_elevates_only_its_bound_session(db):
    now = utcnow()
    user = _user(db)
    first = create_session(db, user)
    second = create_session(db, user)
    factor = _active_factor(db, user, now=now)
    authentication = issue_mfa_challenge(
        db,
        user_id=user.id,
        factor_id=factor.id,
        purpose="authentication",
        verifier="synthetic-authentication-proof",
        now=now,
    )

    result = verify_mfa_challenge_for_session(
        db,
        user_id=user.id,
        session_id=first.session_id,
        challenge_id=authentication.challenge_id,
        verifier="synthetic-authentication-proof",
        now=now,
    )
    assert result.succeeded
    assert _aware(db.get(AuthSession, first.session_id).mfa_verified_at) == now
    assert db.get(AuthSession, second.session_id).mfa_verified_at is None
    _assert_error(
        "mfa_challenge_already_consumed",
        lambda: verify_mfa_challenge_for_session(
            db,
            user_id=user.id,
            session_id=second.session_id,
            challenge_id=authentication.challenge_id,
            verifier="synthetic-authentication-proof",
            now=now,
        ),
    )
    assert db.get(AuthSession, second.session_id).mfa_verified_at is None


def test_enrollment_and_cross_user_challenges_cannot_elevate_session(db):
    now = utcnow()
    owner = _user(db, "owner")
    other = _user(db, "other")
    owner_session = create_session(db, owner)
    other_session = create_session(db, other)
    pending_factor = create_mfa_factor(db, owner, method="synthetic.test")
    enrollment = issue_mfa_challenge(
        db,
        user_id=owner.id,
        factor_id=pending_factor.id,
        purpose="enrollment",
        verifier="synthetic-enrollment-only-proof",
        now=now,
    )
    _assert_error(
        "mfa_challenge_not_authentication",
        lambda: verify_mfa_challenge_for_session(
            db,
            user_id=owner.id,
            session_id=owner_session.session_id,
            challenge_id=enrollment.challenge_id,
            verifier="synthetic-enrollment-only-proof",
            now=now,
        ),
    )
    assert db.get(MfaChallenge, enrollment.challenge_id).consumed_at is None
    assert db.get(AuthSession, owner_session.session_id).mfa_verified_at is None

    verify_mfa_challenge(
        db,
        user_id=owner.id,
        challenge_id=enrollment.challenge_id,
        verifier="synthetic-enrollment-only-proof",
        now=now,
    )
    authentication = issue_mfa_challenge(
        db,
        user_id=owner.id,
        factor_id=pending_factor.id,
        purpose="authentication",
        verifier="synthetic-cross-user-proof",
        now=now,
    )
    _assert_error(
        "invalid_auth_session",
        lambda: verify_mfa_challenge_for_session(
            db,
            user_id=owner.id,
            session_id=other_session.session_id,
            challenge_id=authentication.challenge_id,
            verifier="synthetic-cross-user-proof",
            now=now,
        ),
    )
    assert db.get(MfaChallenge, authentication.challenge_id).consumed_at is None


def test_wrong_expired_revoked_and_exhausted_challenges_do_not_elevate(db):
    now = utcnow()
    user = _user(db)
    issued_session = create_session(db, user)
    model = db.get(AuthSession, issued_session.session_id)
    factor = _active_factor(db, user, now=now)

    wrong = issue_mfa_challenge(
        db,
        user_id=user.id,
        factor_id=factor.id,
        purpose="authentication",
        verifier="synthetic-correct-proof",
        now=now,
        max_attempts=1,
    )
    denied = verify_mfa_challenge_for_session(
        db,
        user_id=user.id,
        session_id=issued_session.session_id,
        challenge_id=wrong.challenge_id,
        verifier="synthetic-wrong-proof",
        now=now,
    )
    assert not denied.succeeded
    assert denied.error_code == "mfa_challenge_attempts_exhausted"
    assert model.mfa_verified_at is None
    _assert_error(
        "mfa_challenge_attempts_exhausted",
        lambda: verify_mfa_challenge_for_session(
            db,
            user_id=user.id,
            session_id=issued_session.session_id,
            challenge_id=wrong.challenge_id,
            verifier="synthetic-correct-proof",
            now=now,
        ),
    )

    expired = issue_mfa_challenge(
        db,
        user_id=user.id,
        factor_id=factor.id,
        purpose="authentication",
        verifier="synthetic-expired-proof",
        now=now - timedelta(minutes=2),
        ttl_seconds=60,
    )
    _assert_error(
        "mfa_challenge_expired",
        lambda: verify_mfa_challenge_for_session(
            db,
            user_id=user.id,
            session_id=issued_session.session_id,
            challenge_id=expired.challenge_id,
            verifier="synthetic-expired-proof",
            now=now,
        ),
    )

    revoked = issue_mfa_challenge(
        db,
        user_id=user.id,
        factor_id=factor.id,
        purpose="authentication",
        verifier="synthetic-revoked-proof",
        now=now,
    )
    revoke_mfa_challenge(db, user_id=user.id, challenge_id=revoked.challenge_id, now=now)
    _assert_error(
        "mfa_challenge_revoked",
        lambda: verify_mfa_challenge_for_session(
            db,
            user_id=user.id,
            session_id=issued_session.session_id,
            challenge_id=revoked.challenge_id,
            verifier="synthetic-revoked-proof",
            now=now,
        ),
    )
    assert model.mfa_verified_at is None


def test_catalog_covers_required_families_and_contract_objects_are_verifier_free(db):
    required = {
        PrivilegedOperation.PLATFORM_ADMIN_GRANT,
        PrivilegedOperation.PLATFORM_ADMIN_REVOKE,
        PrivilegedOperation.PLATFORM_ADMIN_CHANGE,
        PrivilegedOperation.ORGANIZATION_MEMBER_STATUS_CHANGE,
        PrivilegedOperation.ROLE_ASSIGNMENT_CHANGE,
        PrivilegedOperation.MEMBERSHIP_PRODUCT_ACCESS_CHANGE,
        PrivilegedOperation.INVITATION_PRIVILEGE_GRANT,
        PrivilegedOperation.INVITATION_REVOKE,
        PrivilegedOperation.WORKSPACE_ADMINISTRATION_CHANGE,
        PrivilegedOperation.ORGANIZATION_PROFILE_CHANGE,
        PrivilegedOperation.ORGANIZATION_ENTITLEMENT_CHANGE,
        PrivilegedOperation.OTHER_USER_SESSION_REVOCATION,
        PrivilegedOperation.SECURITY_CONTROL_CHANGE,
        PrivilegedOperation.DESTRUCTIVE_ADMINISTRATION,
        PrivilegedOperation.SENSITIVE_EXPORT_ADMINISTRATION,
    }
    assert required == set(PRIVILEGED_OPERATION_CATALOG)
    assert {policy.required_assurance for policy in PRIVILEGED_OPERATION_CATALOG.values()} == {
        AssuranceRequirement.PASSWORD_OR_MFA,
        AssuranceRequirement.MFA,
    }

    user = _user(db)
    model = db.get(AuthSession, create_session(db, user).session_id)
    decision = evaluate_privileged_operation(model, PrivilegedOperation.ROLE_ASSIGNMENT_CHANGE, now=utcnow())
    forbidden_fields = {"password", "verifier", "digest", "token", "secret", "cookie", "authorization"}
    assert forbidden_fields.isdisjoint(vars(decision))
    for policy in PRIVILEGED_OPERATION_CATALOG.values():
        assert forbidden_fields.isdisjoint(vars(policy))


def test_assurance_migration_contract():
    migration = Path("migrations/versions/20260911_0015_auth_assurance.py").read_text(encoding="utf-8")
    assert 'revision = "20260911_0015"' in migration
    assert 'down_revision = "20260910_0014"' in migration
    assert migration.count('op.add_column(') == 2
    assert migration.count('op.drop_column(') == 2
    assert "password_verified_at" in migration
    assert "mfa_verified_at" in migration
    columns = Base.metadata.tables["core_auth_sessions"].columns
    assert columns["password_verified_at"].nullable
    assert columns["mfa_verified_at"].nullable
