# ISI Autonomous Industrialization Master Plan

Status: **OWNER_APPROVED canonical planning baseline - 2026-09-12**.

This plan is binding for the ISI industrialization track unless the owner explicitly approves a later change.

## 1. Purpose

Industrialize the existing ISI platform and its two domain applications, SIMPA and ORDO, through specification-driven development while preserving the current server and deployment setup until a separately approved release/deployment phase.

The immediate objective is not a new infrastructure platform and not a new server. The objective is to make the codebase, data lifecycle, analytical methodology, AI lifecycle, security, quality assurance, observability, release engineering, and deployment automation sufficiently mature that a final release can later be pushed to the current server in one controlled upgrade.

## 2. Locked product model

- ISI is the institutional platform of the Institute for Social Inclusion.
- SIMPA and ORDO are the only domain applications in the current product architecture.
- SIMPA and ORDO remain domain-isolated while reusing shared infrastructure.
- COSMOS is not introduced as a software layer, product, domain, route, tenant, namespace, or menu item.
- Existing FastAPI + Streamlit + PostgreSQL + Redis/RQ + S3-compatible storage + shared AI gateway architecture is preserved unless a later accepted ADR explicitly changes it.
- Existing server topology remains the target deployment topology during this industrialization program.

## 3. Owner-driven direct-main development model

Normal development uses one canonical local repository, one worktree, and the local `main` branch only.

The binding execution chain is:

`specification -> direct implementation on canonical main -> deterministic local validation -> human review -> owner approval -> exact-file staging -> direct commit/push to main -> exact-main GitHub Actions verification -> next task`

Rules:

- Do not create feature, implementation, review, automation, or temporary branches unless the owner explicitly authorizes an exception.
- Do not create extra worktrees, clones, or alternate checkout workspaces for task isolation unless the owner explicitly authorizes an exception.
- Codex or another implementation agent may modify the canonical `main` worktree only within the task scope.
- Task changes remain unstaged and uncommitted until deterministic validation and human review are complete and the owner approves the exact candidate.
- No task is complete because an agent says it is complete. Completion is evidence-based.

### Verification labels

- `IMPLEMENTED`: an unstaged/uncommitted reviewed candidate exists on canonical `main` and required local/task gates pass as available.
- `REVIEW_VERIFIED`: review of the exact candidate or final main SHA has no unresolved technical blocker.
- `OWNER_APPROVED_MAIN_COMMIT`: the owner explicitly approved exact-file staging and commit/push to `main`.
- `CI_VERIFIED`: all blocking GitHub Actions jobs pass on the exact committed `main` SHA.
- `COMPLETE`: implementation, review, owner-approved main commit/push, and exact-main blocking CI are complete.
- `SERVER_VERIFIED`: explicitly approved server acceptance has passed.
- `DEFERRED_SERVER_VERIFICATION`: implementation is complete but the current task intentionally did not touch the server.

A failed required gate returns the active task to implementation/fix state. Required gates must not be weakened merely to obtain green status.

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

## 5. Canonical analytical AI architecture

The owner approved the analytical AI direction on 2026-09-12. ADR-0025 is the authoritative architecture decision for this layer.

The central invariant is:

**Numerical intelligence is computed by deterministic statistical/ML systems; documentary intelligence is extracted/retrieved with provenance; LLM/VLM systems synthesize and explain bounded evidence; humans approve institutional methodology and decisions.**

### 5.1 Three-engine architecture

Production analytical workflows are decomposed into three explicit layers:

1. deterministic statistical/ML engine - indicators, regression, classification, clustering, forecasting, scenario mathematics, uncertainty, calibration, diagnostics;
2. document AI/RAG engine - OCR/VLM extraction, embeddings, retrieval, evidence packaging and provenance;
3. LLM/VLM synthesis engine - bounded explanation, summarization, evidence synthesis, structured narrative and user-facing interpretation.

LLMs/VLMs must not silently calculate authoritative regressions, classifications, scores, forecasts, scenario impacts, eligibility, risk bands, or causal conclusions.

### 5.2 Shared technology, separate domain intelligence

SIMPA and ORDO share infrastructure services including data platform, AI gateway, job execution, model registry, audit, observability and deployment substrate.

They do not implicitly share:

- domain prompts;
- indicator definitions;
- methodology versions;
- feature contracts;
- trained domain models;
- private RAG namespaces;
- scoring semantics;
- forecast/scenario semantics;
- policy conclusions.

### 5.3 Evidence-first user experience

Every analytical view follows:

`Evidence -> Analytics -> Model outputs -> AI interpretation -> Human review`

Minimum presentation requirements where applicable:

