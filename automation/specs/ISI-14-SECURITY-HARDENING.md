# ISI-14 — Security & Hardening

## Status
Implementation package for the ISI Platform baseline after `9223862 Complete administration`.

## Goal
Harden the existing ISI platform without changing the SIMPA/ORDO product architecture or introducing a new authentication stack.

This phase is a cross-cutting security pass over the existing FastAPI / Streamlit / PostgreSQL platform. It preserves the current identity, membership, role, entitlement and workspace model.

## Locked boundaries

- ISI remains one platform with SIMPA and ORDO as separate product domains.
- Role and product entitlement remain separate authorization dimensions.
- No security control may bypass `Membership -> Organization -> Role/Permission -> Product entitlement`.
- No raw password, opaque token, invitation token, reset token or security pepper may be written to audit/security event payloads.
- New session records must not persist raw client IP or raw user-agent values; privacy-preserving hashes are used instead.
- Production configuration is fail-closed when required hardening settings are missing.
- Trusted hosts may not use wildcard `*` in production.
- Production public/app base URLs must use HTTPS.
- Null/development authentication delivery is forbidden in production.
- Security headers are application-wide. HSTS is production-only so local HTTP development remains usable.
- Login throttling must be account-enumeration neutral: the bucket is created for any submitted identifier, whether or not an account exists.
- Session idle timeout is additional to the existing absolute session expiry.
- Existing tenant/product isolation behavior must remain unchanged.
- No automatic commit or push.

## Database revision

`20260828_0012 -> 20260828_0013`

### New tables

- `core_security_rate_limits`
- `core_security_events`

### Hardened session columns

`core_auth_sessions` gains:

- `remote_ip_hash`
- `user_agent_hash`
- `revoked_reason`

Existing raw `remote_ip` / `user_agent` columns remain for backward-compatible schema evolution, but ISI-14 stops writing raw values for newly created sessions.

## HTTP hardening

FastAPI responses receive:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- restrictive `Permissions-Policy`
- baseline `Content-Security-Policy`
- `X-Request-ID`
- `Cache-Control: no-store` on authentication endpoints
- `Strict-Transport-Security` only in production

`TrustedHostMiddleware` is enabled from `SECURITY_ALLOWED_HOSTS`.

## Production configuration gate

When `ISI_ENV=production`, startup requires:

- a non-placeholder `SECURITY_IDENTIFIER_PEPPER` of at least 32 characters;
- explicit non-wildcard `SECURITY_ALLOWED_HOSTS`;
- HTTPS `PUBLIC_BASE_URL` and `APP_BASE_URL`;
- `AUTH_DELIVERY_MODE` not equal to `null`, `none` or `development`.

Development remains compatible with localhost and the current native PostgreSQL workflow.

## Login abuse controls

Default development/test contract:

- window: 15 minutes;
- maximum failures: 5;
- block: 15 minutes.

The rate-limit key is HMAC-SHA256 over normalized identifier + client address, using the configured security pepper. Forwarded client addresses are ignored unless `SECURITY_TRUST_PROXY_HEADERS=true`, and forwarded values are IP-validated before use. No raw email/IP is stored in the rate-limit table.

The first five failed attempts remain normal 401 responses. A subsequent attempt during the block returns 429 with `Retry-After`.

A successful login clears the caller's login-failure bucket.

## Session hardening

The existing absolute session TTL remains in force. ISI-14 adds an idle timeout (default 60 minutes). An idle-expired session is revoked with `revoked_reason=idle_timeout`.

Explicit logout uses `revoked_reason=logout`; password-reset/user-wide invalidation uses `revoked_reason=user_session_reset`.

## Security event model

The append-only security event table records events such as:

- `auth.login` success / failure / throttled;
- future hardening events may reuse the same shared table.

Only privacy-preserving hashes and safe structured metadata are permitted. Metadata keys containing password/token/secret/authorization/cookie/credential semantics are rejected. No raw credentials/tokens are stored.

## Dependency / configuration baseline

The runner adds `python -m pip check` to the acceptance gate. It does not randomly upgrade the `httpx`/Starlette stack; the known deprecation warning remains non-blocking and should be handled as an explicit compatibility task rather than hidden inside security hardening.

## Acceptance

1. exact clean baseline `9223862`;
2. Python 3.11.15;
3. native PostgreSQL at `20260828_0012`;
4. ISI-13 done;
5. static security audit PASS;
6. Alembic offline render PASS;
7. native upgrade to `20260828_0013`;
8. focused ISI-14 tests PASS;
9. native PostgreSQL acceptance PASS;
10. full regression suite PASS;
11. `pip check` PASS;
12. Docker Compose configuration PASS;
13. `git diff --check` PASS;
14. local API/security/browser QA PASS;
15. manual visual QA evidence before task closeout.

## Non-goals

- MFA/WebAuthn implementation;
- external WAF/CDN configuration;
- SMTP/provider deployment;
- secret manager deployment;
- penetration test certification;
- automatic dependency upgrades;
- production cutover.

Those belong to staging/production deployment work after this hardening baseline.
