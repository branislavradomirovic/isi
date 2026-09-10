# ISI Industrialization Master Plan

**Canonical roadmap: ISI-17 through ISI-28**  
**Roadmap version:** 1.0  
**Status snapshot:** 2026-09-10  
**Repository:** `branislavradomirovic/isi`

---

## 0. Canonical status and authority

This document is the **canonical program roadmap for the ISI industrialization workstream from ISI-17 through ISI-28**. It defines the required sequence, purpose, scope, architectural intent, deliverables, acceptance model, non-goals, human-validation boundaries and transition criteria for every milestone.

The authority model is:

1. Explicit owner instruction is highest authority.
2. `MASTER_PLAN.md` is canonical for program scope, ordering, milestone purpose, required deliverables and Definition of Done.
3. `AGENTS.md` is binding for repository-wide engineering, security, privacy, architecture and execution invariants.
4. `automation/specs/<TASK-ID>.md` is the executable specification for an active milestone and must elaborate this Master Plan without silently narrowing, weakening or contradicting it.
5. Accepted ADRs govern architectural decisions. A task may not silently replace a locked architectural choice; a deliberate change requires an explicit owner-approved ADR and corresponding Master Plan update.
6. `automation/tasks.json` is the machine-readable registry and must be synchronized with this roadmap.
7. `automation/STATUS.md` is a human-facing navigation/status surface, not a substitute for this plan.
8. Pull requests, exact-head GitHub Actions, independent review and committed evidence are the operational truth for whether a planned capability was actually implemented and verified.

If two repository artifacts disagree, the implementation must **fail closed**: preserve the stricter security/quality boundary and reconcile the documents before claiming completion.

### Status semantics

The industrialization state model is:

`PLANNED -> SPEC_READY -> IMPLEMENTING -> IMPLEMENTED -> CI_VERIFIED -> REVIEW_VERIFIED -> MERGE_READY -> MERGED`

Additional mandatory qualifiers:

- `DEFERRED_SERVER_VERIFICATION` — repository implementation may be complete, but current-server behavior has not been verified and no server contact is authorized.
- `OWNER_GATED` — execution is forbidden until a new explicit owner authorization is given.
- `DRAFT/PROPOSED` — methodology, formulas, weights, thresholds, forecasts, RPO/RTO targets or policy semantics are working proposals and are not human-validated facts.

A task is not complete because an agent says it is complete. Deterministic repository acceptance, exact-head CI, independent review and post-merge acceptance determine completion.

### Current program status snapshot

| Order | Task | Program status | Implementation status |
|---:|---|---|---|
| 17 | `ISI-17-AUTONOMOUS-DEVELOPMENT-HARNESS` | Complete | **MERGED; CI/review verified; server verification deferred** |
| 18 | `ISI-18-OBSERVABILITY-OPERATIONAL-DIAGNOSTICS` | Complete | **MERGED; exact-head and post-merge CI green; server verification deferred** |
| 19 | `ISI-19-BACKUP-RESTORE-DISASTER-RECOVERY` | Complete | **MERGED as `4713a1deb7ccec0b99b92985424693a50727a1f6`; post-merge CI #51 green; server verification deferred** |
| 20 | `ISI-20-ENTERPRISE-SECURITY-COMPLETION` | Active | **SPEC_READY / IMPLEMENTATION IN PROGRESS on PR #10; not yet merged in this snapshot** |
| 21 | `ISI-21-DATA-GOVERNANCE-PRIVACY` | Future | **NOT IMPLEMENTED** |
| 22 | `ISI-22-INDUSTRIAL-DATA-PLATFORM` | Future | **NOT IMPLEMENTED** |
| 23 | `ISI-23-SIMPA-PRODUCTION-METHODOLOGY` | Future | **NOT IMPLEMENTED; methodology must remain DRAFT/PROPOSED until human validation** |
| 24 | `ISI-24-ORDO-PRODUCTION-METHODOLOGY` | Future | **NOT IMPLEMENTED; methodology/forecast claims require human validation** |
| 25 | `ISI-25-INDUSTRIAL-AI-MLOPS` | Future | **NOT IMPLEMENTED** |
| 26 | `ISI-26-PERFORMANCE-LOAD-RESILIENCE` | Future | **NOT IMPLEMENTED** |
| 27 | `ISI-27-INDUSTRIAL-RELEASE-CANDIDATE` | Future | **NOT IMPLEMENTED** |
| 28 | `ISI-28-CURRENT-SERVER-CONTROLLED-UPGRADE` | Future | **DEFERRED / OWNER_GATED; execution explicitly unauthorized** |

Live branch/PR/CI values may advance after this snapshot. Such movement updates operational status but does not change the milestone scope defined here.

---

## 1. Global architecture and non-negotiable invariants

- ISI is the institutional platform.
- SIMPA and ORDO are the only current domain applications.
- Do not introduce COSMOS as an application, runtime, domain, tenant, namespace, product, menu or user-visible software layer.
- FastAPI remains the backend/API/public service technology unless an owner-approved ADR changes it.
- Streamlit remains the authenticated application UI unless an owner-approved ADR changes it.
- PostgreSQL remains the primary relational database.
- Redis/RQ remains the background-job/queue mechanism unless an approved ADR changes it.
- S3-compatible storage remains the object-storage contract.
- Shared AI gateway/orchestrator remains the only domain path to model providers.
- Preserve `Organization -> Membership -> Role/Permission -> Product entitlement -> Workspace authorization` on every API, worker, report, ingestion, AI and administrative path.
- SIMPA and ORDO may share infrastructure, identity, security, data-platform, AI-gateway, reporting, audit and operations capabilities, but must not share domain semantics implicitly.
- Sensitive SIMPA AI policy remains local-only where already required unless an explicit approved policy change states otherwise.
- AI remains human-in-the-loop for institutional decision support. No autonomous institutional decision, diagnosis, eligibility decision, ranking, causal claim or policy recommendation may be fabricated.
- No production secrets, raw credentials, session tokens, authorization headers, client/institution data or unnecessary PII may be committed to source, tests, logs or evidence.
- No production/current-server action is allowed in ISI-17 through ISI-27. Only ISI-28 may touch the current server, and only after fresh explicit owner approval.

### Global completion gate for ISI-20 through ISI-27

Unless a task explicitly requires stronger checks, each implementation must include:

1. task-local focused tests;
2. `python -m tools.ci.policy_check`;
3. full blocking repository acceptance through `tools/ci/run_isi17_acceptance.sh` or its accepted successor;
4. `tools/ci/migration_check.sh offline` whenever migrations/schema are involved;
5. native PostgreSQL 17 acceptance whenever persistence, transaction semantics or migrations are involved;
6. static Compose/deployment topology validation without deployment;
7. supply-chain/security gates inherited from ISI-17;
8. `git diff --check`;
9. exact final PR head synchronized to GitHub;
10. complete required GitHub Actions acceptance green on that exact head;
11. independent exact-head review with no unresolved technical blocker;
12. committed evidence under `automation/evidence/<TASK-ID>/`;
13. merge to `main` only after the prior gates pass;
14. successful post-merge `main` acceptance before the next task begins.

---

# ISI-17 — Autonomous Development Harness + CI

**Current status:** `MERGED`  
**Implemented:** yes  
**Server verification:** `DEFERRED_SERVER_VERIFICATION`  
**Current operational note:** the old autonomous-delivery orchestration may be intentionally paused; the repository governance/CI harness remains authoritative regardless of whether implementation is driven manually through Cursor/Codex or another approved agent workflow.

## 1. Purpose / business objective

Create a controlled engineering system in which ISI can be industrialized safely, reproducibly and audibly without turning the production server into a development environment. The business purpose is to reduce engineering risk, prevent silent regressions and make each later industrialization milestone independently verifiable.

## 2. Current baseline and dependencies

- Built on completed repository functionality through ISI-14 and the ISI-15 server-readiness baseline.
- ISI-16 production cutover remains on hold/superseded as immediate work.
- The task established the governance baseline used by every later milestone.
- Registry records the implementation as merged; final bookkeeping acceptance run #42 was green.

## 3. Detailed functional scope

Implemented scope includes repository agent rules, autonomous/server execution locks, task/evidence conventions, deterministic dependency installation, owner-facing status tracking, blocking CI, architecture/security regression gates, migration checks, supply-chain checks, build checks and aggregate acceptance.

## 4. Technical scope / architecture

The task intentionally did not redesign the application. It wrapped the existing FastAPI + Streamlit + PostgreSQL + Redis/RQ + S3-compatible storage + shared AI architecture in a deterministic engineering control plane. GitHub became the development control plane; production remained isolated.

## 5. Data model and migrations

No business-domain schema was required. The important database work was CI enforcement of Alembic single-head discipline, offline rendering and isolated PostgreSQL 17 upgrade-to-head validation.

## 6. API / UI / worker / AI implications

