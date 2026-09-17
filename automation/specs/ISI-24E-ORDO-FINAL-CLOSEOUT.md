# ISI-24E — ORDO Final Whole-Phase Gap/Legacy Audit + Closeout

Task ID: **ISI-24E**

Status: **OWNER-SCOPE-FROZEN F01/F02 IMPLEMENTATION CANDIDATE / NOT COMPLETE / NOT CI_VERIFIED**

## Status
ISI-24E remains the current final ORDO production-methodology slice. This F01/F02 remediation candidate does not claim overall ISI-24 COMPLETE or CI_VERIFIED, and ISI-25 remains PLANNED.

## Baseline
- Repository: `branislavradomirovic/isi`
- Canonical local repository: `$HOME/Applications/Python/ISI`
- Branch: `main`
- Accepted transition baseline SHA: `dac9f488ad650330ce258d44617d4b897a31f6aa`
- Accepted transition baseline tree: `bb78978298cd5232cf402c03c9949e20804bd7bc`
- Exact-main CI: `ISI required acceptance` run #89 / `35227300000` / `completed success`
- Alembic sole head: `20260916_0032`

## Canonical bootstrap evidence
Read the complete MasterPlan, `AGENTS.md`, tasks/status ledgers, ORDO methodology baseline, Help coverage matrix, accepted ISI-24A/B/C/D contracts and actual ORDO code/tests before any remediation contract is frozen.

## Dependencies
ISI-24A, ISI-24B, ISI-24C and ISI-24D are accepted exact-main checkpoints. ISI-25 remains planned and MUST NOT be pulled into 24E.

## Objective
Perform the mandatory whole-phase `DONE / PARTIAL / MISSING / DRIFT` audit for every ISI-24 acceptance requirement, customer-facing ORDO workflow, relevant system-inventory row, Help/XAI requirement and legacy/compatibility surface. Resolve or explicitly classify every blocker before final phase closeout.

## Existing architecture
Preserve the accepted ORDO architecture: governed evidence/methodology, deterministic descriptive/spatial/statistical/time-series/forecast authorities, separate forecast/scenario semantics, bounded AI synthesis with human review, and repository/in-app Help/XAI.

## Canonical system inventory impact
No new component, status, ownership boundary, persistence family or model family is introduced. The candidate makes the already accepted `INV-A13`, `INV-C37` and `INV-C38` authorities customer-reachable in place and extends their Help/test evidence. The owner-frozen surface explicitly excludes the MasterPlan, so final inventory wording synchronization is deferred to the separate post-CI closeout/transition candidate. `INV-A19` remains `CURRENT_AS_BUILT`; `INV-A21` remains PARTIAL.

## R1 legacy/drift audit outcome
R1 found 14 requirements DONE and exactly three findings:

- F01: `DRIFT / REMOVE_BEFORE_NEXT_SLICE` - stale user-facing `ISI-11 povezuje` current-product caption;
- F02: `PARTIAL / REMOVE_BEFORE_NEXT_SLICE` - the accepted forecast runtime was not reachable as a complete governed customer workflow;
- F08: `PARTIAL / REMOVE_IN_NAMED_PHASE(ISI-25/ISI-27)` - global cross-product Help remains intentionally incomplete.

F01 and F02 are the only remediation targets. F08 stays deferred. Accepted 24A-D contracts/results are `LEGITIMATE_HISTORY` or `REQUIRED_COMPATIBILITY`; the 24B locked booleans, 24C ESTIMATED/NOT_ESTIMATED semantics and forecast/scenario separation remain authoritative.

## Exact mutable surface - FROZEN 12
This remediation candidate may modify/create exactly:
1. `automation/specs/ISI-24E-ORDO-FINAL-CLOSEOUT.md`
2. `docs/help/ISI-HELP-COVERAGE-MATRIX.md`
3. `docs/help/ORDO-USER-GUIDE.md`
4. `src/api/ordo_analytics_routes.py`
5. `src/domains/ordo/analytics_schemas.py`
6. `src/domains/ordo/analytics_service.py`
7. `src/streamlit_app/ordo_analytics_api.py`
8. `src/streamlit_app/ordo_analytics_workspace.py`
9. `src/streamlit_app/ordo_help_workspace.py`
10. `tests/test_isi_24e_closeout_contract.py`
11. `tests/test_isi_24e_forecast_workflow_api.py`
12. `tests/test_isi_24e_forecast_workflow_ui.py`

