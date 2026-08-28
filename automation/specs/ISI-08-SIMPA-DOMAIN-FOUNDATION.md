# ISI-08 — SIMPA Domain Foundation

## Objective

Create the first real SIMPA domain layer on top of the already accepted ISI shared identity, data and AI foundations.

ISI-08 is intentionally **not** the analytics/AI phase. It establishes the domain vocabulary, local-system structure, source mapping and provenance-ready indicator observation model required by ISI-09.

## Architecture lock

- ISI remains the parent platform.
- SIMPA is an independent flagship domain application under ISI.
- ORDO remains a separate domain and must never reuse SIMPA tables, indicator definitions or UI as if they were shared domain semantics.
- No COSMOS branding or architecture is reintroduced.
- Organization + Workspace remain the tenant boundary.
- All SIMPA runtime scope is hard-fixed to `product_code=SIMPA` and revalidated server-side.
- No person-level beneficiary/citizen model is introduced in ISI-08.
- No fake municipality, user counts, service statistics, risk scores or indicator values are seeded.

## Source-derived conceptual registries

The source material defines nine broad data domains used for local social-protection development and multiple important indicator concepts. ISI-08 turns these into a **conceptual registry**, not validated formulas.

### Dimensions

1. Social needs
2. Poverty/material vulnerability
3. Family, children and youth
4. Violence/crisis situations
5. Older people and persons with disabilities
6. Social-service accessibility
7. Local-system capacity
8. Intersectoral cooperation
9. Outcomes/effects

### Source types

Local government, social-work center, social-service providers, education, health, employment, housing, civil society and demographic/statistical sources.

### Indicator registry

15 conceptual indicators are seeded. Every seeded definition has `methodology_status=conceptual`. ISI-08 does not provide formulas or automatic calculations. Formula validation, statistical methodology and AI/analytics use belong to ISI-09.

## Domain tables

- `simpa_dimensions`
- `simpa_source_types`
- `simpa_indicator_definitions`
- `simpa_local_system_profiles`
- `simpa_local_actors`
- `simpa_monitoring_cycles`
- `simpa_data_mappings`
- `simpa_indicator_observations`

## Shared-data integration

`simpa_data_mappings` references `core_data_sources`; indicator observations may reference `core_data_source_versions`. This preserves provenance without duplicating the shared ingestion/storage layer.

## Privacy position

The phase models local-system structure and aggregate/provenance-ready observations only. It does not introduce citizen/beneficiary identity tables. Future person-level processing, if approved, requires an explicit privacy, legal-basis and data-minimization design rather than being inferred from this foundation.

## API

Prefix: `/api/v1/simpa`

- `GET /catalog`
- `GET /foundation`
- `PUT /profile`
- `GET|POST /actors`
- `GET|POST /cycles`
- `GET|POST /mappings`
- `GET|POST /observations`

Every scoped route requires authenticated SIMPA access. Read operations use `indicator.read`; domain setup uses `workspace.manage`; observation/mapping/monitoring writes use `indicator.manage`.

## UI

For SIMPA only:
- the overview becomes a domain-aware SIMPA foundation dashboard;
- `Indikatori` renders the conceptual registry and real workspace observations;
- empty states explicitly state that no data have been invented.

For ORDO:
- `Indikatori` remains a transparent placeholder for ISI-10.

## Migration

`20260828_0006 -> 20260828_0007`

The migration seeds only canonical conceptual registries. It does not seed municipality profiles, local actors, observations or fake operational data.

## QA

Main runner validates:
- clean baseline `db99eb7`;
- Python 3.11.15;
- ISI-07 done;
- Alembic 0006 -> 0007;
- static domain audit;
- focused tests;
- native PostgreSQL tables/catalog counts;
- full regression suite;
- Docker Compose config;
- git whitespace.

Local QA validates:
- SIMPA user can access catalog/foundation;
- conceptual counts 9/9/15;
- ORDO-only user receives 403 against a SIMPA workspace;
- browser opens once, on port 8506.

No commit or push is performed automatically.
