# ISI-29C — GIS user workflows

## Authority and bootstrap
Owner approved sequential29A-F implementation and all planned verified commits/pushes on2026-10-07. This supersedes per-candidate staging approval; verification/review remain mandatory.29F acceptance/deployment approved in principle, exact release/usage/signed-bundle and server contracts remain mandatory. No server/CI action in29C. Baseline0d59f40aa03ab7115041f1c58052d4610aac3a54 main/origin/direct remote, clean index/tree, one worktree, empty stash. Latest hosted acceptance#96 completed/success on predecessor374dda3 only. Complete MasterPlan previously read; current plan/AGENTS/ledgers/ADR0025,29B specification, spatial/domain/UI/source services and tests reconciled.

DONE:29A/B accepted main, exact-file hashes match approved reports,29B43 focused/native1/regression1247 pass. PARTIAL: institutional GIS source and ORDO identity-only aggregation; no actual boundary dataset/licence. MISSING: map/review/linked read UI. DRIFT:29B approval-pending mutable status REMOVE_BEFORE_NEXT_SLICE; historic candidate/CI evidence LEGITIMATE_HISTORY. ORDO shell.permissions bug REMOVE_BEFORE_NEXT_SLICE in this allowlist. ORDO identity-only history REQUIRED_COMPATIBILITY. Old inventory future-phase notes REMOVE_IN_NAMED_PHASE(ISI-29F). No duplicate geometry map or unclassified incompatible legacy found.

## Locked behavior
Reuse existing Data navigation in authenticated Streamlit; shared safe transport/rendering and separate domain identity selectors. Existing ingestion/governance remains available independently. Scoped geometry catalogue, local single-geometry upload with all29B provenance, DRAFT/PROPOSED/VALIDATED/RETIRED controls, explicit source/licence/location attestation and revision conflicts. SIMPA profile/active institutional actors and ORDO validated units/assets only; no citizens, guessed coordinates or geocoder. Existing ORDO spatial-unit authoring/lifecycle service exposed with bounded request and separate governance/validation permissions; source licence/location still reviewed separately through29B. ORDO and SIMPA overview institutional object forms accept stable external_code; fix actual ORDO permission source.

Map and table use the identical selected geometry IDs; layer/type, exact version, inclusive geometry-date validity and keyboard selection. Map click selects corresponding table/provenance/result; accessible table/dropdown works without WebGL. Catalogue bounded100 with explicit truncation notice, map subset25 /50000 coordinates /1MB geometry; no automatic simplification or arbitrary properties. Multiple overlapping boundary versions are explicit alternatives, not silently merged. Errors/missing/retired/integrity-invalid geometry never plot fake data. Counts describe geometry records only, not indicator values.

Renderer decision updated before replacement: actual IAB browser has WebGL disabled; Pydeck would leave a blank canvas, so rejected candidate is REMOVE_BEFORE_NEXT_SLICE (not shipped). Use installed Streamlit1.63 components.v2 with fixed trusted HTML/CSS/JS and bounded data-only SVG vectors, no new dependency/version/lock change. Python projects WGS84 to Mercator only for rendering (no storage transform); exact geometry/provenance retained. Poles at±90 use table fallback. Polygon holes use evenodd; selection via click/Enter/Space, zoom/pan/reset controls and drag background. JavaScript constructs only fixed DOM tags/attributes, textContent labels, no innerHTML/script/URL from data, no fetch/provider/tile/geocoder. UI selection ID is revalidated against current authorized detail IDs; changing scope/date/revision invalidates widget identity. Geometry colors encode boundary/facility/selection, not risk/value bands. Accessible table/dropdown always available. Official component docs https://docs.streamlit.io/develop/concepts/custom-components/components-v2/register and /communicate; local installed API checked.

ORDO stored spatial aggregation is linked only by exact scoped spatial-unit UUID plus boundary version/CRS and revalidated governed input/methodology/trace/numeric parity. Read-only no fitting/recompute persistence/new model. Unavailable/ineligible results explicitly reported, no raw source records returned. Separate analysis.read authorization before any result query. Stored aggregation has no observation period contract; requested map date controls geometry only, never assigns an analytical period. Single selected result numeric chart with unit/rule/missing/unmatched counts, no comparisons of incompatible units/methodologies. SIMPA no approved result-to-geography binding: geometry only and truthful unavailable analytical overlay. Domain linkage remains domain-owned.