No new domain capability was required. API/UI/worker/AI code remained functionally compatible. Their tests and architecture boundaries became blocking CI concerns.

## 7. Security, privacy and tenant boundaries

Implemented repository policies prohibit production credentials/server mutation, secret leakage, test weakening, cross-tenant/product regressions and unauthorized server-side deployment actions. Existing tenant, product, workspace, authentication and AI isolation tests became part of the industrialization gate.

## 8. Concrete deliverables

Implemented deliverables include `AGENTS.md`, operational lock/release policy documentation, task/evidence templates, `automation/tasks.json`, `automation/STATUS.md`, deterministic dependency resolution, GitHub Actions required acceptance, `.dockerignore`, CI helper scripts and the local acceptance runner.

## 9. Required tests

Implemented tests/gates cover policy, Python quality/compile, full tests, architecture/security, migration, native PostgreSQL, Compose, supply-chain/security scanning and non-deploying build verification.

## 10. CI / quality gates

All required task gates are blocking; failures may not be masked with `|| true`, skipped, xfailed or converted to allowed failures simply to obtain green status. Exact-head GitHub acceptance is authoritative.

## 11. Evidence artifacts

Evidence is maintained under `automation/evidence/ISI-17/` and must identify baseline/final SHAs, gate results, warnings, review state and explicit no-server-action status.

## 12. Acceptance criteria / Definition of Done

Completed when governance documents, deterministic dependencies, blocking CI, migration checks, security/supply-chain gates, build checks, evidence and independent review were accepted and merged. This task is complete at repository level.

## 13. Explicit non-goals

No production deployment, DNS/TLS change, production SMTP, secret-manager deployment, SIMPA/ORDO methodology creation, model/provider rewrite, UI rewrite, Kubernetes migration or broad dependency upgrade.

## 14. Risks and compatibility constraints

The primary ongoing risk is bypassing the harness through direct/unreviewed changes. Later milestones must continue to use the same fail-closed acceptance philosophy even if the interactive development tool changes.

## 15. Human validation requirements

Owner approval is required for architecture-scope changes and all server/deployment activity. Independent review remains required for exact CI-verified heads.

## 16. Transition condition to next ISI task

Satisfied. ISI-17 was merged and acceptance verified; ISI-18 was allowed to begin.

---

# ISI-18 — Observability & Operational Diagnostics

**Current status:** `MERGED`  
**Implemented:** yes  
**Merge:** `b0487d8e9187c6b06efe5fab463875f8d989042c`  
**Verification:** exact-head PR run #46 green; independent review verified; post-merge run #47 green  
**Server verification:** `DEFERRED_SERVER_VERIFICATION`

## 1. Purpose / business objective

Make failures, degradation and execution paths diagnosable from privacy-safe telemetry. The operational objective is to make the system supportable before production hardening without needing access to a live monitoring host.

## 2. Current baseline and dependencies

- Depends on merged ISI-17 governance/CI.
- Reuses existing health, queue/worker, AI registry and ingestion infrastructure.
- Its merged implementation is now inherited by all later tasks.

## 3. Detailed functional scope

Implemented correlation/request IDs, structured JSON application logging, bounded privacy-safe metrics, API latency/outcome metrics, worker/queue telemetry, AI execution telemetry, ingestion telemetry, readiness diagnostics and deterministic JSON/Prometheus metric export contracts.

## 4. Technical scope / architecture

Observability is a shared platform concern. Dynamic identifiers are normalized/removed from labels. Application observability must not introduce domain semantics or make business requests fail because telemetry collection itself failed, except that readiness correctly reports unhealthy dependencies.

## 5. Data model and migrations

No application-schema migration was required; telemetry is operational rather than a new business persistence model.

## 6. API / UI / worker / AI implications

FastAPI requests carry/return correlation IDs. Queue/worker, AI and ingestion paths emit bounded execution metrics. Readiness exposes dependency state using safe reason codes rather than raw exception/configuration details.

## 7. Security, privacy and tenant boundaries

Logs/metrics must never contain request bodies, query strings, authorization headers, cookies, passwords, session tokens, raw prompts/outputs, uploaded content, filenames/object keys or tenant/user/workspace identifiers. Cardinality is bounded.

## 8. Concrete deliverables

Shared observability modules, request middleware, structured logging, metrics export, readiness components, tests, operations contract and evidence under `automation/evidence/ISI-18/`.

## 9. Required tests

Correlation ID handling; invalid-ID replacement; structured log/redaction; path/label privacy; Prometheus export; request metrics; worker/AI/ingestion metrics; readiness aggregation/privacy; full inherited regression suite.

## 10. CI / quality gates

Focused ISI-18 tests plus full ISI-17 acceptance, native PostgreSQL/migration regressions where applicable, security/policy checks and exact-head GitHub Actions.

## 11. Evidence artifacts

`kickoff.md`, `acceptance-summary.md`, `results.json`, final head/CI identifiers, review state and server deferral.

## 12. Acceptance criteria / Definition of Done

Satisfied: repository implementation exists, required CI passed on exact head, independent review passed, merge completed and post-merge CI is green.

## 13. Explicit non-goals

No deployment of Prometheus/Grafana/Loki/OpenTelemetry collectors, production dashboards, alert routing/on-call integration, production capacity verification or domain-methodology change.

## 14. Risks and compatibility constraints

Main ongoing risk is accidental high-cardinality or sensitive-data leakage as new routes/workers are added. ISI-20–27 must reuse bounded telemetry contracts rather than inventing raw ad-hoc logs.

## 15. Human validation requirements

Production monitoring integration and alert thresholds require later operational validation; repository behavior is already CI/review verified.

## 16. Transition condition to next ISI task

Satisfied. Post-merge CI green allowed ISI-19 to begin.

---

# ISI-19 — Backup, Restore & Disaster Recovery Automation

**Current status:** `MERGED`  
**Implemented:** yes  
**Merge:** `4713a1deb7ccec0b99b92985424693a50727a1f6`  
**Verification:** exact synchronized-head CI #50 and independent exact-head review passed; post-merge main CI #51 (`34502016805`) passed  
**Server verification:** `DEFERRED_SERVER_VERIFICATION`

## 1. Purpose / business objective

Provide deterministic, integrity-verifiable backup, restore and recovery mechanisms so ISI has an engineering-grade recovery path before release candidacy. The objective is recoverability of durable relational and application-managed object data without relying on the current production host.

## 2. Current baseline and dependencies

- Depends on merged ISI-18 and the complete ISI-17 gate set.
- PostgreSQL 17 is authoritative relational storage.
- S3-compatible/local `StorageBackend` is authoritative object storage.
- Redis/RQ transient queue state is not treated as authoritative recovery data.

## 3. Detailed functional scope

Implemented versioned recovery manifests, SHA-256 integrity, PostgreSQL logical backup/restore boundaries, object-storage round trip, corruption detection, retention dry-run hooks, encryption boundaries, synthetic recovery rehearsal, schema/invariant verification and proposed RPO/RTO documentation.

## 4. Technical scope / architecture

Recovery operates against explicit synthetic/non-production targets. PostgreSQL and object storage are recovered and verified together. Tooling fails closed on missing artifacts, metadata/version mismatch, digest mismatch, command failure or failed verification.

## 5. Data model and migrations

No new business schema is required merely for backup. Recovery must always validate the existing Alembic head/schema after restore. Any future persistent recovery metadata must still use Alembic.

## 6. API / UI / worker / AI implications

No public recovery API or user UI is required. No production scheduler is required. The capability is operational tooling/services plus CI rehearsal.

## 7. Security, privacy and tenant boundaries

Backup data is sensitive by default. Manifests may contain required identifiers/digests but never credentials or payload excerpts. Restored state must preserve tenant, organization, product and SIMPA/ORDO isolation.

## 8. Concrete deliverables

Recovery manifest, PostgreSQL backup/restore tooling, object-storage backup/restore, verification, retention/encryption hooks, synthetic rehearsal, recovery documentation, proposed RPO/RTO, tests and evidence.

## 9. Required tests

Manifest/version serialization, SHA/corruption, command failure paths, native PostgreSQL 17 backup/restore, local object-storage round trip, S3 adapter contract, retention dry-run, encryption-state metadata, synthetic full rehearsal and post-recovery isolation regressions.

## 10. CI / quality gates

Task-local backup/recovery tests, ISI-19 recovery rehearsal, full ISI-17 acceptance and exact-head GitHub Actions including native PostgreSQL. These gates are complete for the merged repository state.

## 11. Evidence artifacts

`automation/evidence/ISI-19/` contains acceptance/result/recovery evidence, synthetic manifest information, RPO/RTO status, SHAs, CI/review state and server deferral.

## 12. Acceptance criteria / Definition of Done

Satisfied at repository level: implementation, deterministic rehearsal, exact-head CI, independent review, merge and post-merge CI are complete.

## 13. Explicit non-goals

