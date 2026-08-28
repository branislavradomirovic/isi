# ISI-10 — ORDO Domain Foundation

## Goal
Introduce the first real ORDO domain layer on top of the already completed shared identity, data and AI foundations, while preserving strict separation from SIMPA semantics.

## Baseline
- branch: `main`
- exact HEAD: `919b8b5`
- Python: `3.11.15`
- Alembic before: `20260828_0008`
- dependency: `ISI-09-SIMPA-ANALYTICS-AI = done`

## Scope
- ORDO five-pillar registry: Data, Knowledge, Analytics, AI, Human Experience;
- destination-domain dimension registry;
- source-type registry;
- conceptual indicator registry only — no validated formulas in ISI-10;
- destination profile;
- destination asset/resource registry;
- stakeholder registry;
- monitoring cycles;
- mapping from shared data sources into ORDO semantics;
- provenance-ready indicator observations;
- `/api/v1/ordo/*` routes with server-side organization/workspace/product enforcement;
- authenticated Streamlit ORDO overview and indicator workspace;
- SIMPA negative-control and domain-isolation tests.

## Domain invariants
1. ORDO data is scoped by `organization_id + workspace_id` and workspace product must be `ORDO`.
2. `src/domains/ordo/__init__.py` remains empty as a package boundary contract.
3. No SIMPA table, registry or service is reused as ORDO domain logic.
4. Indicator definitions are seeded with `methodology_status = conceptual`.
5. No synthetic destination statistics, scores, scenario results or indicator observations are seeded.
6. Shared `core_data_sources` may be mapped into ORDO only when the source belongs to the same organization/workspace and product.
7. ORDO analytics/scenarios/AI synthesis are intentionally deferred to ISI-11.

## Migration
`20260828_0008 -> 20260828_0009`

Tables:
- `ordo_pillars`
- `ordo_dimensions`
- `ordo_source_types`
- `ordo_indicator_definitions`
- `ordo_destination_profiles`
- `ordo_assets`
- `ordo_stakeholders`
- `ordo_monitoring_cycles`
- `ordo_data_mappings`
- `ordo_indicator_observations`

## Acceptance
- offline Alembic render passes;
- native PostgreSQL upgrade reaches `20260828_0009`;
- 5 pillars, 9 dimensions, 12 source types and 15 conceptual indicators are present;
- ORDO-only user can read ORDO catalog/foundation;
- SIMPA-only user cannot read ORDO scope;
- ORDO asset/stakeholder/profile/cycle operations are scoped to the selected ORDO workspace;
- full regression suite passes;
- browser QA shows real ORDO domain workspace and no fabricated destination results.