Export: dedicated data.export + data.read backend recheck, date/state/domain/storage integrity, feature collection only one selected exact version plus minimal provenance. No results export or public sharing. Request generated at click then explicit download; recheck scope/revision on each rerun, no cache/global state. No new storage/schema/worker/model/security boundary.

## Inventory impact
INV-A22/B29/M22: GIS user surface/transport/map read authority becomes PARTIAL as built; INV-C45 unchanged persistence (existing0035). Technical reference/Help ten items/matrix and task status synchronized. No institutional source or methodological quality certification.

## Exact mutable surface
- `TECHNICAL_DOCUMENTATION.md`
- `automation/STATUS.md`
- `automation/tasks.json`
- `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
- `docs/roadmap/ISI-29-XAI-GIS-ENTITY-FINDINGS-PLAN.md`
- `docs/ops/ISI-DEVELOPMENT-WORKSTATION-REQUIREMENTS.md`
- `docs/help/ISI-SPATIAL-DATA-GUIDE.md`
- `docs/help/ISI-HELP-COVERAGE-MATRIX.md`
- `automation/specs/ISI-29C-GIS-WORKFLOWS.md`
- `pyproject.toml`
- `src/platform/spatial/service.py`
- `src/api/spatial_routes.py`
- `src/domains/simpa/spatial_adapter.py`
- `src/domains/ordo/spatial_adapter.py`
- `src/streamlit_app/spatial_api.py`
- `src/streamlit_app/spatial_view.py`
- `src/streamlit_app/spatial_workspace.py`
- `src/streamlit_app/data_workspace.py`
- `src/streamlit_app/ordo_workspace.py`
- `src/streamlit_app/simpa_workspace.py`
- `tests/test_isi_29c_spatial_api.py`
- `tests/test_isi_29c_spatial_view.py`
- `tests/test_isi_29c_spatial_ui.py`
- `tests/test_isi_29c_ordo_link.py`
- `tools/qa/run_isi29c.py`
- `tools/qa/analyze_isi29c.py`

All other tracked files frozen. Evidence automation/evidence/ISI-29C sanitized synthetic only. Contract and runner/analyzer created before runtime edits.

## Gates
Ruff changed Python; policy/mypy; focused API/unit/UI/linked-domain tests; full regression with existing native-only skips explicit (no DB change); pipcheck/diffcheck; browser desktop/mobile map/dropdown/table parity, selection, zero external tile/source traffic, safe tooltip and fallback. Independent readonly analyzer validates baseline/allowlist/fingerprint/log/XML/browser hashes twice; assistant review. Standing owner approval allows exact verified staging/commit/push after these gates. No CI_VERIFIED/SERVER_VERIFIED; DEFERRED_SERVER_VERIFICATION. 29D-F remain pending.

Sources: https://docs.streamlit.io/develop/api-reference/charts/st.pydeck_chart ; installed Pydeck/Streamlit source confirms explicit style needed, not a claim based on map_style=None documentation.

Legacy style note: existing SIMPA/ORDO foundation UI contains50 pre-existing E701/E702 compound statements, REQUIRED_COMPATIBILITY for bounded behavioral edits. As in29A, new/full modules receive strict Ruff; the two legacy foundation files retain their previous formatting, reviewed exact diff and regression/UI tests. No new compound statement introduced, no predecessor lint/test gate changed.

Final review bounds: ORDO linked read at most10 newest stored results to bound repeated source revalidation, with explicit truncation; unit identity catalogue100. Export audit records actor/fingerprint/state only, no coordinates. Existing unit lifecycle API locks exact scoped row FOR UPDATE before transition; no schema/migration or old-row backfill. Exact native release lane remains29F (29C local no-schema tests use existing-table fixtures). Browser proves click/Enter/Space selection, matching accessible selected table, zoom/reset, mobile390 with no page overflow and zero external assets; final evidence/fingerprint must bind repeated runner.

Final dependency metadata reconciliation (locked before metadata edit): declared Streamlit lower bound1.41 is incompatible with new components.v2 API, REMOVE_BEFORE_NEXT_SLICE. Narrow minimum to tested1.63, keeping existing dev/runtime Streamlit1.63.0 pins and every installed/locked package version unchanged. No install/upgrade or extra renderer dependency.
