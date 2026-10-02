# ISI-27 — Industrial Release Candidate Scope Lock

## Status
`OWNER_APPROVED SCOPE ARCHITECTURE / GOVERNANCE-ONLY CANDIDATE`

## Canonical baseline
- Repository: `branislavradomirovic/isi`
- Branch: `main`
- Exact baseline SHA: `e46128752e29f46dc6d9b8510198739f88da50e9`
- Exact baseline tree: `bc73ca23303d3f3353d440203f96dd698bf42b35`
- ISI-26: `IMPLEMENTATION COMPLETE / ACCEPTED ON MAIN / NOT CI_VERIFIED`.
- Server/live-host verification: `DEFERRED_SERVER_VERIFICATION`.
- Server/DNS/certificates/central Nginx/SMTP/production secrets/data/server Ollama remain ISI-28-only.
- Krcuga and OralScanXAI are strict non-targets.

## Bootstrap authority
The corrected read-only bootstrap authority is ISI-27-B0-R1A:
- report source in owner Downloads: `ISI-27-B0-R1A-BOOTSTRAP-AUDIT-REPORT.md`
- report SHA256: `983f04df3e211bb4f42ebe6affd3dfe4cf3e60638dbb47475a104c7835c342db`
- evidence source in owner Downloads: `ISI-27-B0-R1A-BOOTSTRAP-AUDIT-EVIDENCE.json`
- evidence SHA256: `1166ef29b0c9a49e5f753c2d023f064ccd7921db22674adf9f3631b47cdd70f9`
- DONE=6, PARTIAL=8, MISSING=5, DRIFT=0.
- release blockers not DONE=13.
- Help/XAI production-critical blockers=12.
- SBOM/signed provenance/attestation is `MISSING`, not `PARTIAL`.

The scope-lock package copies those exact artifacts into controlled repository spec paths. It does not regenerate or reinterpret them.

## Objective
Lock the smallest complete ISI-27 execution architecture that can close every B0-R1A release blocker without fragmenting work into micro-tasks and without crossing the ISI-28 production/server boundary.

## Release-blocker ownership map

| B0 finding | State | Owner in ISI-27 |
|---|---|---|
| B0-03 ISI-27 scope authority | MISSING | this scope-lock candidate |
| B0-04 Help/XAI production completeness | MISSING | ISI-27A |
| B0-06 methodology release acceptance | PARTIAL | ISI-27B |
| B0-07 model/evaluation provenance | PARTIAL | ISI-27B |
| B0-08 security/privacy evidence | PARTIAL | ISI-27B |
| B0-09 migration/recovery rehearsal evidence | PARTIAL | ISI-27B |
| B0-11 hosted exact-main acceptance workflow | PARTIAL | ISI-27D |
| B0-13 SBOM / signed provenance / attestation | MISSING | ISI-27C |
| B0-14 container/image vulnerability enforcement | MISSING | ISI-27C |
| B0-15 RC notes/compatibility/known-limits/rollback pack | PARTIAL | ISI-27B + artifact binding in ISI-27C |
| B0-16 immutable release builder/workstation portability | PARTIAL | ISI-27C |
| B0-18 GitHub Actions usage pre/post evidence | PARTIAL | ISI-27D |
| B0-19 exact-RC CI_VERIFIED | MISSING | ISI-27D |

## ISI-27A — Shared Help & Release UX Completeness
Status after scope lock: `SPEC_READY`.

### Objective
Close the twelve real production-critical Help/XAI coverage blockers and make `INV-A21` a truthful release gate.

### Required coverage
- INV-A01 Public website
- INV-A02 Login
- INV-A03 Invitation onboarding
- INV-A04 Email verification
- INV-A05 Password reset
- INV-A06 Authenticated app shell
- INV-A08 Data workspace
- INV-A14 Reporting workspace
- INV-A15 Administration workspace
- INV-A16 Account security workspace
- INV-A17 Public self-registration absence
- INV-A21 Cross-product Help Coverage Matrix

SIMPA/ORDO domain Help/XAI already verified at INV-A10/A11/A12/A13/A18/A19 must remain verified and must not be reimplemented.

### INV-A17 rule
Public self-registration remains `NOT_PRESENT`. ISI-27A must not create public signup. Help coverage may use checklist-level `NOT_APPLICABLE` only with explicit invitation-only rationale and tests proving no self-registration authority exists.

### Expected implementation shape
One shared platform User Guide/help authority plus context-appropriate entry points/content for the listed shared surfaces; exact UI implementation is locked by the later 27A implementation contract after code-level audit. No auth/security semantics may be weakened to improve Help reachability.

### Completion gate
All production-critical Help coverage is `VERIFIED` or explicitly justified checklist-level `NOT_APPLICABLE`; global `INV-A21` becomes `VERIFIED`; no fabricated XAI/methodology/security claim.

## ISI-27B — RC Evidence & Governance Pack
Status after scope lock: `PLANNED`.
Depends on accepted ISI-27A.

### Objective
Produce one exact-candidate release-readiness evidence pack without changing numerical/domain authority.

### Required deliverables
- consolidated SIMPA methodology-state acceptance artifact;
- consolidated ORDO methodology-state acceptance artifact;
- immutable model/evaluation provenance manifest bound to exact repository/candidate identity;
- exact-RC security/privacy acceptance consolidation referencing accepted controls and current regressions;
- exact-RC native PostgreSQL/migration/recovery rehearsal evidence;
- explicit inherited ISI-26 performance/resilience acceptance and truthful retained limits;
- release notes/changelog;
- compatibility statement;
- known limitations;
- rollback instructions and release-to-ISI-28 handoff;
- explicit deferred production/server verification.

