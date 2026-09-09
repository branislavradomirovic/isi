# ISI Autonomous Industrialization Master Plan

Status: **OWNER_APPROVED planning baseline — 2026-09-09**.

This plan is binding for the autonomous industrialization track unless the owner explicitly approves a later change.

## 1. Purpose

Industrialize the existing ISI platform and its two domain applications, SIMPA and ORDO, through specification-driven autonomous development on GitHub while preserving the current server and deployment setup until a separately approved release/deployment phase.

The immediate objective is not a new infrastructure platform and not a new server. The objective is to make the codebase, data/AI lifecycle, methodology, security, quality assurance, observability, release engineering, and deployment automation sufficiently mature that a final release can later be pushed to the current server in one controlled upgrade.

## 2. Locked product model

- ISI is the institutional platform of the Institute for Social Inclusion.
- SIMPA and ORDO are the only domain applications in the current product architecture.
- SIMPA and ORDO remain domain-isolated while reusing shared infrastructure.
- COSMOS is not introduced as a software layer, product, domain, route, tenant, namespace, or menu item.
- Existing FastAPI + Streamlit + PostgreSQL + Redis/RQ + MinIO/S3-compatible storage + shared AI gateway architecture is preserved unless a later accepted ADR explicitly changes it.
- Existing server topology remains the target deployment topology during this industrialization program.

## 3. Autonomous-development operating model

Every industrialization task follows this chain:

`specification -> dedicated branch -> Codex implementation -> deterministic tests -> pull request -> CI/security/review gates -> owner approval -> merge -> next task`

No task is complete merely because an agent claims completion. Status is evidence-based.

### Verification labels

- `IMPLEMENTED`: required code and local task tests pass.
- `CI_VERIFIED`: repository CI acceptance passes.
- `SERVER_VERIFIED`: explicitly approved server acceptance has passed.
- `DEFERRED_SERVER_VERIFICATION`: implementation is ready but the current task intentionally did not touch the server.

### Owner-facing task states

Use the following operational sequence for human tracking:

`SPEC_READY -> IMPLEMENTING -> IMPLEMENTED -> CI_VERIFIED -> REVIEW_VERIFIED -> MERGE_READY -> MERGED`

A failed required gate returns the task to `IMPLEMENTING`; the gate must not be weakened simply to obtain green status.

## 4. Server freeze during industrialization

Until the owner explicitly authorizes deployment:

- no SSH-based implementation work;
- no production DNS changes;
- no central-ingress changes;
- no production SMTP changes;
- no production credential changes;
- no server Ollama model mutation;
- no production data migrations;
- no automatic deployment;
- no use of production secrets in GitHub/Codex development context.

The current server is a deployment target only.

## 5. Industrialization workstream

### ISI-17 - Autonomous Development Harness + CI

Goal: make the repository itself capable of governing autonomous development.

Deliverables:

- binding `AGENTS.md`;
- autonomous-development lock and release policy;
- standard task-spec template;
- evidence format;
- owner-facing task status/dashboard convention;
- GitHub Actions CI baseline;
- deterministic dependency resolution/lock or constraints mechanism;
- formatting/lint/type/dependency/test gates;
- database/Alembic validation including isolated PostgreSQL migration acceptance;
- Docker Compose validation without using production/server runtime;
- `.dockerignore` and container-build hygiene;
- secret, dependency-vulnerability and Python SAST scanning;
- static policy guard proving autonomous workflows cannot execute server deployment/SSH/SCP/DNS mutation paths;
- fail-closed local acceptance runner;
- branch/PR completion contract;
- explicit server-verification deferral mechanism.

Exit condition: a Codex-created PR can be objectively accepted or rejected by repository gates without touching the server.

### ISI-18 - Observability & Operational Diagnostics

Goal: instrument the application so failures and degradation can be diagnosed before and after deployment.

Deliverables:

- correlation/request IDs end-to-end;
- structured logging conventions;
- FastAPI request/error/latency metrics;
- worker/queue metrics;
- AI job/provider/model/prompt metrics;
- data-ingestion metrics;
- DB/Redis/object-storage health instrumentation where application-visible;
- application-level readiness diagnostics;
- privacy-safe logging tests;
- dashboard/export contracts without requiring the future production monitoring host.

