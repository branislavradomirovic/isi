# ISI-20 — Enterprise Security Completion

## Status
`REVIEW_VERIFIED — OWNER MAIN COMMIT / CI PENDING`

## Baseline
Canonical repository HEAD remains `178d0000cc3119277c59c6ec19024c93d136b2f5` on `main`; the ISI-20 reviewed candidate is unstaged and uncommitted in that canonical worktree.

## Dependencies
- `ISI-19-BACKUP-RESTORE-DISASTER-RECOVERY` is merged and post-merge CI verified.
- Existing ISI-17 blocking CI remains authoritative.
- Existing ISI-14 security controls, authentication lifecycle, administration/audit services and access model must be extended rather than bypassed.
- No production credentials or current-server access are required.

## Objective
Complete the repository-side enterprise security controls needed before data-governance and release-candidate work: MFA-ready authentication state/challenge boundaries, user-controlled and administrator-controlled session/device management, step-up protection for privileged operations, expanded privacy-safe security-event coverage, explicit RBAC/product-entitlement/workspace authorization verification, and a deterministic penetration-test readiness pack.

## Existing architecture
- Authentication is implemented under `src/platform/auth/`; `AuthSession` already records token hash, absolute/idle lifecycle timestamps, revocation state and privacy-hashed IP/user-agent fingerprints.
- `src/platform/security/` already provides production-security configuration validation, privacy hashing, login rate limiting, idle-session expiry and `SecurityEvent` recording with sensitive-metadata-key rejection.
- `src/platform/access/` defines SIMPA/ORDO product codes, roles, permissions, organization entitlements, membership product access and role assignments.
- Authorization remains Organization -> Membership -> Role/Permission -> Product entitlement -> Workspace authorization.
- `src/platform/administration/` already provides organization-scoped administrative operations, audit events and last-organization-admin safeguards.
- FastAPI remains the API backend; Streamlit remains the authenticated application UI.

## Locked boundaries
- ISI is the institutional platform. SIMPA and ORDO are the only current domain applications.
- Do not introduce COSMOS as an application, runtime, domain, tenant, namespace, product or user-visible/menu layer.
- Preserve tenant isolation, SIMPA/ORDO isolation and existing product/workspace authorization boundaries.
- No SSH/SCP, deployment, DNS/ingress, production SMTP, production secrets/data, current-server security scanning, production identity-provider enrollment, production KMS/vault mutation or server Ollama action.
- No weakening of authentication, session, audit, access or CI gates.
- MFA implementation must be provider-neutral and testable without requiring a production SMS/email/identity provider. Do not claim production MFA enrollment until an approved deployment integrates and validates a real second-factor delivery/authenticator channel.

