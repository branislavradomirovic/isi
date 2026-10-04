# ISI Technical Documentation

**Version:** 1.6
**Status:** Controlled living technical document  
**Last updated:** 2026-10-03
**Canonical repository:** `branislavradomirovic/isi`  
**As-built feature checkpoint:** `74acd5d9a890733347554633f44a6d5319717ba3` (ISI-27A accepted main; NOT CI_VERIFIED)
**Pre-reconciliation governance baseline:** `ff573b3d76cf29581cb19c255821e9b4c4841108`  
**Current database migration head:** `20260918_0034`

> This document is the concise technical authority for the current ISI as-built platform and its owner-approved deployment target. The MasterPlan remains the canonical architecture/governance/roadmap authority, and code/tests remain the as-built implementation truth. Live production-server state is not inferred from repository source: current-server verification remains deferred to ISI-28.

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
| ISI-27 Industrial Release Candidate | IN PROGRESS / 27A ACCEPTED ON MAIN / 27B ACCEPTED ON MAIN / 27C IN_PROGRESS / NOT CI_VERIFIED |
| ISI-28 Current Server Controlled Upgrade | DEFERRED / owner-gated |

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

No customer-facing workflow, schema, dependency, runtime behavior or deployment topology changed. ISI-27 B0-R1A bootstrap is closed, ISI-27A is accepted on main, and `ISI-27C - Reproducible Release & Supply-Chain Assurance` is the current checkpoint; controlled hosted acceptance remains reserved for 27D. ISI-28 remains the exclusive live-server mutation/capacity-verification phase; Krcuga and OralScanXAI are strict non-targets.

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
Current checkpoint: `ISI-27C - Reproducible Release & Supply-Chain Assurance`.
ISI-27D remains planned, ISI-28 deferred. No hosted/server acceptance is claimed.

27C contract: `automation/specs/ISI-27C-R1-REPRODUCIBLE-RELEASE-SUPPLY-CHAIN.md`.
Its candidate introduces portable immutable release packaging, real image SBOM
and blocking scan, existing-owner SSH-signed provenance and strict serial release
state validation. GitHub Free/private signing uses local owner identity and makes
no Enterprise/SLSA certification claim. INV-M21 owns release assurance; INV-K15
owns build/signing metadata; INV-J32 maps the immutable release bundle. Python 3.11
stdlib, existing OpenSSH 8.2+ and Docker suffice; Trivy runs as an official pinned
CI action or disposable scanner container. No host package installation is required.

## 27C R1 partial verification and approved R2 implementation — 2026-10-04

27C is IN_PROGRESS, with an unstaged/uncommitted candidate; it is not accepted.
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
is ignored and no release/server gate is bypassed. Owner approved preparation
of `automation/specs/ISI-27C-R2-MINIMAL-RUNTIME-BASE-PROPOSAL.md`. The Wolfi/Python
3.11 multistage image is an unstaged candidate under actual vulnerability and
runtime acceptance; no R2 acceptance or production deployment is claimed. 27D remains planned and ISI-28 deferred.
GitHub main remains accepted 27B SHA `16a928b20907d570df2cf05101a969e1f0cda736`.
No new hosted dispatch, 27C commit/push or deployment occurred.


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
Fingerprinted evidence is retained under `automation/evidence/ISI-27C/`. This remains an
unstaged local candidate; no main acceptance, hosted CI or production deployment
is claimed.
