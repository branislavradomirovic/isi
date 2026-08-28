from pathlib import Path


def test_login_route_enforces_shared_security_controls():
    text = Path("src/api/auth_routes.py").read_text()
    for token in ("check_login_allowed", "register_login_failure", "clear_login_failures", "record_security_event", "resolve_client_ip"):
        assert token in text
    assert "HTTP_429_TOO_MANY_REQUESTS" in text
    assert 'headers={"Retry-After": str(decision.retry_after_seconds)}' in text
