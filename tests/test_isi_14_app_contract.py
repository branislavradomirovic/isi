from pathlib import Path


def test_fastapi_security_middleware_and_production_gate_are_installed():
    text = Path("src/api/app.py").read_text()
    assert "TrustedHostMiddleware" in text
    assert "SecurityHeadersMiddleware" in text
    assert "validate_production_security_settings" in text
    assert "parse_allowed_hosts" in text
