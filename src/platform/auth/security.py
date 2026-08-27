from __future__ import annotations

import hashlib
import secrets
from functools import lru_cache

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError


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
