from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.platform.auth.models import AuthSession, AuthToken, Invitation, MfaChallenge, MfaFactor
from src.platform.auth.security import (
    hash_mfa_challenge_verifier,
    hash_password,
    hash_token,
    needs_rehash,
    new_opaque_token,
    verify_mfa_challenge_verifier,
    verify_password,
)
from src.platform.identity.models import Membership, Organization, User
from src.platform.security.service import session_fingerprint_hashes, session_idle_expired


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


@dataclass(frozen=True)
class IssuedMfaChallenge:
    challenge_id: uuid.UUID
    expires_at: datetime


@dataclass(frozen=True)
class MfaChallengeVerificationResult:
    challenge_id: uuid.UUID
    succeeded: bool
    error_code: str | None = None


MFA_CHALLENGE_TTL_SECONDS = 300
MFA_CHALLENGE_MAX_TTL_SECONDS = 900
MFA_CHALLENGE_MAX_ATTEMPTS = 5
_MFA_METHOD_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]{0,39}$")


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
    password_verified: bool = False,
    remote_ip: str | None = None,
    user_agent: str | None = None,
) -> IssuedSession:
    if not user.is_active:
        raise AuthError("inactive_user")
    settings = get_settings()
    now = utcnow()
    expires_at = now + timedelta(seconds=settings.auth_session_ttl_seconds)
    raw = new_opaque_token("isi_sess")
    remote_ip_hash, user_agent_hash = session_fingerprint_hashes(remote_ip, user_agent)
    model = AuthSession(
        user_id=user.id,
        token_hash=hash_token(raw),
        expires_at=expires_at,
        last_seen_at=now,
        password_verified_at=now if password_verified else None,
        remote_ip=None,
        user_agent=None,
        remote_ip_hash=remote_ip_hash,
        user_agent_hash=user_agent_hash,
    )
    session.add(model)
    session.flush()
    return IssuedSession(token=raw, session_id=model.id, expires_at=expires_at)


def _active_bound_session(
    session: Session,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    now: datetime,
) -> tuple[AuthSession, User]:
    model = session.scalar(
        select(AuthSession)
        .where(AuthSession.id == session_id, AuthSession.user_id == user_id)
        .with_for_update()
    )
    if model is None:
        raise AuthError("invalid_auth_session")
    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise AuthError("inactive_user")
    if model.revoked_at is not None:
        raise AuthError("auth_session_revoked")
    if _aware(model.expires_at) <= now:
        raise AuthError("auth_session_expired")
    if session_idle_expired(model.last_seen_at, now=now):
        raise AuthError("auth_session_idle_expired")
    return model, user


def refresh_password_assurance(
    session: Session,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    password: str,
    now: datetime | None = None,
) -> AuthSession:
    """Re-verify a password and refresh assurance for exactly one active session."""
    checked_at = _aware(now or utcnow())
    model, user = _active_bound_session(
        session,
        user_id=user_id,
        session_id=session_id,
        now=checked_at,
    )
    password_hash = user.password_hash
    if not password_hash:
        verify_password(password, _dummy_password_hash())
        raise AuthError("invalid_password")
    if not verify_password(password, password_hash):
        raise AuthError("invalid_password")
    model.password_verified_at = checked_at
    session.flush()
    return model


def verify_mfa_challenge_for_session(
    session: Session,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    challenge_id: uuid.UUID,
    verifier: str,
    now: datetime | None = None,
) -> MfaChallengeVerificationResult:
    """Consume an authentication challenge and bind its assurance to one active session."""
    checked_at = _aware(now or utcnow())
    model, _user = _active_bound_session(
        session,
        user_id=user_id,
        session_id=session_id,
        now=checked_at,
    )
    challenge = session.scalar(
        select(MfaChallenge)
        .where(MfaChallenge.id == challenge_id, MfaChallenge.user_id == user_id)
        .with_for_update()
    )
    if challenge is None:
        raise AuthError("invalid_mfa_challenge")
    if challenge.purpose != "authentication":
        raise AuthError("mfa_challenge_not_authentication")

    result = verify_mfa_challenge(
        session,
        user_id=user_id,
        challenge_id=challenge_id,
        verifier=verifier,
        now=checked_at,
    )
    if result.succeeded:
        model.mfa_verified_at = checked_at
        session.flush()
    return result


