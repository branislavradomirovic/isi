# ISI Autonomous Industrialization Status

This is the human-facing live roadmap for the owner. `automation/tasks.json`, task specifications, pull requests, required CI checks and committed evidence remain authoritative.

Last status update: 2026-09-09.

## Current execution

Current task: `ISI-17-AUTONOMOUS-DEVELOPMENT-HARNESS`

Current state: `IMPLEMENTING`

Codex environment setup: `ACTIVE`

Current blocker: `NONE — LOCAL ACCEPTANCE IN PROGRESS`

Last observed Codex result: ISI-17 implementation harness created.

Current wait state: `AWAITING_LOCAL_ACCEPTANCE_AND_GITHUB_CI`

GitHub handoff: `PR METADATA PENDING FINAL COMMIT`

GitHub Actions: `CONFIGURED — NOT YET CI_VERIFIED`

Baseline: `dce074a744bc3055e1f4a827e0ca8d2073ebe44f`

Implementation branch: `codex/isi-17-autonomous-development-harness`

Last confirmed non-status implementation head: `6b4843789cd435f6aa578d85e5f034457e79497f`

Implementation PR: `#3`

Tracking issue: `#2`

Server verification: `DEFERRED_SERVER_VERIFICATION`

No server action is authorized before ISI-28.

## Owner-facing state model

`SPEC_READY -> IMPLEMENTING -> IMPLEMENTED -> CI_VERIFIED -> REVIEW_VERIFIED -> MERGE_READY -> MERGED`

A failed required gate returns the current task to `IMPLEMENTING`. Required gates must not be weakened merely to make the task green.

## Full industrialization roadmap

| Order | Task | Scope | Live status |
|---:|---|---|---|
| 17 | `ISI-17-AUTONOMOUS-DEVELOPMENT-HARNESS` | Autonomous development harness, GitHub Actions CI, deterministic dependencies, lint/type/test/migration/compose/security/supply-chain gates, evidence/status contracts and server-access policy guards | **IMPLEMENTING — LOCAL ACCEPTANCE IN PROGRESS** |
| 18 | `ISI-18-OBSERVABILITY-OPERATIONAL-DIAGNOSTICS` | Correlation IDs, structured logs, API/worker/AI/data metrics, health/readiness diagnostics and privacy-safe observability | PLANNED |
| 19 | `ISI-19-BACKUP-RESTORE-DISASTER-RECOVERY` | Deterministic PostgreSQL/object-storage backup and restore tooling, checksums, recovery rehearsal, RPO/RTO and rollback-safe recovery | PLANNED |
| 20 | `ISI-20-ENTERPRISE-SECURITY-COMPLETION` | MFA-ready controls, session/device administration, privileged-action controls, broader security events, RBAC/entitlement matrix, SAST/dependency/container/secret scanning and pen-test readiness | PLANNED |
| 21 | `ISI-21-DATA-GOVERNANCE-PRIVACY` | Data classification, ownership, lineage/provenance, retention/purge/anonymization hooks, sensitive-access auditability, export controls and privacy documentation | PLANNED |
| 22 | `ISI-22-INDUSTRIAL-DATA-PLATFORM` | Versioned connectors, schema mapping/versioning, incremental/idempotent ingestion, dedup/reconciliation, quarantine/error handling, freshness/quality, backfill and lineage | PLANNED |
| 23 | `ISI-23-SIMPA-PRODUCTION-METHODOLOGY` | Validated SIMPA indicator/methodology registry, calculation engine/reference datasets, LISI implementation only from owner-approved methodology, provenance/confidence/social-map/policy-monitoring contracts | PLANNED — methodology approval required |
| 24 | `ISI-24-ORDO-PRODUCTION-METHODOLOGY` | Validated ORDO methodology registry, reference calculations, spatial/scenario/development-goal evidence framework and readiness for future evidence-backed forecasting | PLANNED — methodology approval required |
| 25 | `ISI-25-INDUSTRIAL-AI-MLOPS` | Model/prompt registry, eval datasets, structured-output validation, RAG provenance, prompt-injection/PII guards, retries/circuit breakers, human-review traceability and rollback | PLANNED |
| 26 | `ISI-26-PERFORMANCE-LOAD-RESILIENCE` | Workload profiles, API/ingestion/queue/AI/report load tests, failure tests, performance budgets, soak tests and evidence-backed tuning | PLANNED |
| 27 | `ISI-27-INDUSTRIAL-RELEASE-CANDIDATE` | Final CI/security/quality acceptance, migration and recovery rehearsal, methodology acceptance state, release notes, immutable release/artifact strategy, deployment and rollback manifests | PLANNED |
| 28 | `ISI-28-CURRENT-SERVER-CONTROLLED-UPGRADE` | One controlled deployment to the existing server with backup, migration, health/smoke/AI/worker/data-integrity verification and rollback | **DEFERRED — explicit owner approval required** |

## Legacy cutover task

`ISI-16-ISI-RS-PRODUCTION-CUTOVER` remains `ON_HOLD`. It is not an independent executable next task. Its production-cutover intent is superseded by the industrialization sequence above and the final controlled deployment in ISI-28.

## Locked architecture and execution boundaries

- ISI is the institutional platform.
- SIMPA and ORDO are the only current domain applications.
- No COSMOS runtime/application/domain layer.
- Preserve FastAPI + Streamlit + PostgreSQL + Redis/RQ + S3-compatible storage + shared AI gateway unless an owner-approved ADR changes it.
- No autonomous SSH/SCP/server deployment, DNS, central-ingress, production SMTP, production-secret, production-data or server-Ollama mutation before ISI-28.
- Codex must not fabricate SIMPA/ORDO formulas, weights, thresholds, causal claims or predictive capability.

## Update rule

Keep this file synchronized whenever a task changes state, a new blocker appears or clears, a task is split/renamed, a dependency changes, an implementation PR is opened/merged, or an owner approval changes the roadmap. The same change must also be reflected in the authoritative task registry/evidence where applicable.