Server dashboards may remain deferred; instrumentation must be fully code/CI verified.

### ISI-19 - Backup, Restore & Disaster-Recovery Automation

Goal: make recovery deterministic and testable.

Deliverables:

- versioned backup/restore tooling for PostgreSQL and object storage;
- backup metadata/checksums;
- encryption/retention hooks;
- restore verification;
- synthetic full recovery test in CI-compatible environments;
- documented RPO/RTO targets by deployment class;
- rollback-safe migration strategy.

No production backup mutation in this task.

### ISI-20 - Enterprise Security Completion

Goal: close the gap between current hardening and institutional-grade controls that can be code-completed without a new server.

Deliverables:

- MFA-ready authentication architecture and implementation where feasible without external provider dependency;
- stronger session/device administration;
- privileged-action controls;
- security-event coverage expansion;
- security regression suite;
- dependency/SAST/container/secret scanning integration;
- formal RBAC/entitlement test matrix;
- penetration-test readiness pack;
- secret-manager abstraction without requiring production secret-manager deployment.

External pen test and production IdP integration remain separate acceptance items where external systems are required.

### ISI-21 - Data Governance & Privacy Controls

Goal: make data ownership, provenance, sensitivity, retention, and isolation explicit and enforceable.

Deliverables:

- data classification model;
- dataset/source ownership metadata;
- lineage/provenance contracts;
- retention/purge/anonymization hooks;
- tenant/product boundary tests;
- auditability of sensitive data access;
- export controls;
- privacy-impact documentation pack;
- explicit rule that client/institution data never becomes cross-tenant/cross-product shared knowledge automatically.

### ISI-22 - Industrial Data Platform

Goal: evolve ingestion from framework capability to robust production-grade data engineering.

Deliverables:

- versioned source connector contracts;
- schema mapping/versioning;
- incremental/idempotent imports;
- deduplication/reconciliation;
- quarantine/error queues;
- source freshness and quality checks;
- backfill support;
- ingestion lineage;
- standardized canonical ingestion boundary for SIMPA and ORDO;
- reference connector acceptance fixtures.

Real external institution credentials are not required to complete the platform capability.

### ISI-23 - SIMPA Production Methodology

Goal: convert SIMPA's existing methodology infrastructure into a validated, versioned, reproducible analytical product.

Deliverables:

- formal indicator registry contract;
- methodology version lifecycle;
- calculation tests with reference datasets;
- LISI methodology specification and implementation when domain methodology is owner-approved;
- sub-indices/weights/normalization/missing-data rules/versioning/provenance;
- evidence-quality/confidence representation;
- social-map/GIS-ready data model and interfaces;
- policy-monitoring/evaluation workflow;
- explainability/reporting contracts.

Critical rule: Codex must not invent indicator formulas, LISI weights, thresholds, causal claims, or policy conclusions. Domain methodology must come from owner-approved specifications/documents.

### ISI-24 - ORDO Production Methodology

Goal: convert ORDO's evidence-only analytical workflow into a production methodology platform without fabricating predictive capability.

Deliverables:

- validated ORDO indicator-methodology registry;
- reference datasets and calculation tests;
- spatial/GIS-ready domain contracts;
- scenario evidence model;
- development-goal evaluation framework;
- methodology provenance/versioning;
- readiness for future forecasting models without representing unvalidated models as predictions.

Forecasting/causal models are implemented only if separate evidence-backed model specifications are approved.

### ISI-25 - Industrial AI / MLOps

Goal: make AI behavior measurable, versioned, reversible, and auditable.

Deliverables:

- model registry/version contract;
- prompt registry/version enforcement;
- evaluation datasets and regression harness;
- structured-output validation;
- evidence/RAG provenance contracts;
- prompt-injection and unsafe-context tests;
- PII/sensitivity guards;
- retry/timeout/circuit-breaker behavior;
- provider/model fallback policies;
- human-review traceability;
- model/prompt rollback;
- inference quality/latency accounting.

Human-in-the-loop remains a permanent decision-support requirement.

