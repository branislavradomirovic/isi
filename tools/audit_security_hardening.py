from pathlib import Path


def require(path: str, *tokens: str):
    text = Path(path).read_text()
    for token in tokens:
        if token not in text:
            raise SystemExit(f"ISI-14 security audit FAIL: {path} missing {token!r}")
    return text


require("src/platform/security/service.py", "hmac.new", "validate_production_security_settings", "security_identifier_pepper", "SecurityRateLimit", "SecurityEvent", "resolve_client_ip", "_FORBIDDEN_METADATA_FRAGMENTS")
require("src/platform/security/middleware.py", "X-Content-Type-Options", "Content-Security-Policy", "Strict-Transport-Security", "X-Request-ID")
require("src/api/app.py", "TrustedHostMiddleware", "SecurityHeadersMiddleware", "validate_production_security_settings")
require("src/api/auth_routes.py", "check_login_allowed", "register_login_failure", "clear_login_failures", "HTTP_429_TOO_MANY_REQUESTS")
service = require("src/platform/auth/service.py", "session_idle_expired", "session_fingerprint_hashes", "idle_timeout", "user_session_reset")
require("src/platform/auth/models.py", "remote_ip_hash", "user_agent_hash", "revoked_reason")
require("migrations/versions/20260828_0013_security_hardening.py", "core_security_rate_limits", "core_security_events")
if 'remote_ip=(remote_ip or "")' in service or 'user_agent=(user_agent or "")' in service:
    raise SystemExit("ISI-14 security audit FAIL: new sessions still persist raw client fingerprint values")
if "src.domains.simpa" in Path("src/platform/security/service.py").read_text() or "src.domains.ordo" in Path("src/platform/security/service.py").read_text():
    raise SystemExit("ISI-14 security audit FAIL: domain logic leaked into shared security layer")
print("ISI-14 security hardening static audit PASS")
