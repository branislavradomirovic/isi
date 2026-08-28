# ISI-09 — SIMPA Analytics + AI

## Purpose

ISI-09 introduces the first analytical and AI-assisted layer specific to SIMPA, on top of the already accepted shared data and shared AI foundations.

The phase must not silently convert the conceptual indicator registry introduced by ISI-08 into validated methodology. Indicator computation is permitted only when a human-approved methodology version exists and the linked indicator definition has `methodology_status=validated`.

## Scope

- SIMPA monitoring analytics snapshots scoped to Organization + Workspace + SIMPA.
- Evidence-quality metrics: validated observation ratio, provenance coverage, indicator coverage and a transparent structural quality score.
- Versioned indicator methodology registry with explicit draft / validated / retired states.
- Computation engine that refuses unvalidated methodology.
- Provenance-preserving indicator results.
- SIMPA AI synthesis records linked to the shared AI job registry.
- SIMPA-specific structured prompt `simpa.monitoring.synthesis`.
- Sensitive SIMPA synthesis is forced through the shared `local_only` policy and requires human review.
- Human accept / reject review flow for AI synthesis.
- Streamlit `Analitika` workspace for SIMPA.
- Local QA through the existing Ollama model `qwen2.5:7b-instruct` using the shared AI gateway.

## Non-goals

- No automatic validation of any of the 15 conceptual indicators.
- No fabricated formulae, thresholds, risk scores, citizen-level records or policy recommendations.
- No AI institutional decision making.
- No ORDO analytics implementation; ORDO remains reserved for ISI-11.
- No direct Ollama calls from SIMPA domain runtime; all AI requests go through the shared ISI AI service.

## Methodology rule

A computation is valid only if all of the following are true:

1. the indicator is active;
2. the indicator definition is explicitly `validated`;
3. an active validated methodology version exists;
4. the methodology computation type is supported;
5. required validated source observations are present;
6. the result stores its methodology version and source observation provenance.

ISI-09 ships no validated methodology versions by default.

## Analytics semantics

The default monitoring snapshot describes **quality and coverage of evidence**, not the social condition of a municipality and not the level of social risk.

The structural quality score is based only on:

- ratio of validated observations;
- provenance coverage;
- active-indicator coverage.

It is exposed with its components so it can never be mistaken for a domain outcome index.

## AI contract

`simpa.monitoring.synthesis` receives only a bounded SIMPA monitoring snapshot and evidence metadata. It must return structured JSON with:

- `executive_summary`;
- `evidence_quality`;
- `attention_points`;
- `limitations`;
- `human_review_required`.

The prompt explicitly forbids diagnoses, eligibility decisions, benefit decisions, institutional conclusions or claims unsupported by evidence.

For `sensitivity=sensitive`, the existing shared AI policy forces:

- provider policy `local_only`;
- external providers disabled;
- human review required.

## Migration

`20260828_0007 -> 20260828_0008`

New tables:

- `simpa_indicator_methodologies`
- `simpa_analytics_runs`
- `simpa_indicator_results`
- `simpa_ai_syntheses`

The migration also registers the SIMPA monitoring synthesis prompt in the shared AI prompt registry. It does not seed a validated indicator methodology.

## Acceptance

- Alembic reaches `20260828_0008`.
- No conceptual indicator becomes validated automatically.
- Analytics snapshot is tenant/workspace scoped.
- Unvalidated indicator computation is rejected.
- AI synthesis uses product `SIMPA`, local-only sensitive policy and human review.
- Review action is explicit and auditable.
- ORDO cannot read SIMPA analytics endpoints.
- Full regression suite remains green.
- Browser QA shows the SIMPA analytics workspace without fabricated results.
