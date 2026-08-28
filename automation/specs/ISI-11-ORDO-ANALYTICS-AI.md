# ISI-11 — ORDO Analytics + AI

## Objective

Turn the ISI-10 ORDO domain foundation into an evidence-bounded decision-support workflow for destination development. The phase implements validated indicator computation infrastructure, evidence-quality analytics, development goals, scenario framing, evidence-only scenario assessment, and local AI synthesis with mandatory human review.

## Architectural baseline

- ISI remains the parent platform.
- ORDO is one flagship domain product and remains isolated from SIMPA domain semantics.
- Shared PostgreSQL, Data Platform, AI gateway, queueing, audit and identity/access remain platform services.
- Public site remains FastAPI/Jinja and is not changed here.
- Private ORDO GUI remains Streamlit.
- Native local PostgreSQL is used for development; Docker Compose remains deployment topology only.

## ORDO method implemented in this phase

`development goal → evidence → indicator methodology → analytics snapshot → scenario → evidence-only assessment → AI synthesis → human review`

This is intentionally narrower than a predictive model. ISI-11 establishes the decision-support workflow without pretending that unvalidated causal or forecasting models exist.

## Deliverables

### 1. Indicator methodology and computation

Add `ordo_indicator_methodologies` with versioned draft / validated / retired states. Initial ISI-10 indicators stay conceptual. No methodology is seeded as validated.

Only `direct_observation` is supported in ISI-11. An indicator can be computed only when:

- the ORDO indicator is active;
- its methodology status is `validated`;
- a validated methodology row exists;
- a validated observation exists in the same organization/workspace and optional monitoring cycle;
- provenance is retained in the result.

Otherwise return `methodology_not_validated` or `validated_observation_required`.

### 2. Evidence analytics

Add `ordo_analytics_runs` and snapshot logic for:

- observation count;
- validated/draft/rejected observation counts;
- provenance coverage;
- indicator coverage;
- dimension coverage;
- pillar coverage;
- evidence quality score and band.

`evidence_quality_score = 0.45 × validated observation ratio + 0.35 × provenance coverage + 0.20 × indicator coverage`.

This is an evidence-readiness metric only. It must never be described as competitiveness, sustainability, inclusion, employment, quality-of-life, investment or destination performance.

### 3. Development goals

Add `ordo_development_goals` scoped to organization + ORDO workspace. A goal contains a code, title, description, focus area, optional horizon and lifecycle status.

Supported focus areas are planning labels only:

- competitiveness
- sustainability
- inclusion
- employment
- quality_of_life
- destination_development
- custom

No score or target value is fabricated.

### 4. Scenarios

Add `ordo_scenarios` linked to a development goal. Scenario assumptions and measures are user-authored planning inputs. The platform must not silently convert them into facts or predicted outcomes.

### 5. Evidence-only scenario assessment

Add `ordo_scenario_assessments` linked to a scenario and analytics snapshot.

The assessment stores:

- current evidence quality and coverage;
- observed/missing dimensions;
- number of user-authored assumptions and measures;
- limitations.

Database and service invariant: `forecast_performed = false`.

ISI-11 must not calculate causal, financial, visitor-volume, employment, sustainability, inclusion or quality-of-life effects.

### 6. ORDO AI profile

Use the shared ISI AI gateway. Add ORDO-specific registry entries:

- policy: `ordo-decision-support-local`
  - product scope `ORDO`
  - sensitivity `internal`
  - provider policy `local_only`
  - `allow_external=false`
  - `require_human_review=true`
- prompt: `ordo.decision_support.synthesis`

The domain service must not call Ollama directly. The local QA model remains `qwen2.5:7b-instruct` through the shared `isi-ollama-chat-default` registry key. This is a QA choice, not a final production model decision.

### 7. AI output contract

Structured output fields:

- `executive_summary`
- `evidence_basis`
- `development_opportunities`
- `tradeoffs`
- `limitations`
- `next_evidence_needed`
- `forecast_performed`
- `human_review_required`

The prompt must force:

- `forecast_performed=false`
- `human_review_required=true`

It must prohibit fabricated facts, unvalidated formulas, destination ranking, guaranteed recommendations, unsupported forecasts and autonomous development decisions.

### 8. Knowledge namespace contract

ORDO synthesis may reference only:

- `PUBLIC/ISI`
- `PUBLIC/ORDO`
- `ORG-<organization UUID>/ORDO`

SIMPA namespaces are forbidden. The service records this namespace contract. It must not claim that semantic RAG retrieval occurred unless actual retrieved chunks are supplied by the shared AI layer.

### 9. API

Add `/api/v1/ordo/analytics/*` endpoints for:

- summary
- analytics runs
- methodology registry / validation
- indicator compute
- development goals
- scenarios and scenario status
- scenario assessments and review
- AI syntheses and human review

All endpoints require valid ORDO organization/workspace selection plus explicit permissions.

### 10. Streamlit

Replace the ORDO analytics placeholder with a real ORDO analytics workspace containing:

- evidence/readiness dashboard;
- methodology status;
- analytics snapshots;
- development goals;
- scenarios;
- evidence-only scenario assessment;
- local AI decision-support synthesis;
- visible safety and human-review language.

SIMPA analytics remains unchanged and separate.

## Migration

`20260828_0009 → 20260828_0010`

New tables:

- `ordo_indicator_methodologies`
- `ordo_analytics_runs`
- `ordo_indicator_results`
- `ordo_development_goals`
- `ordo_scenarios`
- `ordo_scenario_assessments`
- `ordo_ai_syntheses`

Prompt JSON seeding must use an offline-safe `CAST(:output_schema AS JSON)` path from the start.

## Acceptance gates

1. exact clean baseline `aabd4d3` on `main`;
2. Python 3.11.15;
3. ISI-10 status `done`;
4. native PostgreSQL at `20260828_0009` before install;
5. static audit PASS;
6. Alembic offline SQL render PASS;
7. native migration to `20260828_0010` PASS;
8. focused ISI-11 tests PASS;
9. native PostgreSQL acceptance PASS;
10. full regression suite PASS;
11. Docker Compose config PASS;
12. local ORDO API + real Ollama smoke PASS;
13. browser/visual QA PASS;
14. final analyzer PASS;
15. no automatic commit or push.

## Non-goals

- no automatic destination ranking;
- no fabricated indicator formula;
- no causal or predictive impact model;
- no visitor-volume forecast;
- no investment return forecast;
- no automated employment/inclusion/sustainability effect forecast;
- no autonomous recommendation acceptance;
- no cross-product SIMPA data reuse;
- no direct Ollama call from ORDO domain code;
- no final production model lock-in;
- no production cutover.