### Boundaries
No methodology invention, no LISI semantics, no causal/predictive overclaim, no automatic model promotion/deployment, no server mutation.

## ISI-27C — Reproducible Release & Supply-Chain Assurance
Status after scope lock: `PLANNED`.
Depends on accepted ISI-27B.

### Objective
Create a reproducible immutable release candidate and close missing supply-chain controls.

### Required deliverables
- portable release builder for canonical macOS development and Linux CI/release environments;
- immutable exact Git SHA/tree and archive checksum identity;
- machine-readable SBOM generated from the exact RC;
- provenance/attestation bound to the exact RC artifact and repository identity;
- blocking container/image vulnerability scan in the owner-approved manual release-candidate acceptance workflow;
- release artifact manifest binding RC pack, SBOM, provenance and checksums;
- deterministic tests for release artifact identity and failure semantics.

### Important current finding
`tools/release/build_server_release.sh` uses `sha256sum`; canonical owner development is macOS. 27C must make the builder portable rather than assuming GNU coreutils.

### Workflow boundary
Automatic GitHub Actions triggers remain forbidden. Changes to `.github/workflows/ci.yml` may add release-candidate supply-chain gates only while preserving manual `workflow_dispatch` and all inherited blocking jobs.

## ISI-27D — Exact-Main Release-Candidate Acceptance & Phase Closeout
Status after scope lock: `PLANNED / OWNER-CONTROLLED FINAL GATE`.
Depends on accepted ISI-27C.

### Objective
Qualify one exact main commit as the Industrial Release Candidate and close ISI-27 without touching production.

### Mandatory sequence
1. verify exact clean canonical main and candidate artifact identities;
2. verify all 27A/27B/27C local/review gates are accepted;
3. record owner-controlled GitHub Actions usage precheck;
4. obtain explicit owner approval for the hosted cycle;
5. manually dispatch `ISI required acceptance` with checkpoint `release-candidate` against the exact main SHA;
6. require policy, quality, tests, architecture-security, migration, native-postgres, compose, supply-chain, build and aggregate acceptance, plus any 27C release gates, all success;
7. bind the accepted GitHub run to the exact RC SHA/artifact checksums;
8. record Actions usage postcheck;
9. complete final whole-phase gap/legacy audit;
10. only then mark the exact RC SHA `CI_VERIFIED` and ISI-27 complete.

No package may pre-fabricate a GitHub run ID, usage figure or `CI_VERIFIED` state. Final bookkeeping mechanics are chosen after real hosted evidence exists and must avoid self-referential evidence loops.

## Legacy/drift classification
- historical ISI-15/16 deployment tools: `REMOVE_IN_NAMED_PHASE(ISI-28)` / compatibility-history only; never execute in ISI-27;
- existing SIMPA/ORDO/shared-AI Help authorities: `REQUIRED_COMPATIBILITY` and accepted predecessor authority;
- B0 original parser overcount and B0-R1 syntax defect: `LEGITIMATE_HISTORY`; B0-R1A is corrected authority;
- no current `REMOVE_BEFORE_NEXT_SLICE` item may remain unassigned after this scope lock.

## R1 governance-convergence recovery
The initial 8-path scope-lock candidate passed preflight, scope semantics and exact-surface validation, then targeted governance tests exposed two inherited current-state assertions that still froze the pre-scope `ISI-27=planned` transition. R1 changed only `tests/test_isi_17_harness_contract.py` and `tests/test_isi_26_governance_contract.py` to require the legitimate live transition `ISI-27=in_progress`, `active_checkpoint=ISI-27A-SHARED-HELP-RELEASE-UX-COMPLETENESS`, and `27A=spec_ready`. It did not weaken historical predecessor evidence or alter runtime behavior.

Assistant human review of the resulting 10-path candidate additionally required this canonical spec to record the recovery-expanded surface and remove stale live wording that still described a fresh ISI-27 bootstrap after B0-R1A had already closed. This R2 recovery changes only already-in-surface governance documents/tests and does not expand the final path set.

## Exact mutable surface for the final reviewed scope-lock candidate
Only:
- `TECHNICAL_DOCUMENTATION.md`
- `automation/STATUS.md`
- `automation/tasks.json`
- `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
- `automation/specs/ISI-27-SCOPE-LOCK.md`
- `automation/specs/ISI-27-B0-R1A-BOOTSTRAP-AUDIT-REPORT.md`
- `automation/specs/ISI-27-B0-R1A-BOOTSTRAP-AUDIT-EVIDENCE.json`
- `tests/test_isi_17_harness_contract.py`
- `tests/test_isi_26_governance_contract.py`
- `tests/test_isi_27_scope_contract.py`

No runtime, dependency, migration, Compose, Docker, workflow, deployment or server path may change in scope lock.

## Scope-lock acceptance
Required:
- exact baseline/preflight;
- exact B0-R1A source hashes;
- exact 10-path final surface;
- index remains empty;
- targeted governance tests;
- policy/Ruff/diff checks;
- one complete local regression;
- stable candidate fingerprint;
- human review before owner-approved exact staging/commit/push.

No Codex call is authorized for the scope lock.
