from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.platform.auth.models import AuthSession, AuthToken, Invitation
from src.platform.auth.security import hash_password, hash_token, needs_rehash, new_opaque_token, verify_password
from src.platform.identity.models import Membership, Organization, User


class AuthError(ValueError):
    def __init__(self, code: str, message: str = "authentication operation failed") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class IssuedSession:
    token: str
    session_id: uuid.UUID
    expires_at: datetime


@dataclass(frozen=True)
class IssuedToken:
    token: str
    expires_at: datetime


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def normalize_email(email: str) -> str:
    normalized = email.strip().casefold()
    if not normalized or "@" not in normalized:
        raise AuthError("invalid_email", "invalid email address")
    return normalized


@lru_cache(maxsize=1)
def _dummy_password_hash() -> str:
    return hash_password("ISI-dummy-password-only-for-timing")


def provision_user(
    session: Session,
    *,
    email: str,
    display_name: str,
    password: str,
    email_verified: bool = False,
    is_platform_admin: bool = False,
) -> User:
    normalized = normalize_email(email)
    existing = session.scalar(select(User).where(User.email == normalized))
    if existing is not None:
        raise AuthError("email_exists", "user already exists")
    now = utcnow()
    user = User(
        email=normalized,
        display_name=display_name.strip(),
        password_hash=hash_password(password),
        email_verified_at=now if email_verified else None,
        password_changed_at=now,
        is_platform_admin=is_platform_admin,
        is_active=True,
    )
    session.add(user)
    session.flush()
    return user


def set_password(user: User, password: str) -> None:
    user.password_hash = hash_password(password)
    user.password_changed_at = utcnow()


def authenticate_user(session: Session, email: str, password: str) -> User | None:
    try:
        normalized = normalize_email(email)
    except AuthError:
        verify_password(password, _dummy_password_hash())
        return None

    user = session.scalar(select(User).where(User.email == normalized))
    if user is None:
        verify_password(password, _dummy_password_hash())
        return None
    if not user.is_active or user.email_verified_at is None:
        verify_password(password, user.password_hash or _dummy_password_hash())
        return None
    if not verify_password(password, user.password_hash):
        return None
    if user.password_hash and needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    user.last_login_at = utcnow()
    session.flush()
    return user


def create_session(
    session: Session,
    user: User,
    *,
    remote_ip: str | None = None,
    user_agent: str | None = None,
) -> IssuedSession:
    if not user.is_active:
        raise AuthError("inactive_user")
    settings = get_settings()
    now = utcnow()
    expires_at = now + timedelta(seconds=settings.auth_session_ttl_seconds)
    raw = new_opaque_token("isi_sess")
    model = AuthSession(
        user_id=user.id,
        token_hash=hash_token(raw),
        expires_at=expires_at,
        last_seen_at=now,
        remote_ip=(remote_ip or "")[:64] or None,
        user_agent=(user_agent or "")[:500] or None,
    )
    session.add(model)
    session.flush()
    return IssuedSession(token=raw, session_id=model.id, expires_at=expires_at)


def validate_session(session: Session, raw_token: str) -> tuple[AuthSession, User] | None:
    if not raw_token:
        return None
    model = session.scalar(select(AuthSession).where(AuthSession.token_hash == hash_token(raw_token)))
    if model is None or model.revoked_at is not None or _aware(model.expires_at) <= utcnow():
        return None
    user = session.get(User, model.user_id)
    if user is None or not user.is_active:
        return None
    model.last_seen_at = utcnow()
    session.flush()
    return model, user


def revoke_session(session: Session, raw_token: str) -> bool:
    model = session.scalar(select(AuthSession).where(AuthSession.token_hash == hash_token(raw_token)))
    if model is None:
        return False
    if model.revoked_at is None:
        model.revoked_at = utcnow()
        session.flush()
    return True


def revoke_all_user_sessions(session: Session, user_id: uuid.UUID) -> None:
    session.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )
    session.flush()


def _issue_user_token(session: Session, user: User, purpose: str, ttl_seconds: int, prefix: str) -> IssuedToken:
    now = utcnow()
    session.execute(
        update(AuthToken)
        .where(AuthToken.user_id == user.id, AuthToken.purpose == purpose, AuthToken.consumed_at.is_(None))
        .values(consumed_at=now)
    )
    raw = new_opaque_token(prefix)
    expires_at = now + timedelta(seconds=ttl_seconds)
    session.add(
        AuthToken(
            user_id=user.id,
            purpose=purpose,
            token_hash=hash_token(raw),
            expires_at=expires_at,
        )
    )
    session.flush()
    return IssuedToken(token=raw, expires_at=expires_at)


def create_email_verification_token(session: Session, user: User) -> IssuedToken:
    return _issue_user_token(
        session,
        user,
        "email_verification",
        get_settings().auth_email_verification_ttl_seconds,
        "isi_verify",
    )


