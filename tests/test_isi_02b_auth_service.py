from datetime import timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.core.database import Base
from src.platform import models as platform_models  # noqa: F401
from src.platform.auth.models import AuthSession, AuthToken, Invitation
from src.platform.auth.security import hash_token
from src.platform.auth.service import (
    AuthError,
    accept_invitation,
    authenticate_user,
    confirm_email_verification,
    create_email_verification_token,
    create_invitation,
    create_password_reset_token,
    create_session,
    normalize_email,
    provision_user,
    reset_password_with_token,
    revoke_session,
    utcnow,
    validate_session,
)
from src.platform.identity.models import Membership, Organization, User


@pytest.fixture()
def db():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_email_is_normalized_and_login_requires_verified_active_user(db):
    user = provision_user(
        db,
        email="  TEST.User@Example.COM ",
        display_name="Test User",
        password="A-secure-password-2026",
        email_verified=False,
    )
    db.commit()
    assert user.email == "test.user@example.com"
    assert normalize_email(" X@Example.com ") == "x@example.com"
    assert authenticate_user(db, "test.user@example.com", "A-secure-password-2026") is None

    issued = create_email_verification_token(db, user)
    assert issued.token not in db.scalar(select(AuthToken).where(AuthToken.user_id == user.id)).token_hash
    confirm_email_verification(db, issued.token)
    db.commit()
    assert authenticate_user(db, "TEST.USER@EXAMPLE.COM", "A-secure-password-2026") is not None


def test_session_is_opaque_revocable_and_expiring(db):
    user = provision_user(
        db,
        email="session@example.com",
        display_name="Session User",
        password="A-secure-password-2026",
        email_verified=True,
    )
    issued = create_session(db, user)
    db.commit()
    stored = db.scalar(select(AuthSession).where(AuthSession.user_id == user.id))
    assert stored.token_hash == hash_token(issued.token)
    assert issued.token != stored.token_hash
    assert validate_session(db, issued.token) is not None
    assert revoke_session(db, issued.token)
    db.commit()
    assert validate_session(db, issued.token) is None

    second = create_session(db, user)
    db.flush()
    stored2 = db.scalar(select(AuthSession).where(AuthSession.token_hash == hash_token(second.token)))
    stored2.expires_at = utcnow() - timedelta(seconds=1)
    db.commit()
    assert validate_session(db, second.token) is None


def test_password_reset_is_single_use_and_revokes_existing_sessions(db):
    user = provision_user(
        db,
        email="reset@example.com",
        display_name="Reset User",
        password="Old-secure-password-2026",
        email_verified=True,
    )
    session_token = create_session(db, user).token
    reset = create_password_reset_token(db, user.email)
    assert reset is not None
    _user, issued = reset
    db.commit()

    reset_password_with_token(db, issued.token, "New-secure-password-2026")
    db.commit()
    assert authenticate_user(db, user.email, "Old-secure-password-2026") is None
    assert authenticate_user(db, user.email, "New-secure-password-2026") is not None
    assert validate_session(db, session_token) is None
    with pytest.raises(AuthError):
        reset_password_with_token(db, issued.token, "Another-password-2026")


def test_invitation_creates_verified_user_and_membership_without_product_access(db):
    org = Organization(slug="municipality-a", name="Municipality A", status="active")
    db.add(org)
    db.flush()
    issued = create_invitation(db, organization_id=org.id, email="Invitee@Example.com")
    db.commit()

    user, membership = accept_invitation(
        db,
        raw_token=issued.token,
        display_name="Invitee",
        password="Invitee-password-2026",
    )
    db.commit()
    assert user.email == "invitee@example.com"
    assert user.email_verified_at is not None
    assert membership.organization_id == org.id
    assert membership.status == "active"
    assert db.scalar(select(Membership).where(Membership.user_id == user.id)) is not None
    invitation = db.scalar(select(Invitation).where(Invitation.organization_id == org.id))
    assert invitation.status == "accepted"
    with pytest.raises(AuthError):
        accept_invitation(db, raw_token=issued.token)


def test_invitation_does_not_overwrite_existing_user_password(db):
    org = Organization(slug="municipality-b", name="Municipality B", status="active")
    user = provision_user(
        db,
        email="existing@example.com",
        display_name="Existing",
        password="Existing-password-2026",
        email_verified=True,
    )
    db.add(org)
    db.flush()
    issued = create_invitation(db, organization_id=org.id, email=user.email)
    db.commit()

    accepted_user, _membership = accept_invitation(
        db,
        raw_token=issued.token,
        display_name="Ignored",
        password="Attempted-overwrite-2026",
    )
    db.commit()
    assert authenticate_user(db, accepted_user.email, "Existing-password-2026") is not None
    assert authenticate_user(db, accepted_user.email, "Attempted-overwrite-2026") is None


def test_invitation_can_be_reissued_after_previous_pending_invite_is_revoked(db):
    org = Organization(slug="municipality-c", name="Municipality C", status="active")
    db.add(org)
    db.flush()
    first = create_invitation(db, organization_id=org.id, email="repeat@example.com")
    second = create_invitation(db, organization_id=org.id, email="repeat@example.com")
    db.commit()
    assert first.token != second.token
    invitations = db.scalars(select(Invitation).where(Invitation.organization_id == org.id)).all()
    assert sorted(item.status for item in invitations) == ["pending", "revoked"]
