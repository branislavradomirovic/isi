# ISI-20 Penetration-Test Readiness

This is a repository-side readiness pack, not an external penetration test. Baseline: `178d0000cc3119277c59c6ec19024c93d136b2f5`. Candidate state: unstaged and uncommitted on canonical `main`.

## Attack surface

- Public FastAPI authentication endpoints: login, email verification, password reset, and invitation acceptance. Secret-bearing requests use bounded schemas and do not echo credentials.
- Authenticated FastAPI endpoints: bearer-protected identity/context, self-session inventory/revocation, logout, and current-session password assurance refresh.
- Administration mutations: existing organization/product/permission checks run before centralized step-up evaluation and mutation. Organization-wide checks remain separate where applicable.
- Existing workspace creation/status uses `organization.workspace.change`, and organization-profile changes use `organization.profile.change`; both accept fresh password or MFA assurance. The `administration.destructive` classification remains MFA-only and is not a generic umbrella for those routes.
- Administrator session controls: an organization-wide `members.manage` administrator may inventory and revoke a different member's global login sessions only after the target membership resolves inside the authorized organization. Because `AuthSession` is user-global, both operations fail closed before session access if the target has another active organization membership. Revocation requires `security.other_user_session.revoke` assurance. This guard is not a claim that sessions are tenant-scoped.
- Streamlit: server-side calls reuse the existing bearer token in Streamlit session state. Account Security exposes only bounded device labels/timestamps/state and never raw IP, full user agent, credential, verifier, or hash values.
- Worker-facing boundaries: no new worker mutation or background authorization path is introduced by ISI-20D.

## Authentication, session, and access-control matrix

| Case | Expected control | Repository evidence |
|---|---|---|
| Missing/malformed bearer | 401 before state change | `test_isi_20_enterprise_security.py` |
| Wrong password step-up | 401, safe failure event, no refresh | `test_isi_20_enterprise_security.py` |
| Revoked/absolute-expired/idle-expired session | authentication/assurance fails closed | ISI-20 foundation and enterprise tests |
| Missing/stale assurance | privileged mutation denied | `test_isi_20_access_matrix.py` |
| Password on MFA-only operation | insufficient assurance | ISI-20 assurance/access tests |
| Inactive user/membership | access denied | ISI-20 and ISI-02A access tests |
| Missing permission/entitlement/product access | access denied before assurance | ISI-20 and ISI-02A access tests |
| SIMPA versus ORDO | no implied cross-product access | ISI-20 and ISI-02A access tests |
| Cross-organization member/session ID | target does not resolve | `test_isi_20_access_matrix.py` |
| Same target user active in multiple organizations | inventory and revocation return `global_session_multi_organization_target_not_supported` before global session access; revocation leaves the session unchanged | `test_isi_20_access_matrix.py` |
| Last organization admin | mutation remains blocked | ISI-20 access and ISI-13 safety tests |

## OWASP-style cases mapped to controls

- Broken access control / IDOR: explicit organization selection, membership ownership, permissions, organization-wide permission, product entitlement/access, and workspace/product predicates; negative target-session tests include the fail-closed multi-organization target guard for user-global sessions.
- Authentication failures: opaque distinct login session tokens, absolute/idle/revocation validation, current-session-only password refresh, bounded MFA attempts/expiry/revocation/consume semantics.
- Cryptographic and secret exposure: password and challenge verifier inputs never enter response/event metadata; session/reset/invitation tokens are hashed at rest; IP/user-agent persistence uses the existing privacy-hash strategy.
- Security logging failures: stable login, logout, own-session, password assurance/reset, invitation acceptance, MFA outcome, privileged-operation, and target-session event types.
- Injection/resource exhaustion through audit metadata: recursive key/value validation, supported scalar types only, depth/cardinality/key/string/serialized-size bounds, deterministic rejection before persistence.
- Security misconfiguration: inherited ISI-14 trusted-host/header/session and production fail-closed tests remain blocking.

## Replay, fixation, and leakage probes

Separate successful session creation produces distinct opaque tokens. Revoked, absolute-expired, and idle-expired sessions cannot validate. Consumed, exhausted, expired, or revoked MFA challenges cannot establish assurance. Tests inspect API bodies and event metadata for password/verifier/session-token leakage. Intended one-time token responses in the pre-existing login/development invitation lifecycle are not broadened.

## Step-up bypass probes

Authorization and authentication assurance are evaluated as independent gates. Route order is authentication, established scope/permission and any organization-wide check, catalog classification, centralized session-assurance evaluation, then mutation. Unknown operations fail closed. Organization roles never set or imply `is_platform_admin`.

## CSRF and origin rationale

State-changing FastAPI endpoints require an explicit bearer header. Streamlit makes server-side API calls and stores its bearer value in Streamlit server session state; this slice introduces no application authentication cookie or ambient browser credential. Therefore a synthetic cookie-CSRF mechanism would not model the current boundary. Deployment-specific Streamlit origin, proxy, browser-state, and clickjacking behavior remains an external/manual validation item; inherited ISI-14 headers and trusted-host configuration are unchanged.

## Deferred verification

- `DEFERRED_SERVER_VERIFICATION`: live-host scanning, deployed origin/proxy/browser-state validation, infrastructure and TLS inspection, and server session behavior.
- Real-provider MFA enrollment, authenticator/delivery ceremony, recovery handling, and provider operational controls.
- External/manual penetration testing and authenticated dynamic scanning.
- Production identity delivery, SMTP, DNS, ingress, secret rotation, and deployment validation.

Repository tests must not be represented as an external penetration test.

## Review state

`REVIEW_VERIFIED` for the exact unstaged/uncommitted R3 candidate. No unresolved repository-side technical blocker remains. Owner-approved direct-main commit/push, exact-main GitHub Actions, real-provider MFA, external penetration testing, live infrastructure checks, and server verification remain pending or deferred as documented.
