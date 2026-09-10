# ISI Autonomous Industrialization Status

This is the human-facing live roadmap for the owner. `automation/tasks.json`, task specifications, pull requests, required CI checks and committed evidence remain authoritative.

Last status update: 2026-09-10.

## Current execution

Last completed task: `ISI-18-OBSERVABILITY-OPERATIONAL-DIAGNOSTICS` — `MERGED`.

ISI-18 final PR: #6 -> `main`, merged as `b0487d8e9187c6b06efe5fab463875f8d989042c`.

ISI-18 exact-head PR acceptance: run #46 / `34485179622` — `success` across policy, quality, tests, architecture/security, migration, native-postgres, compose, supply-chain, build and aggregate acceptance.

ISI-18 independent review: `REVIEW_VERIFIED — no unresolved technical blocker`.

ISI-18 post-merge `main` acceptance: run #47 / `34485496540` — `success`.

Current task: `ISI-19-BACKUP-RESTORE-DISASTER-RECOVERY`.

Current state: `IMPLEMENTING — repository publication repaired through authenticated GitHub control plane; exact-head CI pending`.

Implementation branch: `automation/isi-19-backup-restore-dr`.

Tracking issue: #7. Pull request: #8.

Baseline `main` SHA: `b0487d8e9187c6b06efe5fab463875f8d989042c`.

Specification: `automation/specs/ISI-19-BACKUP-RESTORE-DISASTER-RECOVERY.md`.

Implementation scope: deterministic recovery manifests and SHA-256 verification, PostgreSQL 17 logical recovery, scoped local/S3-compatible object recovery, encryption/retention hooks, synthetic recovery rehearsal, proposed RPO/RTO runbook and committed evidence.

The Codex execution workspace completed an implementation candidate but could not publish its local commit because that checkout had no authenticated Git remote. The implementation is therefore being published through the authenticated GitHub control plane. Codex-local checks are not accepted as a replacement for exact-head GitHub CI.

Server verification: `DEFERRED_SERVER_VERIFICATION`. No current-server action is authorized before ISI-28.

## Owner-facing state model

`SPEC_READY -> IMPLEMENTING -> IMPLEMENTED -> CI_VERIFIED -> REVIEW_VERIFIED -> MERGE_READY -> MERGED`

A failed required gate returns the active task to `IMPLEMENTING`. Required gates must not be weakened merely to make a task green.

## Full industrialization roadmap

| Order | Task | Scope | Live status |
|---:|---|---|---|
| 17 | `ISI-17-AUTONOMOUS-DEVELOPMENT-HARNESS` | Autonomous development harness, blocking CI, deterministic dependencies and evidence/server-access guards | **MERGED** |
| 18 | `ISI-18-OBSERVABILITY-OPERATIONAL-DIAGNOSTICS` | Correlation IDs, structured logs, API/worker/AI/data metrics, health/readiness diagnostics and privacy-safe observability | **MERGED — post-merge CI green** |
| 19 | `ISI-19-BACKUP-RESTORE-DISASTER-RECOVERY` | Deterministic PostgreSQL/object-storage backup and restore tooling, checksums, recovery rehearsal, proposed RPO/RTO and rollback-safe recovery | **IMPLEMENTING — ACTIVE** |
| 20 | `ISI-20-ENTERPRISE-SECURITY-COMPLETION` | MFA-ready controls, session/device administration, privileged-action controls, broader security events, RBAC/entitlement matrix and pen-test readiness | PLANNED |
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
