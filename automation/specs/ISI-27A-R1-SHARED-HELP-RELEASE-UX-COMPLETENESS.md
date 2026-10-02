# ISI-27A-R1 — Shared Help & Release UX Completeness

## Status
`LOCKED IMPLEMENTATION CONTRACT / ONE LARGE RUNNER-MEDIATED CODEX SLICE`

## Baseline
- Repository: `branislavradomirovic/isi`
- Canonical local repository: `/Users/branislavradomirovic/Applications/Python/ISI`
- Branch: `main`
- Exact baseline SHA: `39dc1d59a74a03c86f68df093cc07e32d41d028c`
- Exact baseline tree: `3c7027b375b041043f7305cdab008aee35f16ef7`
- Baseline relation required: `HEAD == origin/main == direct remote main`.
- Worktree/index: clean; stash empty; exactly one worktree.
- Hosted GitHub Actions: **not authorized** by this development package.
- Server/live-host verification: `DEFERRED_SERVER_VERIFICATION`.

## Canonical bootstrap evidence
ISI-27 scope lock is accepted on exact main SHA `39dc1d59a74a03c86f68df093cc07e32d41d028c`.

The corrected code-level surface audit is `ISI-27A-R0-R1`:
- owner Downloads report: `ISI-27A-R0-R1-SHARED-HELP-SURFACE-AUDIT-REPORT.md`
- report SHA256: `77a2a0ac6d9d95e31eda6f9bc9eb8f439711c5aafeff97db8ee33d6e36fb3c25`
- owner Downloads evidence: `ISI-27A-R0-R1-SHARED-HELP-SURFACE-AUDIT-EVIDENCE.json`
- evidence SHA256: `1cac5fb07c8d3e9580d8013f58095f87c595ebb80d3022cdd56bb253130e7907`
- corrected production-critical Help/XAI blockers: exactly 12.
- protected predecessor Help/XAI rows already VERIFIED: exactly 6 (`INV-A10`, `INV-A11`, `INV-A12`, `INV-A13`, `INV-A18`, `INV-A19`).
- `INV-A17` public self-registration: `NOT_PRESENT`; no public signup route exists and none may be added.

DONE / PARTIAL / MISSING / DRIFT for this implementation boundary:
- DONE: domain SIMPA/ORDO/shared-AI Help/XAI; auth service/API lifecycle; app shell/workspaces; public site seams.
- PARTIAL/MISSING: shared/public/auth/shell/data/reporting/admin/security Help coverage and global matrix completion.
- DRIFT: none accepted from R0-R1; later material-action tables must never overwrite canonical top-level matrix coverage.

## Dependencies
- accepted ISI-27 scope lock on `39dc1d59a74a03c86f68df093cc07e32d41d028c`;
- corrected `ISI-27A-R0-R1` read-only code-level audit;
- accepted predecessor security/auth, data, reporting, administration, SIMPA/ORDO Help/XAI, and shared AI contracts.

## Objective
Close the twelve corrected ISI-27A shared Help/release-UX blockers in one complete repository-side slice without changing domain methodology, authorization authority, persistence schema, deployment topology, or server state.

The implementation must provide truthful, reachable Help and safe customer UX for:
1. `INV-A01` Public website;
2. `INV-A02` Login;
3. `INV-A03` Invitation onboarding;
4. `INV-A04` Email verification;
5. `INV-A05` Password reset;
6. `INV-A06` Authenticated app shell;
7. `INV-A08` Data workspace;
8. `INV-A14` Reporting workspace;
9. `INV-A15` Administration workspace;
10. `INV-A16` Account security workspace;
11. `INV-A17` Public self-registration absence;
12. `INV-A21` Cross-product Help Coverage Matrix.

Completion requires all twelve to be truthfully `VERIFIED` as Help/release UX coverage, while `INV-A17` remains runtime status `NOT_PRESENT` and is VERIFIED only as an explicitly documented/tested invitation-only absence. `INV-A07` and `INV-A20` are non-production-critical and must not be silently promoted or pulled into this release-blocker slice.

