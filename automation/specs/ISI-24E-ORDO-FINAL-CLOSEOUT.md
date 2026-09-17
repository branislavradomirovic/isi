# ISI-24E — ORDO Final Whole-Phase Gap/Legacy Audit + Closeout

Task ID: **ISI-24E**

Status: **OWNER-SCOPE-FROZEN BOOTSTRAP / AUDIT CONTRACT**

## Status
ISI-24E is the current final ORDO production-methodology audit/closeout slice. This document does not itself claim overall ISI-24 COMPLETE.

## Baseline
- Repository: `branislavradomirovic/isi`
- Canonical local repository: `$HOME/Applications/Python/ISI`
- Branch: `main`
- Accepted ISI-24D SHA: `49377e808845fc8746f0484ea7b452954c9e83b4`
- Accepted ISI-24D tree: `c8ea52299d80551ee303dbeef95d343b59448892`
- Exact-main CI: `ISI required acceptance` run #88 / `35220908672` / `completed success`
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
Transition impact: NONE to inventory statuses. `INV-A19` remains `CURRENT_AS_BUILT`; `INV-A21` remains globally partial until later shared Help work. Any audit-discovered inventory drift must be explicitly classified before remediation.

## Legacy/drift audit
Mandatory whole-phase audit includes at minimum:
- stale current-slice/status/task/spec wording;
- stale historical phase captions in user-facing ORDO screens (including the accepted-main `ISI-11` caption seed finding);
- historical tests that freeze mutable global current state;
- obsolete/duplicate ORDO routes/services/schema/configuration;
- unsupported forecast/scenario presentation or execution claims;
- Help/User Guide claims not backed by runtime;
- raw-source bypass of governed analytical boundaries;
- stale flags/environment variables/dependencies;
- accidental ISI-25 model-promotion/evaluation semantics;
- deployment/server authority drift.

Every finding is exactly one of: `LEGITIMATE_HISTORY`, `REQUIRED_COMPATIBILITY`, `REMOVE_BEFORE_NEXT_SLICE`, `REMOVE_IN_NAMED_PHASE(<phase>)`.

## Exact mutable surface
This activation/transition candidate may modify/create exactly:
1. `automation/STATUS.md`
2. `automation/tasks.json`
3. `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
4. `automation/specs/ISI-24E-ORDO-FINAL-CLOSEOUT.md`
5. `tests/test_isi_24c_governance_contract.py`
6. `tests/test_isi_24d_help_xai_contract.py`
7. `tests/test_isi_17_harness_contract.py`
8. `tests/test_isi_24e_closeout_contract.py`

This is NOT the remediation surface. If audit findings require product/code changes, a separate exact remediation surface must be frozen before implementation.

## Implementation-tool authority
No Codex is authorized for this transition/audit activation candidate. Read-only audit does not spend Codex tokens.

## Locked boundaries
- overall ISI-24 stays `IN PROGRESS`;
- ISI-25 stays `PLANNED`;
- `INV-A19` remains `CURRENT_AS_BUILT`;
- `INV-A21` remains globally partial;
- no server/DNS/ingress/production mutation;
- no new methodology/formula/threshold/causal response coefficient;
- no automatic model selection/promotion/fallback.

## Required behavior
Governance must record the accepted 24D SHA/tree/run, make 24E current, and keep historical 24C/24D tests focused on their accepted contracts rather than freezing mutable global-current state.

## Impact
Governance/test-only transition. No runtime, API, schema, migration, dependency, workflow or deployment behavior changes.

## Security and privacy
No production data/secrets/provider credentials are accessed. Existing tenant/product authorization boundaries remain unchanged.

## Tests
- dedicated 24E transition contract;
- historical 24C/24D governance contracts remain green without global-current freeze;
- ISI-17 harness/policy remain green;
- full Python regression;
- `git diff --check`;
- Alembic sole-head verification.

## Exact acceptance commands
Use the deterministic transition runner and independent analyzer supplied outside the repository. No staging/commit/push occurs in the transition package.

## Evidence
Accepted 24D: SHA `49377e808845fc8746f0484ea7b452954c9e83b4`, tree `c8ea52299d80551ee303dbeef95d343b59448892`, run #88 / `35220908672`, success.

## Non-goals
No final 24E remediation, no overall ISI-24 completion, no ISI-25 work, no deployment.

## Forbidden changes
Backend/API/schema/migrations/dependencies/workflow/server changes are forbidden in this activation candidate.

## Human review and owner gate
Candidate remains unstaged/uncommitted after deterministic validation and independent analysis. Exact staging/commit/push requires fresh explicit owner approval after assistant human review.

## Completion definition
This activation step is complete only when 24D accepted history is synchronized, 24E is current, exact eight-path candidate passes tests/analyzer, and human review finds no transition blocker. ISI-24E itself is not COMPLETE until the whole-phase audit/remediation/closeout later passes exact-main CI.

## Deferred server verification
Server/live-host verification and all production mutation remain deferred to owner-approved ISI-28.
