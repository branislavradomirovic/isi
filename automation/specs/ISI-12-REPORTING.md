# ISI-12 — Shared Reporting

## Status
Implementation task. The task remains `ready` until explicit local browser QA is accepted and recorded.

## Baseline
- Required Git HEAD: `d9e8135` — `Complete ORDO analytics and AI`.
- Required clean working tree.
- Required Python: `3.11.15`.
- Required native PostgreSQL/Alembic before: `20260828_0010`.
- Required predecessor: `ISI-11-ORDO-ANALYTICS-AI = done`.
- Local development continues to use native PostgreSQL; Docker Compose is deployment topology only.

## Architectural contract
ISI has one shared reporting engine for both flagship products. The engine owns report identity, immutable versions, review/publish lifecycle, provenance manifests and export artefacts. SIMPA and ORDO keep separate domain adapters and never share domain records.

The boundary is:

`SIMPA/ORDO domain snapshot -> product adapter -> shared reporting version -> review -> publication -> immutable export artefact`

The shared reporting core must not infer SIMPA or ORDO semantics itself. Product adapters construct evidence-bounded report content from real persisted domain records.

## Scope

### Persistence
Migration `20260828_0011` introduces:
- `core_reports`;
- `core_report_versions`;
- `core_report_reviews`;
- `core_report_exports`.

Every report is scoped by `organization_id + workspace_id + product_code`. Every report version stores:
- immutable structured content;
- a provenance source manifest;
- SHA-256 of content;
- SHA-256 of source manifest;
- lifecycle timestamps.

### Lifecycle
A version follows:

`draft -> in_review -> approved -> published`

or:

`draft -> in_review -> rejected`

Publishing a newly approved version supersedes any previously published version of the same report. Content is not edited in place after generation; new source state produces a new version.

### Provenance and isolation
Each source-manifest item must contain the same:
- organization;
- workspace;
- product;

as the report version. Cross-tenant, cross-workspace and cross-product source references are rejected. Checksums are mandatory.

### SIMPA adapter
Initial report type:
- `monitoring_summary` from a real `simpa_analytics_runs` snapshot.

The report may include real computed/reviewed indicator results. A SIMPA AI synthesis is included only when both the synthesis and underlying AI job have explicit accepted human review. Evidence-quality metrics must never be relabeled as social-risk scores, municipality scores or eligibility decisions.

### ORDO adapter
Initial report types:
- `destination_snapshot` from a real `ordo_analytics_runs` snapshot;
- `scenario_review` from a real `ordo_scenario_assessments` record.

ORDO scenario reporting preserves the hard invariant `forecast_performed=false`. It must not invent forecast impact, visitor growth, employment effects, sustainability improvements or other predicted outcomes. Reviewed AI content is included only after explicit accepted human review and is rejected if it claims a forecast.

### API
Adds `/api/v1/reporting/*` for:
- source discovery;
- report registry/list/detail;
- first version generation;
- new version generation;
- submit for review;
- approve/reject review;
- publish;
- export artefact generation;
- scoped export download.

Authorization reuses already-existing platform permissions in this phase:
- `report.read` for viewing/download;
- `analysis.run` for report/version generation and submission;
- `organization.manage` for report review and publication.

Dedicated granular reporting permissions can be introduced in ISI-13 administration without weakening this task's server-side product/tenant checks.

### Export artefacts
Initial deterministic export formats:
- JSON;
- Markdown;
- HTML.

Each export is an immutable database-backed artefact with filename, MIME type and SHA-256. ISI-12 intentionally does not pretend to have a production PDF renderer. PDF/print hardening can be added after an explicit renderer/dependency decision and dedicated visual verification.

### Streamlit
The existing `Izveštaji` shell navigation becomes a real shared reporting workspace. It supports:
- product-aware source selection;
- report creation;
- version history;
- provenance display;
- review trail;
- explicit publication;
- export/download.

The active shell product determines which domain adapter is available. SIMPA never sees ORDO report sources and ORDO never sees SIMPA report sources.

## Safety invariants
- No report without provenance.
- No cross-product source manifest.
- No cross-tenant/workspace source manifest.
- No publication before review approval.
- No mutable overwrite of a published version.
- No unreviewed AI content in report content.
- No ORDO forecast claim in scenario reporting.
- No SIMPA social-risk/eligibility inference from evidence-quality metrics.
- No fake statistics, indicator values, report claims or publication state.

## Non-goals
- No PDF renderer in this task.
- No public unauthenticated publication portal.
- No email distribution.
- No scheduled recurring reports.
- No new AI generation inside the reporting engine.
- No administration redesign (ISI-13).
- No security hardening/cutover work (ISI-14+).
- No automatic Git commit or push.

## Acceptance
The main runner must pass:
- exact baseline gate;
- static reporting audit;
- offline migration render;
- native PostgreSQL migration to `20260828_0011`;
- focused ISI-12 contracts;
- native PostgreSQL acceptance;
- full regression suite;
- Docker Compose config;
- `git diff --check`.

Then local QA must prove real SIMPA and ORDO report lifecycles and browser behavior before the visual QA evidence is recorded.

## Next
`ISI-13-ADMINISTRATION`