No production backup execution, production restore, disaster declaration, production retention deletion, DNS/ingress/SMTP/secrets/Ollama changes or verified production RPO/RTO claim.

## 14. Risks and compatibility constraints

Production RPO/RTO and capacity remain unvalidated until ISI-28. Future schema/object changes must preserve recovery manifest compatibility/versioning and add recovery coverage where needed.

## 15. Human validation requirements

Owner/operations approval is required before any real production backup/restore/recovery action. Proposed RPO/RTO targets remain proposals until real infrastructure validation.

## 16. Transition condition to next ISI task

Satisfied. ISI-19 merged and post-merge CI #51 is green, so ISI-20 is the active milestone.

---

# ISI-20 — Enterprise Security Completion

**Current status:** `SPEC_READY / IMPLEMENTING`  
**Implemented:** not yet proven on GitHub in this roadmap snapshot  
**Tracking:** issue #9, draft PR #10, branch `automation/isi-20-enterprise-security`  
**Snapshot PR head:** `6bd5b151ade39fc203ed6fbb44b31885a0d7a5e9`  
**Baseline:** `4713a1deb7ccec0b99b92985424693a50727a1f6`  
**Server verification:** `DEFERRED_SERVER_VERIFICATION`

## 1. Purpose / business objective

Complete repository-side enterprise security controls before data governance and final industrialization. The objective is to establish demonstrable authentication assurance, privileged-operation protection, privacy-safe security evidence and an explicit authorization matrix suitable for an institutional platform.

## 2. Current baseline and dependencies

- ISI-19 is merged and post-merge CI verified.
- Existing ISI-14 authentication/session/security controls are inherited, not replaced.
- Existing identity/access/admin architecture is inherited.
- Current implementation branch/PR already contains the detailed ISI-20 task specification; implementation must extend existing services rather than bypass them.

## 3. Detailed functional scope

Required implementation:

- provider-neutral MFA factor/readiness model;
- challenge lifecycle: issue, expiry, bounded attempts, consumption, replay rejection, revocation;
- authentication-assurance state and freshness;
- centralized step-up authorization for privileged operations;
- central machine-readable privileged-operation catalog;
- safe user session/device inventory;
- self session revocation and bounded admin session revocation;
- broader privacy-safe SecurityEvent lifecycle;
- recursively bounded sensitive-metadata rejection;
- complete organization/RBAC/product-entitlement/workspace authorization negative matrix;
- SIMPA/ORDO isolation proof;
- organization-admin versus platform-admin separation;
- platform-admin self-escalation and last-active-admin protection;
- session fixation/replay/token-leakage tests;
- state-changing browser origin/CSRF contract while preserving non-browser bearer clients;
- security header/cookie/configuration contract assertions;
- CI-safe penetration-test readiness pack without claiming an external penetration test.

## 4. Technical scope / architecture

Implement within `src/platform/auth/`, `src/platform/security/`, `src/platform/access/`, `src/platform/administration/` and appropriate FastAPI routes/dependencies. Privileged authorization must be centralized and fail closed. Existing server-side tenant/product/workspace checks remain authoritative.

## 5. Data model and migrations

A new Alembic revision based on `20260828_0013` is expected, currently planned as `20260910_0014_enterprise_security.py`. It must support constrained MFA factor/challenge persistence and any required assurance/session-device metadata. Low-entropy verifier material requires keyed one-way verification, not plain unsalted hashing. PostgreSQL transaction/locking semantics must prevent concurrent challenge replay.

## 6. API / UI / worker / AI implications

API may add authenticated session-security endpoints and privileged-operation enforcement. UI may expose account/session security without pretending a production MFA provider is configured. Workers must not bypass privileged/tenant/product context. AI policy is not functionally redesigned here but security controls must also protect AI-related privileged boundaries where applicable.

## 7. Security, privacy and tenant boundaries

Never persist/log plaintext OTPs, recovery codes, MFA seeds, raw session tokens, reset/invitation tokens, authorization headers or cookies. Session inventory must not expose raw IP/full user-agent. Organization-admin must never imply platform-admin. Cross-organization and SIMPA/ORDO boundaries must be explicitly negative-tested.

## 8. Concrete deliverables

- MFA/assurance/session-security models/services/migration;
- privileged-operation catalog and centralized authorization;
- safe session inventory/revocation services/endpoints as appropriate;
- platform-admin mutation safeguards;
- recursive SecurityEvent validation and new event coverage;
- origin/browser security contract;
- `tests/test_isi_20_enterprise_security.py`;
- `tests/test_isi_20_access_matrix.py`;
- `tests/test_isi_20_security_events.py`;
- native PostgreSQL schema/concurrency coverage;
- control matrix, attack-surface inventory and penetration-readiness pack;
- complete `automation/evidence/ISI-20/`;
- synchronized registry/status/PR metadata.

## 9. Required tests

MFA enrollment/challenge/replay/attempt/expiry/revoke; assurance/step-up allow/deny; session inventory/revocation; security-change invalidation; recursive event metadata rejection; access matrix; platform-admin safeguards; session fixation/replay/token leakage; origin/browser state change; production configuration; migration offline/live; PostgreSQL concurrency/schema; full legacy auth/access/admin regressions.

## 10. CI / quality gates

At minimum: policy check, three focused ISI-20 test modules, ISI-14 + ISI-02A/02B/02C relevant regressions, offline migration, native PostgreSQL, full ISI-17 acceptance and `git diff --check`; then authoritative exact-head GitHub Actions and independent review.

## 11. Evidence artifacts

Under `automation/evidence/ISI-20/`: kickoff, acceptance summary, results JSON, security-control/access matrix, penetration-test-readiness summary, baseline/final SHA, exact CI run, independent review state, residual risks/deferrals and `DEFERRED_SERVER_VERIFICATION`.

## 12. Acceptance criteria / Definition of Done

`IMPLEMENTED` requires code, migration, tests, control matrix, readiness pack and local/task acceptance. `CI_VERIFIED` requires all blocking GitHub jobs green on the exact synchronized final head. `REVIEW_VERIFIED` requires independent review of that same head. `MERGED` requires merge and successful post-merge main CI.

## 13. Explicit non-goals

No current-server scan/deployment, production MFA provider enrollment, external/live-host penetration test, identity architecture replacement, production secret rotation, DNS/ingress/SMTP/SSO cutover, domain methodology change or COSMOS layer.

## 14. Risks and compatibility constraints

Key risks: MFA verifier leakage, challenge races, event-transaction semantics, accidental platform-admin derivation from organization roles, bearer-client breakage from overly broad origin enforcement, exposure of legacy raw session metadata and overclaiming security validation.

## 15. Human validation requirements

External penetration testing, production MFA integration and live-host security behavior require later explicit human/owner authorization. Independent exact-head code/security review is mandatory before merge.

## 16. Transition condition to next ISI task

ISI-21 may begin only after ISI-20 is merged to `main`, all required exact-head review/CI gates have passed, and post-merge main CI is green. Any failed security gate returns ISI-20 to `IMPLEMENTING`.

---

# ISI-21 — Data Governance & Privacy Controls

**Current status:** `PLANNED / NOT IMPLEMENTED`  
**Dependency:** ISI-20 must be merged and post-merge verified  
**Server verification:** `DEFERRED_SERVER_VERIFICATION`

## 1. Purpose / business objective

Turn the existing data platform into a governable institutional data environment. The objective is to know what data exists, who owns it, how sensitive it is, where it came from, how long it may be retained, who accessed/exported it and how it can be safely purged or anonymized without silently breaking provenance.

## 2. Current baseline and dependencies

Already inherited before ISI-21:

- organization/workspace/product authorization;
- shared data sources and source-version provenance foundations;
- audit/security events;
- object storage abstraction;
- backup/recovery tooling;
- enterprise security from ISI-20 once accepted;
- SIMPA/ORDO aggregate/provenance-oriented domain models.

Not yet implemented as a complete governance system: canonical classification taxonomy, ownership/stewardship contracts, retention policies, purge/anonymization orchestration, sensitive-access policy and governance export/privacy evidence.

## 3. Detailed functional scope

Implement:

- versioned data-classification taxonomy (for example public/internal/confidential/restricted or an owner-approved equivalent);
- classification assignment to relevant data sources, source versions, stored objects and governed domain datasets;
- data owner/steward/custodian roles or references with explicit accountability;
- lawful-purpose/legal-basis metadata hooks where required, while avoiding fabricated legal conclusions;
- processing-purpose and sensitivity metadata;
- provenance/lineage visibility from source -> version -> ingestion -> normalized records -> analytical result/report/AI evidence where technically available;
- retention-policy definitions with version, effective dates, scope and status;
- retention evaluation/dry-run producing candidates without destructive action by default;
- purge/anonymization execution boundaries with explicit authorization, idempotency and evidence;
- legal-hold/retention-exception hooks if the owner-approved policy requires them;
- sensitive-data access audit events;
- export-control checks and export manifests;
- privacy-safe data inventory and governance dashboard/API;
- machine-readable privacy/governance control matrix.