### ISI-26 - Performance, Load & Resilience Engineering

Goal: establish measurable capacity and failure behavior.

Deliverables:

- target workload profiles;
- API/load tests;
- ingestion stress tests;
- queue/worker concurrency tests;
- AI-job concurrency tests;
- large-report tests;
- soak tests where feasible in CI/staging;
- controlled failure tests for Redis/DB/object-store/AI/SMTP dependencies;
- performance budgets and documented bottlenecks;
- index/pooling/worker tuning changes backed by measurements.

The current server's final capacity remains `DEFERRED_SERVER_VERIFICATION` until deployment testing.

### ISI-27 - Industrial Release Candidate & Acceptance Pack

Goal: produce one release candidate that is technically ready for controlled deployment to the current server.

Deliverables:

- full CI/security/quality gate green;
- migration rehearsal green;
- backup/restore rehearsal green;
- performance acceptance green at defined non-server workload baseline;
- SIMPA methodology acceptance state explicit;
- ORDO methodology acceptance state explicit;
- security/privacy/UAT checklists;
- versioned release notes;
- signed/immutable release artifact strategy;
- deployment manifest;
- rollback manifest;
- deferred server-verification checklist.

Exit condition: owner may authorize one controlled deployment task.

### ISI-28 - Current Server Controlled Upgrade

Status: intentionally deferred and not executable during the autonomous industrialization track.

Goal: deploy the accepted release candidate to the existing server with backup, migration, health checks, smoke tests, AI/worker checks, and rollback.

This is the only phase allowed to touch the current server, DNS, ingress, real SMTP, production secrets, or production data, and only after explicit owner approval.

## 6. Task dependency model

Default serial dependency:

`ISI-17 -> ISI-18 -> ISI-19 -> ISI-20 -> ISI-21 -> ISI-22 -> ISI-23 -> ISI-24 -> ISI-25 -> ISI-26 -> ISI-27 -> ISI-28`

Individual implementation subtasks may run in parallel inside a task, but task baselines remain serial unless the owner approves a dependency change.

## 7. Codex implementation contract

For each task Codex must receive:

- exact baseline/ref;
- objective;
- locked architecture;
- required behavior;
- DB/API/UI/worker/configuration impact;
- security/privacy constraints;
- required tests;
- exact acceptance commands;
- required evidence;
- explicit non-goals;
- forbidden changes;
- completion definition.

Codex must implement on a dedicated branch and open/update a PR. A reviewer agent may inspect the diff against the specification, but CI and deterministic acceptance remain authoritative.

Every implementation PR must expose a concise owner-facing status block with task ID, baseline/head SHAs, current state, required CI jobs, evidence path, known warnings and deferred server-verification status.

## 8. Human gates

Human approval remains required at minimum for:

- architecture changes;
- new external dependencies with material operational impact;
- security-policy changes;
- SIMPA/ORDO methodology validation;
- claims of predictive/causal capability;
- merge of major industrialization milestones during the initial autonomous-development phase;
- any server/deployment action;
- any production secret or data mutation.

## 9. Final deployment concept

The final server action should be release-based rather than a casual `git pull`.

Expected deployment sequence:

1. verify currently deployed release and clean operational state;
2. backup DB/object storage/configuration;
3. fetch exact approved release/tag;
4. build/pull exact application artifacts;
5. run migration preflight;
6. apply migrations;
7. start/update services;
8. readiness/health checks;
9. API/UI/worker/AI smoke tests;
10. data-integrity checks;
11. record deployed version and evidence;
12. rollback automatically or procedurally if a hard acceptance gate fails.

## 10. Owner approval record

Owner approval was explicitly given on 2026-09-09 for:

- the locked ISI -> {SIMPA, ORDO} product architecture;
- exclusion of COSMOS from the current runtime/application architecture;
- server freeze through ISI-27;
- the serial ISI-17 through ISI-28 industrialization sequence;
- the human approval boundaries above;
- use of ISI-17 as the first Codex implementation task;
- the repository-audit findings as binding ISI-17 implementation input.

Planning changes that materially alter these points require a new explicit owner approval.