## Required behavior
1. Introduce explicit second-factor/MFA readiness state for users with a provider-neutral factor/challenge contract. Persist only one-way/non-secret verification material or encrypted-at-rest material through an explicit boundary; never persist or log raw OTPs, recovery secrets or enrollment seeds in plaintext evidence/logs.
2. Provide deterministic challenge lifecycle semantics: issued, expires, bounded attempts, consumed/replayed rejection, revoked/invalidated state and privacy-safe security events. Tests may use a synthetic deterministic verifier; production delivery/enrollment remains deferred.
3. Add an explicit authentication-assurance/step-up state for sensitive operations. Password re-verification and/or an active verified second factor may satisfy the step-up contract according to a centrally defined policy; expired or insufficient assurance must fail closed.
4. Define the privileged-operation catalog centrally. At minimum, platform-admin changes, member/role/product-access administration, invitation privilege grants, organization entitlement changes, session revocation of another user, security-control changes and destructive/export-sensitive administration must be classifiable as privileged. Do not scatter ad-hoc string checks across domain modules.
5. Add session inventory and revocation services that expose only safe device/session descriptors: session ID, creation/last-seen/expiry, current-session marker, revocation state/reason and privacy-safe/friendly device information derived without exposing raw IP addresses or full raw user-agent strings.
6. Users must be able to revoke one of their own sessions and revoke all other sessions. Administrators may revoke another user’s sessions only through existing organization/access boundaries and the privileged-operation/step-up policy. Because `AuthSession` is user-global rather than organization-bound, administrator target-session inventory and revocation fail closed with `global_session_multi_organization_target_not_supported` whenever the target user has another active organization membership; tenant-scoped sessions remain a separate future architectural change.
7. Session/token revocation after password reset and other existing invalidation behavior must remain intact. Security-sensitive account changes must have explicit deterministic session-invalidation rules.
8. Expand `SecurityEvent` coverage for successful/failed login, rate-limit blocks, logout/session revocation, password reset/change, invitation security lifecycle, MFA/challenge lifecycle, privileged-operation allow/deny, access/role/entitlement administration and suspicious/replay rejection outcomes. Event metadata must remain bounded and privacy-safe.
9. Strengthen security-event metadata validation recursively so sensitive nested keys/values cannot leak credentials/tokens/cookies/authorization material through structured metadata. Add deterministic bounded metadata/schema behavior.
10. Provide a machine-readable security control catalog/matrix linking privileged actions and sensitive capabilities to required permission, product/workspace scope, authentication assurance and emitted audit/security events.
11. Add deterministic tests proving organization -> membership -> role/permission -> product entitlement -> workspace authorization cannot be bypassed by platform security additions. SIMPA access must never imply ORDO access and vice versa.
12. Add negative authorization tests for inactive users/memberships, expired entitlements, missing product access, wrong workspace/product, insufficient role/permission and cross-organization attempts.
13. Add protection against privilege self-escalation and last-administrator removal regressions. Any platform-admin grant/revoke boundary must be explicit, auditable and fail closed; do not infer platform-admin authority from organization-level roles.
14. Add session fixation/replay-oriented tests: new authentication establishes a fresh opaque session token, revoked/expired/idle-expired sessions fail, consumed challenges fail replay, and sensitive tokens never appear in security/audit logs or API responses except where the existing authentication lifecycle explicitly returns a newly issued opaque token to its intended caller.
15. Add CSRF/origin protection contract tests for state-changing authenticated browser operations where applicable to the existing FastAPI/Streamlit topology. If a framework boundary makes a particular control deployment-specific, document the exact residual risk and keep a fail-closed server-side authorization check.
16. Add baseline security-header/cookie/session configuration assertions and production fail-closed checks without contacting the current server.
17. Add a deterministic repository-side penetration-test readiness pack containing: attack-surface inventory, authentication/session/access-control test matrix, OWASP-style test cases mapped to implemented controls, explicit deferred external/manual tests, and machine-readable results from CI-safe probes/tests. Do not claim a real external penetration test was performed.
18. Add/modify Alembic migration(s) for any new persistent security/MFA/session metadata. Upgrade/downgrade or equivalent migration acceptance must remain single-head and pass PostgreSQL 17 CI.
19. Add evidence under `automation/evidence/ISI-20/` and synchronize task registry/status/direct-main metadata as the state advances. The candidate remains unstaged and uncommitted on canonical `main` until owner approval.
20. Preserve compatibility with existing authentication and administration APIs unless a narrowly documented security fix requires an intentional contract change covered by tests.

## Impact
- Database/migrations: expected for MFA/challenge/assurance/session-security metadata; all schema changes require Alembic coverage.
- API: may add authenticated session-security endpoints/services and privileged-operation enforcement; no public unauthenticated security-administration surface.
- UI: may add or prepare account-security/session-management surfaces in Streamlit if consistent with the existing app shell; implementation must remain usable without a production second-factor provider.
- Workers: no new privileged background action may bypass user/tenant/product authorization context.
- Configuration: only non-secret policy/configuration with safe defaults. Production-sensitive values remain externally supplied and fail closed.

## Security and privacy
- Never log/store raw passwords, OTPs, enrollment secrets, recovery codes, invitation/reset tokens, authorization headers, session cookies or bearer/session tokens.
- Raw remote IP and full user-agent data must not be newly persisted; use existing privacy-hash strategy and bounded/friendly device descriptors.
- Security/audit metadata must be recursively validated and bounded.
- MFA/step-up must fail closed on expired, replayed, over-attempted, revoked or ambiguous state.
- Cross-tenant, cross-organization and cross-product authorization must be explicitly tested.
- Administrator target-session inventory and revocation must not expose or mutate a user-global session when the target has an active membership in another organization; the limitation is returned as a conflict without session data.
- Sensitive SIMPA AI/data policy remains unchanged and local-only where already required.
- Evidence must contain synthetic identifiers only and no secrets.

