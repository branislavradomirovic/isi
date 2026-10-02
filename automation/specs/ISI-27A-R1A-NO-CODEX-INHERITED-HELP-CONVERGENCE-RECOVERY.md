# ISI-27A-R1A — No-Codex Inherited Help Test Convergence Recovery

## Status
`RECOVERY_READY / OWNER_EXECUTION_REQUIRED / NO_CODEX`

## Baseline
- canonical repository: `/Users/branislavradomirovic/Applications/Python/ISI`
- branch: `main`
- accepted scope-lock baseline HEAD/origin/direct remote: `39dc1d59a74a03c86f68df093cc07e32d41d028c`
- tree: `3c7027b375b041043f7305cdab008aee35f16ef7`
- R1 implementation was interrupted only because the Codex workspace exhausted credits after 241,508 tokens.

## Proven R1 prestate
Before the credit interruption the R1 candidate had already demonstrated:
- 59/59 new ISI-27A tests passing;
- targeted regression: 298 passed, 11 skipped;
- compile/Ruff/mypy/policy/git-diff-check passing;
- exact R1 mutable surface passing, copied R0-R1 audit hashes passing, index empty, HEAD/origin unchanged;
- no staging, commit, push, hosted Actions dispatch, server mutation or production-secret access.

The full local suite had not reached a formal PASS. Codex identified stale inherited Help assertions and then exhausted workspace credits before reporting final full-suite closure.

## Objective
Preserve the existing unstaged R1 implementation candidate and, without any Codex invocation, converge only four historical predecessor tests that freeze the former global `INV-A21=PARTIAL` state. Then execute deterministic focused/quality/full-local acceptance and emit a human-review bundle.

## Canonical current Help authority
The current top-level `docs/help/ISI-HELP-COVERAGE-MATRIX.md` may legitimately promote the corrected ISI-27A production-critical shared Help rows and `INV-A21` to `VERIFIED` when backed by the R1 implementation/tests. Historical SIMPA/ORDO checkpoint facts remain historical; this recovery must not rewrite domain methodology, domain Help/XAI, or accepted prior-phase CI facts.

## Exact R1 prestate surface
The recovery must start with exactly the following 26 unstaged/uncommitted paths and an empty index:

- `TECHNICAL_DOCUMENTATION.md`
- `automation/STATUS.md`
- `automation/tasks.json`
- `docs/help/ISI-HELP-COVERAGE-MATRIX.md`
- `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
- `src/public/templates/partials/footer.html`
- `src/public/templates/partials/header.html`
- `src/streamlit_app/administration_workspace.py`
- `src/streamlit_app/api_client.py`
- `src/streamlit_app/app.py`
- `src/streamlit_app/data_workspace.py`
- `src/streamlit_app/reporting_workspace.py`
- `src/streamlit_app/security_workspace.py`
- `tests/test_isi_17_harness_contract.py`
- `tests/test_isi_23d_help_xai_contract.py`
- `tests/test_isi_24d_help_xai_contract.py`
- `tests/test_isi_25b_monitoring_xai_help.py`
- `tests/test_isi_27_scope_contract.py`
- `automation/specs/ISI-27A-R0-R1-SHARED-HELP-SURFACE-AUDIT-EVIDENCE.json`
- `automation/specs/ISI-27A-R0-R1-SHARED-HELP-SURFACE-AUDIT-REPORT.md`
- `automation/specs/ISI-27A-R1-SHARED-HELP-RELEASE-UX-COMPLETENESS.md`
- `docs/help/ISI-SHARED-USER-GUIDE.md`
- `src/streamlit_app/shared_help_workspace.py`
- `tests/test_isi_27a_auth_ux_contract.py`
- `tests/test_isi_27a_public_help_contract.py`
- `tests/test_isi_27a_shared_help_contract.py`

## R1A authorized surface expansion
Only these five new candidate paths are authorized beyond the exact R1 prestate:
- `automation/specs/ISI-27A-R1A-NO-CODEX-INHERITED-HELP-CONVERGENCE-RECOVERY.md` — runner-installed recovery authority.
- `tests/test_isi_23e_simpa_closeout.py`
- `tests/test_isi_23e_simpa_synthetic_e2e.py`
- `tests/test_isi_24e_closeout_contract.py`
- `tests/test_isi_24e_forecast_workflow_ui.py`

Generated deterministic evidence may be written only below:
- `automation/evidence/ISI-27A-SHARED-HELP-RELEASE-UX-COMPLETENESS/R1A/**`

No other repository path may change.

## Required recovery changes
1. Preserve all already accepted/historical SIMPA and ORDO phase facts.
2. Replace only predecessor assertions that freeze the old global Help status:
   - `INV-A21` current top-level coverage becomes `VERIFIED` rather than `PARTIAL`.
   - predecessor tests must still require SIMPA/ORDO-owned rows to remain `VERIFIED`.
   - no test may weaken or remove domain methodology, authorization, XAI, provenance, forecast/scenario, or CI-history assertions.
3. Where a test name/text says the global matrix must not upgrade, rename/reword only that historical-current-state assertion so it accurately follows current canonical matrix authority.
4. Preserve `INV-A17=NOT_PRESENT` and invitation-only onboarding. Never add public signup.
5. Update only the already-mutated 27A governance notes to record that R1A authorizes the four inherited-test convergence paths; do not claim `CI_VERIFIED`, `SERVER_VERIFIED`, ISI-27 completion, or production deployment.
6. Do not change runtime code during R1A. The existing R1 runtime candidate is frozen for this recovery.

## Forbidden
- any Codex call;
- stage/commit/push;
- branch/worktree creation;
- `.github`, dependency, lockfile, migration, Compose/Docker, release/deploy/server changes;
- FastAPI auth service/routes, platform auth/access/security/data/reporting service changes;
- `src/domains/**` changes;
- SIMPA/ORDO/AI Help authority changes;
- production SMTP, server, DNS, ingress, secrets, production data, Ollama/model mutation;
- public self-registration;
- test deletion, skip, xfail or semantic weakening.

## Acceptance
- exact R1 prestate and baseline PASS before patch;
- R0-R1 audit copied hashes remain exact:
  - report `77a2a0ac6d9d95e31eda6f9bc9eb8f439711c5aafeff97db8ee33d6e36fb3c25`
  - evidence `1cac5fb07c8d3e9580d8013f58095f87c595ebb80d3022cdd56bb253130e7907`
- R1 original contract remains byte-identical to package-installed authority;
- four inherited convergence tests pass with all new 27A tests;
- compile/Ruff/mypy/policy/git diff check pass;
- one full local `python -m pytest --tb=short` pass;
- exact final candidate surface = 31 paths plus generated R1A evidence prefix;
- index remains empty;
- no Codex, GitHub Actions dispatch, server mutation, stage/commit/push;
- human-review ZIP emitted to `$HOME/Downloads` only after all acceptance gates pass.

## Completion boundary
R1A PASS means `IMPLEMENTED / READY_FOR_INDEPENDENT_ANALYSIS`, not `CI_VERIFIED` and not `SERVER_VERIFIED`. Staging/commit/push remains a later explicit owner gate after independent analysis and assistant human review.
