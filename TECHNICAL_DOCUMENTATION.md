# ISI Technical Documentation

**Version:** 1.9
**Status:** Controlled living technical document  
**Last updated:** 2026-10-10
**Canonical repository:** `branislavradomirovic/isi`  
**Last CI and recorded server checkpoint:** `f587ed0a194043cadf7190ceae9f6f29c1d76c55` (run37914718258: all12 exact required jobs success; bounded preproduction deployment recorded)
**Pre-reconciliation governance baseline:** `ff573b3d76cf29581cb19c255821e9b4c4841108`  
**Current database migration head:** `20261008_0037`; recorded deployed head `20261008_0037`

> This document is the concise technical authority for the current ISI as-built platform and its owner-approved deployment target. The MasterPlan remains the canonical architecture/governance/roadmap authority, and code/tests remain the as-built implementation truth. Live production-server state is not inferred from repository source: current-server verification remains deferred to ISI-28.

## Current reconciled snapshot — 2026-10-10

29A–29F software is CI_VERIFIED / REVIEW_VERIFIED at exact main f587ed0a194043cadf7190ceae9f6f29c1d76c55, required acceptance37914718258 completed/success (all12 jobs). Recorded signed ISI-only deployment passed in PREPRODUCTION_TESTING, schema20261008_0037; automation/evidence/ISI-29F/release/closeout.json. No fresh server probe in30A. Full institutional production remains unverified; SMTP pending, new backups owner-deferred, extraction quality UNCALIBRATED.

ISI-30A IN_PROGRESS presentation candidate: context transitions, accessible responsive shared style and reachable existing ORDO scenarios; no schema/API/worker/provider/dependency/model/RBAC change. Backend remains authorization truth. Sequenced remaining customer authoring/Help/manual work in ISI-30 plan; no new CI/server verification inherited.

## 1. Purpose and scope

ISI is the institutional technology platform of the Institute for Social Inclusion. It contains two domain products only:

- **SIMPA** - social-protection intelligence and monitoring at aggregate/system level;
- **ORDO** - destination intelligence, planning, forecasting and scenario support.

SIMPA and ORDO share identity, security, data, AI/MLOps, reporting, audit and operational infrastructure while preserving separate domain models, indicator/methodology contracts, private namespaces, analytics and user workflows. **COSMOS is not an ISI application/domain/runtime layer.**

The platform currently includes a public institutional website, an authenticated application shell, governed data ingestion/analytics, SIMPA and ORDO domain workflows, shared AI/MLOps governance, deterministic reporting, administration, security, observability and repository-side recovery controls.

## 2. Current industrialization status

| Phase | Current state |
|---|---|
| ISI-17 Autonomous Development Harness + CI | COMPLETE |
| ISI-18 Observability & Operational Diagnostics | COMPLETE |
| ISI-19 Backup, Restore & DR | COMPLETE; server verification deferred |
| ISI-20 Enterprise Security | COMPLETE / CI_VERIFIED |
| ISI-21 Data Governance & Privacy | COMPLETE / CI_VERIFIED |
| ISI-22 Industrial Data Platform | COMPLETE / CI_VERIFIED |
| ISI-23 SIMPA Production Methodology + Help/XAI | COMPLETE / CI_VERIFIED |
| ISI-24 ORDO Production Methodology + Help/XAI | COMPLETE / CI_VERIFIED |
| ISI-25 Industrial AI / MLOps | IMPLEMENTATION COMPLETE / ACCEPTED ON MAIN / NOT CI_VERIFIED |
| ISI-26 Performance, Load & Resilience | IMPLEMENTATION COMPLETE / ACCEPTED ON MAIN / NOT CI_VERIFIED |
| ISI-27 Industrial Release Candidate | COMPLETE / exact RC CI_VERIFIED;f587ed0 later consolidated acceptance |
| ISI-28 Current Server Controlled Upgrade | IN_PROGRESS /f587ed0 recorded preproduction deployment; full production gates open |

ISI-25A is accepted at `f0047321ee4410522697144ecfa464087f1b83bc`. ISI-25B is accepted at `7e11ee2a6f7546eacc3207e15cacfc35f6d04f3e`. Hosted full acceptance was deliberately not run for those development checkpoints under the owner CI-cost policy; `CI_VERIFIED` is therefore not claimed for ISI-25.

## 3. Technology stack

### 3.1 Language and application framework

| Component | Current repository baseline |
|---|---|
| Python | `>=3.11,<3.13`; canonical dev/CI baseline Python 3.11 |
| FastAPI | 0.141.1 |
| Uvicorn | 0.52.4 |
| Starlette | 1.6.0 |
| Streamlit | 1.63.0 |
| Jinja2 | 3.1.6 |
| Pydantic | 2.13.5 |
| pydantic-settings | 2.15.0 |
| SQLAlchemy | 2.0.52 |
| Alembic | 1.19.2 |
| psycopg | 3.3.5 |
| Redis client | 6.4.0 |
| RQ | 2.12.0 |
| HTTPX | 0.28.1 |
| boto3 | 1.43.91 |
| statsmodels | 0.15.0 |
| Argon2 | argon2-cffi 25.1.0 |

`requirements.lock` is the dependency lock authority for normal development installation.

### 3.2 Server-shaped infrastructure in the ISI repository

`docker-compose.server.yml` defines an independent Compose project named `isi` with:

- PostgreSQL `17-alpine`;
- Redis `7-alpine` with AOF enabled;
- MinIO/S3-compatible object storage;
- one-shot MinIO bucket initialization;
- Alembic migration service;
- FastAPI `api`;
- Streamlit `streamlit`;
- `data-worker`;
- `ai-worker`;
- profile-gated `edge` Nginx only for pre-cutover compatibility;
- profile-gated Mailpit only for pre-cutover/non-production mail capture.

The ISI repository does not own the final shared production edge.

## 4. Application architecture

### 4.1 Presentation boundary

The public institutional site uses FastAPI + Jinja2 + HTML/CSS/SVG/minimal JavaScript. The authenticated analytical application uses Streamlit while FastAPI remains backend authorization/data truth.

Current FastAPI routing includes:

- public institutional routes/static/media;
- authentication;
- app context and authenticated shell;
- data platform;
- AI/MLOps;
- SIMPA domain + analytics;
- ORDO domain + analytics;
- reporting;
- administration;
- deployment/readiness diagnostics.

Health endpoint: `/api/v1/health`.

The authenticated Streamlit application is configured under `/app` in the server-shaped Compose topology.

### 4.2 Domain separation

SIMPA and ORDO may share stable platform abstractions only. Product-specific indicators, methodology, prompts, schemas, analytics and policy semantics remain in separate domain packages.

Authorization is re-evaluated against organization, membership, product entitlement, role/permission and workspace scope. Knowing an object UUID is never sufficient authorization.

## 5. Shared-host deployment target and ingress

### 5.1 Owner-locked shared edge

The current owner-approved target is:

- shared edge container: `central-ingress-nginx-1`;
- Compose project: `central-ingress`;
- service: `nginx`;
- Krcuga shared-host application port: `8443`;
- OralScanXAI shared-host application port: `8444`;
- ISI shared-host application port: `8445`;
- ISI public target: `https://isi.opus.rs:8445/`.

**Caddy is not current ISI target authority.** Older Caddy statements are historical infrastructure evidence only.

### 5.2 ISI integration boundary

The ISI `api` and `streamlit` services attach to the external Docker network `isi_ingress` with aliases:

- `isi-api` -> API port `8000`;
- `isi-streamlit` -> Streamlit port `8501`.

Target routing contract:

```text
https://isi.opus.rs:8445/
        |
        v
central-ingress-nginx-1
        |
        +-- /app/      -> isi-streamlit:8501
        +-- /, /api/  -> isi-api:8000
```

The exact live certificate, NAT/listener and central-Nginx route state must be freshly read-only audited under ISI-28 before any production mutation.

### 5.3 Pre-cutover `isi-edge`

The repository `edge` service and `docker/nginx/isi-server-precutover.conf` are **COMPATIBILITY/PRECUTOVER ONLY**:

- profile `precutover`;
- default loopback bind `127.0.0.1:8445`;
- local TLS certificate mount;
- noindex/nofollow;
- routing to internal API/Streamlit.