## 4. Technical scope / architecture

Data governance must be a shared platform layer, not SIMPA/ORDO domain logic. It should integrate with existing `core_data_*`, storage, reporting, audit and security services. Classification and retention enforcement must occur server-side and remain scope-aware across API, worker, report and AI data paths.

## 5. Data model and migrations

Expected persistence includes versioned classification/policy metadata, ownership/stewardship references, retention rules/evaluations/actions, data-governance events and export manifests/references. Exact table names are set in the task spec, but every schema addition requires Alembic upgrade/downgrade and native PostgreSQL tests. Avoid duplicating domain data solely to attach governance metadata; prefer stable references and explicit scope.

## 6. API / UI / worker / AI implications

- API: authenticated governance inventory, classification, ownership, retention-evaluation and controlled export endpoints.
- UI: administration/governance surfaces for authorized users; ordinary users see only governance metadata they are permitted to see.
- Workers: purge/anonymization/backfill jobs must revalidate authorization and scope from durable records.
- AI: classification must influence what content may enter external/local model paths and what may be retained in prompts/results; no raw sensitive material is copied into governance logs.

## 7. Security, privacy and tenant boundaries

Classification metadata must not itself leak sensitive content. Cross-organization data inventory is forbidden except explicit platform-admin capability. Purge/anonymization must preserve auditability without retaining the sensitive payload being removed. Backups/retention interaction must be documented; deletion from live data must not falsely claim immediate deletion from immutable recovery media if that is not technically true.

## 8. Concrete deliverables

- ISI-21 task specification;
- classification registry/policy services;
- ownership/stewardship contracts;
- retention evaluation + safe execution boundaries;
- purge/anonymization hooks;
- sensitive access/export audit;
- export manifest/control service;
- governance APIs/UI as appropriate;
- migration(s);
- focused unit/integration/PostgreSQL tests;
- privacy/governance documentation and control matrix;
- evidence under `automation/evidence/ISI-21/`.

## 9. Required tests

Classification lifecycle; invalid/downgrade transitions; cross-tenant classification access; ownership scope; retention date/effective-rule resolution; dry-run non-destructive behavior; purge/anonymization idempotency; legal-hold/exception behavior if implemented; audit evidence; export authorization; backup/retention disclosure; AI/data-path sensitivity enforcement; migration round trip; full regressions.

## 10. CI / quality gates

Focused ISI-21 tests + policy check + migration/native PostgreSQL + complete ISI-17 acceptance + exact-head GitHub Actions. Add static checks that destructive governance actions cannot execute by default or without authorization.

## 11. Evidence artifacts

Classification/control catalog, synthetic governance inventory, retention dry-run results, purge/anonymization synthetic acceptance, export-control matrix, migration/CI results, known privacy/legal deferrals and `DEFERRED_SERVER_VERIFICATION`.

## 12. Acceptance criteria / Definition of Done

All relevant persisted data classes can be governed through explicit policy/ownership/retention metadata; sensitive access/export is auditable; destructive actions are authorization-bound and testable; tenant/product isolation is proven; CI/review/merge/post-merge gates pass.

## 13. Explicit non-goals

No legal opinion, no automatic declaration of GDPR or other regulatory compliance, no production data purge, no production DPO workflow, no external data sharing, no server-side retention deletion and no new domain methodology.

## 14. Risks and compatibility constraints

Risk of overclaiming compliance, breaking historical provenance through deletion, inconsistent classification across derived artifacts, backup-versus-erasure semantics and accidental cross-tenant inventory visibility. Policies must be versioned and explainable.

## 15. Human validation requirements

Final classification taxonomy, retention periods, lawful-basis/purpose semantics, legal-hold policy and real privacy/legal compliance statements require owner/legal/privacy review. Code may provide a DRAFT/PROPOSED framework before those values are institutionally approved.

## 16. Transition condition to next ISI task

ISI-22 begins only after the governance schema/policy is merged and post-merge green, because industrial ingestion must attach classification, ownership, provenance and retention semantics from the start.

---

# ISI-22 — Industrial Data Platform

**Current status:** `PLANNED / NOT IMPLEMENTED`  
**Dependency:** ISI-21 merged and post-merge verified  
**Server verification:** `DEFERRED_SERVER_VERIFICATION`

## 1. Purpose / business objective

Upgrade shared ingestion from a foundational data-source capability into an industrial, reproducible and operable data platform. The business objective is trustworthy repeatable ingestion with clear schema/versioning, quality, reconciliation and lineage instead of one-off imports.

## 2. Current baseline and dependencies

Inherited: `core_data_sources`/versions and storage abstractions from earlier shared-data work; observability; backup/recovery; enterprise security; ISI-21 classification/governance. Missing: standardized versioned connector SDK/registry, robust incremental checkpoints, schema contracts, quarantine/reconciliation and industrial DQ/freshness/backfill controls.

## 3. Detailed functional scope

Implement:

- versioned connector/interface contract for file, database/API or other owner-approved source classes;
- connector registry and capability metadata;
- source configuration validation without persisting secrets in plaintext;
- schema discovery and explicit schema-mapping/version lifecycle;
- canonical field/type mapping contracts;
- incremental ingestion checkpoints/watermarks;
- deterministic idempotency keys and duplicate detection;
- safe replay/backfill ranges;
- batch/run lifecycle with queued/running/succeeded/partial/failed/quarantined semantics;
- row/object-level rejection/quarantine without leaking sensitive payload in logs;
- reconciliation counts/digests and source-versus-ingested validation;
- freshness/SLA metadata and stale-source detection;
- data-quality checks with machine-readable results;
- lineage from source/version/run to materialized dataset/domain mapping;
- retry/resume semantics;
- observability for volume, duration, outcome and bounded error codes;
- governed retention/classification propagation from ISI-21.

## 4. Technical scope / architecture

Build on shared data modules and Redis/RQ workers. Connector implementations must be adapters behind a stable interface. Domain modules consume mapped/provenance-ready data rather than embedding connection logic. Secrets remain externally supplied; configuration stored in DB must be non-secret or encrypted through an approved boundary.

## 5. Data model and migrations

Expected additions: connector definitions/versions, schema definitions/mappings, ingestion runs/checkpoints, quality results, quarantine metadata, reconciliation records and lineage edges/references. Migrations must be additive/backward-compatible unless a separately documented transition is required.

## 6. API / UI / worker / AI implications

- API: manage sources/connectors/schema maps/runs, inspect DQ/quarantine/reconciliation/lineage.
- UI: data operations workspace for authorized users with run state, freshness, mapping and quality visibility.
- Workers: durable idempotent ingestion/backfill jobs with explicit scope checks and retries.
- AI: no AI is required to ingest data; if AI assists mapping later, it must produce reviewable proposals, never silently alter canonical schema mappings.

## 7. Security, privacy and tenant boundaries

Connector secrets never appear in DB/log/evidence unless through an approved encrypted-secret boundary. Every run/checkpoint/quarantine item is organization/product/workspace scoped. No cross-product reuse of private data without explicit governance and authorization. Quarantine/error diagnostics must avoid raw sensitive record values.

## 8. Concrete deliverables

Connector SDK/registry, schema registry/mapping, run/checkpoint engine, idempotency/dedup, quarantine, DQ, reconciliation, freshness, backfill/resume, lineage, APIs/UI/workers, migration(s), tests, operator documentation and evidence.

## 9. Required tests

Connector contract; version compatibility; schema drift; idempotent replay; duplicate handling; incremental checkpoint; failed/retry/resume; quarantine privacy; reconciliation mismatch; freshness; DQ rules; backfill; cross-tenant/product isolation; storage integration; native PostgreSQL; worker concurrency; regression suite.

## 10. CI / quality gates

Focused ISI-22 tests, native PostgreSQL and migration checks, worker integration, object-storage adapter tests, full blocking acceptance, exact-head GitHub Actions and independent review. Deterministic synthetic fixtures are required.

## 11. Evidence artifacts

Synthetic ingestion manifests, schema versions/maps, run/reconciliation/quality results, lineage example, backfill/replay proof, migration and exact-head CI/review state, warnings and server deferral.

## 12. Acceptance criteria / Definition of Done

Repeated ingestion of the same synthetic source is deterministic/idempotent; schema changes are versioned; errors are quarantined safely; reconciliation and quality are visible; lineage and governance survive the path; full CI/review/merge/post-merge gates pass.

## 13. Explicit non-goals

No production connectors requiring production credentials, no production ingestion, no arbitrary ETL platform rewrite, no domain methodology, no fabricated data transformation semantics and no external data sharing.

## 14. Risks and compatibility constraints

Schema drift, duplicate amplification, non-idempotent retries, secret leakage, high-volume performance and backfill consistency are primary risks. Existing shared-data/domain references must remain compatible or be migrated explicitly.

## 15. Human validation requirements