- methodology/version;
- source/provenance;
- sample/time coverage;
- missing evidence;
- uncertainty/confidence intervals;
- model diagnostics/quality;
- explainability appropriate to model family;
- limitations;
- explicit human-review state.

### 5.4 SIMPA analytical boundary

SIMPA is a local social-protection intelligence and monitoring system operating at aggregate/system level.

Preferred unit of analysis:

`local system x indicator x period x monitoring cycle x source/provenance`

SIMPA must not become a citizen-level eligibility, benefit, diagnosis, automated-risk, or punitive decision engine.

Permitted analytical families, once their methodology is explicitly versioned and approved, include descriptive analysis, validated indicator computation, regression, system-level classification, trend analysis and unsupervised analytical profiling.

Ordinary regression/correlation must not be presented as causality.

### 5.5 ORDO analytical boundary

ORDO is a destination-intelligence, planning, forecasting and scenario-support system.

Forecast and scenario are distinct:

- forecast = model-based probabilistic estimate from validated historical data;
- scenario = user-authored assumptions combined with deterministic or validated transformations;
- scenario output must not be presented as forecast unless an approved response model exists.

If no validated impact model exists, the system reports `impact = NOT_ESTIMATED` rather than fabricating an effect.

Forecasts require temporal backtesting and uncertainty intervals.

### 5.6 Model selection and champion/challenger governance

No local model is permanently selected by name in this master plan.

Current owner-supplied MacBook models are evaluation candidates:

- `qwen3:1.7b-q4_K_M` - lightweight routing/tagging/extraction candidate;
- `qwen3:4b-instruct-2507-q4_K_M` - primary text-LLM candidate;
- `qwen3-vl:4b-instruct-q4_K_M` - primary VLM/document candidate;
- `qwen2.5vl:3b` - VLM challenger/fallback candidate;
- `qwen2.5:7b-instruct` - stronger/slower text challenger and existing QA baseline;
- `gemma3:4b` - independent cross-family challenger.

A dedicated multilingual embedding model is required for RAG. Initial candidates may include `qwen3-embedding:0.6b`, with larger or alternate multilingual challengers such as `qwen3-embedding:4b` or `bge-m3` if retrieval quality requires them. These are evaluation candidates, not an installation or production lock.

Each promoted model capability must have a stable key, version/checksum, dataset/eval-set version, methodology/feature/prompt version, validation metrics, approval state, rollback target and code SHA where applicable.

A challenger replaces a champion only after evidence-backed improvement on the relevant acceptance protocol.

### 5.7 Canonical evaluation sets

Create and version separate evaluation sets:

- `SIMPA-EVAL-v1`
- `ORDO-EVAL-v1`

LLM/VLM evaluation prioritizes grounded factuality, hallucination rate, structured-output validity, source/provenance compliance, Serbian-language quality, instruction compliance, reasoning quality, latency and resource footprint.

Statistical/ML evaluation uses problem-appropriate metrics, calibration where relevant, explicit baseline comparison and temporal validation for forecasts.

### 5.8 Human methodology approval boundary

No formula, weight, threshold, class definition, risk band, causal claim, forecast methodology, recommendation policy or production model may be represented as validated merely because it is implemented or AI-generated.

Methodology lifecycle is explicit, at minimum:

`DRAFT -> PROPOSED -> VALIDATED -> RETIRED`

Human approval and supporting evidence are mandatory for transition to `VALIDATED`.

## 6. Industrialization workstream

### ISI-17 - Autonomous Development Harness + CI

Goal: make the repository capable of governing autonomous development.

Status: completed in the canonical history.

Core deliverables include binding agent instructions, deterministic dependencies, blocking GitHub Actions gates, isolated migration/native PostgreSQL validation, supply-chain checks, policy guards and evidence conventions.

### ISI-18 - Observability & Operational Diagnostics

Goal: instrument the application so failures and degradation can be diagnosed before and after deployment.

Status: completed in the canonical history.

### ISI-19 - Backup, Restore & Disaster-Recovery Automation

Goal: make recovery deterministic and testable.

Status: completed in the canonical history.

### ISI-20 - Enterprise Security Completion

Goal: close the gap between baseline hardening and institutional-grade repository-side security controls.

Status: **COMPLETE / CI_VERIFIED**.

Completion record:

- implementation commit: `f4b3a3c2486a2d3a051a70d582245e199d1b36ba`;
- final canonical main SHA after documentation-only secret-scan wording fix: `61df1aa7622cb59ee60e2781fee98f8885324d55`;
- authoritative GitHub Actions: `ISI required acceptance` run #58, run ID `34655017377`;
- workflow conclusion: `success`;
- policy, quality, tests, architecture-security, migration, native-postgres, compose, supply-chain, build and aggregate acceptance all passed;
- server verification remains `DEFERRED_SERVER_VERIFICATION`;
- real-provider MFA and external penetration testing remain explicitly not performed.

