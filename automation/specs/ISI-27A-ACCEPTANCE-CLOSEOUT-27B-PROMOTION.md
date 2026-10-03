# ISI-27A Acceptance Closeout + ISI-27B Promotion Contract

## Authority

Accepted ISI-27A main SHA: `74acd5d9a890733347554633f44a6d5319717ba3`.
Accepted tree: `a69b8582a77555611b64a5527548e67a5b0c45cb`.
Accepted candidate fingerprint: `01ed26dd8e1193606f17c097f88ba0fd68b4f3ce2127de0845468998d3dc8d64`.
Independent analysis + human review: PASS / REVIEW_VERIFIED.
Local deterministic acceptance: 1030 passed, 43 skipped, 0 failed.

## Purpose

Record the already-accepted ISI-27A implementation on canonical `main` and move the live governance checkpoint to ISI-27B. This is governance-only synchronization. It does not introduce runtime behavior.

## Exact mutable surface

- `automation/tasks.json`
- `automation/STATUS.md`
- `TECHNICAL_DOCUMENTATION.md`
- `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
- `automation/specs/ISI-27A-ACCEPTANCE-CLOSEOUT-27B-PROMOTION.md`
- `automation/specs/ISI-27A-ACCEPTANCE-CLOSEOUT-EVIDENCE.json`
- `tests/test_isi_17_harness_contract.py`
- `tests/test_isi_26_governance_contract.py`
- `tests/test_isi_27_scope_contract.py`
- `tests/test_isi_27a_shared_help_contract.py`

## Required resulting state

- Parent ISI-27 remains `in_progress`.
- Parent active checkpoint becomes `ISI-27B-RC-EVIDENCE-GOVERNANCE-PACK`.
- ISI-27A becomes `done` and records exact accepted SHA/tree/fingerprint.
- ISI-27B becomes `spec_ready` and remains non-CI-verified.
- ISI-27C and ISI-27D remain `planned`.
- ISI-28 remains `deferred`.
- `CI_VERIFIED=NO`, `SERVER_VERIFIED=NO`, `GITHUB_ACTIONS_DISPATCH=NO`, `SERVER_MUTATION=NO` remain binding.

## Forbidden

No runtime/application code, auth, domain, Help content, workflow, migration, dependency, Docker/Compose, release builder, deployment or server path may change. No Codex call. No staging, commit, push or hosted Actions dispatch.


## Independent-review R1 governance consistency recovery — 2026-10-03

Independent review found stale live/current-state duplicates outside `automation/tasks.json`: the live status ledger still named ISI-26 as the last accepted slice, the phase table and technical/MasterPlan current-checkpoint text still described 27A as the active implementation candidate, and the pre-acceptance candidate block was not explicitly marked historical. R1 synchronizes those live authorities to accepted 27A / active 27B, labels the old candidate block as historical, and strengthens governance assertions. No runtime/auth/domain/Help/workflow/dependency/server semantics change.

## Independent-review R2/R3/R4 final closeout recovery chain — 2026-10-03

- R2 removed one trailing-whitespace defect in `TECHNICAL_DOCUMENTATION.md`; no semantic state changed.
- R3 aligned the accepted-main closeout date with GitHub commit creation `2026-10-02T22:18:25Z`, which is `2026-10-03` in `Europe/Belgrade`, and added a fail-closed date assertion.
- R4 resolved the final stale live pointers outside the explicitly historical dated owner-approval record: the live ISI-26 registry note and current Phase-24/Phase-25 status paragraphs now state that ISI-27A is accepted and ISI-27B is current.
- The dated `2026-10-01 ISI-25B closure and shared-ingress governance reconciliation` record remains unchanged as legitimate historical truth.
- No runtime, auth, domain, Help, workflow, dependency, migration, deployment or server semantics changed in R2/R3/R4.

## R4-R1 historical-ledger validation and remaining live-summary recovery — 2026-10-03

R4 reached its exact ten-path target fingerprint before `validate-r4.py` failed.
Both that validator and the new repository test mistakenly forbade the historical
27A-current sentence globally, although R4 intentionally retained it in the dated
owner-approval record. This is a validation-scope defect, not authorization to
delete or rewrite history. R4-R1 checks the current Phase-24/25 sections and live
predecessor notes, permits exactly one historical occurrence, and pins the whole
dated section to SHA256 `52747042e67f3c21fb8a8b2be10f8a91688fcbba9833a621ad9e06605211bb87`
inside `## 11. Owner approval record`.

The mandatory audit additionally found four remaining live summaries: the
ISI-25 parent note still said ISI-26 was current/next; the ISI-26 STATUS summary
still named 27A as next; Technical Documentation section 15 still described
shared Help as a local 27A candidate; and INV-A21 retained the same candidate
wording. All four now record accepted 27A/current 27B while retaining the open
27B/27C/27D release gates and every hosted/server limitation.

R4-R1 changes seven paths within the existing ten-path closeout surface:
`automation/tasks.json`, `automation/STATUS.md`, `TECHNICAL_DOCUMENTATION.md`,
the Master Plan INV-A21 narrative, this contract, closeout JSON evidence and
`tests/test_isi_27_scope_contract.py`. The three other test files remain
byte-identical to R4. The dated historical ledger and the two R4-corrected
Phase-24/25 sections remain byte-identical to R4. No runtime, auth, domain,
Help content, workflow, dependency, migration, deployment or server file changes.

Canonical system inventory impact: NONE. INV-A21 remains CURRENT_AS_BUILT with
the same paths, test authority, ownership and scope; only acceptance wording is
reconciled to the already accepted implementation.

The repository guard includes 21 negative controls for stale live pointers,
missing/duplicate section anchors, historical deletion/tampering/relocation,
stale Help summaries and premature release/server-state promotion. No test is
skipped, weakened or bypassed. Required focused checks, original quality/policy
commands and one full local regression remain mandatory. Candidate readiness
is established only by the runner and read-only analyzer; independent human
review and explicit owner approval of an exact commit remain separate gates.

No Codex CLI call, staging, commit/push, hosted dispatch or server action is
authorized. This recovery does not start ISI-27B implementation.