def confirm_email_verification(session: Session, raw_token: str) -> User:
    model = session.scalar(
        select(AuthToken).where(
            AuthToken.token_hash == hash_token(raw_token),
            AuthToken.purpose == "email_verification",
        )
    )
    if model is None or model.consumed_at is not None or _aware(model.expires_at) <= utcnow():
        raise AuthError("invalid_or_expired_token")
    user = session.get(User, model.user_id)
    if user is None or not user.is_active:
        raise AuthError("invalid_or_expired_token")
    now = utcnow()
    user.email_verified_at = user.email_verified_at or now
    model.consumed_at = now
    session.flush()
    return user


def create_password_reset_token(session: Session, email: str) -> tuple[User, IssuedToken] | None:
    try:
        normalized = normalize_email(email)
    except AuthError:
        return None
    user = session.scalar(select(User).where(User.email == normalized, User.is_active.is_(True)))
    if user is None:
        return None
    issued = _issue_user_token(
        session,
        user,
        "password_reset",
        get_settings().auth_password_reset_ttl_seconds,
        "isi_reset",
    )
    return user, issued


def reset_password_with_token(session: Session, raw_token: str, new_password: str) -> User:
    model = session.scalar(
        select(AuthToken).where(
            AuthToken.token_hash == hash_token(raw_token),
            AuthToken.purpose == "password_reset",
        )
    )
    if model is None or model.consumed_at is not None or _aware(model.expires_at) <= utcnow():
        raise AuthError("invalid_or_expired_token")
    user = session.get(User, model.user_id)
    if user is None or not user.is_active:
        raise AuthError("invalid_or_expired_token")
    set_password(user, new_password)
    model.consumed_at = utcnow()
    revoke_all_user_sessions(session, user.id)
    session.flush()
    return user


def create_invitation(
    session: Session,
    *,
    organization_id: uuid.UUID,
    email: str,
    invited_by_user_id: uuid.UUID | None = None,
) -> IssuedToken:
    organization = session.get(Organization, organization_id)
    if organization is None or organization.status != "active":
        raise AuthError("invalid_organization")
    normalized = normalize_email(email)
    now = utcnow()
    existing = session.scalar(
        select(Invitation).where(
            Invitation.organization_id == organization_id,
            Invitation.email == normalized,
            Invitation.status == "pending",
        )
    )
    if existing is not None:
        existing.status = "revoked"
        existing.revoked_at = now
        session.flush()
    raw = new_opaque_token("isi_invite")
    expires_at = now + timedelta(seconds=get_settings().auth_invitation_ttl_seconds)
    session.add(
        Invitation(
            organization_id=organization_id,
            email=normalized,
            token_hash=hash_token(raw),
            invited_by_user_id=invited_by_user_id,
            expires_at=expires_at,
        )
    )
    session.flush()
    return IssuedToken(token=raw, expires_at=expires_at)


def revoke_invitation(session: Session, raw_token: str) -> bool:
    invitation = session.scalar(select(Invitation).where(Invitation.token_hash == hash_token(raw_token)))
    if invitation is None:
        return False
    if invitation.status == "pending":
        invitation.status = "revoked"
        invitation.revoked_at = utcnow()
        session.flush()
    return True


def accept_invitation(
    session: Session,
    *,
    raw_token: str,
    display_name: str | None = None,
    password: str | None = None,
) -> tuple[User, Membership]:
    invitation = session.scalar(select(Invitation).where(Invitation.token_hash == hash_token(raw_token)))
    if (
        invitation is None
        or invitation.status != "pending"
        or invitation.revoked_at is not None
        or _aware(invitation.expires_at) <= utcnow()
    ):
        raise AuthError("invalid_or_expired_invitation")

    user = session.scalar(select(User).where(User.email == invitation.email))
    now = utcnow()
    if user is None:
        if not display_name or password is None:
            raise AuthError("new_user_details_required")
        user = User(
            email=invitation.email,
            display_name=display_name.strip(),
            password_hash=hash_password(password),
            email_verified_at=now,
            password_changed_at=now,
            is_active=True,
            is_platform_admin=False,
        )
        session.add(user)
        session.flush()
    else:
        if not user.is_active:
            raise AuthError("inactive_user")
        user.email_verified_at = user.email_verified_at or now

    membership = session.scalar(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.organization_id == invitation.organization_id,
        )
    )
    if membership is None:
        membership = Membership(user_id=user.id, organization_id=invitation.organization_id, status="active")
        session.add(membership)
        session.flush()
    elif membership.status != "active":
        raise AuthError("membership_not_active")

    # ISI-13 invitation access grants
    try:
        from src.platform.administration.service import AdministrationError, apply_invitation_grants
        apply_invitation_grants(session, invitation=invitation, membership=membership)
    except AdministrationError as exc:
        raise AuthError("invalid_invitation_access_grants", exc.code) from exc

    invitation.status = "accepted"
    invitation.accepted_at = now
    session.flush()
    return user, membership
