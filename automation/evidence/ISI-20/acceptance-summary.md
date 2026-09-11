# ISI-20D R3 Acceptance Summary

State: **REVIEW_VERIFIED — OWNER MAIN COMMIT / CI PENDING** for the unstaged/uncommitted R3 candidate on canonical `main`.

Baseline: `178d0000cc3119277c59c6ec19024c93d136b2f5`.

Candidate state: unstaged and uncommitted on canonical `main`. No final `main` commit SHA exists yet.

Implemented controls include recursive bounded security-event metadata validation, current-session password re-verification, security-event coverage for the touched authentication/session/MFA/administration surfaces, centralized step-up enforcement on every existing administration mutation, fail-closed administrator target-session inventory/revocation, and the Streamlit Account Security surface. Existing workspace creation/status and organization-profile changes use specific `password_or_mfa` operations; `administration.destructive` remains MFA-only. No migration was required or changed.

R3 closes the R2 human-review blocker locally. `AuthSession` remains user-global and is not claimed to be tenant-scoped. After the target membership resolves in the authorized organization and self-targeting is rejected, both administrator target-session operations check for any other active membership belonging to that user. If one exists in a different organization, inventory and revocation stop before global sessions are queried or mutated with `global_session_multi_organization_target_not_supported`, mapped to HTTP 409 without target session data. The existing single-organization path, cross-organization different-user denial, target-session ownership check, centrally catalogued revocation step-up, and idempotent successful revocation remain covered.

R2 preserves the exhaustive `assert required == set(PRIVILEGED_OPERATION_CATALOG)` contract and expands its expected set with `WORKSPACE_ADMINISTRATION_CHANGE` and `ORGANIZATION_PROFILE_CHANGE`. The ISI-19 registry entry now exactly matches its canonical-baseline value, including baseline status `implemented`; R2 changed no other ISI-19 field.

Final human review: `REVIEW_VERIFIED` — the exact R3 candidate has no unresolved technical blocker; owner-approved direct-main commit/push and exact-main CI remain pending.

Observed R3 local verification:

- `python -m tools.ci.policy_check` — PASS.
- `python -m pytest -q tests/test_isi_20_access_matrix.py` — PASS, 7 tests.
- `python -m pytest -q tests/test_isi_20_auth_assurance.py tests/test_isi_20_enterprise_security.py tests/test_isi_20_access_matrix.py tests/test_isi_20_security_events.py` — PASS, 34 tests.
- `python -m pytest -q tests/test_isi_20_mfa_challenge_foundation.py tests/test_isi_20_auth_assurance.py tests/test_isi_20_session_management.py tests/test_isi_14_session_contract.py tests/test_isi_14_production_config_contract.py tests/test_isi_02a_access_matrix.py` — PASS, 45 tests.
- `tools/ci/migration_check.sh offline` — PASS, single head through `20260911_0016`.
- `env -u DATABASE_URL python -m pytest -q` — PASS; counts recorded in `results.json`.
- `python -m json.tool` for `automation/tasks.json`, `results.json`, and `security-control-matrix.json` — PASS.
- `git diff --check` — PASS.

Warnings and residual risks: native PostgreSQL, real-provider MFA, deployed Streamlit origin/browser behavior, live infrastructure/TLS, and external/manual penetration testing were not validated by R3. Administrator target-session controls remain deliberately unavailable for accounts with active memberships in multiple organizations until a separate tenant-scoped session architecture is designed.

Direct-main state: `main_commit: PENDING`, `push: PENDING`, `ci: PENDING`, `review: REVIEW_VERIFIED`. Final completion requires an owner-approved commit/push on `main` and successful blocking GitHub Actions verification of that exact `main` SHA; no branch, pull request, or merge is required for ISI-20.

Server/live-host state: `DEFERRED_SERVER_VERIFICATION`.