def validate_session(session: Session, raw_token: str) -> tuple[AuthSession, User] | None:
    if not raw_token:
        return None
    model = session.scalar(select(AuthSession).where(AuthSession.token_hash == hash_token(raw_token)))
    now = utcnow()
    if model is None or model.revoked_at is not None or _aware(model.expires_at) <= now:
        return None
    user = session.get(User, model.user_id)
    if user is None or not user.is_active:
        return None
    if session_idle_expired(model.last_seen_at, now=now):
        model.revoked_at = now
        model.revoked_reason = "idle_timeout"
        session.flush()
        return None
    model.last_seen_at = now
    session.flush()
    return model, user


def revoke_session(session: Session, raw_token: str) -> bool:
    model = session.scalar(select(AuthSession).where(AuthSession.token_hash == hash_token(raw_token)))
    if model is None:
        return False
    if model.revoked_at is None:
        model.revoked_at = utcnow()
        model.revoked_reason = "logout"
        session.flush()
    return True


def revoke_all_user_sessions(session: Session, user_id: uuid.UUID) -> None:
    session.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=utcnow(), revoked_reason="user_session_reset")
    )
    session.flush()


def create_mfa_factor(
    session: Session,
    user: User,
    *,
    method: str,
    display_name: str | None = None,
) -> MfaFactor:
    if not user.is_active:
        raise AuthError("inactive_user")
    normalized_method = method.strip().casefold()
    if not _MFA_METHOD_PATTERN.fullmatch(normalized_method):
        raise AuthError("invalid_mfa_method")
    normalized_display_name = display_name.strip() if display_name else None
    if normalized_display_name and len(normalized_display_name) > 120:
        raise AuthError("invalid_mfa_display_name")
    factor = MfaFactor(
        user_id=user.id,
        method=normalized_method,
        status="pending",
        display_name=normalized_display_name,
    )
    session.add(factor)
    session.flush()
    return factor


