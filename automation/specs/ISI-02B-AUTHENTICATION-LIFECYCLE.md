# ISI-02B — Authentication Lifecycle

## Status
Implementation package following accepted ISI-02A identity/access/workspace foundation.

## Purpose
Implement secure invite-first user authentication for the shared ISI Platform without coupling authentication to SIMPA or ORDO.

## Locked decisions

1. Authentication is shared platform infrastructure.
2. There is no `simpa_user` or `ordo_user` authentication type.
3. Public self-registration is not introduced. Institutional access is invitation/provisioning based.
4. Passwords are hashed with Argon2id through `argon2-cffi`; plaintext passwords are never stored.
5. Authenticated sessions use opaque high-entropy bearer tokens. Only SHA-256 token digests are stored in PostgreSQL.
6. Session tokens are revocable and expire server-side.
7. Password reset, email verification and invitation secrets are single-use, expiring, opaque tokens; raw secrets are never persisted.
8. Password reset revokes all existing sessions for that user.
9. Invitation acceptance proves control of the invited email address and marks it verified.
10. Authentication does not grant product access. Organization entitlement, membership product access and RBAC remain ISI-02A concerns.
11. Local development uses the existing native PostgreSQL `isi` database. No Docker PostgreSQL is started by this task.
12. Email transport is abstracted. The default delivery adapter is intentionally no-op; production SMTP/provider integration is a later infrastructure task. API responses never expose reset/verification secrets.
13. Deny-by-default and account-enumeration-resistant public responses are required.

## Data model changes

Extend `core_users` with:
- `email_verified_at`
- `last_login_at`
- `password_changed_at`

Create:
- `core_auth_sessions`
- `core_auth_tokens`
- `core_invitations`

`core_auth_tokens.purpose` is restricted to:
- `email_verification`
- `password_reset`

## Password policy
- minimum 12 characters;
- maximum 256 characters;
- Argon2id hash;
- rehash-on-success when the configured Argon2 parameters change.

## Session policy
Default TTL: 12 hours.

A session is valid only when:
- token hash exists;
- session is not revoked;
- session is not expired;
- referenced user exists and is active.

## Token policy
Defaults:
- email verification: 24 hours;
- password reset: 30 minutes;
- invitation: 7 days.

Tokens are generated with `secrets.token_urlsafe(32)` and stored only as SHA-256 digests.

## Invitation policy
An invitation binds one email address to one organization.

Acceptance:
- validates one-time invitation token;
- rejects expired/revoked/accepted invitations;
- creates a user when none exists;
- does not overwrite an existing user's password;
- marks email verified;
- creates an active organization membership when absent;
- refuses to silently reactivate revoked/suspended memberships;
- does not grant SIMPA/ORDO entitlement, product access or roles.

## API contract

Add `/api/v1/auth` endpoints:
- `POST /login`
- `POST /logout`
- `GET /me`
- `POST /email-verification/request`
- `POST /email-verification/confirm`
- `POST /password-reset/request`
- `POST /password-reset/confirm`
- `POST /invitations/accept`

Bearer token format:

`Authorization: Bearer <opaque-session-token>`

No JWT is introduced in ISI-02B.

## Out of scope
- open public registration;
- SMTP/provider configuration;
- invitation creation UI/API authorization;
- organization/product selector UI;
- Streamlit authenticated shell integration;
- MFA/passkeys;
- SSO/OIDC/SAML;
- generalized audit-event service;
- SIMPA/ORDO domain logic.

## Acceptance gate
- task starts from clean `main` after ISI-02A commit;
- Argon2 password tests pass;
- opaque session lifecycle tests pass;
- verification/reset/invitation token tests pass;
- API login/me/logout tests pass;
- reset endpoint is account-enumeration resistant;
- native PostgreSQL migration reaches `20260827_0002`;
- native PostgreSQL auth tables and user columns exist;
- native PostgreSQL transactional auth smoke test passes;
- full pytest suite passes;
- Alembic offline render passes;
- Docker Compose is configuration-only and valid;
- changed paths stay within ISI-02B scope;
- runner/analyzer never commit or push.
