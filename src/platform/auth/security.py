from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from functools import lru_cache

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from src.core.config import Settings, get_settings


class PasswordPolicyError(ValueError):
    pass


@lru_cache(maxsize=1)
def password_hasher() -> PasswordHasher:
    # argon2-cffi PasswordHasher uses Argon2id by default.
    return PasswordHasher()


def validate_password_policy(password: str) -> None:
    if len(password) < 12:
        raise PasswordPolicyError("password must contain at least 12 characters")
    if len(password) > 256:
        raise PasswordPolicyError("password must contain at most 256 characters")


def hash_password(password: str) -> str:
    validate_password_policy(password)
    return password_hasher().hash(password)


def verify_password(password: str, encoded_hash: str | None) -> bool:
    if not encoded_hash:
        return False
    try:
        return bool(password_hasher().verify(encoded_hash, password))
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(encoded_hash: str) -> bool:
    try:
        return password_hasher().check_needs_rehash(encoded_hash)
    except InvalidHashError:
        return True


def new_opaque_token(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _mfa_verifier_key(settings: Settings) -> bytes:
    pepper = settings.security_identifier_pepper.strip()
    if pepper:
        return pepper.encode("utf-8")
    if settings.isi_env.strip().casefold() == "production":
        raise ValueError("production MFA verifier hashing requires SECURITY_IDENTIFIER_PEPPER")
    return b"isi-development-only-privacy-hash"


def hash_mfa_challenge_verifier(
    challenge_id: uuid.UUID,
    verifier: str,
    settings: Settings | None = None,
) -> str:
    """Key and domain-separate low-entropy challenge material before persistence."""
    settings = settings or get_settings()
    payload = f"isi:mfa-challenge-verifier:v1\x00{challenge_id}\x00{verifier}".encode("utf-8")
    return hmac.new(_mfa_verifier_key(settings), payload, hashlib.sha256).hexdigest()


def verify_mfa_challenge_verifier(
    challenge_id: uuid.UUID,
    verifier: str,
    expected_digest: str,
    settings: Settings | None = None,
) -> bool:
    candidate = hash_mfa_challenge_verifier(challenge_id, verifier, settings)
    return hmac.compare_digest(candidate, expected_digest)
