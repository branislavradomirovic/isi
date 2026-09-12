# ADR-0025 - SIMPA/ORDO Analytical AI Methodology Architecture

Status: **OWNER-APPROVED CANONICAL DECISION**
Decision date: **2026-09-12**

## Context

ISI contains two domain products, SIMPA and ORDO. They share platform infrastructure but must preserve separate domain semantics, methodology, feature contracts, prompts, trained domain models, private knowledge namespaces and human-review responsibilities.

Earlier ISI foundations correctly separated source evidence, methodology-governed analytical results and AI synthesis. This ADR makes the production analytical boundary explicit before ISI-21 through ISI-25.

## Decision

### 1. Three-engine analytical architecture

Every production analytical workflow is decomposed into three explicit layers:

1. **Deterministic statistical/ML engine** - indicator calculation, regression, classification, clustering, forecasting, scenario mathematics, uncertainty, calibration and diagnostics.
2. **Document AI/RAG engine** - OCR/VLM extraction, embeddings, retrieval and evidence packaging with provenance.
3. **LLM/VLM synthesis engine** - bounded explanation, summarization, evidence synthesis and user-facing narrative.

LLMs/VLMs must not silently calculate authoritative regressions, classifications, scores, forecasts or scenario impacts. Numerical outputs must be produced by deterministic/versioned analytical code or by an explicitly registered ML model.

### 2. Shared technology, separate domain intelligence

SIMPA and ORDO share the ISI data platform, AI gateway, model registry, MLOps infrastructure, jobs, audit, observability and deployment substrate.

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

### 3. SIMPA analytical boundary

SIMPA is a local social-protection intelligence and monitoring system operating at aggregate/system level. It must not become a citizen-level eligibility, benefit, diagnosis or automated-risk decision engine.

Preferred unit of analysis:

`local system x indicator x period x monitoring cycle x source/provenance`

SIMPA may use descriptive analytics, validated indicator computation, regression, system-level classification, trend analysis and unsupervised analytical profiling only when the relevant methodology is explicitly versioned and approved.

No causal language may be inferred from ordinary regression/correlation. No individual person may be labelled high-risk, eligible/ineligible or otherwise subjected to an automated institutional decision by this methodology.

### 4. ORDO analytical boundary

ORDO is a destination-intelligence, planning, forecasting and scenario-support system.

Forecasting and scenarios are separate concepts:

- **forecast** = model-based probabilistic estimate from validated historical data;
- **scenario** = user-authored assumptions and deterministic/validated transformations;
- a scenario must not be presented as a forecast unless an approved response model exists.

If no validated impact model exists, the system reports `impact = NOT_ESTIMATED` rather than fabricating an effect.

Forecasts require temporal backtesting and uncertainty intervals. Scenario/forecast outputs may later use Monte Carlo or equivalent uncertainty propagation only when methodology and data justify it.

### 5. Model selection is evaluation-driven, not hard-coded

No local LLM/VLM is declared the permanent production champion by this decision.

Current owner-supplied MacBook models approved as evaluation candidates:

- `qwen3:1.7b-q4_K_M` - routing/tagging/light extraction candidate;
- `qwen3:4b-instruct-2507-q4_K_M` - primary text-LLM candidate;
- `qwen3-vl:4b-instruct-q4_K_M` - primary VLM/document candidate;
- `qwen2.5vl:3b` - VLM challenger/fallback candidate;
- `qwen2.5:7b-instruct` - stronger/slower text challenger and existing QA baseline;
- `gemma3:4b` - independent cross-family challenger.

A dedicated embedding model is required for RAG. Initial candidate set may include `qwen3-embedding:0.6b`, with `qwen3-embedding:4b` or `bge-m3` as challengers if retrieval quality requires them. These are candidate decisions, not installation or production-lock decisions.

### 6. Champion/challenger governance

Every deployed statistical, ML, embedding, LLM or VLM capability must have:

- stable model key;
- model version/checksum;
- dataset/eval-set version;
- feature/prompt/methodology version;
- validation metrics;
- approval state;
- rollback target;
- exact code SHA where applicable.

A challenger replaces a champion only after it demonstrates evidence-backed improvement under the relevant acceptance protocol. Benchmark reputation alone is insufficient.

### 7. SIMPA model-family policy

Preferred starting families, selected by target semantics:

- continuous outcome: Linear/Ridge/Elastic Net baseline, then Gradient Boosting challenger;
- counts: Poisson baseline, Negative Binomial where over-dispersion warrants it;
- rates/proportions: binomial/fractional models where statistically appropriate;
- repeated municipality/system observations: fixed/mixed effects or hierarchical models;
- trends/time: simple trend/ETS/SARIMAX before more complex challengers;
- system-level classification: Logistic Regression baseline, then tree/boosting challenger;
- unsupervised profiling: K-Means, hierarchical clustering or mixture models only with methodology-backed interpretation.