def revoke_mfa_factor(
    session: Session,
    *,
    user_id: uuid.UUID,
    factor_id: uuid.UUID,
    now: datetime | None = None,
) -> MfaFactor:
    factor = session.scalar(select(MfaFactor).where(MfaFactor.id == factor_id, MfaFactor.user_id == user_id))
    if factor is None:
        raise AuthError("mfa_factor_not_found")
    if factor.status != "revoked":
        revoked_at = now or utcnow()
        factor.status = "revoked"
        factor.revoked_at = revoked_at
        session.execute(
            update(MfaChallenge)
            .where(
                MfaChallenge.factor_id == factor.id,
                MfaChallenge.user_id == user_id,
                MfaChallenge.consumed_at.is_(None),
                MfaChallenge.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        session.flush()
    return factor


def issue_mfa_challenge(
    session: Session,
    *,
    user_id: uuid.UUID,
    factor_id: uuid.UUID,
    purpose: str,
    verifier: str,
    now: datetime | None = None,
    ttl_seconds: int = MFA_CHALLENGE_TTL_SECONDS,
    max_attempts: int = MFA_CHALLENGE_MAX_ATTEMPTS,
) -> IssuedMfaChallenge:
    if purpose not in {"enrollment", "authentication"}:
        raise AuthError("invalid_mfa_challenge_purpose")
    if not verifier or len(verifier) > 256:
        raise AuthError("invalid_mfa_verifier")
    if not 1 <= ttl_seconds <= MFA_CHALLENGE_MAX_TTL_SECONDS:
        raise AuthError("invalid_mfa_challenge_ttl")
    if not 1 <= max_attempts <= 10:
        raise AuthError("invalid_mfa_challenge_attempt_policy")
    factor = session.scalar(select(MfaFactor).where(MfaFactor.id == factor_id, MfaFactor.user_id == user_id))
    required_status = "pending" if purpose == "enrollment" else "active"
    user = session.get(User, user_id)
    if user is None or not user.is_active or factor is None or factor.status != required_status:
        raise AuthError("mfa_factor_not_ready")

    issued_at = now or utcnow()
    session.execute(
        update(MfaChallenge)
        .where(
            MfaChallenge.factor_id == factor.id,
            MfaChallenge.user_id == user_id,
            MfaChallenge.purpose == purpose,
            MfaChallenge.consumed_at.is_(None),
            MfaChallenge.revoked_at.is_(None),
        )
        .values(revoked_at=issued_at)
    )
    challenge_id = uuid.uuid4()
    expires_at = issued_at + timedelta(seconds=ttl_seconds)
    challenge = MfaChallenge(
        id=challenge_id,
        user_id=user_id,
        factor_id=factor.id,
        purpose=purpose,
        verifier_digest=hash_mfa_challenge_verifier(challenge_id, verifier),
        issued_at=issued_at,
        expires_at=expires_at,
        attempt_count=0,
        max_attempts=max_attempts,
    )
    session.add(challenge)
    session.flush()
    return IssuedMfaChallenge(challenge_id=challenge_id, expires_at=expires_at)


def revoke_mfa_challenge(
    session: Session,
    *,
    user_id: uuid.UUID,
    challenge_id: uuid.UUID,
    now: datetime | None = None,
) -> MfaChallenge:
    challenge = session.scalar(
        select(MfaChallenge).where(MfaChallenge.id == challenge_id, MfaChallenge.user_id == user_id)
    )
    if challenge is None:
        raise AuthError("invalid_mfa_challenge")
    if challenge.consumed_at is not None:
        raise AuthError("mfa_challenge_already_consumed")
    if challenge.revoked_at is None:
        challenge.revoked_at = now or utcnow()
        session.flush()
    return challenge


def verify_mfa_challenge(
    session: Session,
    *,
    user_id: uuid.UUID,
    challenge_id: uuid.UUID,
    verifier: str,
    now: datetime | None = None,
) -> MfaChallengeVerificationResult:
    """Consume one challenge while locking its row on databases that support FOR UPDATE."""
    challenge = session.scalar(
        select(MfaChallenge)
        .where(MfaChallenge.id == challenge_id, MfaChallenge.user_id == user_id)
        .with_for_update()
    )
    if challenge is None:
        raise AuthError("invalid_mfa_challenge")
    checked_at = now or utcnow()
    if challenge.revoked_at is not None:
        raise AuthError("mfa_challenge_revoked")
    if challenge.consumed_at is not None:
        raise AuthError("mfa_challenge_already_consumed")
    if challenge.attempt_count >= challenge.max_attempts:
        raise AuthError("mfa_challenge_attempts_exhausted")
    if _aware(challenge.expires_at) <= checked_at:
        raise AuthError("mfa_challenge_expired")

    factor = session.scalar(
        select(MfaFactor).where(MfaFactor.id == challenge.factor_id, MfaFactor.user_id == user_id)
    )
    user = session.get(User, user_id)
    if user is None or not user.is_active or factor is None or factor.status == "revoked":
        challenge.revoked_at = checked_at
        session.flush()
        return MfaChallengeVerificationResult(
            challenge_id=challenge.id,
            succeeded=False,
            error_code="mfa_factor_not_ready",
        )
    if not verifier or len(verifier) > 256 or not verify_mfa_challenge_verifier(
        challenge.id, verifier, challenge.verifier_digest
    ):
        challenge.attempt_count += 1
        session.flush()
        if challenge.attempt_count >= challenge.max_attempts:
            return MfaChallengeVerificationResult(
                challenge_id=challenge.id,
                succeeded=False,
                error_code="mfa_challenge_attempts_exhausted",
            )
        return MfaChallengeVerificationResult(
            challenge_id=challenge.id,
            succeeded=False,
            error_code="invalid_mfa_verifier",
        )

    if challenge.purpose == "enrollment":
        if factor.status != "pending":
            raise AuthError("mfa_factor_not_ready")
        factor.status = "active"
        factor.verified_at = checked_at
    elif factor.status != "active":
        raise AuthError("mfa_factor_not_ready")
    challenge.consumed_at = checked_at
    session.flush()
    return MfaChallengeVerificationResult(challenge_id=challenge.id, succeeded=True)


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