Real source mappings, business meaning of fields, DQ thresholds and production freshness SLAs require domain/data-owner approval. The platform may validate structural rules automatically, not business truth.

## 16. Transition condition to next ISI task

ISI-23 begins only when SIMPA can consume versioned, governed, quality/provenance-aware data through a stable platform contract.

---

# ISI-23 — SIMPA Production Methodology

**Current status:** `PLANNED / NOT IMPLEMENTED`  
**Methodology state target:** `DRAFT/PROPOSED` until explicit human validation  
**Dependency:** ISI-22 merged and post-merge verified  
**Server verification:** `DEFERRED_SERVER_VERIFICATION`

## 1. Purpose / business objective

Convert the existing SIMPA conceptual registry and evidence-quality analytics into a complete, testable working methodology for user evaluation while preserving strict separation between a software-supported methodology proposal and a human-validated institutional methodology.

## 2. Current baseline and dependencies

Already implemented in ISI-08/09:

- nine conceptual SIMPA dimensions and source types;
- 15 conceptual indicators;
- local-system profiles, actors, monitoring cycles, mappings and observations;
- versioned methodology infrastructure with draft/validated/retired lifecycle;
- computation refusal when methodology is unvalidated;
- provenance-preserving results;
- evidence-quality analytics;
- SIMPA AI synthesis with sensitive local-only policy and human review.

Not implemented: an owner/domain-approved production-grade SIMPA methodology with complete indicator definitions/formulas/reference data/thresholds, validation evidence and end-user guidance.

## 3. Detailed functional scope

Produce a complete **DRAFT/PROPOSED** SIMPA working methodology covering:

- methodology purpose, unit of analysis, monitoring-cycle semantics and intended use;
- indicator catalog with canonical code/name/definition, numerator/denominator or computation specification where evidence supports it;
- required source types and minimum evidence requirements;
- missing-data treatment;
- observation validation workflow;
- computation type and formula expression boundary;
- units, scaling/normalization where applicable and justified;
- time/reference-period alignment;
- aggregation rules only where supported;
- confidence/evidence-quality/provenance representation;
- versioning and change-control workflow;
- explicit limitations and prohibited interpretations;
- user workflow from source mapping -> observation -> validation -> computation -> monitoring snapshot -> synthesis -> human review;
- representative synthetic/reference test cases;
- visible distinction between evidence-quality metrics and actual social-system outcome indicators;
- no automatic conversion of conceptual indicators to validated state.

## 4. Technical scope / architecture

Extend `src/domains/simpa/` while preserving shared-platform boundaries. Methodology definitions should be versioned durable domain records; computations must use validated active versions only. Keep SIMPA domain semantics out of shared modules. Use shared data lineage, reporting, AI and governance services by reference.

## 5. Data model and migrations

Review existing `simpa_indicator_methodologies`, results and monitoring structures. Add only fields/tables necessary for production-methodology metadata such as structured calculation specification, source requirements, reference-data version, validation evidence/status, confidence rules or methodology package/version. All changes require Alembic and PostgreSQL acceptance.

## 6. API / UI / worker / AI implications

- API: methodology package/version browsing, draft editing/proposal, validation state, calculation preview/execute, provenance and reference-data endpoints as appropriate.
- UI: complete SIMPA methodology workspace, clear status badges (`CONCEPTUAL`, `DRAFT/PROPOSED`, `VALIDATED`, `RETIRED`), data requirement guidance and result provenance.
- Workers: calculations/backfills must pin methodology/reference-data versions and remain idempotent.
- AI: synthesis may explain evidence and limitations but may not validate methodology or invent formulas/weights/thresholds.

## 7. Security, privacy and tenant boundaries

SIMPA workspace data remains organization/workspace scoped. Sensitive SIMPA AI remains `local_only`. No person-level data model may be added merely to satisfy a methodology example; any future person-level processing requires explicit privacy/legal design. Methodology artifacts may be shared/public only through explicit governance.

## 8. Concrete deliverables

- detailed ISI-23 executable task spec;
- DRAFT/PROPOSED methodology package;
- indicator calculation/source/reference-data contracts;
- methodology/version UI and APIs;
- provenance/confidence/limitation presentation;
- deterministic synthetic reference cases;
- **detailed in-app Help for the entire SIMPA workflow**;
- **SIMPA User Guide** covering roles, setup, data mapping, monitoring cycles, observations, methodology states, calculations, analytics, AI synthesis, human review, limitations and troubleshooting;
- tests, migrations if required and evidence.

## 9. Required tests

Methodology state transitions; refusal of conceptual/draft computations unless explicitly preview-only; validated-version pinning; formula/reference-data versioning; source completeness; missing-data behavior; tenant/product isolation; provenance; deterministic reference cases; UI/API status wording; AI non-fabrication/human-review contract; Help/User Guide completeness checks; full regressions.

## 10. CI / quality gates

Focused SIMPA methodology tests, static policy preventing auto-validation/fabricated methodology, migration/native PostgreSQL where needed, full acceptance, exact-head CI and independent technical/domain-boundary review.

## 11. Evidence artifacts

Methodology version manifest, indicator/source/reference mapping, synthetic reference-case results, provenance examples, Help/User Guide completeness report, human-validation register and explicit list of elements still `DRAFT/PROPOSED`.

## 12. Acceptance criteria / Definition of Done

Software can represent and execute the approved subset of methodology deterministically, preserve provenance/versioning and present limitations. A complete user-testable DRAFT/PROPOSED methodology and documentation exist. Nothing is labelled institutionally `VALIDATED` without recorded human approval/evidence.

## 13. Explicit non-goals

No fabricated formulas, weights, thresholds, risk scores, causal effects, eligibility/benefit decisions, automatic social diagnosis, autonomous policy recommendation or false claim of scientific/institutional validation.

## 14. Risks and compatibility constraints

The largest risk is semantic overreach: turning software examples into apparent validated policy. Existing ISI-09 guard that refuses unvalidated methodology must remain. Changes must preserve historical result reproducibility through methodology/reference-data version pinning.

## 15. Human validation requirements

Domain experts/owner must review and explicitly approve every formula, weight, threshold, definition, reference source, interpretation and validation-state promotion. User testing feedback must be recorded separately from formal validation evidence.

## 16. Transition condition to next ISI task

ISI-24 may begin after the complete SIMPA DRAFT/PROPOSED working methodology, Help/User Guide, deterministic tests and repository gates are merged and post-merge green. Human validation may remain explicitly pending provided no unvalidated claim is promoted.

---

# ISI-24 — ORDO Production Methodology

**Current status:** `PLANNED / NOT IMPLEMENTED`  
**Methodology state target:** `DRAFT/PROPOSED` until explicit human validation  
**Dependency:** ISI-23 merged and post-merge verified  
**Server verification:** `DEFERRED_SERVER_VERIFICATION`

## 1. Purpose / business objective

Convert the ORDO domain foundation and evidence-only decision-support workflow into a complete, transparent and user-testable production-methodology proposal for destination planning, without fabricating predictive/causal certainty.

## 2. Current baseline and dependencies

Already implemented in ISI-10/11:

- ORDO five-pillar registry;
- conceptual dimensions/source types/indicators;
- destination profiles/assets/stakeholders/cycles/mappings/observations;
- methodology/version infrastructure;
- evidence-quality analytics;
- development goals and user-authored scenarios;
- evidence-only scenario assessment with `forecast_performed=false`;
- local-only ORDO decision-support AI profile with mandatory human review;
- strict SIMPA separation.

Not implemented: complete owner/domain-approved production methodology, validated reference calculations, evidence standards, scenario evaluation methodology or any validated forecasting model.

## 3. Detailed functional scope

Produce a complete **DRAFT/PROPOSED** ORDO methodology covering:

- methodology purpose, planning unit/destination scope and intended decisions;
- pillar/dimension/indicator interpretation;
- canonical indicator computation and source requirements only where supported;
- methodology/reference-data versions;
- evidence sufficiency and confidence rules;
- spatial/geographic scope and comparison rules where technically applicable;
- development-goal framing;
- scenario assumption/measures structure;
- evidence-only scenario evaluation methodology;
- explicit distinction between observed evidence, assumptions, modeled quantities and forecasts;
- if future predictive models are proposed, they remain disabled/unvalidated until separate evidence and human approval exist;
- provenance from data/source to indicator/snapshot/scenario assessment/report/AI synthesis;
- limitations, missing-data behavior and prohibited interpretations;
- deterministic synthetic/reference cases;
- version/change governance.

## 4. Technical scope / architecture

Extend `src/domains/ordo/`, not shared semantic modules. Reuse shared data, governance, reporting and AI infrastructure. Preserve current invariant that domain services do not call Ollama/providers directly. Scenario and methodology records must remain fully organization/workspace/ORDO scoped.

## 5. Data model and migrations