All outputs require uncertainty/diagnostics and clear non-causal wording unless a separate causal design has been approved.

### 8. ORDO model-family policy

Preferred starting families, selected by target semantics:

- arrivals/overnights/count demand: Poisson/Negative Binomial baseline, then boosted models;
- occupancy/rates: fractional/beta-type regression where appropriate;
- average stay/continuous targets: linear/robust baseline, then boosted models;
- time-series demand: ETS/SARIMA baseline, then ML/hybrid challengers;
- multi-destination panels: fixed/mixed effects or hierarchical models.

Time-series evaluation must use rolling-origin/backtesting rather than random train/test split. Core metrics include MAE, RMSE, sMAPE, MASE and prediction-interval coverage where applicable.

### 9. Explainability and uncertainty are mandatory

For classical models expose coefficients, confidence intervals, diagnostics and sample size where applicable.

For tree/boosting models expose validated global/local explainability such as SHAP, feature importance or partial dependence when appropriate.

UI language must state that feature contribution does not imply causal effect.

Forecasts must expose ranges/intervals rather than only a single point estimate.

### 10. Evidence-first presentation contract

The canonical user-facing order is:

`Evidence -> Analytics -> Model outputs -> AI interpretation -> Human review`

SIMPA should emphasize evidence quality, indicator status, statistical association, uncertainty, missing evidence and limitations.

ORDO should emphasize KPI/time-series views, seasonality, forecast intervals, scenario deltas, maps/spatial evidence where available, model explanations and limitations.

AI narrative never precedes or replaces the underlying evidence/model result.

### 11. Document AI/VLM contract

VLMs may assist with OCR, table/chart extraction, document understanding, metadata extraction and visual evidence tagging.

Machine-extracted facts are marked `EXTRACTED_UNVERIFIED` until validated by deterministic checks or human review where required.

### 12. RAG contract

RAG uses a dedicated embedding model and preserves tenant/product/namespace isolation.

Allowed existing namespace families remain:

- `PUBLIC/ISI`
- `PUBLIC/SIMPA`
- `PUBLIC/ORDO`
- `ORG-<organization UUID>/SIMPA`
- `ORG-<organization UUID>/ORDO`

No cross-product private retrieval is permitted.

### 13. Evaluation protocol

Create and version separate evaluation sets:

- `SIMPA-EVAL-v1`
- `ORDO-EVAL-v1`

LLM/VLM evaluation must prioritize grounded factuality, hallucination rate, structured-output validity, source/provenance compliance, Serbian-language quality, instruction compliance, reasoning quality, latency and resource footprint.

Statistical/ML evaluation must use problem-appropriate predictive/diagnostic metrics, calibration where relevant, temporal validation for forecasts and explicit baseline comparison.

### 14. Human approval boundary

No formula, weight, threshold, class definition, risk band, causal claim, forecast methodology, recommendation policy or production model may be represented as validated merely because it is implemented or generated by AI.

Human approval and supporting evidence remain mandatory for transition from `DRAFT`/`PROPOSED` to `VALIDATED` methodology state.

## Roadmap consequences

This decision is implemented across the existing industrialization sequence:

- **ISI-21 - Data Governance & Privacy:** analytical-data classification, purpose/retention/provenance rules and sensitive feature governance.
- **ISI-22 - Industrial Data Platform:** canonical analytical datasets, schema/feature contracts, temporal keys, quality/quarantine, idempotent ingestion, missing-value semantics and reproducible dataset versions.
- **ISI-23 - SIMPA Production Methodology:** detailed SIMPA indicator/methodology catalogue, permitted model families, validation rules, uncertainty, presentation contract, Help and User Guide.
- **ISI-24 - ORDO Production Methodology:** detailed ORDO indicators, time-series/forecast/scenario methodology, spatial/evidence framework, uncertainty, presentation contract, Help and User Guide.
- **ISI-25 - Industrial AI / MLOps:** champion/challenger registry, eval datasets, embeddings/RAG, LLM/VLM evaluation, model promotion/rollback, prompt/version governance, structured outputs and human-review traceability.
- **ISI-26/27:** performance, resilience and release-candidate acceptance of the complete analytical stack.

## Non-decisions

This ADR does not validate any specific SIMPA or ORDO formula, weight, threshold, classification band, causal model, forecast model or production LLM/VLM. Those remain methodology/evaluation tasks.
