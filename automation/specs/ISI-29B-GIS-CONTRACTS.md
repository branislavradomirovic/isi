# ISI-29B — Governed GIS geometry contracts

Status: IMPLEMENTED local candidate subject to final exact gates/review; owner approved local 29A–29F implementation. Baseline main/origin/main cad6892fd2d710b8263b936c06bb3d8137cdeddc, clean index/worktree, one worktree, empty stash. 29A approved exact fingerprint f220dd3dce9b172c05dc6982167f73b2cd848924b0060d48b1da4143970e492a committed/pushed. Latest accepted CI remains #96 on 374dda3; no CI inherited by cad6892, no dispatch/server authority.

## Bootstrap / DONE / PARTIAL / MISSING / DRIFT
MasterPlan complete read and AGENTS/ledger/ADR-0025/24A/24B/29 plan/workstation/ops boundaries reconstructed. DONE: 29A local charts/gates/review and owner main checkpoint. PARTIAL: ORDO identity GIS and SIMPA geography labels. MISSING: geometry storage/topology/lifecycle/scoped retrieval. DRIFT: mutable 29A candidate wording after approved commit: REMOVE_BEFORE_NEXT_SLICE, synchronize this candidate. Immutable legacy checkpoint/CI narratives LEGITIMATE_HISTORY; ORDO identity-only v1 REQUIRED_COMPATIBILITY; ORDO overview permission correction REMOVE_IN_NAMED_PHASE(ISI-29C). No duplicate geometry implementation or external geocoder found; one main worktree, no stash/branches used, no unclassified incompatible legacy.

## Locked contract
Generic spatial transport/storage and version metadata belong to shared infrastructure. Domain adapters retain SIMPA local-system/actor and ORDO spatial-unit/asset identity semantics. No indicator formulas, joins, numerical results, AI, workers, frontend maps or provider topology change. Geometry versions immutable; lifecycle revision and human review audited. Preserve v1 identity rows. New core_spatial_geometry_versions table via additive Alembic0035; upgrade/downgrade/native PG required.

Input one GeoJSON geometry (Point/Polygon/MultiPolygon), explicit WGS84 longitude/latitude axis order; CRS84 or EPSG:4326 only, exact identity transform recorded. Reject unknown/projected CRS rather than guessing; reprojection deferred until explicit transform contract. Require source URI/version, declared original source SHA256, licence and validity. Source metadata is declared until reviewer attests, not independently fetched/licensed. No approved institutional boundary dataset exists locally: synthetic self-authored geometry validates software only; no real boundary set auto-imported.

Bound payload 200000 bytes, 10000 coordinates, nesting8; finite 2D lon[-180,180]/lat[-90,90], polygon rings closed and >=4, no edges crossing antimeridian without explicit source splitting. Shapely2.1.2 GEOS validates topology; no make_valid, simplification, snapped coordinates, guessed CRS, distance/area/causal calculation. Point requires domain facility/asset identity; SIMPA local-system and ORDO spatial-unit require polygon. No citizen locations. Domain identity and validity rechecked on validation/retrieval; provenance snapshot must match.

API organization/product/workspace selection and permissions precede any lookup/storage access. Register=data.upload; propose=data.governance.manage; validate=data.validate with explicit source/licence/location attestation; retire=data.governance.manage; read=data.read. Actor must be current active scoped membership. DRAFT->PROPOSED->VALIDATED->RETIRED (DRAFT/PROPOSED may RETIRE); no resurrection/edit-in-place/delete. Only validated geometry and overlapping requested date exposed for use; metadata contains no storage key. Fingerprint binds scope, provenance, immutable domain binding, hashes and validity; tampering fails closed. Existing content-addressed storage; storage/transaction failure may leave unreferenced private objects, never silent overwrite or broad cleanup.

## Dependency decision
Shapely==2.1.2 pinned runtime/dev locks, existing NumPy retained. BSD3 Shapely + bundled GEOS LGPL2.1 notices remain in supply-chain artefacts; no host GEOS/GDAL/PROJ installation. Official Python>=3.10 and macOS/Linux wheels incl musllinux x86_64 satisfy Python3.11 baseline; check actual local wheel/import and runtime-platform wheel before declaring compatibility. No pyproj/GeoPandas/PostGIS. Record workstation/MasterPlan before install. Sources: https://shapely.readthedocs.io/en/2.1.2/installation.html and https://pypi.org/project/shapely/2.1.2/ . Deployment image scan/release remains later29F/approved checkpoint.