## Existing architecture
- Public site: FastAPI/Jinja2 under `src/public/**`; existing header/footer already expose the application URL.
- Private application: Streamlit `src/streamlit_app/app.py` with organization/product/workspace selection and permission-aware navigation.
- Auth lifecycle authority: `src/api/auth_routes.py`, `src/platform/auth/service.py`, `src/platform/auth/delivery.py`.
- Existing delivery links target Streamlit `app_base_url` with query keys `invitation_token`, `verify_token`, and `reset_token`.
- Existing API authority supports login, invitation acceptance, email-verification request/confirm, password-reset request/confirm; public self-registration is intentionally absent.
- Data, reporting, administration and account-security workspaces already exist and must retain their semantics.
- SIMPA Help/XAI, ORDO Help/XAI and shared AI Help/XAI are accepted predecessor authorities and are protected from reimplementation.

## Canonical system inventory impact
Affected user-surface rows: `INV-A01`, `INV-A02`, `INV-A03`, `INV-A04`, `INV-A05`, `INV-A06`, `INV-A08`, `INV-A14`, `INV-A15`, `INV-A16`, `INV-A17`, `INV-A21`.

Required inventory synchronization:
- preserve component STATUS values (`CURRENT_AS_BUILT` or `NOT_PRESENT` for A17); Help completion does not invent a new runtime component status;
- add shared Help/User Guide paths and 27A test authority where relevant;
- update responsibilities/removal notes only as needed to record Help/release UX completion;
- keep `INV-A07` `PRODUCTION_CRITICAL=NO` and `INV-A20` `PRODUCTION_CRITICAL=NO` unchanged;
- keep `INV-A17` runtime STATUS `NOT_PRESENT` and explicitly invitation-only.

## Legacy/drift audit
- R0 initial matrix parser over-read later material-action tables: `LEGITIMATE_HISTORY`; corrected R0-R1 is authority.
- Existing SIMPA/ORDO/shared-AI Help/XAI: `REQUIRED_COMPATIBILITY`; do not rewrite or downgrade.
- Existing auth service/API/token semantics: `REQUIRED_COMPATIBILITY`; 27A adds presentation/client reachability only.
- Historical tests freezing global matrix `PARTIAL` or shared rows as non-VERIFIED: `REMOVE_BEFORE_NEXT_SLICE` only where they conflict with legitimate 27A completion; update assertions while preserving their historical/domain protections.
- No other unclassified incompatible legacy is authorized.

## Exact mutable surface
Codex may modify/create only these repository paths. Everything else is immutable.

### Locked 27A authority and corrected audit copies
- `automation/specs/ISI-27A-R1-SHARED-HELP-RELEASE-UX-COMPLETENESS.md` — runner-installed byte-identical contract; Codex must not edit.
- `automation/specs/ISI-27A-R0-R1-SHARED-HELP-SURFACE-AUDIT-REPORT.md` — runner-installed byte-identical audit copy; Codex must not edit.
- `automation/specs/ISI-27A-R0-R1-SHARED-HELP-SURFACE-AUDIT-EVIDENCE.json` — runner-installed byte-identical audit copy; Codex must not edit.

### Shared Help authority
- `docs/help/ISI-SHARED-USER-GUIDE.md` — new canonical shared/public/auth/shell/workspace guide.
- `docs/help/ISI-HELP-COVERAGE-MATRIX.md` — promote only the corrected 12 shared release blockers when supported by implementation/tests; preserve predecessor rows.
- `src/streamlit_app/shared_help_workspace.py` — new canonical shared in-app Help authority.

### Existing customer UI seams
- `src/streamlit_app/app.py`
- `src/streamlit_app/api_client.py`
- `src/streamlit_app/data_workspace.py`
- `src/streamlit_app/reporting_workspace.py`
- `src/streamlit_app/administration_workspace.py`
- `src/streamlit_app/security_workspace.py`
- `src/public/templates/partials/header.html`
- `src/public/templates/partials/footer.html`