### ISI-21 - Data Governance & Privacy Controls

Goal: make data ownership, provenance, sensitivity, retention, isolation and analytical-purpose governance explicit and enforceable.

Required deliverables now include:

- data classification model;
- dataset/source ownership metadata;
- lineage/provenance contracts;
- retention/purge/anonymization hooks;
- tenant/product boundary tests;
- auditability of sensitive data access;
- export controls;
- privacy-impact documentation pack;
- explicit rule that client/institution data never becomes cross-tenant/cross-product shared knowledge automatically;
- analytical-data purpose tags and sensitivity classes;
- feature provenance and feature-purpose governance hooks;
- dataset version identity sufficient for later reproducible SIMPA/ORDO model evaluation;
- rules for derived/aggregated data and de-identification state;
- explicit distinction between raw source, normalized record, analytical feature, indicator result, model output and AI narrative.

### ISI-22 - Industrial Data Platform

Goal: evolve ingestion from framework capability to robust production-grade data engineering and reproducible analytical datasets.

Required deliverables include:

- versioned source connector contracts;
- schema mapping/versioning;
- incremental/idempotent imports;
- deduplication/reconciliation;
- quarantine/error queues;
- source freshness and quality checks;
- backfill support;
- ingestion lineage;
- standardized canonical ingestion boundary for SIMPA and ORDO;
- reference connector acceptance fixtures;
- canonical analytical dataset contracts;
- stable temporal/granularity keys;
- explicit missing-value semantics (`missing` is not silently converted to zero);
- feature contracts and reproducible dataset versions;
- source-to-feature lineage and quality state;
- analytical snapshot contracts consumed by deterministic statistical/ML engines and domain AI synthesis.

### ISI-23 - SIMPA Production Methodology

Goal: convert SIMPA methodology infrastructure into a validated, versioned, reproducible analytical product.

The canonical design baseline is `docs/roadmap/ISI-SIMPA-METHODOLOGY-v1.md` and ADR-0025.

Required deliverables include:

- formal indicator registry contract;
- methodology lifecycle;
- calculation tests with reference datasets;
- LISI methodology specification and implementation only when owner-approved;
- sub-indices/weights/normalization/missing-data rules/versioning/provenance where the approved methodology requires them;
- evidence-quality/confidence representation;
- social-map/GIS-ready data model and interfaces;
- policy-monitoring/evaluation workflow;
- deterministic statistical model contracts by target semantics;
- uncertainty, diagnostics and calibration rules;
- system-level classification only where classes are explicitly defined and validated;
- non-causal wording for ordinary association models;
- explainability and reporting contracts;
- detailed in-app Help and SIMPA User Guide.

Critical rule: no Codex/LLM may invent indicator formulas, LISI weights, thresholds, citizen risk labels, causal claims, eligibility logic or policy conclusions.

### ISI-24 - ORDO Production Methodology

Goal: convert ORDO evidence/scenario infrastructure into a production destination-intelligence methodology without fabricating predictive capability.

The canonical design baseline is `docs/roadmap/ISI-ORDO-METHODOLOGY-v1.md` and ADR-0025.

Required deliverables include:

- validated ORDO indicator-methodology registry;
- reference datasets and calculation tests;
- spatial/GIS-ready contracts;
- scenario evidence model;
- development-goal evaluation framework;
- methodology provenance/versioning;
- regression/model-family contracts by target semantics;
- time-series forecasting protocol using rolling-origin/backtesting;
- forecast intervals and uncertainty diagnostics;
- explicit scenario-versus-forecast boundary;
- deterministic scenario engine with `NOT_ESTIMATED` when no approved impact model exists;
- optional uncertainty propagation/Monte Carlo only after methodology validation;
- explainability and presentation contracts;
- detailed in-app Help and ORDO User Guide.

Forecasting or causal claims are production-valid only when separate evidence-backed methodology/model specifications are approved.

### ISI-25 - Industrial AI / MLOps

Goal: make statistical/ML, embedding, LLM and VLM behavior measurable, versioned, reversible and auditable.

The canonical evaluation baseline is `docs/roadmap/ISI-AI-MODEL-EVALUATION-PROTOCOL-v1.md` and ADR-0025.

Required deliverables include:

