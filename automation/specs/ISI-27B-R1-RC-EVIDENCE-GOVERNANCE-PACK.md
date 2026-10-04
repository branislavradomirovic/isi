# ISI-27B R1 — exact-candidate evidence and governance

## Locked implementation contract

Baseline: canonical main `c177f9d705efd6f68d95ef7d13847b03a8e19229`.
Owner has approved continuing all release work, reviewed-candidate commit/push,
and final ISI deployment. This slice implements the already approved 27B scope.
27C, 27D and ISI-28 retain their separate gates and sequencing.

## Reconciliation

DONE: accepted 27A and public portal remediation (c177f9d); clean synchronized
main; existing domain/security/privacy/native migration/recovery authorities.
PARTIAL: individual predecessor evidence needs exact-candidate consolidation.
MISSING: consolidated 27B pack; reproducible signed release/image SBOM (27C);
exact-main hosted acceptance (27D); current server acceptance (28).
DRIFT: predecessor tests freeze live checkpoint state. Those assertions are
REMOVE_BEFORE_NEXT_SLICE when checkpoint promotion occurs, and must be migrated
to dependency-aware validation without changing historical acceptance facts.
Historical deployment scripts are REMOVE_IN_NAMED_PHASE(ISI-28); synthetic
evaluation fixtures are REQUIRED_COMPATIBILITY, never production promotion proof.

## Exact mutable surface

- this contract
- tools/release/evidence.py
- tools/qa/run_isi27b.py
- tools/qa/analyze_isi27b.py
- tests/test_isi_27b_release_evidence.py
- docs/release/ISI-RC-GOVERNANCE-PACK.md
- docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md
- TECHNICAL_DOCUMENTATION.md
- automation/STATUS.md
- automation/tasks.json
- .gitignore
- tests/test_isi_21_native_postgres.py
- tools/ci/native_postgres_tests.sh
- tools/ci/isi19_recovery_rehearsal.sh

Canonical system inventory impact: new INV-M20 development evidence authority.
No domain, runtime, numerical, authentication or production configuration changes.

## Acceptance contract

The deterministic runner executes full local pytest, isolated native PostgreSQL
17 migrations and recovery, existing ISI-26 performance catalogue, policy and
diff checks. It records real exit codes and immutable report hashes, verifies
the source fingerprint did not change, and generates separate SIMPA/ORDO
methodology acceptance and model/evaluation provenance manifests. XML failures,
empty/missing suites, skipped native tests, incomplete performance scenarios,
invalid recovery or source changes fail closed. Independent analysis checks
the exact source and report hashes without executing or mutating code or Git.

Output is an exclusive newly created directory beneath
automation/evidence/ISI-27B/. Never overwrite an existing evidence pack.
Source identity includes all tracked and nonignored candidate files and deletions.
No database dump, raw institutional data or credential is copied into the pack.

Repository methodology acceptance proves lifecycle/reference/model contracts
using synthetic tests. It does not certify live institutional methodology or
model registry state. Evaluation foundation fixtures must explicitly remain
non-production and insufficient for model promotion. Native tests supply real
PostgreSQL evidence separately from the full suite's intentional native skips.

Completion requires all gates, read-only independent analysis and review. This
slice cannot claim CI_VERIFIED, production capacity or SERVER_VERIFIED.

## R1 recovery — observed deterministic blockers

The first runner completed all commands, then rejected generated native reports
as source drift: `test-results/` was not ignored. Add only that generated-output
ignore rule; retain the outputs locally. The native report also exposed one
inherited conditional skip when no active workspace exists. Classify it
REMOVE_BEFORE_NEXT_SLICE and replace reliance on shared mutable database state
with a transaction-owned synthetic organization/user/membership/workspace.
Keep every existing schema/privacy assertion and rollback the fixture. The final
runner must repeat all acceptance against the corrected exact source.

The first corrected native execution exposed the previously skipped fixture's
missing SIMPA reference product. Bootstrap the existing canonical reference
catalog inside the same rolled-back fixture transaction; do not relax its FK.

Targeted native reruns exposed a startup race: the temporary PostgreSQL init
server accepts Unix-socket probes before stopping. Both disposable CI/recovery
readiness probes must use loopback TCP, which only the final server exposes.
This is bounded deterministic harness recovery, not a production change.
Replace GNU-only mapfile with the equivalent Bash 3.2-compatible array loop in
that same native harness; no new workstation dependency is introduced.

Final command gates then passed, but consolidation rejected JSONL corrupted by
stderr warnings interleaved with stdout. Capture stderr in separate companion
files for every gate. Preserve strict JSON parsing and fingerprint validation;
do not filter, suppress or silently drop malformed evidence records. Add a
deterministic stream-separation test and repeat final exact-source acceptance.

All final gates and content verification passed (1070 regression, 45 native,
10 performance scenarios), but independent surface analysis then incorrectly
rejected pre-existing Markdown hard breaks in tracked technical documentation.
For tracked files check changed lines with git diff --check; for new files check
the whole new file. Preserve historical bytes. Run that scope preflight before
the deterministic gate cycle, and repeat the final exact-source evidence pack.

Historical implementation contract. Accepted on main `16a928b20907d570df2cf05101a969e1f0cda736` after local acceptance and review. Locked baseline analyzers are historical candidate tools; later release assembly owns new exact-source consolidation. NOT CI_VERIFIED / DEFERRED_SERVER_VERIFICATION.