It is not final production ingress authority and must not be promoted into a parallel edge.

## 6. Data and persistence architecture

### 6.1 PostgreSQL

PostgreSQL is authoritative relational persistence. The server-shaped target uses PostgreSQL 17. Schema evolution is Alembic-controlled; current repository head is `20260918_0034`.

Major persistence families include:

- organizations, users, memberships, product access, roles and workspaces;
- authentication sessions/tokens/invitations/MFA foundation;
- security rate limits/events;
- shared data sources, immutable versions, ingestion jobs and governed analytical artifacts;
- knowledge/RAG metadata and embeddings;
- AI models/prompts/policies/jobs/attempts/audit;
- AI registrations, fallback relations, evaluation datasets/runs/results/reviews;
- ISI-25B promotion benchmarks, capability thresholds, promotion decisions, runtime/circuit state and drift snapshots;
- SIMPA domain/methodology/analytics/statistical evidence;
- ORDO domain/evidence/spatial/statistical/time-series/forecast evidence;
- versioned reports/reviews/exports;
- administration/audit state.

### 6.2 Redis/RQ

Redis is queue transport, not business authority. Data jobs use queue `isi-data` and AI jobs use `isi-ai` when backend `rq` is configured. Development can use deterministic inline execution through the same worker functions.

Volatile Redis state must never be the sole copy of durable business truth.

### 6.3 Object storage

Raw source bytes are stored outside PostgreSQL through the shared storage abstraction:

- local content-addressed filesystem for development;
- S3-compatible backend for staging/production-shaped deployment;
- MinIO is the repository server-shaped S3-compatible implementation.

Storage keys are organization/product/workspace scoped and content-addressed by SHA-256. Production-shaped profiles fail closed unless S3 configuration and credentials are explicitly provided.

## 7. Governed data and analytical boundary

The canonical data flow is:

`External source -> source/version -> governed ingestion -> normalized records -> governance/dedup/quarantine -> immutable governed output -> reproducible dataset/snapshot/features -> deterministic analytics -> bounded AI interpretation/reporting -> human review`

Key rules:

- missing, zero, not-collected, suppressed and not-applicable states are not silently conflated;
- source/data provenance is preserved;
- downstream analytics may not bypass the governed reproducible boundary by reading arbitrary raw source bytes;
- numerical/statistical truth is owned by deterministic/versioned analytical code or explicitly registered ML models;
- LLM/VLM output does not become numerical or lifecycle authority.

## 8. SIMPA technical boundary

SIMPA is aggregate/system-level social-protection intelligence and monitoring.

Current implemented direction includes:

- methodology lifecycle `DRAFT -> PROPOSED -> VALIDATED -> RETIRED`;
- methodology-owned immutable reference suites/cases;
- deterministic statistical model contracts/results;
- uncertainty, diagnostics, calibration and production-eligibility evidence where supported;
- evidence-first presentation and dedicated Help/User Guide/XAI;
- bounded AI interpretation downstream of governed analytics.

Hard limits:

- no citizen-level eligibility, benefit, diagnosis or automated risk decisioning;
- no unapproved LISI formula, weight or threshold;
- no automatic policy conclusion;
- no causal wording from ordinary association/regression;
- unsupported confidence/feature importance/SHAP must be presented as unavailable, not invented.

Sensitive SIMPA AI requests remain local-only under the current policy.

## 9. ORDO technical boundary

ORDO is destination intelligence, planning, forecasting and scenario support.

Current implemented direction includes:

- governed evidence identity/provenance;
- governed spatial-unit identity and descriptive aggregation;
- statistical and time-series specification contracts;
- deterministic forecast runtime for explicitly requested naive/seasonal-naive families at the accepted boundary;
- rolling-origin/backtesting and exact forecast metrics;
- leakage-safe empirical residual intervals and uncertainty diagnostics;
- persisted `ESTIMATED` / `NOT_ESTIMATED` outcomes;
- scenario/forecast separation;
- dedicated Help/User Guide and faithful XAI.

Hard limits:

- scenario is not automatically a forecast;
- unsupported impact remains `NOT_ESTIMATED`;
- no automatic forecast-family selection/fallback;
- no causal impact claim without an approved model/methodology;
- no fabricated certainty or policy recommendation.

## 10. AI / MLOps architecture

### 10.1 Provider boundary

AI access is provider-independent behind the shared gateway.

Current provider states:

- **Ollama** - implemented local HTTP chat/embedding provider;
- **development stub** - deterministic development/test provider, forbidden in production;
- **external provider** - reserved type but not configured; it fails closed until an adapter, privacy/security approval and evaluation contract exist.

The server-shaped target reaches host Ollama through `host.docker.internal`/Linux host-gateway. Server model installation/mutation remains frozen until ISI-28.

### 10.2 Registry and runtime

The platform persists model, prompt and policy identity plus capability/model registrations. Legacy unbound jobs remain selected/default-model-only. Governed bound jobs use an exact source registration and never scan arbitrary registrations heuristically.

Fallback execution is constrained by persisted edge identity, semantic/provider policy, sensitive-data rules, review requirements and deterministic circuit state.

### 10.3 Evaluation and promotion

ISI-25A established:

- immutable capability/model fingerprints;
- candidate/challenger/retired lifecycle;
- fallback/rollback identity;
- frozen `SIMPA-EVAL-v1` and `ORDO-EVAL-v1` foundation fixtures;
- typed evaluation runs/results and human-review traces.

ISI-25B added:

- separate frozen promotion benchmarks;
- capability-specific threshold/hard-gate/circuit policies;
- deterministic evaluator engines, including numerical, retrieval and safety evidence where applicable;
- evidence-gated promotion decisions;
- single capability champion/rollback pin;
- deterministic runtime circuit state;
- explicit rollback;
- on-demand drift snapshots;
- shared faithful AI XAI/read model.

Foundation fixtures are not promotion evidence. There is no generic weighted “winner score”, permanent hard-coded winner, automatic model installation, online learning, silent promotion/rollback or deployment mutation.

## 11. Reporting

Shared reporting persists:

`draft -> in_review -> approved/rejected -> published/superseded`

A report version is an immutable content/provenance snapshot. New evidence creates a new version. Publication does not overwrite history.

Current deterministic renderers:

- JSON;
- Markdown;
- HTML.

Exports are checksum-backed. Reporting performs no new AI inference; previously persisted AI content can be carried forward only when its required human-review state is accepted.

There is no active production PDF/document-conversion service in the current architecture.

## 12. Authentication and security

### 12.1 Passwords and tokens

- Password hashing: Argon2id via `argon2-cffi`.
- Password length contract: minimum 12, maximum 256 characters.
- Sessions and auth tokens use opaque random tokens; persisted token authority is hashed.
- Default absolute session TTL: 12 hours.
- Default idle session TTL: 1 hour.
- Email verification TTL: 24 hours.
- Password reset TTL: 30 minutes.
- Invitation TTL: 7 days.

Public self-registration is not present; onboarding is invitation-based.

### 12.2 MFA state

The repository contains MFA factor/challenge persistence and assurance foundations, including keyed challenge-verifier hashing. This is a security foundation, **not a claim that a real production MFA provider/workflow has been server-validated**.

### 12.3 Login protection and security events

Default login protection:

- 15-minute failure window;
- 5 failures;
- 15-minute block.

Rate-limit and security-event identifiers are privacy-hashed. Security events are append-only application evidence.

### 12.4 HTTP security

FastAPI applies:

- TrustedHost middleware;
- `X-Content-Type-Options: nosniff`;
- `X-Frame-Options: DENY`;
- strict referrer policy;
- restrictive Permissions-Policy;
- CSP;
- request IDs;
- `Cache-Control: no-store` on auth routes;
- HSTS in production.

Production configuration fails closed if:

- security pepper is missing/weak;
- allowed hosts contain wildcard `*`;
- public/app URLs are not HTTPS;
- authentication delivery is unset;
- staging/production data storage is not S3-compatible;
- RQ job backends are not selected;
- SMTP is not explicitly configured;
- proxy-header trust is not enabled behind the deployment reverse proxy;
- production uses Mailpit/local SMTP, draft preview, development AI stub or staging/preproduction data identities.