## Canonical system inventory impact
INV-B29/C45/M22 become PARTIAL after local verified geometry/storage/API candidate. INV-A22 maps/SHAP/entity TARGET beyond accepted29A; no GIS UI now. Update MasterPlan+technical reference+ledger+guide. Source import Help ten-item checklist, matrix PARTIAL until review and hosted release evidence.

## Exact mutable surface
- `TECHNICAL_DOCUMENTATION.md`
- `automation/STATUS.md`
- `automation/tasks.json`
- `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
- `docs/roadmap/ISI-29-XAI-GIS-ENTITY-FINDINGS-PLAN.md`
- `docs/ops/ISI-DEVELOPMENT-WORKSTATION-REQUIREMENTS.md`
- `docs/help/ISI-SPATIAL-DATA-GUIDE.md`
- `docs/help/ISI-HELP-COVERAGE-MATRIX.md`
- `automation/specs/ISI-29B-GIS-CONTRACTS.md`
- `pyproject.toml`
- `requirements.lock`
- `requirements.runtime.lock`
- `src/platform/spatial/__init__.py`
- `src/platform/spatial/contracts.py`
- `src/platform/spatial/models.py`
- `src/platform/spatial/service.py`
- `src/domains/simpa/spatial_adapter.py`
- `src/domains/ordo/spatial_adapter.py`
- `src/platform/models.py`
- `src/api/app.py`
- `src/api/spatial_routes.py`
- `migrations/versions/20261007_0035_spatial_geometry_versions.py`
- `tests/test_isi_29b_geometry_contract.py`
- `tests/test_isi_29b_spatial_registry.py`
- `tests/test_isi_29b_spatial_api.py`
- `tests/test_isi_29b_native_postgres.py`
- `tools/qa/run_isi29b.py`
- `tools/qa/analyze_isi29b.py`

All other tracked paths frozen. Ignored sanitized evidence automation/evidence/ISI-29B. Runner/analyzer created before runtime editing. No staging/commit/push before exact candidate owner approval, no hosted CI/server action.

## Gates
Exact dirty allowlist/baseline/index/stash/worktree; ruff changed code, policy, mypy existing lane; focused geometry/service/API tests; native PG migration upgrade/downgrade and persistence constraints (zero skipped required); full regression; dependency check/audit and wheel-platform evidence; diffcheck; readonly analyzer exact hashes/log/XML; human review. No bypass/weakened predecessor tests; unsupported geometry/source states explicit. Full production or institutional methodology certification not claimed.


## Deferred server verification
DEFERRED_SERVER_VERIFICATION; 29F later release/approved deployment. No CI_VERIFIED/COMPLETE claim.

## Human review and owner gate
Verify exact final fingerprint/log/XML/dependency reports and review all touched surfaces. Explicit owner approval of29A does not approve29B staging/commit/push; retain29B unstaged until new exact approval. No hosted Actions unless separate checkpoint approval.


29B local verification closeout: IMPLEMENTED / REVIEW_VERIFIED unstaged candidate; 42 focused and 1 native PostgreSQL test passed in the pre-final-review cycle (full migration upgrade/downgrade/reupgrade, constraints and stale concurrent write rejection), 1246 regression passes / 43 existing native-lane skips, zero failures/errors. Independent analyzer repeat PASS; runtime dependency audit and fixed musllinux wheel/local import checks PASS. Exact final candidate identity is automation/evidence/ISI-29B/human-review.json, with complete repeated gates on this documentation-synchronized candidate required. This supersedes mutable 29B IN_PROGRESS/verification-pending notes above; previous candidate narratives are LEGITIMATE_HISTORY. No CI/server acceptance or staging/commit/push; institutional geometry dataset/licence and projected CRS remain explicit missing/unsupported states. 29C–F still not implemented.

Final bounded review correction: reject non-string geometry type as a controlled validation failure; require native fixture loopback host before any DB access. Full exact-candidate gates must pass again; final counts/identity in automation/evidence/ISI-29B/human-review.json supersede prior cycle counts. No test gate bypass.