## Tests
- MFA/factor/challenge lifecycle and replay/attempt/expiry tests.
- Privileged-operation assurance/step-up allow/deny tests.
- Session inventory/current-session/device-descriptor/revoke-one/revoke-others tests.
- Password/security-change session invalidation regression tests.
- Security-event coverage and recursive sensitive-metadata rejection tests.
- RBAC/entitlement/workspace matrix tests including SIMPA/ORDO and cross-organization isolation.
- Privilege self-escalation and last-admin safeguards.
- Session fixation/replay/token-leak regression tests.
- CSRF/origin/state-changing browser-operation contract tests where applicable.
- Production security configuration/cookie/header regressions.
- Alembic offline/live and native PostgreSQL 17 coverage for new tables/constraints.
- CI-safe penetration-test readiness assertions and documentation completeness checks.
- Existing test suite remains blocking and may not be weakened, skipped, deleted or xfailed to obtain green status.

## Exact acceptance commands
```bash
python -m tools.ci.policy_check
python -m pytest -q tests/test_isi_20_enterprise_security.py tests/test_isi_20_access_matrix.py tests/test_isi_20_security_events.py
python -m pytest -q tests/test_isi_14_session_contract.py tests/test_isi_14_production_config_contract.py tests/test_isi_02a_access_matrix.py
tools/ci/migration_check.sh offline
tools/ci/native_postgres_tests.sh
tools/ci/run_isi17_acceptance.sh
git diff --check
```

After an owner-approved direct commit and push, the authoritative GitHub Actions run on the exact committed `main` SHA must pass every blocking job inherited from the current main branch, including policy, quality, full tests, architecture/security, PostgreSQL 17 migration/native/recovery checks, Compose, supply-chain, non-deploying build and aggregate acceptance.

## Evidence
Required under `automation/evidence/ISI-20/`:
- `kickoff.md`
- `acceptance-summary.md`
- `results.json`
- security-control/access matrix artifact
- penetration-test-readiness summary explicitly distinguishing CI-verified controls from deferred external/manual tests
- baseline/final SHA and exact CI run ID/number
- independent exact-head review state
- warnings/residual risks/deferrals
- explicit `DEFERRED_SERVER_VERIFICATION`

## Non-goals
- Current-server security scanning or deployment.
- Production MFA provider enrollment/delivery configuration.
- External penetration testing against a live host.
- Replacing the identity/access architecture or introducing a new application/domain.
- Production secret rotation, SMTP, DNS, ingress, SSO/IdP cutover or server Ollama changes.
- Inventing new SIMPA/ORDO methodology or changing domain analytical semantics.

## Forbidden changes
- No SSH/SCP/current-server contact or production data/secrets.
- No plaintext OTP/enrollment/recovery/session/reset/invitation secrets in persistence, logs, fixtures or evidence.
- No bypass of membership, permission, entitlement, product or workspace authorization.
- No treating an organization-admin role as platform-admin authority.
- No weakening CI/security tests to make the task pass.
- No COSMOS runtime/application/domain/product/tenant/menu layer.
- No claim that CI security tests constitute an external penetration test or server verification.

## Completion definition
`IMPLEMENTED` requires an uncommitted reviewed candidate on canonical `main`, with code, any required migrations, tests, control matrix, penetration-test-readiness pack and evidence templates present and local/task gates passing where executable.

`CI_VERIFIED` requires every blocking GitHub Actions job to pass on the exact owner-approved committed `main` SHA.

`REVIEW_VERIFIED` requires review of the exact candidate or final `main` SHA with no unresolved technical blocker, including privilege boundaries, token/secret handling and tenant/product isolation.

Final task completion requires an owner-approved direct commit and push to `main`, followed by successful blocking CI on that exact `main` SHA before ISI-21 begins. ISI-20 does not require an implementation branch, pull request, or merge.

## Deferred server verification
`DEFERRED_SERVER_VERIFICATION` — production MFA integration, live-host security scanning, external/manual penetration testing, real infrastructure/session behavior and deployment validation are intentionally deferred. Current-server work is owner-gated under ISI-28 and requires fresh explicit approval.