- model registry/version contract across statistical/ML, embedding, LLM and VLM capabilities;
- champion/challenger lifecycle;
- prompt registry/version enforcement;
- `SIMPA-EVAL-v1` and `ORDO-EVAL-v1` dataset contracts;
- structured-output validation;
- evidence/RAG provenance contracts;
- multilingual embedding evaluation;
- retrieval evaluation and namespace isolation;
- prompt-injection and unsafe-context tests;
- PII/sensitivity guards;
- retry/timeout/circuit-breaker behavior;
- provider/model fallback policies;
- human-review traceability;
- model/prompt rollback;
- inference quality/latency/resource accounting;
- deterministic promotion criteria that require challenger improvement over the registered baseline.

Human-in-the-loop remains a permanent decision-support requirement.

### ISI-26 - Performance, Load & Resilience Engineering

Goal: establish measurable capacity and failure behavior across API, data, statistical/ML and AI flows.

Deliverables include workload profiles, load/stress tests, AI-job concurrency, large-report tests, controlled dependency failures, performance budgets and evidence-backed tuning.

### ISI-27 - Industrial Release Candidate & Acceptance Pack

Goal: produce one release candidate technically ready for controlled deployment.

Release acceptance must include explicit SIMPA and ORDO methodology states, Help/User Guide completeness, model/eval provenance, security/privacy acceptance, migration/recovery rehearsals and performance acceptance.

### ISI-28 - Current Server Controlled Upgrade

Status: intentionally deferred and not executable during the industrialization track without fresh explicit owner approval.

This is the only phase allowed to touch the current server, DNS, ingress, real SMTP, production secrets or production data.

## 7. Task dependency model

Default serial dependency:

`ISI-17 -> ISI-18 -> ISI-19 -> ISI-20 -> ISI-21 -> ISI-22 -> ISI-23 -> ISI-24 -> ISI-25 -> ISI-26 -> ISI-27 -> ISI-28`

The canonical AI decision does not authorize out-of-order production implementation. It strengthens the requirements of ISI-21 through ISI-25 while preserving the serial dependency model.

## 8. Implementation-agent contract

For each implementation task, the agent must receive:

- exact baseline/ref;
- objective;
- locked architecture and relevant ADRs;
- required behavior;
- DB/API/UI/worker/configuration impact;
- security/privacy constraints;
- methodology constraints;
- required tests;
- exact acceptance commands;
- required evidence;
- explicit non-goals;
- forbidden changes;
- completion definition.

Normal owner-driven execution occurs directly on the canonical local `main` worktree. The agent must not stage, commit or push without explicit owner authorization.

A reviewer may inspect the exact diff against the specification, but deterministic acceptance and exact-main GitHub Actions remain authoritative.

Every task status must expose task ID, baseline/head SHA, current evidence-backed state, required gates, evidence path, known warnings and server-verification status.

## 9. Human gates

Human approval remains required at minimum for:

- architecture changes;
- new external dependencies with material operational impact;
- security-policy changes;
- SIMPA/ORDO methodology validation;
- formula/weight/threshold/class-definition approval;
- claims of predictive or causal capability;
- production champion model promotion where methodology or institutional output changes materially;
- major industrialization milestone completion;
- any server/deployment action;
- any production secret or production data mutation.

## 10. Final deployment concept

The final server action is release-based rather than a casual `git pull`.

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

## 11. Owner approval record

Owner approvals now binding in this master plan include:

### 2026-09-09 industrialization baseline

- locked ISI -> {SIMPA, ORDO} product architecture;
- exclusion of COSMOS from the current runtime/application architecture;
- server freeze through ISI-27;
- serial ISI-17 through ISI-28 industrialization sequence;
- human approval boundaries;
- repository-audit findings as implementation input.

### 2026-09-12 workflow and analytical AI canonicalization

- one canonical local repository, one worktree and owner-driven direct-main development model;
- no normal feature/implementation/review branch or PR requirement;
- ISI-20 completion on canonical main after successful run #58;
- deterministic statistical/ML engine for authoritative numerical analytics;
- document AI/RAG with provenance for extraction/retrieval;
- LLM/VLM as bounded synthesis/explanation rather than silent numerical authority;
- separate SIMPA and ORDO domain intelligence over shared infrastructure;
- SIMPA aggregate/system-level boundary and prohibition on citizen-level automated institutional decisions;
- ORDO forecast-versus-scenario separation and `NOT_ESTIMATED` when an impact model is not validated;
- champion/challenger model governance;
- dedicated embedding-model evaluation for RAG;
- `SIMPA-EVAL-v1` and `ORDO-EVAL-v1`;
- evidence-first presentation order;
- methodology lifecycle requiring human approval before `VALIDATED`.

Material changes to these points require a new explicit owner approval and, where architectural, a new or superseding ADR.
