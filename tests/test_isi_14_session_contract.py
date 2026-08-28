from datetime import datetime, timedelta, timezone

from src.core.config import Settings
from types import SimpleNamespace
import pytest

from src.platform.security.service import _safe_metadata, privacy_hash, resolve_client_ip, session_idle_expired


def test_idle_timeout_and_privacy_hash():
    settings = Settings(auth_session_idle_ttl_seconds=3600, security_identifier_pepper="z" * 48)
    now = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)
    assert not session_idle_expired(now - timedelta(minutes=59), now=now, settings=settings)
    assert session_idle_expired(now - timedelta(minutes=61), now=now, settings=settings)
    hashed = privacy_hash("192.0.2.10", "remote-ip", settings)
    assert hashed and len(hashed) == 64 and "192.0.2.10" not in hashed


def test_proxy_headers_are_ignored_by_default_and_validated_when_enabled():
    request = SimpleNamespace(client=SimpleNamespace(host="10.0.0.10"), headers={"x-forwarded-for": "203.0.113.7, 10.0.0.10"})
    assert resolve_client_ip(request, Settings(security_trust_proxy_headers=False)) == "10.0.0.10"
    assert resolve_client_ip(request, Settings(security_trust_proxy_headers=True)) == "203.0.113.7"


def test_security_event_metadata_rejects_sensitive_keys():
    assert _safe_metadata({"retry_after_seconds": 10}) == {"retry_after_seconds": 10}
    with pytest.raises(ValueError):
        _safe_metadata({"reset_token": "must-not-be-recorded"})