### 12.5 RBAC and isolation

Current role catalogue:

- `organization_admin`;
- `domain_manager`;
- `analyst`;
- `data_manager`;
- `reviewer`;
- `viewer`.

Permissions cover organization/member/workspace management, data, governance/export, indicators, analysis, scenarios, reports, audit and AI execution.

Backend authorization remains authoritative. UI visibility is not authorization. Cross-tenant and cross-product access are blocker-severity defects.

## 13. Privacy and observability

Observability intentionally avoids raw request bodies, query strings, auth/cookie material, passwords/tokens, AI prompt/output contents, uploaded payloads, filenames/storage keys and tenant/user identifiers.

Current telemetry covers bounded HTTP, queue, worker, AI and ingestion metrics. Dynamic identifiers are normalized out of metric labels.

`/api/v1/diagnostics/readiness` checks PostgreSQL, Redis when RQ is configured, and configured object storage. Failure details use bounded reason codes rather than leaking connection strings or exception text.

HTTP metrics export is disabled by default. Prometheus/Grafana/Loki/OpenTelemetry deployment, production alert routing and current-server capacity evidence remain deferred.

## 14. Backup, restore and disaster recovery

Repository recovery authority covers durable PostgreSQL plus application-managed object storage. Redis/RQ state is not restored as authoritative business data.

ISI-19 provides synthetic/non-production backup/restore verification and recovery-manifest/digest contracts. Production schedule, storage capacity, encryption/KMS integration, real retention, measured RPO/RTO, operational ownership and server rollback remain ISI-28 work.

Existing production RPO/RTO numbers in the recovery runbook are **proposed planning values only**, not operational guarantees.

## 15. Help, User Guide and XAI governance

Production-complete user-facing functionality requires Help coverage in the canonical Help Coverage Matrix.

SIMPA and ORDO domain Help/XAI are implemented and phase-accepted. Shared Help/presentation is accepted on main at `74acd5d9a890733347554633f44a6d5319717ba3` (`NOT CI_VERIFIED`); exact-RC evidence, supply-chain assurance and hosted acceptance remain owned by 27B/27C/27D.

XAI must remain faithful to actual model/run evidence. The platform must not invent:

- confidence/probability without semantics/calibration;
- feature importance or SHAP when unsupported;
- causal effect;
- forecast certainty;
- evidence/provenance;
- human validation state.

## 16. Development and CI governance

Normal development:

- one canonical local repository;
- branch `main`;
- exactly one worktree;
- iMac or MacBook Air, never active concurrently on the same ISI project;
- GitHub `origin/main` is the only code handoff;
- no copying virtual environments, `.env`, DB/Redis/Docker state, caches, logs or credentials between Macs.

Codex policy:

- standard `codex` CLI;
- one canonical owner account;
- project-specific wrappers/CODEX_HOME profiles are legacy;
- Codex never stages, commits, pushes or deploys unless explicitly authorized.

CI policy:

- local deterministic runners/analyzers are the normal development lane;
- full `ISI required acceptance` is manual `workflow_dispatch` only;
- no automatic full-CI push/PR/schedule trigger without explicit approval;
- `CI_VERIFIED` is claimed only for an explicitly approved exact-main hosted acceptance that completes successfully.

## 17. Deployment and release governance

ISI-27 owns the industrial release candidate and acceptance pack.

ISI-28 is the **only** phase allowed to touch:

- current server;
- DNS;
- certificates;
- shared central Nginx;
- production SMTP;
- production secrets;
- production data;
- server Ollama/model state.

An ISI-28 ingress operation must begin read-only and must prove Krcuga `:8443` and OralScanXAI `:8444` remain unaffected before/after any approved shared-edge change.

A routine repository push is never a production deployment.

## 18. Known deferred or intentionally absent capabilities

The following are not current ISI production capabilities unless a later owner-approved architecture change adds them:

- commercial checkout/payment/PayPal;
- application-owned scheduler;
- dedicated Vision service;
- dedicated Audio service;
- active external AI provider;
- live external research/web retrieval provider;
- external document-conversion/PDF service;
- automatic online learning;
- automatic model installation/deployment;
- automatic causal/policy decisioning.

## 19. ISI-26 closeout and ISI-27 handoff

ISI-26 is **IMPLEMENTATION COMPLETE / ACCEPTED ON MAIN / NOT CI_VERIFIED**. R1 is accepted on main SHA `e4b5b7f5927bc553fd616800d37beb5d115bb46e` (tree `9a30b280ba44798b987167c155f0be6ccc13776e`) from candidate fingerprint `98653d20a5223d4f6be66f3ee2017f998865b00ecb08a0950c07123d60dc2e24` after local acceptance, native PostgreSQL acceptance, assistant human review, independent analysis and owner-approved direct-main finalization. ISI-26A through ISI-26D remain formal coverage/gate identities and are accepted through the grouped R1 implementation; ISI-26E closes the whole-phase audit.

`tools/performance/` defines ten immutable versioned workloads, bounded concurrent execution, nearest-rank percentiles, completed-operation throughput, separate correctness authority and validated sorted JSON evidence. Synthetic in-process APIs preserve authentication and scope checks. Isolated SQLite lanes exercise inspection workers, persisted report rendering and registered AI fallback; deterministic statistical/forecast engines preserve domain semantics. Queue transport/provider timeout tests use doubles, never a real server/model.

Timing budgets remain `UNCALIBRATED` where the locked calibration conditions are not met. Portable host resource measurement remains `UNAVAILABLE`; Compose memory limits are configuration only. These truthful repository states do not block closeout and are not production SLOs. `PRODUCTION_CAPACITY_VERIFIED=false`, `SERVER_VERIFIED=false`, `GITHUB_ACTIONS_DISPATCH=NO` and `CI_VERIFIED=NO` remain explicit.

No customer-facing workflow, schema, dependency, runtime behavior or deployment topology changed. ISI-27 B0-R1A bootstrap is closed, ISI-27A-C are accepted on main, and `ISI-27D - Exact-Main RC Acceptance & Phase Closeout` is the current checkpoint. Hosted acceptance remains reserved for the explicit 27D checkpoint. ISI-28 remains the exclusive live-server mutation/capacity-verification phase; Krcuga and OralScanXAI are strict non-targets.

## 19A. ISI-27 scope lock

Corrected B0-R1A bootstrap authority is repository-visible through `automation/specs/ISI-27-B0-R1A-BOOTSTRAP-AUDIT-REPORT.md` and `.json`. It records DONE=6, PARTIAL=8, MISSING=5, DRIFT=0, thirteen release blockers not DONE, twelve real Help/XAI blockers and SBOM/attestation as MISSING.

ISI-27 execution is locked into four larger gates: 27A closes shared Help/release UX completeness; 27B creates the exact-RC evidence/governance pack; 27C creates the portable immutable release artifact and missing supply-chain assurance; 27D performs the owner-controlled exact-main hosted release-candidate acceptance and phase closeout.

The release builder must be portable across canonical macOS development and Linux CI/release environments. Automatic GitHub Actions triggers remain forbidden. Production/server capacity is not verified in ISI-27 and no server/DNS/ingress/SMTP/production secret/data/Ollama action is authorized.

## 20. Canonical source index

Primary authorities:

- `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`;
- `TECHNICAL_DOCUMENTATION.md`;
- `AGENTS.md`;
- `automation/STATUS.md`;
- `automation/tasks.json`;
- `docs/architecture/ADR-0025-simpa-ordo-analytical-ai-methodology.md`;
- `docs/architecture/ADR-0026-shared-central-nginx-ingress.md`;
- `docker-compose.server.yml`;
- `src/core/config.py`;
- `src/api/app.py`;
- `src/platform/**`;
- `src/domains/simpa/**`;
- `src/domains/ordo/**`;
- `tests/**`.

Historical deployment documents remain useful only when the MasterPlan/ADR classification says `LEGITIMATE_HISTORY` or `REQUIRED_COMPATIBILITY`.

## 21. Change log

