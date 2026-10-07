# TASK-ID — Title

## Status
`DRAFT` | `SPEC_READY` | `OWNER_APPROVED`

## Baseline
Exact commit SHA, tree SHA, `origin/main` relation, exact-main CI evidence and compatibility baseline.

## Canonical bootstrap evidence
Proof that the complete MasterPlan, AGENTS, task/status ledgers, relevant ADR/spec/ops documents and actual as-built code were reviewed before implementation. Include `DONE / PARTIAL / MISSING / DRIFT`.

## Dependencies
Task IDs, approvals, data or methodology inputs.

## Objective
Evidence-verifiable outcome.

## Existing architecture
Relevant modules, contracts, data/control flow and accepted ADR/owner decisions.

## Legacy/drift audit
List every relevant finding and classify it as `LEGITIMATE_HISTORY`, `REQUIRED_COMPATIBILITY`, `REMOVE_BEFORE_NEXT_SLICE`, or `REMOVE_IN_NAMED_PHASE(<phase>)`. Unclassified incompatible legacy blocks implementation.

## Exact mutable surface
Enumerate every repository path Codex/implementation may modify. Everything else is immutable for the task unless the owner approves a scope change.

## Canonical system inventory impact
Identify every affected `INV-*` row in the MasterPlan and describe the required status/path/responsibility/boundary/test/legacy update. If there is no impact, write `Canonical system inventory impact: NONE` and explain why.

## Implementation-tool authority
State whether Codex is required. If yes, use standard `codex` with the canonical owner Outlook account, locked MD contract + runner + independent analyzer, per the superseding 2026-09-19 owner decision; no staging, commit, push, deploy or production secrets.

## Locked boundaries
Product, tenant, authorization, technology and human-review invariants.

## Required behavior
Numbered, testable requirements.

## Impact
- Database/migrations:
- API:
- UI:
- Workers:
- Configuration:

## Security and privacy
Threat boundaries, sensitive-data handling, authorization and audit requirements.

## Tests
New and regression coverage; tests must not be weakened, skipped, xfailed or deleted.

## Exact acceptance commands
Non-interactive, fail-closed commands.

## Evidence
Required files under `automation/evidence/<TASK-ID>/`, including commits, commands, results and deferrals.

## Non-goals
Explicit exclusions.

## Forbidden changes
Actions the implementation may not perform.

## Human review and owner gate
Define the assistant human-review evidence and explicit owner approval required before exact-file staging/commit/push.

## Completion definition
Deterministic criteria for `IMPLEMENTED`, `REVIEW_VERIFIED`, owner-approved main commit/push, exact-main `CI_VERIFIED`, and `COMPLETE`.

## Deferred server verification
State `DEFERRED_SERVER_VERIFICATION` unless server work is explicitly owner-approved.