### Governance/current-state synchronization
- `automation/STATUS.md`
- `automation/tasks.json`
- `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
- `TECHNICAL_DOCUMENTATION.md`

### New 27A tests
- `tests/test_isi_27a_shared_help_contract.py`
- `tests/test_isi_27a_auth_ux_contract.py`
- `tests/test_isi_27a_public_help_contract.py`

### Narrow inherited-test convergence
- `tests/test_isi_23d_help_xai_contract.py`
- `tests/test_isi_24d_help_xai_contract.py`
- `tests/test_isi_25b_monitoring_xai_help.py`
- `tests/test_isi_17_harness_contract.py`
- `tests/test_isi_27_scope_contract.py`

### Deterministic acceptance evidence written by runner
Only under:
- `automation/evidence/ISI-27A-SHARED-HELP-RELEASE-UX-COMPLETENESS/**`

No other path is mutable.

## Implementation-tool authority
Exactly one runner-mediated invocation of the standard `codex` CLI is authorized.

Codex must:
- read this contract, complete MasterPlan, AGENTS, status/task ledgers, corrected R0-R1 audit, relevant auth/public/workspace/help code and predecessor tests before editing;
- remain in the canonical local `main` worktree;
- not create/switch branches or worktrees;
- not stage, commit, push, dispatch Actions, deploy, contact the server, or access production secrets;
- not edit this installed contract or the copied R0-R1 audit artifacts.

The independent analyzer does not invoke Codex and does not mutate repository state.

## Locked boundaries
- ISI contains only SIMPA and ORDO domain products; do not introduce COSMOS or cross-project behavior.
- No database/Alembic changes.
- No dependency/lockfile changes.
- No FastAPI auth route/service/security/RBAC semantic changes.
- No Compose/Docker/deploy/release/workflow changes.
- No SIMPA/ORDO domain logic, methodology, statistical/forecast/XAI, or domain Help content changes.
- No AI model/prompt/policy changes.
- No production SMTP/server/DNS/certificate/central-Nginx/production-secret/data/server-Ollama action.
- Automatic GitHub Actions triggers remain forbidden; this package dispatches no hosted CI.

## Required behavior

### A. Canonical shared Help contract
Create `src/streamlit_app/shared_help_workspace.py` with exactly twelve canonical topics `ISI-H01` through `ISI-H12`, all `coverage="VERIFIED"`, mapped one-to-one to the twelve corrected release blockers in order:
- H01 A01 Public website
- H02 A02 Login
- H03 A03 Invitation onboarding
- H04 A04 Email verification
- H05 A05 Password reset
- H06 A06 Authenticated app shell
- H07 A08 Data workspace
- H08 A14 Reporting workspace
- H09 A15 Administration workspace
- H10 A16 Account security workspace
- H11 A17 invitation-only / public self-registration absence
- H12 A21 using shared Help + coverage authority

Each topic must contain the same ten substantive fields used by accepted SIMPA/ORDO Help contracts:
`what`, `when`, `roles_permissions`, `steps`, `fields_statuses`, `example`, `non_goals`, `errors_recovery`, `limitations`, `provenance_review`.

Provide:
- full authenticated shared Help rendering;
- public-safe Help rendering that requires no authentication and exposes only public/auth/onboarding/recovery/absence guidance, never private tenant/workspace data;
- a compact topic-summary helper used by contextual workspace Help entry points.

### B. Canonical shared User Guide
Create `docs/help/ISI-SHARED-USER-GUIDE.md` synchronized with `ISI-H01..H12`.

The guide must:
- describe actual as-built UI/API behavior only;
- state institutional access is invitation-only and there is no public signup;
- explain login, invitation, verification and reset one-time-token behavior without exposing token values;
- state UI visibility is not authorization; backend RBAC/product/workspace scope remains authority;
- explain Data, Reporting, Administration and Account Security workflows, permissions, recovery, limitations and provenance/audit boundaries;
- preserve real-provider MFA and production SMTP as deferred/not verified until their existing owner phases;
- explicitly direct SIMPA/ORDO/AI users to the already accepted domain/shared-AI guides for domain methodology/XAI.

### C. Public Help entry point
Do not add a new database-backed public-content model or route.

Use the existing public header/footer seams to add a public Help link to the existing application base URL with the query intent `help=public` (for example `{{ app_url }}?help=public`).

The Streamlit app must recognize `help=public` before authentication and render only public-safe shared Help topics. No login/session token is required to view this public Help. The public site itself remains FastAPI/Jinja2; no public routing architecture change is introduced.

### D. Existing auth lifecycle customer UX
Do not change `src/api/auth_routes.py`, `src/platform/auth/service.py`, `src/platform/auth/delivery.py`, auth models, password policy, token TTLs, enumeration resistance, session revocation rules or invitation authorization semantics.

Complete only the Streamlit/client presentation over the already accepted APIs:

1. `invitation_token` query intent:
   - unauthenticated invitation acceptance form asks only for display name/password required by the existing API;
   - calls existing `POST /api/v1/auth/invitations/accept` through `api_client`;
   - on success stores only the returned session token in the existing session-state authority, removes sensitive invitation query material, and reruns into normal authenticated context;
   - never prints/logs/persists the raw invitation token.

2. `verify_token` query intent:
   - presents an explicit email-verification confirmation action;
   - calls existing `POST /api/v1/auth/email-verification/confirm`;
   - on success clears the sensitive query material and returns user to login guidance;
   - does not create a new session or alter existing auth semantics.

3. `reset_token` query intent:
   - presents a new-password + confirmation form;
   - calls existing `POST /api/v1/auth/password-reset/confirm`;
   - backend remains password-policy/session-revocation authority;
   - on success clears sensitive query material and returns user to login guidance;
   - never prints/logs/persists the raw reset token.

4. Login page recovery entry points:
   - password-reset request by email through existing `POST /api/v1/auth/password-reset/request`;
   - email-verification request by email through existing `POST /api/v1/auth/email-verification/request`;
   - responses remain deliberately neutral/account-enumeration-resistant; UI must not disclose whether an account exists.

5. Public Help:
   - login/onboarding/recovery Help is viewable without auth;
   - no public registration form/button/API is introduced.

If a user is already authenticated, one-time unauthenticated token flows must not silently replace or escalate the existing session. Fail safe and provide clear recovery guidance.

### E. Authenticated shell shared Help
Add an always-available authenticated navigation item with stable code `isi_help` and Serbian label such as `ISI Help`/`Pomoć` without removing or merging product-specific `simpa_help` and `ordo_help`.

`_render_shell` must route `isi_help` to the shared Help workspace. Product-specific Help remains product-isolated and unchanged.

`INV-A06` Help must explain organization/product/workspace selection, role/permission visibility, no-access state, backend authority and human accountability.

### F. Contextual workspace Help
Add compact, non-invasive Help entry points using the shared topic authority:
- Data -> `ISI-H07`
- Reporting -> `ISI-H08`
- Administration -> `ISI-H09`
- Account Security -> `ISI-H10`

Do not duplicate business logic or permission decisions in Help. Contextual Help must not expose data or alter state.

### G. Public self-registration absence
`INV-A17` remains runtime `NOT_PRESENT`.

Requirements:
- no `register`, `signup`, `self-registration`, anonymous tenant join, or account-creation route/form is added;
- public/shared Help explicitly says institutional access is invitation-only;
- tests prove the accepted auth route set still lacks public signup authority;
- Help coverage may be `VERIFIED` because the absence itself is explicit, justified and tested; this does **not** change the inventory runtime STATUS from `NOT_PRESENT`.

### H. Help Coverage Matrix completion
Update only truthful current coverage.

The canonical top-level rows for exactly the corrected twelve blockers must become `VERIFIED`, with concrete Help/test evidence. For A17 the evidence must explicitly say runtime `NOT_PRESENT`, invitation-only, and absence tested.

Preserve VERIFIED status and predecessor evidence for A09/A10/A11/A12/A13/A18/A19. Do not reimplement them.

Keep:
- `INV-A07` non-production-critical and not silently promoted by this slice;
- `INV-A20` `OUT_OF_SCOPE`/`NOT_PRESENT` and non-production-critical.

`INV-A21` may become `VERIFIED` only if every production-critical customer-facing row is VERIFIED as Help coverage or the explicit A17 absence rule is satisfied. Add a 27A material-action section mapping `ISI-H01..H12` to exact tests/evidence.

### I. Inherited-test convergence
Update only stale assertions that intentionally froze pre-27A global Help state:
- ISI-23D and ISI-24D must continue protecting their domain VERIFIED rows and domain isolation, but must no longer require global `INV-A21=PARTIAL` or shared rows non-VERIFIED after accepted 27A implementation.
- ISI-25B must continue protecting shared-AI guide/XAI behavior but must no longer require `REMOVE_IN_NAMED_PHASE(ISI-27)` or global matrix PARTIAL after 27A completes.
- ISI-17/ISI-27 scope governance tests may advance `27A` from `spec_ready` to an evidence-backed implementation-candidate state while preserving the 27A->27B->27C->27D chain.

Do not weaken unrelated predecessor assertions.

### J. Governance/current state
During this unstaged candidate:
- parent `ISI-27` stays `in_progress`;
- active checkpoint stays `ISI-27A-SHARED-HELP-RELEASE-UX-COMPLETENESS`;
- 27A becomes `in_progress` with an explicit implementation-candidate/not-CI-verified note and spec path to this contract;
- 27B/27C/27D remain `planned`;
- ISI-28 remains deferred/server-only;
- do not claim `CI_VERIFIED`, `COMPLETE`, `SERVER_VERIFIED`, production SMTP verification or live deployment.

## Impact
- Database/migrations: **NONE**.
- API backend: **NONE**; existing routes are consumed, not changed.
- UI: shared/public Help entry points; existing one-time auth lifecycle presentation; contextual workspace Help.
- Workers: **NONE**.
- Configuration: **NONE**.
- Dependencies: **NONE**.
- Deployment/workflow: **NONE**.

## Security and privacy
- Never log, display, persist in repository evidence, or echo raw passwords, invitation/reset/verification tokens, session tokens, authorization headers, cookies or production secrets.
- Sensitive one-time query values may exist only as the browser-provided input required to call the existing API; remove them after successful completion.
- Account recovery request responses remain account-enumeration resistant.
- UI must never substitute for backend authorization.
- Help must not disclose cross-tenant/product/workspace data or imply permissions the user lacks.
- No public signup.
- No weakening of rate limits, password policy, session revocation, token expiry/single-use, security events, step-up/MFA foundation or admin controls.

## Tests
Create three focused 27A test authorities:

### `tests/test_isi_27a_shared_help_contract.py`
Must prove at minimum:
- exactly 12 `ISI-H01..ISI-H12` topics, each VERIFIED and all ten required fields non-empty;
- exact mapping to the corrected 12 inventory IDs;
- shared authenticated Help routing exists with code `isi_help`;
- contextual Data/Reporting/Admin/Security Help references exact topic IDs;
- canonical matrix top-level corrected 12 rows are VERIFIED with concrete 27A evidence;
- A07 and A20 are not silently promoted;
- protected predecessor Help rows remain VERIFIED;
- A17 inventory runtime status remains NOT_PRESENT and public signup remains forbidden;
- 27A governance state is in-progress candidate, not CI/server verified.

### `tests/test_isi_27a_auth_ux_contract.py`
Must prove at minimum:
- delivery query keys `invitation_token`, `verify_token`, `reset_token` are recognized by Streamlit UX;
- `api_client` has bounded functions calling the exact existing auth endpoints;
- login recovery requests remain neutral/account-enumeration-safe in UI wording;
- successful sensitive-token flows clear query material;
- invitation acceptance may establish the existing returned session only after success;
- verify/reset flows do not invent session semantics;
- no signup/register route or UI authority exists;
- raw token/password values are not logged or written to evidence.

### `tests/test_isi_27a_public_help_contract.py`
Must prove at minimum:
- public header/footer provide a Help entry point to `help=public`;
- Streamlit public Help is reachable before authentication;
- public Help includes login/invitation/verification/reset/invitation-only guidance;
- private data/workspace content is not required for public Help;
- SIMPA/ORDO Help modules remain product-scoped and unchanged in authority.

Inherited tests may be updated only as described in section I.

## Exact acceptance commands
The package runner performs, fail-closed:
1. package checksum + selftest;
2. exact main/origin/direct-remote/clean/one-worktree preflight;
3. R0-R1 report/evidence SHA verification and byte-identical controlled copy;
4. byte-identical contract install;
5. exactly one `codex exec --sandbox workspace-write --ephemeral` implementation pass;
6. exact mutable-surface validator;
7. protected dependency/migration/deploy/workflow/auth-service/domain-help guards;
8. Python compile + Ruff + full mypy;
9. focused `tests/test_isi_27a_*.py`;
10. targeted inherited public/auth/shell/reporting/admin/security/Help regression set;
11. `tools/ci/policy_check.py` and `git diff --check`;
12. one complete local pytest regression;
13. deterministic validator evidence + candidate fingerprint;
14. confirm HEAD/origin remain baseline and index remains empty.

Native PostgreSQL acceptance is intentionally not rerun in 27A because this exact surface cannot modify schema, DB services, migrations, FastAPI auth services/routes or persistence semantics. Exact-main native PostgreSQL remains mandatory later at the owner-approved 27D release-candidate hosted acceptance checkpoint.

## Evidence
Runner-generated repository-local evidence only under:
`automation/evidence/ISI-27A-SHARED-HELP-RELEASE-UX-COMPLETENESS/`

At minimum:
- `candidate-files.txt`
- `manifest.json`
- `help-coverage-summary.json`
- `candidate-diff.sha256`

Evidence must state:
- baseline SHA/tree;
- corrected R0-R1 audit SHAs;
- exact candidate path set;
- corrected 12 coverage state;
- protected predecessor Help state;
- A17 `NOT_PRESENT` runtime boundary;
- `GITHUB_ACTIONS_DISPATCH=NO`;
- `SERVER_MUTATION=NO`;
- `STAGE_COMMIT_PUSH=NO`;
- `CI_VERIFIED=NO`;
- `SERVER_VERIFIED=NO`.

Evidence must never contain raw auth/session secrets.

## Non-goals
- public self-registration;
- new auth backend or security policy;
- new role/permission/entitlement behavior;
- SMTP/server validation;
- MFA provider integration;
- DB/schema migration;
- SIMPA/ORDO methodology/runtime/Help rewrite;
- AI model/eval/promotion changes;
- report/data/admin/security business-rule changes;
- release SBOM/attestation/image scanning (27C);
- hosted exact-main RC acceptance (27D);
- production deployment/server verification (ISI-28).

## Forbidden changes
- `.github/**`
- `migrations/**`, `alembic.ini`
- `pyproject.toml`, `requirements*.lock`
- Docker/Compose/deploy/release/server tooling
- `src/api/auth_routes.py`
- `src/platform/auth/**`
- `src/platform/access/**`
- `src/platform/administration/**`
- `src/platform/security/**`
- `src/platform/data/**`
- `src/platform/reporting/**`
- `src/domains/**`
- `src/streamlit_app/simpa_help_workspace.py`
- `src/streamlit_app/ordo_help_workspace.py`
- `docs/help/SIMPA-USER-GUIDE.md`
- `docs/help/ORDO-USER-GUIDE.md`
- `docs/help/ISI-AI-USER-GUIDE.md`
- any server/network/production-secret access
- staging, commit, push or GitHub Actions dispatch.

## Human review and owner gate
After deterministic runner acceptance:
1. independent analyzer (no Codex, no mutation);
2. assistant human review of the exact candidate/evidence;
3. explicit owner approval of the reviewed exact path set/fingerprint;
4. only then a separate exact staging/commit/normal-push finalizer may be created.

A development push does not authorize hosted CI. 27D later requires a separate explicit owner approval before manual `release-candidate` Actions dispatch.

## Completion definition
This R1 candidate is `IMPLEMENTED` only when the package runner passes all local deterministic gates and produces a stable fingerprint while remaining unstaged/uncommitted.

`REVIEW_VERIFIED` requires independent analysis plus assistant human review of that exact fingerprint with no unresolved blocker.

27A becomes accepted on main only after explicit owner-approved exact staging/commit/normal push and remote equality.

27A does **not** become `CI_VERIFIED` or overall ISI-27 `COMPLETE` at that point; hosted exact-main RC qualification belongs to 27D.

## Deferred server verification
`DEFERRED_SERVER_VERIFICATION` — all live server/deployment/capacity verification remains ISI-28-only.