Review existing ORDO methodology/analytics/goals/scenarios/assessments. Add structured calculation/reference-data/spatial/methodology-package/version fields or tables only where necessary. Preserve historical result reproducibility and `forecast_performed` semantics.

## 6. API / UI / worker / AI implications

- API: methodology/version/reference data; calculation preview/execute; scenario methodology; evidence/provenance.
- UI: ORDO methodology workspace and transparent scenario/evidence workflow; visible DRAFT/PROPOSED versus VALIDATED labels.
- Workers: analytics/scenario recomputation pins exact versions and scope.
- AI: must distinguish evidence from assumptions and never convert a DRAFT methodology into a validated recommendation or forecast.

## 7. Security, privacy and tenant boundaries

Strict organization/workspace/ORDO scope; no SIMPA private namespace/data reuse. No sensitive destination/client data in public/shared AI context. Governance/classification from ISI-21 applies to sources, reports and AI evidence.

## 8. Concrete deliverables

- ISI-24 executable spec;
- ORDO DRAFT/PROPOSED methodology package;
- reference-calculation and evidence contracts;
- scenario/evidence methodology;
- spatial/reference-data contracts where applicable;
- deterministic reference cases;
- methodology UI/API;
- **detailed in-app ORDO Help**;
- **ORDO User Guide** covering destination setup, data mapping, observations, methodologies, analytics, goals, scenarios, assessments, AI synthesis, human review, limitations and troubleshooting;
- tests, migration(s) if required and evidence.

## 9. Required tests

Methodology states/versioning; calculation determinism; evidence insufficiency; scenario assumption/fact separation; `forecast_performed=false` preservation unless a separately validated model is explicitly introduced; SIMPA isolation; AI output contract; provenance; Help/User Guide completeness; migration/native PostgreSQL; full regressions.

## 10. CI / quality gates

Focused ORDO methodology/scenario tests, anti-fabrication policy tests, migration/native PostgreSQL as needed, full blocking acceptance, exact-head CI and independent technical/domain review.

## 11. Evidence artifacts

Methodology manifest, source/reference mapping, synthetic calculation/scenario cases, provenance samples, explicit forecast/non-forecast state, Help/User Guide completeness, human-validation register, exact-head CI/review state and server deferral.

## 12. Acceptance criteria / Definition of Done

ORDO has a complete transparent DRAFT/PROPOSED methodology usable for controlled user testing, with deterministic evidence-based calculations where defined, no hidden forecasting claims, full provenance and documentation. Validation labels require human evidence.

## 13. Explicit non-goals

No automatic destination ranking, fabricated formula, causal impact, visitor-volume forecast, investment-return forecast, guaranteed recommendation, autonomous scenario selection or unreviewed model prediction.

## 14. Risks and compatibility constraints

Risk of presenting planning assumptions as predictions, conflating evidence quality with destination performance and breaking historical scenario reproducibility. Every result must pin methodology/data/reference versions and disclose limitations.

## 15. Human validation requirements

Domain/owner approval is mandatory for formulas, evidence thresholds, interpretation, spatial comparison rules and any future predictive/causal model. Forecasting claims require separate validation evidence before activation.

## 16. Transition condition to next ISI task

ISI-25 begins after ORDO methodology/help/user-guide package is merged and post-merge green with all unvalidated elements explicitly marked. This gives MLOps a stable set of real SIMPA/ORDO AI use cases to govern.

---

# ISI-25 — Industrial AI / MLOps

**Current status:** `PLANNED / NOT IMPLEMENTED`  
**Dependency:** ISI-24 merged and post-merge verified  
**Server verification:** `DEFERRED_SERVER_VERIFICATION`

## 1. Purpose / business objective

Industrialize the shared AI capability so model/prompt behavior is reproducible, measurable, policy-controlled, reviewable and safely reversible across SIMPA and ORDO. The objective is not simply to call models; it is to manage AI as an auditable production capability.

## 2. Current baseline and dependencies

Already inherited from ISI-07/09/11 and later tasks: provider-neutral gateway, model/prompt/policy registries, structured output validation, AI job/attempt provenance, RAG namespace guards, local-only sensitive SIMPA policy, ORDO local decision-support profile, human review, observability, governance and stable domain methodologies. Missing: mature evaluation datasets/runs, release/promotion policy, drift/regression tracking, stronger prompt-injection/PII controls, circuit breakers, rollback and operational model/prompt change governance.

## 3. Detailed functional scope

Implement:

- model version/deployment profile lifecycle with draft/candidate/approved/retired states;
- prompt lifecycle and promotion gates tied to exact version/checksum;
- curated versioned evaluation datasets using synthetic/de-identified/approved content only;
- offline evaluation runner and metrics appropriate to each structured task;
- schema validity, groundedness/evidence-reference checks and safety-policy results;
- golden/reference cases for SIMPA and ORDO without pretending subjective quality is fully automatable;
- regression thresholds that block accidental degradation;
- RAG retrieval provenance: namespace, source/chunk IDs, content/version hashes and citation/evidence link where applicable;
- prompt-injection detection/containment boundary for retrieved/user content;
- PII/sensitive-data routing guards integrated with ISI-21 classification;
- retry, timeout, backoff and circuit-breaker policy;
- provider/model fallback rules consistent with `local_only` constraints;
- cost/token/latency telemetry where providers expose it safely;
- human-review traceability and reviewer decision provenance;
- model/prompt rollback capability to last approved version;
- change/evaluation manifest for every promoted AI configuration;
- failure/degraded-mode behavior when providers/models are unavailable.

## 4. Technical scope / architecture

Extend shared AI orchestration only; do not move domain prompts/semantics into shared code. Provider adapters remain behind the gateway. Evaluation tooling must run without production secrets/data. Domain execution references stable registry keys and immutable version snapshots.

## 5. Data model and migrations

Expected additions/extensions: evaluation datasets/cases/runs/results, model/prompt release/promotion records, safety-policy results, retrieval provenance references and rollback/change manifests. Reuse existing jobs/attempts/audit tables where appropriate; do not duplicate telemetry unnecessarily.

## 6. API / UI / worker / AI implications

- API: authorized registry/evaluation/release/review inspection and operations.
- UI: AI operations/governance views for model/prompt/eval state, failures and human review.
- Workers: evaluation batches and async AI jobs with concurrency/backoff/circuit-breaking.
- AI: structured output, provenance, sensitivity policy and human-review requirements become release gates rather than optional conventions.

## 7. Security, privacy and tenant boundaries

Sensitive/private data must not enter external providers against policy. RAG private namespaces remain org/product scoped. Evaluation datasets must be synthetic, de-identified or explicitly approved. Prompt injection from user/retrieved content must never override system/policy/authorization boundaries. Model outputs remain untrusted until schema/policy checks and required review pass.

## 8. Concrete deliverables

MLOps registry extensions, evaluation framework/datasets, regression gates, retrieval provenance, injection/PII guards, retry/circuit breakers, human-review provenance, rollback, APIs/UI, migration(s), tests, AI operations documentation and evidence.

## 9. Required tests

Registry lifecycle; immutable versions; eval reproducibility; structured output failure; regression threshold; RAG namespace/provenance; prompt-injection cases; sensitivity/provider policy; retry/circuit breaker; failure/degraded mode; rollback; human review; cross-product isolation; token/secret leakage; PostgreSQL/worker concurrency; full regressions.

## 10. CI / quality gates

Deterministic offline AI evaluation using approved stub/local fixtures; no CI dependence on production model service. Focused security/policy tests, migration/native PostgreSQL, full acceptance, exact-head GitHub Actions and independent AI/security review.

## 11. Evidence artifacts

Evaluation dataset manifests/checksums, evaluation run results, model/prompt promotion matrix, regression/safety results, retrieval provenance examples, rollback rehearsal, human-review state and explicit provider/server deferrals.

## 12. Acceptance criteria / Definition of Done

Every active domain AI capability can identify exact model/prompt/policy versions, has deterministic evaluation coverage, rejects invalid/unsafe outputs, preserves provenance, obeys sensitivity routing, supports human review and rollback, and passes repository CI/review gates.

## 13. Explicit non-goals

No autonomous institutional decisions, no broad external-provider enablement, no training on production/client data without separate approval, no unvalidated model quality claim, no replacement of domain methodology with LLM output and no production model/server mutation.

## 14. Risks and compatibility constraints

Evaluation metric misuse, hidden provider drift, prompt injection, data leakage, model fallback violating local-only policy and non-reproducible outputs are primary risks. Existing stable registry keys/API contracts must remain backward compatible or be versioned.

## 15. Human validation requirements

Human/domain reviewers define acceptable qualitative evaluation criteria and approve promotion of model/prompt versions for institutional use. Any external provider/data-processing policy requires explicit owner/privacy/security approval.

## 16. Transition condition to next ISI task

ISI-26 begins once AI execution has deterministic operational/evaluation controls, because performance/load testing must exercise realistic bounded AI workloads and degraded modes rather than an unstable model layer.

