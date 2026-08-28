# ADR-0019 — ORDO Analytics + AI

Status: proposed by ISI-11, accepted when ISI-11 closes.

## Decision

ORDO analytics is implemented as an ORDO-owned domain layer on top of the shared ISI Data and AI platform. It does not reuse SIMPA analytics models, tables, prompts or policy profiles.

The analytical process follows the ORDO method: development goal → evidence integration → indicator methodology → analytics snapshot → scenario framing → evidence-bounded scenario assessment → AI synthesis → human judgment.

## Safety and methodology boundaries

1. The 15 ISI-10 indicator definitions remain conceptual until a methodology is explicitly authored and validated.
2. ISI-11 supports only `direct_observation` as a validated computation type. No hidden formula is introduced.
3. `evidence_quality_score` measures evidence readiness only. It is not a destination performance, competitiveness, sustainability, inclusion, employment, quality-of-life or investment score.
4. A scenario is a user-authored planning object containing assumptions and measures. ORDO never turns these inputs into asserted facts.
5. `ordo_scenario_assessments.forecast_performed` is database-constrained to `false`. ISI-11 assessments describe evidence readiness and missing evidence; they do not predict effects.
6. ORDO AI uses the shared AI gateway through the ORDO-specific `ordo-decision-support-local` policy: `local_only`, no external provider, mandatory human review.
7. The ORDO prompt requires `forecast_performed=false` and `human_review_required=true`.
8. Knowledge context is restricted to `PUBLIC/ISI`, `PUBLIC/ORDO`, and `ORG-<organization UUID>/ORDO`. SIMPA namespaces are not valid ORDO context.
9. ISI-11 records the namespace contract but does not claim semantic RAG retrieval when no retrieved chunks have actually been supplied.

## Data model

New ORDO tables:

- `ordo_indicator_methodologies`
- `ordo_analytics_runs`
- `ordo_indicator_results`
- `ordo_development_goals`
- `ordo_scenarios`
- `ordo_scenario_assessments`
- `ordo_ai_syntheses`

The migration also seeds:

- prompt `ordo.decision_support.synthesis`
- policy `ordo-decision-support-local`

No validated ORDO indicator methodology is seeded.

## Why

ORDO is intended to help a destination understand connected natural, cultural, economic, social, spatial and institutional processes. That requires more than dashboards, but scenario capability must not be confused with unsupported prediction. ISI-11 therefore establishes the analytical and AI workflow while keeping methodology validation, causality and development decisions explicitly human-controlled.