| Version | Date | Change |
|---|---|---|
| 1.6 | 2026-10-03 | ISI-27A accepted on main; governance synchronized to 27B SPEC_READY without claiming hosted CI or server verification. |
| 1.5 | 2026-10-02 | ISI-27A shared Help/release UX implementation candidate established and locally accepted before owner-approved main finalization. |
| 1.4 | 2026-10-02 | ISI-27 corrected B0-R1A bootstrap accepted as scope authority; four-gate RC execution architecture locked; 27A becomes SPEC_READY. |
| 1.3 | 2026-10-02 | ISI-26 R1 accepted on main; 26A-26D formal gates accepted through R1; 26E whole-phase closeout completed; ISI-27 becomes next. |
| 1.2 | 2026-10-01 | R1 full-slice candidate supersedes active micro-task execution; adds local performance contracts, workload/evidence tooling and explicit capacity limitations. |
| 1.1 | 2026-10-01 | ISI-26-B0 closed; locks 26A-26E performance/resilience slice model and 26A contract-first/no-false-production-SLO rule. |
| 1.0 | 2026-10-01 | Initial consolidated technical baseline; closes stale ISI-25B status, establishes ISI-26 as next, records central Nginx as final shared-edge authority, locks `https://isi.opus.rs:8445/`, and preserves ISI-28 as the exclusive live-server mutation phase. |


## Historical pre-acceptance record — ISI-27A R1 implementation candidate

Baseline: `39dc1d59a74a03c86f68df093cc07e32d41d028c`, tree
`3c7027b375b041043f7305cdab008aee35f16ef7`. Contract:
`automation/specs/ISI-27A-R1-SHARED-HELP-RELEASE-UX-COMPLETENESS.md`.
This subsection is retained only as pre-acceptance history and is superseded for live status by the accepted-main closeout below.
At that checkpoint, 27A was `in_progress`, an unstaged/uncommitted implementation-candidate, NOT CI_VERIFIED.
At that checkpoint, parent ISI-27 remained in_progress; the active checkpoint was
`ISI-27A-SHARED-HELP-RELEASE-UX-COMPLETENESS`; 27B/27C/27D were planned.

Shared Help authority: `src/streamlit_app/shared_help_workspace.py`, twelve topics
ISI-H01..H12, mirrored in `docs/help/ISI-SHARED-USER-GUIDE.md`.
Public header/footer target `help=public`; public-safe guidance needs no session.
Authenticated `isi_help` and contextual Data/Reporting/Admin/Account Security Help
use that authority. Invitation/verification/reset presentation consumes existing
APIs and clears sensitive queries on success; active sessions cannot be replaced
by one-time links. Public self-registration remains NOT_PRESENT/invitation-only.
The twelve corrected matrix rows have focused 27A Help/test authority; A07/A20
are not promoted. Protected SIMPA/ORDO/AI Help content is unchanged.

Bootstrap classification: accepted auth/domain/service authorities DONE;
shared Help/auth presentation PARTIAL/MISSING at baseline, addressed in this
candidate. Protected auth/domain authorities and shell markers are
REQUIRED_COMPATIBILITY. Earlier phase/global Help statements are LEGITIMATE_HISTORY;
the current top-level matrix supersedes their global status only, not methodology.
The R0 parser over-read is LEGITIMATE_HISTORY; corrected R0-R1 hashes match.
Historical tests freezing global PARTIAL are REMOVE_BEFORE_NEXT_SLICE.
ISI-27A-R1A authorizes only four inherited predecessor Help assertions to converge
with the current top-level matrix authority; no domain/runtime semantics, predecessor
acceptance facts, methodology, XAI or authorization behavior are changed. At that checkpoint, full local
acceptance and independent review were still required; no test bypass was permitted.

Local HEAD and origin/main match baseline; direct remote verification is unavailable
in this sandbox because GitHub DNS resolution failed. The latest recorded hosted
acceptance is predecessor run #90 / 35238623960 on 5937daa2ea7ff9c476bd6a05a04841d1534aefe2,
not this candidate; 25/26 hosted acceptance was deliberately deferred. Runner
fingerprint, complete deterministic acceptance and independent review remain gates.

STAGE_COMMIT_PUSH=NO; GITHUB_ACTIONS_DISPATCH=NO; SERVER_MUTATION=NO;
CI_VERIFIED=NO; SERVER_VERIFIED=NO. Real-provider MFA is not verified; production
SMTP and live deployment/capacity remain ISI-28-only, DEFERRED_SERVER_VERIFICATION.


### ISI-27A-R1A no-Codex inherited Help convergence

R1A continues the existing unstaged R1 candidate after workspace-credit exhaustion. It authorizes only four predecessor test assertions that froze the historical global `INV-A21=PARTIAL` state. Runtime/auth/domain code is frozen to the R1 prestate. The current top-level Help matrix may be `VERIFIED` for the corrected production-critical 27A scope while predecessor phase facts remain historical. `INV-A17` remains `NOT_PRESENT` and onboarding remains invitation-only. Full local regression, independent analysis and human review remain open; `CI_VERIFIED=NO`, `SERVER_VERIFIED=NO`, `STAGE_COMMIT_PUSH=NO`, `GITHUB_ACTIONS_DISPATCH=NO`, `SERVER_MUTATION=NO`.


## ISI-27A accepted-main closeout and ISI-27B promotion — 2026-10-03

ISI-27A Shared Help & Release UX Completeness is **ACCEPTED ON MAIN / NOT CI_VERIFIED** on SHA `74acd5d9a890733347554633f44a6d5319717ba3`, tree `a69b8582a77555611b64a5527548e67a5b0c45cb`, accepted candidate fingerprint `01ed26dd8e1193606f17c097f88ba0fd68b4f3ce2127de0845468998d3dc8d64`. Deterministic local acceptance is `1030 passed / 43 skipped / 0 failed`; independent analysis and human review are PASS / REVIEW_VERIFIED.

This closeout is governance-only. It changes no runtime/auth/domain/Help semantics. `INV-A17` remains `NOT_PRESENT` and invitation-only. Hosted GitHub Actions were not dispatched and `CI_VERIFIED=NO`; no live server, DNS, ingress, SMTP, production secret/data or server Ollama mutation occurred and `SERVER_VERIFIED=NO`.

Parent ISI-27 remains `IN PROGRESS`; the active checkpoint is now **ISI-27B — RC Evidence & Governance Pack** (`spec_ready`). ISI-27C and ISI-27D remain planned; ISI-28 remains deferred and is still the only server-mutable phase.

## Historical pre-acceptance record — ISI-27B R1 candidate (2026-10-04)

Public portal remediation is accepted on main `c177f9d705efd6f68d95ef7d13847b03a8e19229`.
Owner approved reviewed-candidate finalization and final deployment; release order
remains 27B -> 27C -> 27D -> ISI-28. The locked 27B implementation contract is
`automation/specs/ISI-27B-R1-RC-EVIDENCE-GOVERNANCE-PACK.md`. INV-M20 owns exact
candidate/report consolidation. Local full/native/recovery/performance acceptance
and independent review remain required before promotion. CI_VERIFIED=NO;
SERVER_VERIFIED=NO. Public operator information is ISI with GoraNova as confirmed
by the owner; the Gmail privacy contact is approved. Provider/legal processing
facts must remain grounded in public records and the ISI-28 runtime audit.

## ISI-27B accepted-main closeout and ISI-27C promotion — 2026-10-04

ISI-27B is ACCEPTED ON MAIN / REVIEW_VERIFIED / NOT CI_VERIFIED on
`16a928b20907d570df2cf05101a969e1f0cda736` (tree
`2513af18b6d3a7b338f3a11b63444e7181f95a63`). Local acceptance: 1071 regression
passes, 43 runner-gated native skips, 45 native PostgreSQL passes with zero skips,
PostgreSQL 17/object restore PASS, ten accepted performance scenarios. Pack hash
`9da45b26e811b6320c951e4285f83353aa306413c96052d5a75112b5ec67c8c1`;
candidate `d97b16ce6f3cd179d8fca5b05e838d6644a6eda1bdff61c2399c4b0952e22a86`.
Independent analysis, review, committed-file comparison and remote equality PASS.
Current checkpoint: `ISI-28 - Current Server Controlled Upgrade`.
ISI-27D is specification-ready; ISI-28 remains deferred. No hosted/server acceptance is claimed.

