from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import math
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from src.core.config import Settings, get_settings
from src.platform.security.models import SecurityEvent, SecurityRateLimit


class SecurityConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int = 0


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def parse_allowed_hosts(raw: str) -> list[str]:
    hosts = [item.strip() for item in raw.split(",") if item.strip()]
    return hosts or ["localhost", "127.0.0.1", "testserver"]


def validate_production_security_settings(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    if settings.isi_env.strip().casefold() != "production":
        return
    pepper = settings.security_identifier_pepper.strip()
    if len(pepper) < 32 or pepper.casefold() in {"change-me", "changeme", "development", "test"}:
        raise SecurityConfigurationError("production requires a non-placeholder SECURITY_IDENTIFIER_PEPPER >= 32 chars")
    hosts = parse_allowed_hosts(settings.security_allowed_hosts)
    if "*" in hosts:
        raise SecurityConfigurationError("production SECURITY_ALLOWED_HOSTS may not contain wildcard '*'")
    if not settings.public_base_url.casefold().startswith("https://"):
        raise SecurityConfigurationError("production PUBLIC_BASE_URL must use HTTPS")
    if not settings.app_base_url.casefold().startswith("https://"):
        raise SecurityConfigurationError("production APP_BASE_URL must use HTTPS")
    if settings.auth_delivery_mode.strip().casefold() in {"", "null", "none", "development"}:
        raise SecurityConfigurationError("production authentication delivery must be configured")


def _pepper(settings: Settings) -> bytes:
    raw = settings.security_identifier_pepper.strip()
    if raw:
        return raw.encode("utf-8")
    return b"isi-development-only-privacy-hash"


def privacy_hash(value: str | None, namespace: str, settings: Settings | None = None) -> str | None:
    if not value:
        return None
    settings = settings or get_settings()
    payload = f"{namespace}\x00{value}".encode("utf-8")
    return hmac.new(_pepper(settings), payload, hashlib.sha256).hexdigest()


def session_fingerprint_hashes(
    remote_ip: str | None, user_agent: str | None, settings: Settings | None = None
) -> tuple[str | None, str | None]:
    return privacy_hash(remote_ip, "remote-ip", settings), privacy_hash(user_agent, "user-agent", settings)


def resolve_client_ip(request: Any, settings: Settings | None = None) -> str | None:
    settings = settings or get_settings()
    direct = request.client.host if getattr(request, "client", None) else None
    if not settings.security_trust_proxy_headers:
        return direct
    forwarded = request.headers.get("x-forwarded-for", "") if getattr(request, "headers", None) else ""
    candidate = forwarded.split(",", 1)[0].strip() if forwarded else ""
    if not candidate:
        return direct
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return direct


def session_idle_expired(
    last_seen_at: datetime | None,
    *,
    now: datetime | None = None,
    settings: Settings | None = None,
) -> bool:
    if last_seen_at is None:
        return False
    settings = settings or get_settings()
    ttl = max(1, int(settings.auth_session_idle_ttl_seconds))
    return _aware(last_seen_at) + timedelta(seconds=ttl) <= (now or utcnow())


def rate_limit_key(action: str, subject: str, remote_ip: str | None, settings: Settings | None = None) -> str:
    normalized = subject.strip().casefold()
    material = f"{normalized}|{remote_ip or 'unknown'}"
    result = privacy_hash(material, f"rate-limit:{action}", settings)
    assert result is not None
    return result


def _window_expired(row: SecurityRateLimit, *, now: datetime, window_seconds: int) -> bool:
    return _aware(row.window_started_at) + timedelta(seconds=window_seconds) <= now


def check_login_allowed(
    session: Session,
    *,
    email: str,
    remote_ip: str | None,
    now: datetime | None = None,
    settings: Settings | None = None,
) -> RateLimitDecision:
    settings = settings or get_settings()
    now = now or utcnow()
    key = rate_limit_key("login", email, remote_ip, settings)
    row = session.get(SecurityRateLimit, key)
    if row is None:
        return RateLimitDecision(True)
    if row.blocked_until is not None and _aware(row.blocked_until) > now:
        retry = max(1, int((_aware(row.blocked_until) - now).total_seconds()))
        return RateLimitDecision(False, retry)
    if _window_expired(row, now=now, window_seconds=settings.security_login_window_seconds):
        row.attempt_count = 0
        row.window_started_at = now
        row.blocked_until = None
        row.last_attempt_at = now
        session.flush()
    return RateLimitDecision(True)


def register_login_failure(
    session: Session,
    *,
    email: str,
    remote_ip: str | None,
    now: datetime | None = None,
    settings: Settings | None = None,
) -> RateLimitDecision:
    settings = settings or get_settings()
    now = now or utcnow()
    key = rate_limit_key("login", email, remote_ip, settings)
    row = session.get(SecurityRateLimit, key)
    if row is None:
        row = SecurityRateLimit(
            key_hash=key,
            action="login",
            attempt_count=0,
            window_started_at=now,
            blocked_until=None,
            last_attempt_at=now,
        )
        session.add(row)
    elif _window_expired(row, now=now, window_seconds=settings.security_login_window_seconds):
        row.attempt_count = 0
        row.window_started_at = now
        row.blocked_until = None
    row.attempt_count += 1
    row.last_attempt_at = now
    if row.attempt_count >= settings.security_login_max_failures:
        row.blocked_until = now + timedelta(seconds=settings.security_login_block_seconds)
    session.flush()
    if row.blocked_until is not None and _aware(row.blocked_until) > now:
        return RateLimitDecision(False, max(1, int((_aware(row.blocked_until) - now).total_seconds())))
    return RateLimitDecision(True)


def clear_login_failures(
    session: Session,
    *,
    email: str,
    remote_ip: str | None,
    settings: Settings | None = None,
) -> None:
    settings = settings or get_settings()
    row = session.get(SecurityRateLimit, rate_limit_key("login", email, remote_ip, settings))
    if row is not None:
        session.delete(row)
        session.flush()


_FORBIDDEN_METADATA_FRAGMENTS = (
    "password",
    "token",
    "secret",
    "authorization",
    "cookie",
    "credential",
    "verifier",
    "recovery_code",
    "api_key",
    "otp",
)
_METADATA_MAX_DEPTH = 5
_METADATA_MAX_CONTAINER_ITEMS = 50
_METADATA_MAX_KEY_LENGTH = 80
_METADATA_MAX_STRING_LENGTH = 1000
_METADATA_MAX_SERIALIZED_BYTES = 8192
_SENSITIVE_METADATA_VALUE = re.compile(
    r"(?i)(?:\b(?:authorization|cookie|set-cookie)\s*:|\b(?:bearer|basic)\s+[a-z0-9._~+/=-]+"
    r"|\b(?:access_token|refresh_token|session_token|token|password|otp|credential)=[^\s&;,]+"
    r"|\bisi_(?:sess|reset|invite|verify)_[a-z0-9_-]+|\beyJ[a-z0-9_-]+\.[a-z0-9_-]+\.[a-z0-9_-]+)"
)


def _validate_metadata_value(value: Any, *, depth: int) -> Any:
    if depth > _METADATA_MAX_DEPTH:
        raise ValueError("security event metadata exceeds maximum depth")
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("security event metadata number must be finite")
        return value
    if isinstance(value, str):
        if len(value) > _METADATA_MAX_STRING_LENGTH:
            raise ValueError("security event metadata string is too long")
        if _SENSITIVE_METADATA_VALUE.search(value):
            raise ValueError("security event metadata contains a sensitive value")
        return value
    if isinstance(value, list):
        if len(value) > _METADATA_MAX_CONTAINER_ITEMS:
            raise ValueError("security event metadata container has too many items")
        return [_validate_metadata_value(item, depth=depth + 1) for item in value]
    if isinstance(value, dict):
        if len(value) > _METADATA_MAX_CONTAINER_ITEMS:
            raise ValueError("security event metadata container has too many items")
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("security event metadata keys must be strings")
            if not key or len(key) > _METADATA_MAX_KEY_LENGTH:
                raise ValueError("security event metadata key length is invalid")
            folded = key.casefold()
            if any(fragment in folded for fragment in _FORBIDDEN_METADATA_FRAGMENTS):
                raise ValueError("security event metadata contains a forbidden sensitive key")
            result[key] = _validate_metadata_value(item, depth=depth + 1)
        return result
    raise ValueError("security event metadata contains an unsupported value type")


def _safe_metadata(value: dict | None) -> dict:
    if value is not None and not isinstance(value, dict):
        raise ValueError("security event metadata must be a dictionary")
    data = _validate_metadata_value(value or {}, depth=0)
    encoded = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > _METADATA_MAX_SERIALIZED_BYTES:
        raise ValueError("security event metadata exceeds total size budget")
    return data


def record_security_event(
    session: Session,
    *,
    event_type: str,
    outcome: str,
    user_id: uuid.UUID | None = None,
    subject: str | None = None,
    remote_ip: str | None = None,
    user_agent: str | None = None,
    metadata: dict | None = None,
    settings: Settings | None = None,
) -> SecurityEvent:
    settings = settings or get_settings()
    event = SecurityEvent(
        event_type=event_type,
        outcome=outcome,
        user_id=user_id,
        subject_hash=privacy_hash(subject.strip().casefold() if subject else None, "security-subject", settings),
        remote_ip_hash=privacy_hash(remote_ip, "remote-ip", settings),
        user_agent_hash=privacy_hash(user_agent, "user-agent", settings),
        event_metadata=_safe_metadata(metadata),
    )
    session.add(event)
    session.flush()
    return event
