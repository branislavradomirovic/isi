# ADR-0022 — ISI Security Hardening

## Decision
Apply security controls as a shared platform concern, not inside SIMPA or ORDO domain code.

The ISI platform keeps opaque server-side sessions, Argon2id passwords, existing authorization and product entitlements. ISI-14 adds application-wide security headers/trusted-host enforcement, production fail-closed configuration checks, database-backed login throttling, privacy-preserving session fingerprints, an idle session timeout, revocation reasons and append-only security events.

## Rationale
Security policy must protect both flagship products consistently while preserving strict domain and tenant isolation. Database-backed throttling is deterministic across API processes and does not depend on a single in-memory worker. Privacy hashes reduce unnecessary storage of network/client identifiers.

## Consequences
Production cannot start with localhost/HTTP-style development security defaults. Deployment must provide an explicit pepper, trusted hosts, HTTPS base URLs and a real authentication delivery mode.

No MFA claim is made by this phase. No external security appliance is implied.
