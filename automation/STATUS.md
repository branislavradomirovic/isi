# ISI Autonomous Industrialization Status

This is the human-facing live roadmap for the owner. `automation/tasks.json`, task specifications, pull requests, required CI checks and committed evidence remain authoritative.

Last status update: 2026-09-10.

## Current execution

Current task: `ISI-17-AUTONOMOUS-DEVELOPMENT-HARNESS`

Formal current state: `IMPLEMENTING` while the final evidence/status synchronization head awaits its own complete CI run.

Implementation content state: `CI_VERIFIED + INDEPENDENT_RE-REVIEW_PASS`.

Current blocker: `FINAL EVIDENCE/STATUS SYNC MUST PASS FULL CI BEFORE INTEGRATION`.

Baseline: `dce074a744bc3055e1f4a827e0ca8d2073ebe44f`

Parent integration branch: `codex/isi-17-autonomous-development-harness` (PR #3 -> `main`)

Implementation branch: `codex/implement-isi-17-ci-for-autonomous-development` (PR #4 -> PR #3 branch)

Verified remediated implementation head: `058911544e9f262b790087f4aa0d134da3d9dbaf`

Verified CI run: `ISI required acceptance` run #18 / `34462606259` — `success`.

CI evidence: ordinary pytest 320 total / 304 passed / 16 native-gated skipped / 0 failed; dedicated native PostgreSQL 18 total / 18 passed / 0 skipped / 0 failed; all policy, quality, architecture/security, migration, compose, supply-chain, build and aggregate acceptance gates passed.

Independent re-review: `PASS — no technical blocker on verified implementation content`.

Final synchronization rule: the current evidence/status-only head must itself pass every blocking gate. GitHub checks remain authoritative; if any gate fails, ISI-17 returns to `IMPLEMENTING` and is not merged.

Tracking issue: `#2`

Server verification: `DEFERRED_SERVER_VERIFICATION`

No server action is authorized before ISI-28.

## Owner-facing state model

`SPEC_READY -> IMPLEMENTING -> IMPLEMENTED -> CI_VERIFIED -> REVIEW_VERIFIED -> MERGE_READY -> MERGED`

A failed required gate returns the current task to `IMPLEMENTING`. Required gates must not be weakened merely to make the task green.

## Full industrialization roadmap

| Order | Task | Scope | Live status |
|---:|---|---|---|
| 17 | `ISI-17-AUTONOMOUS-DEVELOPMENT-HARNESS` | Autonomous development harness, GitHub Actions CI, deterministic dependencies, lint/type/test/native-PostgreSQL/migration/compose/security/supply-chain gates, evidence/status contracts and server-access policy guards | **IMPLEMENTING — FINAL EVIDENCE SYNC CI** |
| 18 | `ISI-18-OBSERVABILITY-OPERATIONAL-DIAGNOSTICS` | Correlation IDs, structured logs, API/worker/AI/data metrics, health/readiness diagnostics and privacy-safe observability | PLANNED |
| 19 | `ISI-19-BACKUP-RESTORE-DISASTER-RECOVERY` | Deterministic PostgreSQL/object-storage backup and restore tooling, checksums, recovery rehearsal, RPO/RTO and rollback-safe recovery | PLANNED |
| 20 | `ISI-20-ENTERPRISE-SECURITY-COMPLETION` | MFA-ready controls, session/device administration, privileged-action controls, broader security events, RBAC/entitlement matrix, SAST/dependency/container/secret scanning and pen-test readiness | PLANNED |
| 21 | `ISI-21-DATA-GOVERNANCE-PRIVACY` | Data classification, ownership, lineage/provenance, retention/purge/anonymization hooks, sensitive-access auditability, export controls and privacy documentation | PLANNED |
| 22 | `ISI-22-INDUSTRIAL-DATA-PLATFORM` | Versioned connectors, schema mapping/versioning, incremental/idempotent ingestion, dedup/reconciliation, quarantine/error handling, freshness/quality, backfill and lineage | PLANNED |
| 23 | `ISI-23-SIMPA-PRODUCTION-METHODOLOGY` | DRAFT/PROPOSED SIMPA methodology registry, calculation/reference-data contracts, LISI proposal, provenance/confidence/social-map/policy-monitoring contracts, plus detailed in-app Help and SIMPA User Guide; no methodology is labelled validated before human/user-testing approval | PLANNED — draft methodology + help required |
| 24 | `ISI-24-ORDO-PRODUCTION-METHODOLOGY` | DRAFT/PROPOSED ORDO methodology registry, reference calculations, spatial/scenario/development-goal evidence framework, plus detailed in-app Help and ORDO User Guide; no forecasting/validated methodology claim without evidence and human/user-testing approval | PLANNED — draft methodology + help required |
| 25 | `ISI-25-INDUSTRIAL-AI-MLOPS` | Model/prompt registry, eval datasets, structured-output validation, RAG provenance, prompt-injection/PII guards, retries/circuit breakers, human-review traceability and rollback | PLANNED |
| 26 | `ISI-26-PERFORMANCE-LOAD-RESILIENCE` | Workload profiles, API/ingestion/queue/AI/report load tests, failure tests, performance budgets, soak tests and evidence-backed tuning | PLANNED |
| 27 | `ISI-27-INDUSTRIAL-RELEASE-CANDIDATE` | Final CI/security/quality acceptance, migration and recovery rehearsal, methodology acceptance state, Help/User Guide completeness, release notes, immutable release/artifact strategy, deployment and rollback manifests | PLANNED |
| 28 | `ISI-28-CURRENT-SERVER-CONTROLLED-UPGRADE` | One controlled deployment to the existing server with backup, migration, health/smoke/AI/worker/data-integrity verification and rollback | **DEFERRED — explicit owner approval required** |

## Legacy cutover task

`ISI-16-ISI-RS-PRODUCTION-CUTOVER` remains `ON_HOLD`. It is not an independent executable next task. Its production-cutover intent is superseded by the industrialization sequence above and the final controlled deployment in ISI-28.

## Locked architecture and execution boundaries

- ISI is the institutional platform.
- SIMPA and ORDO are the only current domain applications.
- No COSMOS runtime/application/domain layer.
- Preserve FastAPI + Streamlit + PostgreSQL + Redis/RQ + S3-compatible storage + shared AI gateway unless an owner-approved ADR changes it.
- No autonomous SSH/SCP/server deployment, DNS, central-ingress, production SMTP, production-secret, production-data or server-Ollama mutation before ISI-28.
- Draft SIMPA/ORDO methodology may be proposed for user testing, but no formula, weight, threshold, risk score, causal claim, forecast or methodology may be represented as validated without human approval and supporting evidence.

## Update rule

Keep this file synchronized whenever a task changes state, a new blocker appears or clears, a task is split/renamed, a dependency changes, an implementation PR is opened/merged, or an owner approval changes the roadmap. The same change must also be reflected in the authoritative task registry/evidence where applicable.
