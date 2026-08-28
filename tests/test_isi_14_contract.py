from pathlib import Path


def test_security_shared_platform_boundary():
    service = Path("src/platform/security/service.py").read_text()
    middleware = Path("src/platform/security/middleware.py").read_text()
    assert "src.domains.simpa" not in service + middleware
    assert "src.domains.ordo" not in service + middleware
    assert "SecurityHeadersMiddleware" in middleware
    assert "validate_production_security_settings" in service


def test_auth_session_privacy_fields_are_registered():
    models = Path("src/platform/auth/models.py").read_text()
    assert "remote_ip_hash" in models
    assert "user_agent_hash" in models
    assert "revoked_reason" in models
