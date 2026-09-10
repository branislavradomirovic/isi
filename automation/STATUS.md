# ISI Autonomous Industrialization Status

This is the human-facing live roadmap for the owner. `automation/tasks.json`, task specifications, pull requests, required CI checks and committed evidence remain authoritative.

Last status update: 2026-09-10.

## Current execution

Last completed task: `ISI-17-AUTONOMOUS-DEVELOPMENT-HARNESS`

Final state: `MERGED`.

Main merge commit: `1e4d23543520c7c69ac96e1e79a83ad750b82fae`.

Final parent PR: #3 -> `main`, merged 2026-09-10.

Implementation PR: #4 -> PR #3 branch, merged before parent integration.

Verified CI:

- PR #4 current-head acceptance: run #31 / `34463553604` — `success`.
- PR #3 parent-integration acceptance: run #33 / `34463767042` — `success`.
- `main` post-merge acceptance: run #34 / `34463983460` — `success`.
- final bookkeeping acceptance: run #38 / `34464399365` — `success`.
- Ordinary pytest evidence: 320 total / 304 passed / 16 native-gated skipped / 0 failed.
- Dedicated native PostgreSQL evidence: 18 total / 18 passed / 0 skipped / 0 failed against PostgreSQL 17.
- All blocking gates passed: policy, quality, tests, architecture/security, migration, native-postgres, compose, supply-chain, build, aggregate acceptance.

Independent review: `REVIEW_VERIFIED — no unresolved technical blocker`.

Known warning: superseded intermediate workflow runs failed during remediation and may still appear in GitHub email history; they are not the final state. GitHub-hosted actions currently emit a Node 20 deprecation warning while being forced onto Node 24.

Evidence: `automation/evidence/ISI-17/`.

Server verification: `DEFERRED_SERVER_VERIFICATION`.

No server action is authorized before ISI-28.

Next serial task: `ISI-18-OBSERVABILITY-OPERATIONAL-DIAGNOSTICS` — `PLANNED`, kickoff next.

## Owner-facing state model

`SPEC_READY -> IMPLEMENTING -> IMPLEMENTED -> CI_VERIFIED -> REVIEW_VERIFIED -> MERGE_READY -> MERGED`

A failed required gate returns the active task to `IMPLEMENTING`. Required gates must not be weakened merely to make a task green.

## Full industrialization roadmap

| Order | Task | Scope | Live status |
|---:|---|---|---|
| 17 | `ISI-17-AUTONOMOUS-DEVELOPMENT-HARNESS` | Autonomous development harness, GitHub Actions CI, deterministic dependencies, lint/type/test/native-PostgreSQL/migration/compose/security/supply-chain gates, evidence/status contracts and server-access policy guards | **MERGED** |
| 18 | `ISI-18-OBSERVABILITY-OPERATIONAL-DIAGNOSTICS` | Correlation IDs, structured logs, API/worker/AI/data metrics, health/readiness diagnostics and privacy-safe observability | **PLANNED — NEXT** |
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