27C contract: `automation/specs/ISI-27C-R1-REPRODUCIBLE-RELEASE-SUPPLY-CHAIN.md`.
Its candidate introduces portable immutable release packaging, real image SBOM
and blocking scan, existing-owner SSH-signed provenance and strict serial release
state validation. GitHub Free/private signing uses local owner identity and makes
no Enterprise/SLSA certification claim. INV-M21 owns release assurance; INV-K15
owns build/signing metadata; INV-J32 maps the immutable release bundle. Python 3.11
stdlib, existing OpenSSH 8.2+ and Docker suffice; Trivy runs as an official pinned
CI action or disposable scanner container. No host package installation is required.

## 27C R1 partial verification and approved R2 implementation — 2026-10-04

At the earlier R1 checkpoint, 27C was IN_PROGRESS with an unstaged candidate.
An earlier frozen candidate (`17d0801a8fcfe073055e959e52006c429d008a072befc3649a4c1158e2c99d1d`)
passed 1105 regression tests (43 intentional native skips), 45 native PostgreSQL
tests (zero skips), PostgreSQL/object restore, all 10 performance scenarios,
quality, policy, Compose and changed-line checks. Later review/contract changes
require final rerun; this is not final-candidate acceptance. Evidence:
`automation/evidence/ISI-27C/local-r1/partial-verification.json`.

Actual image scanning discovered new security drift: urllib3 2.7.0 and build-only
tooling findings were corrected in the candidate; Python dependency audit and
real runtime imports pass. The corrected Debian image still has 45 HIGH OS
findings. Image acceptance FAIL; classified REMOVE_BEFORE_NEXT_SLICE. No finding
is ignored and no release/server gate is bypassed. Owner approved the bounded
R2 proposal in `automation/specs/ISI-27C-R2-MINIMAL-RUNTIME-BASE-PROPOSAL.md`.
The Wolfi/Python 3.11 implementation then passed the full local gates and was
accepted on main `b6f0bfaf453360da72f866d4bbd1d47b51655bf4`. It is not
CI_VERIFIED or SERVER_VERIFIED; 27D is specification-ready and ISI-28 deferred.
No hosted dispatch or production deployment occurred.


### ISI-27C R2 minimal runtime candidate