---

# ISI-26 — Performance, Load & Resilience Engineering

**Current status:** `PLANNED / NOT IMPLEMENTED`  
**Dependency:** ISI-25 merged and post-merge verified  
**Server verification:** `DEFERRED_SERVER_VERIFICATION`

## 1. Purpose / business objective

Establish evidence-based capacity and resilience characteristics before release candidacy. The objective is to identify bottlenecks/failure modes, define measurable performance budgets and prove graceful behavior under load using synthetic non-production environments.

## 2. Current baseline and dependencies

Inherited: observability, recovery, security, governance, industrial ingestion, stable domain methodologies, MLOps. Missing: formal workload profiles, repeatable load tests, performance budgets, resilience/failure-injection cases, soak tests and evidence-backed tuning.

## 3. Detailed functional scope

Implement:

- representative synthetic workload profiles for public API, authenticated API, Streamlit-backed API interactions, ingestion, queue workers, AI jobs and reporting;
- concurrency/throughput/latency/error-rate measurements;
- p50/p95/p99 latency and queue-wait metrics where meaningful;
- database connection/query hotspots and bounded query-count checks for critical paths;
- object-storage transfer performance for representative synthetic sizes;
- ingestion throughput/backpressure;
- worker saturation and retry behavior;
- AI timeout/provider-unavailable/circuit-breaker behavior;
- report generation load/time/memory checks;
- resilience tests for PostgreSQL/Redis/object-storage/AI temporary unavailability using controlled test doubles/ephemeral services;
- restart/retry/idempotency behavior;
- soak/stability test profile at CI-appropriate reduced scale plus optional longer non-production profile;
- explicit performance budgets and regression thresholds;
- evidence-backed tuning only where bottlenecks are demonstrated;
- capacity assumptions clearly marked as lab/non-production until ISI-28.

## 4. Technical scope / architecture

Use repository-safe load tooling and ephemeral/local services. Do not benchmark the production/current server. Instrument through ISI-18 metrics. Avoid architecture rewrites solely to improve microbenchmarks; changes must be measured and compatible.

## 5. Data model and migrations

No schema change is inherently required. Any performance-motivated indexes/schema changes must have explicit query evidence, Alembic migration, correctness regressions and downgrade plan.

## 6. API / UI / worker / AI implications

All major execution planes are measured. UI performance is assessed through backend/service behavior and focused browser checks where deterministic. Worker/AI/report queues must expose saturation/backpressure rather than silently losing jobs.

## 7. Security, privacy and tenant boundaries

All load data is synthetic. Load tooling cannot bypass authorization or reuse production credentials. Performance optimizations must not weaken tenant checks, logging redaction, audit events, security headers, step-up or AI policy.

## 8. Concrete deliverables

Workload catalog, load/resilience test harness, performance budgets, baseline/results reports, tuning changes where justified, failure-mode matrix, soak profile, dashboards/evidence based on existing telemetry, tests and `automation/evidence/ISI-26/`.

## 9. Required tests

API load; ingestion load; worker queue saturation; AI degraded mode; report generation; storage; temporary dependency failures; retries/idempotency; recovery after dependency return; performance-regression assertions; full functional/security regressions after tuning.

## 10. CI / quality gates

CI uses deterministic bounded performance smoke thresholds robust enough to catch major regression without flaky micro-timing. Longer load/soak profiles may run separately in non-production but must not be claimed if not executed. Exact-head CI and independent review remain mandatory.

## 11. Evidence artifacts

Workload definitions, environment description, baseline/final metrics, thresholds, failures/tuning rationale, soak/resilience results, limitations and explicit `NOT_SERVER_VALIDATED` capacity claims.

## 12. Acceptance criteria / Definition of Done

Critical workloads meet agreed repository/non-production budgets or have explicitly accepted limitations; dependency failures degrade safely; no data/authorization corruption occurs under concurrency; exact-head CI/review/merge/post-merge gates pass.

## 13. Explicit non-goals

No production load testing, no DDoS/security stress against live hosts, no unsupported capacity promise, no Kubernetes/cloud rewrite and no tuning that sacrifices correctness/security for benchmark numbers.

## 14. Risks and compatibility constraints

Flaky benchmarks, hardware-dependent thresholds, DB lock/contention changes, queue starvation and accidental security bypass through caching are key risks. Results must record environment and avoid false precision.

## 15. Human validation requirements

Owner/operations must approve final performance budgets and acceptable trade-offs. Real production capacity/SLA remains unverified until controlled server validation in ISI-28.

## 16. Transition condition to next ISI task

ISI-27 begins only after workload/resilience evidence is merged, significant regressions are resolved or explicitly accepted and post-merge CI is green.

---

# ISI-27 — Industrial Release Candidate & Acceptance Pack

**Current status:** `PLANNED / NOT IMPLEMENTED`  
**Dependency:** ISI-26 merged and post-merge verified  
**Server verification:** `DEFERRED_SERVER_VERIFICATION`

## 1. Purpose / business objective

Freeze a release candidate that is technically reproducible, security/quality accepted, recoverable, documented and operationally ready for an owner-controlled deployment decision. ISI-27 is the repository-side industrialization exit gate.

## 2. Current baseline and dependencies

Requires every prior industrial milestone ISI-17 through ISI-26 to be merged and post-merge green, with unresolved deferrals explicitly documented. No release candidate may be created from an unreviewed branch or partial task state.

## 3. Detailed functional scope

Implement/complete:

- final cross-cutting regression and acceptance pack;
- final database migration single-head and upgrade-path rehearsal;
- synthetic backup/restore/recovery rehearsal against release-candidate artifacts;
- security-control matrix and ISI-20 readiness closure status;
- data-governance/privacy control completeness;
- ingestion/data-platform operational completeness;
- SIMPA and ORDO methodology state inventory, distinguishing DRAFT/PROPOSED from human VALIDATED;
- SIMPA/ORDO in-app Help and User Guide completeness;
- AI model/prompt/evaluation/rollback manifest;
- performance/resilience acceptance summary;
- immutable build artifact metadata and checksums;
- SBOM/provenance/signing target defined by ISI-17 and realized to the practical approved level;
- release notes/changelog;
- configuration inventory and required external secrets list without secret values;
- deployment preflight checklist for ISI-28;
- rollback manifest/procedure;
- known-issues/residual-risk register;
- explicit go/no-go decision package.

## 4. Technical scope / architecture

No major new feature architecture belongs here. ISI-27 integrates, verifies, freezes and packages the accepted system. Any substantial feature gap discovered here should normally return to the responsible preceding task/fix rather than being hidden inside release packaging.

## 5. Data model and migrations

No gratuitous schema change. Validate a clean upgrade from supported baseline to final head and a fresh install to head. Verify downgrade/rollback strategy according to migration/recovery policy; destructive/non-reversible migrations must be explicitly identified and operationally mitigated.

## 6. API / UI / worker / AI implications

All surfaces are release-tested as an integrated product: public/API, authenticated UI, domain workflows, workers, ingestion, reporting and AI. Version/build identifiers and release metadata should be discoverable where appropriate without leaking sensitive internals.

## 7. Security, privacy and tenant boundaries

Final acceptance re-runs tenant/SIMPA/ORDO isolation, authentication/MFA/step-up/session, governance/export, secret scanning, SAST/dependency audit, AI policy and evidence/redaction controls. Release artifacts must not embed production secrets.

## 8. Concrete deliverables

Release candidate tag/artifact strategy, immutable checksums, SBOM/provenance/signing artifacts as approved, release notes, complete acceptance report, recovery rehearsal, configuration/deployment checklist, rollback manifest, known issues, SIMPA/ORDO documentation completeness, final evidence under `automation/evidence/ISI-27/`.

## 9. Required tests

Full repository tests; exact migration/recovery rehearsal; security regression suite; governance/data-platform/domain methodology cases; AI evaluation/rollback; performance smoke/resilience; build/Compose; documentation link/completeness checks; installation/startup smoke in ephemeral non-production environment.

## 10. CI / quality gates

All required ISI-17 gates plus all task-added blocking gates must be green on the exact release-candidate commit. Artifact checksum/SBOM/provenance steps must be deterministic. Independent final review is mandatory.

## 11. Evidence artifacts

Master acceptance matrix, exact SHA/tag, CI run IDs, build digests, SBOM/provenance/signing state, migration/recovery results, security/governance/AI/performance summaries, methodology validation state, documentation completeness, known issues and server-deployment deferral.

## 12. Acceptance criteria / Definition of Done

One exact immutable commit/artifact set has all repository acceptance green, independent review complete, release notes/config/rollback/recovery/documentation complete, no unresolved critical blocker and an explicit owner-facing go/no-go package. Production is still untouched.

## 13. Explicit non-goals

No current-server deployment, DNS/ingress mutation, production secret injection, production data migration, live penetration test or production verification. Those belong exclusively to separately authorized ISI-28.

