# ISI Autonomous Industrialization Status

This is the human-facing live roadmap for the owner. `automation/tasks.json`, task specifications, owner-approved direct-main commits, required CI checks and evidence remain authoritative.

Last status update: 2026-09-12.

## Current execution

Last completed task: `ISI-19-BACKUP-RESTORE-DISASTER-RECOVERY` — merged in the canonical baseline preceding ISI-20D R0.

Current task: `ISI-20-ENTERPRISE-SECURITY-COMPLETION`.

Current state: `REVIEW_VERIFIED — exact R3 candidate reviewed with no unresolved technical blocker; owner-approved main commit and CI pending`.

Development branch: `main` only.

Baseline `main` SHA: `178d0000cc3119277c59c6ec19024c93d136b2f5`.

ISI-20D R3 closes the R2 human-review blocker locally: because `AuthSession` is user-global, administrator target-session inventory and revocation now fail closed before session access when the target has an active membership in another organization. Single-organization targets remain supported, and the established membership, authorization, organization-wide permission, self-target, session-ownership, step-up, and idempotency controls remain intact. Required R3 local gates pass. Current direct-main state: `main_commit: PENDING`, `push: PENDING`, `ci: PENDING`, `review: REVIEW_VERIFIED`. Final human review found no unresolved technical blocker. No commit, push, CI run, deployment, external penetration test, or real-provider MFA validation is claimed.

Server verification: `DEFERRED_SERVER_VERIFICATION`. No current-server action is authorized before ISI-28.

## Owner-facing state model

`SPEC_READY -> IMPLEMENTING -> IMPLEMENTED -> REVIEW_VERIFIED -> OWNER_APPROVED_MAIN_COMMIT -> CI_VERIFIED -> COMPLETE`

A failed required gate returns the active task to `IMPLEMENTING`. Required gates must not be weakened merely to make a task green.

## Full industrialization roadmap

| Order | Task | Scope | Live status |
|---:|---|---|---|
| 17 | `ISI-17-AUTONOMOUS-DEVELOPMENT-HARNESS` | Autonomous development harness, blocking CI, deterministic dependencies and evidence/server-access guards | **MERGED** |
| 18 | `ISI-18-OBSERVABILITY-OPERATIONAL-DIAGNOSTICS` | Correlation IDs, structured logs, API/worker/AI/data metrics, health/readiness diagnostics and privacy-safe observability | **MERGED — post-merge CI green** |
| 19 | `ISI-19-BACKUP-RESTORE-DISASTER-RECOVERY` | Deterministic PostgreSQL/object-storage backup and restore tooling, checksums, recovery rehearsal, proposed RPO/RTO and rollback-safe recovery | **MERGED IN CANONICAL BASELINE** |
| 20 | `ISI-20-ENTERPRISE-SECURITY-COMPLETION` | MFA-ready controls, session/device administration, privileged-action controls, broader security events, RBAC/entitlement matrix and pen-test readiness | **REVIEW_VERIFIED — OWNER MAIN COMMIT / CI PENDING** |
| 21 | `ISI-21-DATA-GOVERNANCE-PRIVACY` | Data classification, ownership, lineage/provenance, retention/purge/anonymization hooks, sensitive-access auditability, export controls and privacy documentation | PLANNED |
| 22 | `ISI-22-INDUSTRIAL-DATA-PLATFORM` | Versioned connectors, schema mapping/versioning, incremental/idempotent ingestion, dedup/reconciliation, quarantine/error handling, freshness/quality, backfill and lineage | PLANNED |
| 23 | `ISI-23-SIMPA-PRODUCTION-METHODOLOGY` | DRAFT/PROPOSED SIMPA methodology, calculation/reference-data contracts, provenance/confidence, plus detailed in-app Help and SIMPA User Guide | PLANNED — draft methodology + help required |
| 24 | `ISI-24-ORDO-PRODUCTION-METHODOLOGY` | DRAFT/PROPOSED ORDO methodology, reference calculations, spatial/scenario/evidence framework, plus detailed in-app Help and ORDO User Guide | PLANNED — draft methodology + help required |
| 25 | `ISI-25-INDUSTRIAL-AI-MLOPS` | Model/prompt registry, eval datasets, structured-output validation, RAG provenance, prompt-injection/PII guards, retries/circuit breakers, human-review traceability and rollback | PLANNED |
| 26 | `ISI-26-PERFORMANCE-LOAD-RESILIENCE` | Workload profiles, API/ingestion/queue/AI/report load tests, failure tests, performance budgets, soak tests and evidence-backed tuning | PLANNED |
| 27 | `ISI-27-INDUSTRIAL-RELEASE-CANDIDATE` | Final CI/security/quality acceptance, migration/recovery rehearsal, methodology state, Help/User Guide completeness, release notes and immutable artifact/rollback manifests | PLANNED |
| 28 | `ISI-28-CURRENT-SERVER-CONTROLLED-UPGRADE` | Controlled deployment to the existing server only after separate owner approval | **DEFERRED — explicit owner approval required** |

## Locked architecture and execution boundaries

- ISI is the institutional platform.
- SIMPA and ORDO are the only current domain applications.
- No COSMOS runtime/application/domain layer.
- Preserve FastAPI + Streamlit + PostgreSQL + Redis/RQ + S3-compatible storage + shared AI gateway unless an owner-approved ADR changes it.
- No autonomous SSH/SCP/server deployment, DNS, ingress, production SMTP, production secrets/data or server Ollama mutation before ISI-28.
- Draft SIMPA/ORDO methodology may be proposed for user testing, but no formula, weight, threshold, risk score, causal claim, forecast or methodology may be represented as validated without human approval and supporting evidence.