The owner approved bounded implementation of the reviewed R2 contract.
`docker/Dockerfile` builds dependencies in an isolated builder stage and carries
the Python 3.11 application environment into a runtime stage based on the pinned
Chainguard Wolfi index in `docker/runtime-base.lock.json`. The runtime lock hash,
Git revision and candidate fingerprint are embedded in OCI labels. Release
acceptance must bind the image SBOM and vulnerability scan to the image config
digest and pass disposable FastAPI, Streamlit, public health and unauthenticated
access checks. The exact amd64 candidate passed those checks: 117 CycloneDX
components, no HIGH/CRITICAL findings under Trivy 0.75.0, API and Streamlit
health 200, unauthenticated account access 401, and the Python 3.11/UTC/scientific
runtime smoke passed. Full local regression (1,159 tests, 43 existing skips),
native PostgreSQL (45/0 skips), restore/recovery, 10 performance scenarios,
quality, policy, diff and Compose gates passed; independent analysis also passed.
Fingerprinted evidence is retained under `automation/evidence/ISI-27C/`. The
implementation was accepted on main `b6f0bfaf453360da72f866d4bbd1d47b51655bf4`
(tree `8d52631012121c078d077a39d75e201d4ffadcbd`, candidate fingerprint
`7dc381dd31d94e6ada447c7cffc945399bddbe4a7ec138ec88ae69e77e9be8ea`). Hosted
CI and production deployment are not claimed; 27D remains the active gate. Its first exact-main checkpoint (#91 on `61a11c1ff839e66a458ac77ed05d4c860214f267`) failed in the hosted test/build portability checks and historical Gitleaks scan. The local candidate fixes the two deterministic runner defects and includes the owner-approved exact-fingerprint baseline for the 11 context-reviewed historical findings; the full-history scan remains enabled, and acceptance has not yet verified the baseline. The run and Actions usage postcheck are recorded in local ignored evidence under `automation/evidence/ISI-27D/`.

## ISI-27D checkpoint #92 — 2026-10-05

Owner-approved run [#92](https://github.com/branislavradomirovic/isi/actions/runs/37274367540)
on exact main `587b8e1e92a4a8a2550cccf4a732a3798f0c312e` completed with
failure. All ten upstream jobs passed, including regression, native PostgreSQL,
recovery, runtime/image scans and the owner-approved full-history Gitleaks
baseline. `release-bundle` failed because the build artifact was named
`image-runtime-check.json` while the bundle/signer require `runtime-check.json`;
aggregate acceptance failed. No signed bundle, CI_VERIFIED or SERVER_VERIFIED
is claimed. The bounded unstaged recovery normalizes the producer filename and
adds producer/preserve/upload/consumer contract coverage. Validation passed:
88 targeted tests; full local regression 1,118 passed, 43 existing skips, zero
failures/errors; policy, Compose, syntax, JSON and diff checks. The first local
regression invocation lacked Alembic on PATH; the unchanged suite passed after
activating the existing project environment. No application behavior changed.
Evidence is local/ignored under `automation/evidence/ISI-27D/checkpoint-92/`.
Actions postcheck: GitHub Free, 158/2000 minutes, displayed 0/0.5 GB storage;
reporting may lag. Next gate: validate/review the exact recovery candidate, then
owner-approved commit/push and a separate exact-SHA hosted checkpoint. Terms/
Privacy publication and live operational policies remain pending; only ISI-28
may perform controlled server deployment after release prerequisites pass.

## ISI-27D accepted RC and owner-approved ISI-28 start — 2026-10-05

Exact RC `2b1f2ef20a2310df23947f2ac2128d16f81a98ea` is CI_VERIFIED / REVIEW_VERIFIED:
manual checkpoint #93 (run 37277358285), all 12 required jobs success; signed
source/image/SBOM/evidence bundle verified against pinned owner trust. Actions
pre/post observations: 158/191 of 2000 minutes; displayed storage 0/0.5 GB
(rounded/lagged). Exact identities and whole-phase classification are in
`automation/specs/ISI-27D-ACCEPTANCE-CLOSEOUT.md`; immutable artifacts/evidence
remain local under `automation/evidence/ISI-27D/checkpoint-93/`. Earlier #91/#92
failures and predecessor NOT CI_VERIFIED labels are historical states only.

The owner explicitly instructed continuation to full production. Current
checkpoint: **ISI-28 - Current Server Controlled Upgrade**, starting with the
fresh read-only audit in `automation/specs/ISI-28-R1-CONTROLLED-PRODUCTION-UPGRADE.md`.
Terms/Privacy and live provider/retention/operational facts remain preproduction
gates. No server mutation or SERVER_VERIFIED is claimed. A later source commit
does not inherit this exact RC's CI verification.

Accepted predecessor states: **27A ACCEPTED ON MAIN / 27B ACCEPTED ON MAIN / 27C ACCEPTED ON MAIN**; the consolidated exact RC is CI_VERIFIED through #93.

Current execution state: **ISI-28 IN_PROGRESS**; exact ISI-27 RC is CI_VERIFIED, production remains unverified.

### ISI-28 legal portal integration candidate

Published PublicPage records of existing type `legal` are discoverable through
localized footer links and sitemap even when excluded from primary navigation.
Draft/archived notices and missing translations produce no public legal link.
Existing localized page renderer supplies canonical/alternate metadata. This
adds no schema, seeded legal facts, consent mechanism or authentication change.
Final legal text and production publication remain pending factual verification.

### ISI-28 observed server and preparation

SSH on port 222 is functional. Observed source main is bf4a648b1e118a0b087b437579d2f3f12ef2db94,
schema 20260828_0013; API/UI and workers use different old images. Central ISI
Nginx overrides robots and applies a noindex header. The application itself
returns production robots internally. Existing aliases/networks match ADR-0026.
Protected DB backup/isolated restore, logical object recovery and accepted-image
migration rehearsal passed; the restored copy reached 20260918_0034 without
decreasing original table counts. Docker containerd reports OCI manifest IDs;
accepted hosted config digest is verified through the signed archive together
with loaded rootfs/config/platform. No production schema/runtime replacement
has occurred. SMTP is owner-deferred To Be Defined and currently uses Mailpit.
Configured nomic-embed-text is absent from observed host Ollama models.
Operational plan/evidence boundaries: docs/ops/ISI-28-CONTROLLED-DEPLOYMENT-PLAN.md.

## ISI-28 R2 activation candidate — 2026-10-06

Baseline 3986a03182eed04ba8055a6156d6722bca1504f5 passed exact required
acceptance #94 (37436821260), all 12 jobs. Signed image was verified and loaded
on the server without replacing live services. Exact-image isolated migration
passed 0013 to 0034, 90 to 140 tables; original counts not decreased.
Owner-approved ISI Nginx candidate is active: public robots/sitemap reachable,
public global noindex removed; app/API noindex retained. Non-ISI config bytes
were preserved and Krcuga/OralScanXAI HTTP baselines remained 200.

Owner now authorizes legal publication with visible placeholders and operational
policy targets, while SMTP remains pending. R2 adds an explicit pending email
mode with no silent delivery and account-independent unavailable request routes;
login and token-confirmation semantics remain unchanged. SR/EN versioned legal
payload and digest-bound collision-safe publisher are source candidates only.
These new changes do not inherit checkpoint #94 acceptance. No final cutover,
legal publication, operational enforcement or SERVER_VERIFIED is asserted.
Exact contract: `automation/specs/ISI-28-R2-PRODUCTION-ACTIVATION.md`.

## ISI-28 checkpoint95 activation and R3 closeout — 2026-10-06

Exact accepted main **1bf0552d702c0e6cefc659b38184f505118f11d1**, tree
514052fa0b0ddc7778068ccb2a94bfc6e0f444ef: all 12 jobs completed success in
manual checkpoint #95 / 37503549452; owner signature and every bundle/image
digest passed verification. Actions usage pre/post239/261 of2000 minutes.
Server source fast-forwarded cleanly to this exact SHA without resetting files.
Four ISI application runtimes now use the signed accepted image (config digest
3295bac2a9c36fca204536e3fc146a7051f9be13a571cf98899aa51b9fec94cb;
loaded OCI manifest6cdbbe13fa49c26d3a862c79fed3f324c93c41ba0148d5e8dca25feb658e848f).
New database isi_production restored with exact original counts then migrated
0013 to0034/140tables; old DB remains. New isi-production bucket copied one
42-byte object with exact key/hash/metadata/tags, private policy and versioning
enabled; old bucket remains. Fresh coordinated pre-cutover dump/object checkpoint
and protected config/prior images are retained server-only. First activation
helper failed by inspecting removed old ISI IDs and safely rolled back; corrected
activation passed and preserved non-ISI container identities. This history is
LEGITIMATE_HISTORY, not a waived acceptance failure.

SR/EN Terms/Privacy published from payload9f79b1d2b90825079be6cfb6aae24237fb24f5928b1395c5d9095e55d00fd426.
Live login/me/context/logout for SIMPA-only/ORDO-only/dual users, database/Redis/S3
readiness, both real RQ workers and existing storage readback passed. External
HTTPS (normal TLS validation) returned200 for public/legal/robots/sitemap/favicon/
manifest/app/API/diagnostics routes; public indexing and private noindex correct.
Krcuga8443 and OralScanXAI8444 returned200; no additional Nginx mutation.

Whole ISI-28 remains **IN_PROGRESS**, not full SERVER_VERIFIED: default embedding
execution timed out; a two-thread synthetic probe passed768dimensions in0.33s,
not domain retrieval quality or champion promotion. R3 adds optional per-ISI
thread configuration and desktop navigation correction after1280px live drift.
R3 adds bounded ops code but scheduling/restore/offsite/alerts are not verified.
Offsite destination and monitored duty-holder/channel require actual owner input.
SMTP explicitly pending; email-dependent workflows unavailable by design.
Operational retention periods remain targets until scoped enforcement/hold/recovery
evidence passes; no blanket institutional purge. Capacity and final operational
recovery acceptance remain open. Evidence: automation/evidence/ISI-28/r3/.

## Owner-narrowed preproduction test scope — 2026-10-06

Owner explicitly deferred all new backup creation and requested application/server
testing in pre-production mode. No new backup/cron-backup/offsite/purge is to be
activated. Preserve existing rollback and recovery media. R3 now contains only
read-only release-bound monitoring, responsive header repair and optional per-ISI
provider resource bounds plus tests. Existing data target names isi_production
and isi-production record where the test candidate runs, not a claim of full
production acceptance. Keep the production security profile and SMTP pending;
operational mode is **PREPRODUCTION_TESTING**. Whole ISI-28 stays IN_PROGRESS.
Offsite recovery/real alerts/duty holders/capacity remain full-production gates
for later, not prerequisites that block the owner-requested test scope.
Earlier backup-plan paragraphs are superseded for current execution.


29A local verification record: IMPLEMENTED / REVIEW_VERIFIED candidate; 23 focused and 1203 regression passes, 43 existing native-lane skips, zero failures/errors. Four responsive widths and keyboard backtest selection verified on synthetic local preview. Exact report/fingerprint: `automation/evidence/ISI-29A/human-review.json`. No CI_VERIFIED or server deployment of 29A. 29B–F remain unimplemented; 29B read-only preparation recorded separately.


## ISI-29A approved main checkpoint and 29B continuation — 2026-10-07

Owner approved exact 29A candidate f220dd3dce9b172c05dc6982167f73b2cd848924b0060d48b1da4143970e492a; committed/pushed main `cad6892fd2d710b8263b936c06bb3d8137cdeddc` and direct remote equality verified with clean worktree. This supersedes mutable 29A unstaged/approval-pending wording; predecessor candidate/CI records remain LEGITIMATE_HISTORY. 29A NOT CI_VERIFIED; latest hosted acceptance #96 remains exact predecessor 374dda3. No CI/server action.

29B scoped geometry/storage/API/domain-adapter candidate is IN_PROGRESS. Contract automation/specs/ISI-29B-GIS-CONTRACTS.md; core_spatial_geometry_versions / migration0035; generic immutable geometry provenance and shared storage, separate SIMPA/ORDO adapters. WGS84 explicit lon/lat only; unknown/projected CRS and invalid topology rejected; no reprojection/provider/geocoder/tiles/PostGIS/indicator or AI changes. One geometry per version, human lifecycle, scoped permissions, immutable fingerprint and content hash. Actual approved boundary dataset absent; synthetic software tests only. Shapely2.1.2 added with existing NumPy preserved; no other lock versions upgraded. Help docs/help/ISI-SPATIAL-DATA-GUIDE.md covers source import/review, with GIS user interface still 29C. Native upgrade/downgrade, regression/dependency/independent review are gates, not yet claimed PASS in this record. 29C–F remain unimplemented. No new staging/commit/push or server mutation authorized by prior29A approval.


29B final candidate: scoped geometry API/storage/native0035 migration and separate SIMPA/ORDO identity adapters implemented locally. Initial39 focused/native1/regression gates PASS; final synchronized candidate requires repeated exact gates and independent/human review. Help ten-item guide present, new action matrix PARTIAL. Next29C map/table workflows; 29C–F not implemented. Institutional boundary data/licence not supplied; projected CRS rejected. No CI/server verification, no deployment or staging/commit/push of29B.


29B local verification closeout: IMPLEMENTED / REVIEW_VERIFIED unstaged candidate; 42 focused and 1 native PostgreSQL test passed in the pre-final-review cycle (full migration upgrade/downgrade/reupgrade, constraints and stale concurrent write rejection), 1246 regression passes / 43 existing native-lane skips, zero failures/errors. Independent analyzer repeat PASS; runtime dependency audit and fixed musllinux wheel/local import checks PASS. Exact final candidate identity is automation/evidence/ISI-29B/human-review.json, with complete repeated gates on this documentation-synchronized candidate required. This supersedes mutable 29B IN_PROGRESS/verification-pending notes above; previous candidate narratives are LEGITIMATE_HISTORY. No CI/server acceptance or staging/commit/push; institutional geometry dataset/licence and projected CRS remain explicit missing/unsupported states. 29C–F still not implemented.

Final bounded review correction: reject non-string geometry type as a controlled validation failure; require native fixture loopback host before any DB access. Full exact-candidate gates must pass again; final counts/identity in automation/evidence/ISI-29B/human-review.json supersede prior cycle counts. No test gate bypass.


## ISI-29B approved main and ISI-29C implementation — 2026-10-07

29B approved exact candidate1c5a531c6ba7e206a1d822e295d70b2e3377257fc06873872d6c07210331f418 committed/pushed main0d59f40aa03ab7115041f1c58052d4610aac3a54; all28 committed file hashes match approval, clean single main worktree/direct remote equality. Final29B43 focused/native1/regression1247 passes,43 predecessor native skips; NOT CI_VERIFIED, no new server verification. Latest hosted acceptance#96 remains predecessor374dda3. This supersedes mutable29B approval-pending notes; earlier candidate gates/history remain LEGITIMATE_HISTORY.

Owner now explicitly approves all planned verified29A-F commits/pushes; repeated per-candidate commit approval is no longer required. Exact deterministic gates, independent readonly analysis and assistant review remain mandatory.29F acceptance/deployment authorization is subject to usage pre/post, exact committed main CI, signed image/bundle and approved ISI-28 server contract. Shared edge non-target protection remains mandatory. SMTP pending/new backups owner-deferred.

29C locked candidate: automation/specs/ISI-29C-GIS-WORKFLOWS.md. Existing Data surface now includes shared GIS catalogue/import/review/date/layer/version/map/table/selected provenance and explicit geometry export. Existing ORDO spatial-unit identity lifecycle exposed; actual ORDO overview permission source fixed, stable resource code input added. Separate domain selectors; no new navigation/schema/formula/provider/model. Geometry date is not observation period. ORDO exact identity-only stored result viewer revalidates source/methodology/boundary/trace/arithmetic; no result-to-geography association exists for SIMPA, displayed unavailable. No institutional boundary source/licence auto-created.

Actual browser WebGL limitation rejected the Pydeck draft renderer (REMOVE_BEFORE_NEXT_SLICE). Final renderer uses existing Streamlit1.63 components.v2 with fixed code/data-only SVG DOM; no new dependencies/lock/install. Bounded25features/50000coordinates/1MB; render-only Mercator with exact source coordinates retained; safe textContent labels, selection/pan/zoom/keyboard controls and table fallback, no tiles/provider keys/user markup. Local focused/full/browser/independent gates required before IMPLEMENTED/REVIEW_VERIFIED closeout; evidence automation/evidence/ISI-29C.29D-F remain unimplemented. DEFERRED_SERVER_VERIFICATION.


## ISI-29C local verification closeout — 2026-10-07

IMPLEMENTED local candidate:37 focused tests and1283 regression tests pass,44 existing native-lane skips, zero failures/errors; lint/policy/mypy/pip/diff gates PASS. Synthetic desktop1280/mobile390 browser checks PASS: map click/Enter/Space, linked selected table/provenance, ORDO result table/chart, zoom/reset, no page overflow or external assets. Exact synchronized candidate requires matching acceptance/browser/independent-analysis/human-review reports under automation/evidence/ISI-29C before approved staging. First unfinished runtime package29D;29E/F planned. Standing owner approval covers verified commit/push. No new CI/server acceptance; DEFERRED_SERVER_VERIFICATION, no full-production claim. Historical pending notes above are LEGITIMATE_HISTORY superseded by this closeout.


## ISI-29C approved main / ISI-29D attribution candidate — 2026-10-08

29C accepted main a77f9f0b4e43038554ee203a0c5ad22cd0b9e981, exact26-file candidate025263734c8ff82ef85c01f01a229e8724ea22ed6b13cfffb312426bacf7f82d; repeated local7gate/independent twice/assistant review PASS.37 focused/1283 regression passes,44 existing native-lane skips; main/origin/direct equality and clean one-worktree checkpoint recorded. No hosted/server verification inherited. Mutable prior29C candidate/current-next text superseded (LEGITIMATE_HISTORY).

29D IN_PROGRESS locked automation/specs/ISI-29D-MODEL-ATTRIBUTION.md: additive0036 simpa_attribution_artifacts, exact interventional continuous OLS explanation from stored coefficients and revalidated complete-case training cohort. No refitting/dependency/provider/model-family change. Domain-owned source/result/contract/background/artifact hashes and immutable metadata; read revalidates source/methodology and stored metric/prediction parity. Scoped analysis.read, explicit analysis.run creation, fingerprint-only audit. Existing SIMPA result expander gains matrix/heatmap/global mean-absolute/local waterfall and ten-item Help docs/help/ISI-SHAP-GUIDE.md. Technical1e-8 tolerance is not institutional threshold.512 selected rows/24features bounded; original training cohort only, correlated features limitations visible. ORDO naive/seasonal SHAP remains unsupported; conditional new model execution not automatically selected. NOT CI_VERIFIED; server deferred to29F. Local/native/full/browser/independent/human exact gates required before phase closeout. Browser access restored on 2026-10-08; synthetic desktop1280/mobile390 visual/keyboard/viewer/unsupported/tamper gates passed, with screenshots under automation/evidence/ISI-29D/. Contradictory legacy non-SHAP caption corrected only in the new attribution panel. Native0036 test participates in the existing hosted native lane without skips. Final local gates/independent review are rerun on the exact updated candidate before authorized commit/push.29E/F unimplemented; current owner explicitly requests checkpoint/deployment of verified current source in preproduction-testing mode, separate from29F whole-plan completion.


## ISI-29E entity/claim extraction candidate — 2026-10-08

29A–29D are CI_VERIFIED / REVIEW_VERIFIED at exact main 95fec43590e9b1d3eb44d55867666581118ec650 (ISI required acceptance run37746165918, all12 completed/success). Recorded signed deployment and scoped server acceptance passed in PREPRODUCTION_TESTING, schema0036; automation/evidence/ISI-29D/release/closeout.json. No fresh server probe in29E. SMTP pending, new backups owner-deferred, institutional/capacity/operational full-production gates remain open.

29E IN_PROGRESS on canonical main; locked automation/specs/ISI-29E-ENTITY-CLAIM-EXTRACTION.md. Additive0037 core_extraction_requests/artifacts/reviews; shared transport/persistence with separate SIMPA/ORDO prompts and scoped gazetteers. Governed aggregate nonpersonal UTF-8 TXT or validated/frozen snapshot cells only; exact Unicode spans/cells and version/hash/record lineage. Local registered AI queue/model/policy; source/actor/prompt/model/request pinned and checked before/after worker execution and at read. Historical code hash remains provenance; pending execution requires current code parity. No parser/OCR/VLM/geocoder/dependency/model install or new numerical authority. Exact-name suggestions remain unresolved until final attested data.validate review; entity registry identity and separately dated polygon claim scope revalidated. Accepted/rejected reviews append once; only accepted findings participate in scoped exact period/geometry retrieval. Invalidated/purged/reclassified input blocks current quotation/retrieval. No raw-content audit, cross-product retrieval, report promotion or fabricated coordinates/truth/causality. Real-domain extraction quality UNCALIBRATED; separate SR Latin/Cyrillic/EN annotated synthetic fixtures are software tests only. Data workspace gains explicit load/create/cancel/source/review/filter controls and ten-item Help.

Local deterministic focused/native/regression/browser/independent gates required on exact candidate before IMPLEMENTED / REVIEW_VERIFIED and standing approved commit/push. 29E is NOT CI_VERIFIED; DEFERRED_SERVER_VERIFICATION. 29F remains first planned package after verified29E: linked reports/Help/Word and whole-plan acceptance/controlled deployment. Historical candidate/CI notes above are LEGITIMATE_HISTORY; this snapshot supersedes current status statements.


### ISI-29E local closeout authority

IMPLEMENTED / REVIEW_VERIFIED applies only to the exact30-file candidate with matching PASS acceptance.json, browser-verification.json, independent-analysis.json and human-review.json under automation/evidence/ISI-29E. Final synchronized candidate must pass all8 gates again before staging; test counts and file hashes are recorded in those reports. Native0037 upgrade/downgrade/reupgrade uses a disposable loopback PostgreSQL schema. Synthetic desktop1280/mobile390 source/identity/territory review, accepted-only period retrieval, ORDO rejection, Help and no page overflow are exercised; no real model quality certification. Earlier51-focused/1375-regression cycle passed and is retained under verified-cycle-51; a final controlled storage-I/O failure case is included in the synchronized candidate.

Standing owner approval covers verified29A-F commit/push. First unfinished package after verified29E is29F (linked evidence/report/Help/Word/final acceptance and controlled deployment). NOT CI_VERIFIED / DEFERRED_SERVER_VERIFICATION for29E; recorded server remains95fec435/schema0036. No new Actions dispatch, server/Nginx/model mutation or SMTP/backups action occurs here. Real adjudicated extraction quality remains UNCALIBRATED; full-production operational gates remain open.

29E final governance review: general AI jobs retain metadata only for extraction; successful raw input/output/structured copies are cleared in the worker transaction. Quotations remain solely in source-revalidated extraction artifacts, preventing general AI/report reads from bypassing source withdrawal (REMOVE_BEFORE_NEXT_SLICE, resolved in this candidate; legacy non-extraction jobs REQUIRED_COMPATIBILITY). Code fingerprint pins service/contracts/models and the selected product extraction/spatial adapter. Empty pending request text and runtime-policy/model parameter drift fail before provider execution. Signed/decimal/date fragments cannot silently become partial numeric value/period tokens; spelling stays verbatim without numerical interpretation or domain formula. Exact final gates required after these bounded corrections.

## Linked evidence reports ISI 29F candidate

ISI-LINKED-EVIDENCE-v1 uses existing immutable report version/content/source
manifest and existing draft/review/approved/published lifecycle. One accepted
source-anchored claim, separately reviewed polygon/date or UNRESOLVED, optional
stored SIMPA continuous OLS result with existing SHAP artifact or ORDO forecast
with faithful XAI. Human note and attestation define contextual association,
not automated matching/corroboration/causality. Report read/lifecycle/export and
saved download rebuild current scoped evidence and compare both content/manifest
hashes. Revoked source/rights and changed geometry/result fail closed. No schema
change, new inference, parser or dependency. Existing independent reports remain
compatibility. Streamlit holds no raw export session cache;2MB packet cap.
HTML/Markdown/JSON reporting unchanged; Word remains screenshot user manual.
Help docs/help/ISI-LINKED-REPORTS-GUIDE.md and inline10-item guide.
Full final exact-source acceptance/controlled deployment remains required.

29F review refinement: section cell values are explicit text while the linked packet retains typed JSON. A claim-structure expander keeps map/result review readable. Saved linked export content must match its stored SHA-256 before download. Word29F uses the reviewed baseline plus labeled synthetic feature screens; final artifact/render/review identities live in manual-verification.json. Exact-main acceptance and ISI-only deployment remain conditional on release/closeout.json evidence, with PREPRODUCTION_TESTING, pending SMTP and deferred backups retained.

2026-10-09 owner Help extension: existing shared/product Help renders a trusted local illustrated manual, numbered workflows, field tables and dated baseline availability. 36 existing topics retain canonical content; additional product chapters cover GIS/extraction/linked reports and SIMPA SHAP. 37 local reviewed images are hash-bound in docs/help/ISI-ILLUSTRATED-MANUAL.json; no remote image fetching, runtime/customer data reads or public exposure of private topics. Public six-topic allowlist is retained. Final local/browser/manual gates must be rerun on the extended exact candidate before standing-approved commit/push/checkpoint/deployment.


ISI-30 continuation2026-10-10:30A reviewed/local verified19-file candidate360e841e committed/pushed c92bacca870edc04f1a3ef126954f0162f449d5d. Latest hosted/server proof remains f587ed0; no inheritance. Owner authorizes30B–F verified commit/push/final checkpoint/scoped deployment without further confirmation.30B1 source version/quality/ingestion inspection and bounded FAILED retry IN_PROGRESS;30B2–D authoring,30E Help/Word,30F acceptance/deployment remain pending. SMTP pending, no new backups, strict non-target protection.


ISI-30B1 local IMPLEMENTED/REVIEW_VERIFIED committed/pushed be2ae69:24focused/1456regression PASS,46 inherited skips,1280/390 synthetic version/upload/evaluation/output/retry/readonly review.30B2 IN_PROGRESS typed existing inbound/batch connector, schema mapping, identity policy, author-entered operational thresholds, activation and idempotent governed upload. Exact contract automation/specs/ISI-30B2-GOVERNED-INGESTION.md; scoped backend remains authority. No formula/schema/dependency/secrets/remote connector added.30B operator/privacy/analytical authoring,30C/D,30E illustrated HelpWord,30F remain pending. Latest CI/server f587ed0 unchanged.


ISI-30B2 IMPLEMENTED/REVIEW_VERIFIED committed/pushed daa1c6e:31focused/1487regression PASS/46 inherited skips,1280/390 synthetic authoring/activation/upload review.30B3 IN_PROGRESS typed analytical dataset/feature registry, field contracts/activation, governed-output snapshot creation, eligible snapshot feature versions and revision-pinned confirmed lifecycles. Exact automation/specs/ISI-30B3-ANALYTICAL-AUTHORING.md. No raw-source promotion, new methodology/formula/schema/dependency.30B4 operator/privacy,30C/D,30E HelpWord and30F still pending; CI/server f587ed0 unchanged.


ISI-30B3 IMPLEMENTED/REVIEW_VERIFIED committed/pushed6a70f46:23focused/1510regression PASS/46 inherited skips,1280/390 synthetic registry/contract/snapshot/feature/lifecycle/read-only checks.30B4A IN_PROGRESS existing backfill/replay/dead-letter operator forms and explicit offset-aware observation time; exact automation/specs/ISI-30B4A-INGESTION-RECOVERY.md.30B4B privacy/record governance,30C/D,30E HelpWord and30F remain pending. No new CI/server claim; f587ed0 remains last proof. Legacy stale30A task registry status REMOVE_BEFORE_NEXT_SLICE corrected to local reviewed completion; task done labels do not confer hosted/server verification.


ISI-30B4A IMPLEMENTED/REVIEW_VERIFIED committed/pushed15204d7:33focused/1543regression PASS/46 inherited skips,1280/390 synthetic backfill/replay/dead-letter/read-only checks.30B4B IN_PROGRESS typed source governance profile and explicit quarantine review/resolution. Record review audit found current accepted record may change after read; additive optional expected_current_accepted_record_id now checked under existing server lock, new UI always supplies reviewed ID or explicit null. Historical omitted-field callers REQUIRED_COMPATIBILITY, no database migration/permission expansion/formula. Inventory INV-A08/A21/B10 reviewed-current resolution contract updated. Retention/anonymization/export/purge30B4C,30C/D,30E and30F remain pending; last CI/server f587ed0 unchanged.


ISI-30B4B IMPLEMENTED/REVIEW_VERIFIED committed/pushed444238e:17focused/1560regression PASS/46 inherited skips,1280/390 synthetic governance/quarantine/review/readonly checks.30B4C IN_PROGRESS existing retention policy/hold/metadata purge request, external anonymization evidence/proposal/review, scoped allowed export. Governance-only paginated anonymization GET added for retrievable review; final review now uses row lock. No database migration, AI method/provider/formula or permission expansion. Physical purge classified OPERATOR_ONLY: no customer execute button or unverified archive claim; existing operator step-up/retention APIs retained. Sensitive export remains fail-closed with real MFA requirement.30C/D,30E HelpWord,30F remain pending; last CI/server f587ed0 unchanged.


## 2026-10-10 — 30B privacy closeout / 30C1 scope lock
ISI-30B4C IMPLEMENTED/REVIEW_VERIFIED committed/pushed606fc92:21focused/1581regression PASS/46 inherited skips,1280/390 synthetic privacy controls/read-only/ORDO checks.30B customer data workflows locally reviewed; physical purge OPERATOR_ONLY, real sensitive-export MFA remains fail-closed.30C1 IN_PROGRESS typed existing global SIMPA methodology/reference-suite/statistical lifecycle; global registry/supersession disclosed, no formula or automatic approval. Contract automation/specs/ISI-30C1-SIMPA-METHODOLOGY-WORKFLOWS.md.30C2 ORDO,30D,30E illustrated HelpWord,30F pending. Last CI/server f587ed0 unchanged.