## 14. Risks and compatibility constraints

Last-minute feature creep, documentation drift, artifact/source mismatch, untracked migration assumptions and overclaiming DRAFT methodology or lab performance as production-validated are primary risks. Freeze discipline is mandatory.

## 15. Human validation requirements

Owner accepts the release candidate/go-no-go package. Domain experts confirm methodology validation labels. Security/privacy/operations residual risks requiring human acceptance are explicitly listed. Approval of ISI-27 does **not automatically authorize ISI-28**.

## 16. Transition condition to next ISI task

ISI-28 remains `OWNER_GATED` even after ISI-27 completion. It begins only when the owner provides fresh explicit authorization to touch the current server and identifies/accepts the release candidate to deploy.

---

# ISI-28 — Current Server Controlled Upgrade

**Current status:** `DEFERRED / OWNER_GATED / EXECUTION NOT AUTHORIZED`  
**Dependency:** accepted ISI-27 release candidate  
**This is the only milestone in this roadmap permitted to touch the current server, and only after new explicit owner approval.**

## 1. Purpose / business objective

Safely deploy the accepted industrial release candidate to the existing ISI server with a controlled, evidence-backed preflight, backup, migration, validation and rollback process that minimizes service/data risk.

## 2. Current baseline and dependencies

Not executable now. Future prerequisites:

- ISI-17 through ISI-27 merged and accepted;
- exact owner-approved RC SHA/tag/artifact digest;
- ISI-27 go/no-go pack;
- known server topology and access approved by owner;
- explicit maintenance window/operational decision;
- verified backup destination and rollback prerequisites.

## 3. Detailed functional scope

Once separately authorized, the controlled procedure is expected to include:

- identify exact current server/environment and deployed version without exposing secrets;
- inventory running services, versions, storage and configuration relevant to the approved deployment;
- preflight disk/memory/database/object-storage/migration compatibility;
- establish change/maintenance window and abort criteria;
- create/verify production PostgreSQL and application-object backup using ISI-19 tooling or approved equivalent;
- capture current deployment/configuration manifest with secrets redacted;
- verify restore/rollback prerequisites before destructive migration;
- stage immutable approved release artifacts;
- apply configuration changes with external secret injection, never source-controlled secret values;
- controlled service stop/start or rolling procedure appropriate to existing topology;
- run database migrations exactly once with logged revision transition;
- perform health/readiness/smoke checks;
- verify authentication, tenant/product isolation, critical SIMPA/ORDO workflows, reporting, workers, storage and AI gateway using approved non-destructive smoke cases;
- validate observability and operational diagnostics;
- validate production backup/recovery/RPO-RTO assumptions to the permitted extent;
- execute rollback immediately if predefined abort conditions occur;
- capture server verification evidence and final owner-facing status.

## 4. Technical scope / architecture

Deployment must preserve the accepted architecture and existing server topology unless ISI-27/owner-approved deployment design explicitly changes it. No casual production `git pull` is the target operating model; immutable accepted artifacts are preferred. DNS/ingress/SMTP/Ollama/secrets may only be changed if specifically included in the owner-approved ISI-28 execution plan.

## 5. Data model and migrations

Apply only migrations already accepted in the RC. Before migration, verify backup/rollback conditions. Record current and target Alembic revisions. Do not invent or patch production schema manually. Any unexpected production data/schema condition triggers abort/reassessment rather than ad-hoc destructive repair.

## 6. API / UI / worker / AI implications

Post-deployment smoke must cover FastAPI, authenticated Streamlit, background queues/workers, storage, SIMPA/ORDO workflows and shared AI routing according to the approved scope. Production model/provider changes are not implicit; they require explicit configuration approval.

## 7. Security, privacy and tenant boundaries

Production credentials/data must never be copied to chat, source, evidence or logs. Evidence uses redacted identifiers/results. Tenant/product isolation and privileged security paths receive non-destructive smoke verification. Access is least-privilege and limited to the approved operation.

## 8. Concrete deliverables

Owner-approved execution plan, preflight report, verified pre-change backup, exact release/artifact manifest, migration log, smoke/readiness results, rollback readiness/result, production configuration delta with secrets redacted, server verification evidence and final deployment report.

## 9. Required tests

Preflight health/readiness, backup verification, migration state, API/UI critical smoke, auth/session/MFA/step-up as applicable, SIMPA/ORDO isolation, storage, worker queue, report, AI gateway, observability and post-deployment backup/recovery checks. Tests must be non-destructive unless a specific destructive test is explicitly approved.

## 10. CI / quality gates

No server deployment unless the exact RC artifact already passed ISI-27 CI/review. ISI-28 adds deployment-specific preflight, migration, smoke and rollback gates; any failed critical gate triggers abort/rollback according to the approved runbook.

## 11. Evidence artifacts

Create a redacted `automation/evidence/ISI-28/` pack only after authorization/execution, containing owner authorization reference, RC SHA/digest, backup verification, preflight, migration revisions, smoke/readiness results, rollback status, warnings and final `SERVER_VERIFIED` or failure/rollback state. No secrets or sensitive production payloads.

## 12. Acceptance criteria / Definition of Done

`SERVER_VERIFIED` is allowed only after the owner-approved RC is deployed, migrations and critical smoke pass, service health/readiness is acceptable, no unresolved critical blocker remains and rollback/backup evidence is captured. If deployment is rolled back, ISI-28 is not complete merely because rollback succeeded.

## 13. Explicit non-goals

Before explicit authorization: **all execution is a non-goal**. Even after authorization, unrelated server modernization, OS-wide upgrades, arbitrary DNS/SMTP/model changes or infrastructure redesign are out of scope unless separately approved.

## 14. Risks and compatibility constraints

Highest-risk milestone: production data loss, migration incompatibility, service outage, configuration drift, secret exposure, storage mismatch and rollback failure. All steps therefore require exact artifact identity, backup verification, abort criteria and minimal-change discipline.

## 15. Human validation requirements

Fresh explicit owner authorization is mandatory before any SSH/SCP/server/DNS/ingress/production SMTP/production secret/data/server Ollama action. Owner approval is also required for maintenance window, material configuration changes, abort/rollback decisions where not automatic and final production acceptance.

## 16. Transition condition after ISI-28

Industrialization program ISI-17 -> ISI-28 is complete only when ISI-28 is explicitly owner-authorized and reaches evidence-backed `SERVER_VERIFIED`. Until then, repository release readiness may be complete while production deployment remains deliberately deferred.

---

# Program-wide implementation ledger

This ledger answers the canonical question **what exists today versus what still has to be built**.

## Implemented and merged

- **ISI-17:** governance, deterministic CI, repository safety, evidence and release controls.
- **ISI-18:** privacy-safe observability, metrics, correlation and readiness diagnostics.
- **ISI-19:** deterministic backup/restore/recovery tooling and CI recovery rehearsal.

## Active implementation

- **ISI-20:** detailed spec exists; enterprise-security implementation must be completed, synchronized to PR #10, exact-head CI verified, independently reviewed and merged. A green CI result on an old/spec-only head does not prove implementation.

## Not yet implemented

- **ISI-21:** complete data-governance/privacy control plane.
- **ISI-22:** industrial connector/ingestion/schema/DQ/reconciliation/backfill/lineage platform.
- **ISI-23:** complete SIMPA DRAFT/PROPOSED production methodology + in-app Help + User Guide.
- **ISI-24:** complete ORDO DRAFT/PROPOSED production methodology + in-app Help + User Guide.
- **ISI-25:** industrial AI/MLOps evaluation, governance, safety, provenance, resilience and rollback.
- **ISI-26:** repeatable performance/load/resilience engineering and evidence.
- **ISI-27:** immutable industrial release candidate and integrated acceptance pack.

## Explicitly deferred / not authorized

- **ISI-28:** current-server controlled upgrade. No server, DNS, ingress, production SMTP, production secrets/data or server Ollama action is authorized until fresh explicit owner approval.

---

# Required maintenance of this Master Plan

For every task transition:

1. Update the task's current status and exact merged/active references without rewriting historical evidence.
2. If implementation reveals a material scope/architecture change, update this plan explicitly in the same reviewed change or before claiming completion.
3. Create/maintain the corresponding detailed task spec under `automation/specs/` derived from these 16 sections.
4. Keep `automation/tasks.json` and `automation/STATUS.md` synchronized.
5. Never change `NOT IMPLEMENTED` to `IMPLEMENTED` based solely on agent narrative; require repository code/tests/evidence.
6. Never change a methodology from `DRAFT/PROPOSED` to `VALIDATED` without explicit recorded human approval and supporting evidence.
7. Never change `DEFERRED_SERVER_VERIFICATION` to `SERVER_VERIFIED` without an explicitly authorized server execution and evidence.
8. Never silently remove a security, privacy, tenant-isolation, recovery, AI-human-review or CI requirement to make a later task easier.

**End of canonical ISI industrialization roadmap.**