## F02 implementation decision and RBAC
Expose the accepted time-series specification lifecycle and 24C runtime as one governed customer workflow. `analysis.read` controls spec list/detail and series-identity discovery plus persisted forecast reads; `indicator.manage` controls create/propose/validate/retire; `analysis.run` controls forecast execution. There is no `analysis.review` permission.

Authoring accepts only customer-controlled `OrdoTimeSeriesSpecV1` fields plus exact scope/run identity. The service resolves the current validated indicator methodology and injects its ID/version/fingerprint and locked booleans. Lifecycle routes prove the path specification belongs to the payload organization/workspace before mutation. Identity discovery reuses the forecast binding revalidation and returns only deterministic unique key/value combinations.

## Locked boundaries
- overall ISI-24 stays `IN PROGRESS`;
- ISI-25 stays `PLANNED`;
- `INV-A19` remains `CURRENT_AS_BUILT`;
- `INV-A21` remains globally partial;
- no server/DNS/ingress/production mutation;
- no new methodology/formula/threshold/causal response coefficient;
- no automatic model selection/promotion/fallback.
- no migration, model/table, dependency, workflow, ISI-25 or server expansion;

## Required behavior
Remove F01 wording. Add scope-safe spec list/detail/create/propose/validate/retire and series-identity discovery APIs, Streamlit wrappers, and a permission-aware UI that authors specifications, performs human lifecycle transitions, executes only a selected VALIDATED spec plus discovered identity and explicit candidate family/accepted interval, and refreshes persisted XAI results. Preserve the existing forecast POST/list/detail routes and accepted engine semantics.

## Impact
API/service and Streamlit workflow expansion over existing persistence/runtime only. No schema, migration, model-family, dependency, CI workflow or deployment change.

## Security and privacy
No production data/secrets/provider credentials are accessed. Existing tenant/product authorization boundaries remain unchanged.

## Tests
- extend `tests/test_isi_24e_closeout_contract.py` for remediation truth and current status boundaries;
- add `tests/test_isi_24e_forecast_workflow_api.py` for paths, strict server-authoritative authoring, scope and permission/runtime invariants;
- add `tests/test_isi_24e_forecast_workflow_ui.py` for client/UI/Help/User Guide/matrix behavior;
- retain relevant 24B/24C/24D compatibility and `git diff --check`; Alembic remains `20260916_0032`.

## Exact acceptance commands
Use the deterministic transition runner and independent analyzer supplied outside the repository. No staging/commit/push occurs in the transition package.

## Evidence
Accepted 24D: SHA `49377e808845fc8746f0484ea7b452954c9e83b4`, tree `c8ea52299d80551ee303dbeef95d343b59448892`, run #88 / `35220908672`, success.

## Non-goals
No overall ISI-24 completion, no ISI-25 champion/challenger/evaluation/promotion/fallback work, no new forecast family/engine change, no causal/policy/ranking/confidence claim, no global F08 Help completion and no deployment.

## Forbidden changes
No migrations/models/dependencies/CI workflow/server configuration, staging, commit, push, deployment or production secrets/data.

## Human review and owner gate
Candidate remains unstaged/uncommitted after deterministic validation and independent analysis. Exact staging/commit/push requires fresh explicit owner approval after assistant human review.

## Completion definition
This candidate remains `IN PROGRESS / NOT COMPLETE / NOT CI_VERIFIED` even after local gates pass. Final accepted remediation evidence and transition to ISI-25 require a separate owner-approved closeout/transition candidate after exact-main CI.

## Deferred server verification
Server/live-host verification and all production mutation remain deferred to owner-approved ISI-28.
