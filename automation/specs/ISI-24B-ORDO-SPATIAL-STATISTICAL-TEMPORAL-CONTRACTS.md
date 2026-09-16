# ISI-24B - ORDO Spatial Processing + Statistical/Time-Series Contracts

Task ID: **ISI-24B**

Status of this document: **OWNER-SCOPE-FROZEN IMPLEMENTATION CONTRACT**

This document is the complete implementation authority for this slice. Do not broaden it. Do not stage, commit, push, deploy, create branches/worktrees, use production secrets, or touch the server.

## 1. Immutable accepted baseline

- Repository: `branislavradomirovic/isi`
- Canonical local repository: `$HOME/Applications/Python/ISI`
- Branch: `main`
- Baseline commit: `04b0738933030f1d69de52f9260c7b2f11042d0e`
- Baseline tree: `6c688c698fb5bf9520e0a4437c5f372a9790df2c`
- Accepted exact-main workflow: `ISI required acceptance` run #85, run ID `35138374174`, completed/success
- Accepted Alembic sole head: `20260916_0030`
- ISI-24A is COMPLETE / CI_VERIFIED on this baseline.

## 2. Objective

Implement the next governed ORDO methodology slice:

**ISI-24B - Spatial Processing + Statistical/Time-Series Contracts**

This slice adds deterministic identity-based spatial aggregation, corrects the ORDO indicator-methodology lifecycle, and introduces versioned statistical-model and time-series specification contracts. It deliberately does not implement forecasting execution. ISI-24C owns forecast fitting/execution, rolling-origin execution, backtesting results, forecast intervals and runtime `NOT_ESTIMATED` completion.

## 3. Architecture invariants

Preserve all accepted architecture and governance. In particular:

- numerical authority remains deterministic and versioned;
- ORDO consumes governed reproducible analytical artifacts, never raw source bytes;
- organization/workspace/product isolation remains fail-closed;
- methodology/model/specification validation is a human action;
- `DRAFT -> PROPOSED -> VALIDATED -> RETIRED` is the canonical methodology lifecycle;
- scenario and forecast remain separate semantic objects;
- the accepted scenario DB boundary `forecast_performed = false` remains intact;
- a map or spatial association is evidence presentation, not causal proof;
- no formula, weight, threshold, impact coefficient or policy conclusion may be invented;
- no new external dependency is permitted in this slice.

## 4. Exact mutable surface - FROZEN 20

The implementation may modify/create exactly these paths and no others:

1. `automation/STATUS.md`
2. `automation/tasks.json`
3. `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
4. `src/api/ordo_analytics_routes.py`
5. `src/domains/ordo/analytics_models.py`
6. `src/domains/ordo/analytics_schemas.py`
7. `src/domains/ordo/analytics_service.py`
8. `tests/test_isi_17_harness_contract.py`
9. `automation/specs/ISI-24B-ORDO-SPATIAL-STATISTICAL-TEMPORAL-CONTRACTS.md`
10. `migrations/versions/20260916_0031_ordo_spatial_statistical_temporal_contracts.py`
11. `src/domains/ordo/spatial_processing.py`
12. `src/domains/ordo/statistical_contracts.py`
13. `src/domains/ordo/time_series_contracts.py`
14. `tests/test_isi_24b_methodology_lifecycle.py`
15. `tests/test_isi_24b_spatial_processing_contract.py`
16. `tests/test_isi_24b_statistical_contract.py`
17. `tests/test_isi_24b_time_series_contract.py`
18. `tests/test_isi_24b_governance_contract.py`
19. `tests/test_isi_24b_reference_calculations.py`
20. `tests/test_isi_24a_governance_contract.py`

Owner-approved R2 governance extension: path 20 is historical-test maintenance only. It must migrate the 24A governance test from a stale live-current-slice assertion to the accepted 24A checkpoint without weakening 24A non-goals, migration truth, or inventory coverage. No production-code scope is added.

Everything outside these 20 paths is immutable for this task.

Explicitly do not modify:

- `src/domains/ordo/models.py`
- `src/domains/ordo/schemas.py`
- `src/domains/ordo/service.py`
- any Streamlit file
- ORDO reporting adapter
- shared data-platform code
- CI workflow
- dependency files
- server/deployment files

If a genuine blocker proves that another path is required, stop and report the blocker. Do not silently expand scope.

## 5. ORDO indicator methodology lifecycle correction

### 5.1 Persistence

Change `OrdoIndicatorMethodology` from the current three-state lifecycle to exactly:

`draft -> proposed -> validated -> retired`

Add nullable trace fields:

- `proposed_by_membership_id`
- `proposed_at`
- `retired_by_membership_id`
- `retired_at`
- `retirement_note`

Keep the existing validation trace fields:

- `validation_note`
- `approved_by_membership_id`
- `approved_at`

Historical rows must remain truthful. Existing historical `validated` rows MUST NOT receive fabricated proposal timestamps/actors. They remain readable and valid compatibility evidence.

### 5.2 Service transitions

Implement exact transition behavior:

- create methodology -> `draft`
- `propose_methodology(...)`: only `draft -> proposed`; actor is required
- `validate_methodology(...)`: only `proposed -> validated`; actor is required; validation note remains required
- when a new methodology is human-validated, any prior validated methodology for the same indicator may be retired as part of that same explicit human validation transaction, with real actor/time and a truthful supersession retirement note
- `retire_methodology(...)`: only `validated -> retired`; actor and nonblank retirement note are required
- no lifecycle reversal
- no skipped `draft -> validated`
- no automatic promotion to proposed/validated

Use stable failure identifiers so tests can assert fail-closed behavior, including:

- `methodology_not_draft`
- `methodology_not_proposed`
- `methodology_not_validated`
- `methodology_actor_required`
- `retirement_note_required`

When the active validated methodology is explicitly retired without a replacement, synchronize the indicator summary truthfully rather than leaving it falsely validated.

### 5.3 API

Keep the existing validate endpoint but make it respect the new lifecycle.

Add:

- `POST /api/v1/ordo/analytics/methodologies/{methodology_id}/propose`
- `POST /api/v1/ordo/analytics/methodologies/{methodology_id}/retire`

Add Pydantic request types:

- `MethodologyProposeRequest`
- `MethodologyRetireRequest`

These routes use the existing ORDO scope/permission model and `indicator.manage` permission. Do not add Streamlit controls in 24B; ORDO Help/UI completion is owned by 24D.

## 6. Spatial processing contract

### 6.1 Boundary

24A already created `OrdoSpatialUnit` identity/provenance. Do not alter that entity.

24B spatial processing is deliberately **identity-based descriptive aggregation of records already attributed to a governed spatial unit**. It is not a geometry engine.

Create a strict Pydantic contract in `src/domains/ordo/spatial_processing.py`:

- class: `OrdoSpatialAggregationContractV1`
- schema version: `ORDO-SPATIAL-AGGREGATION-v1`

Required semantic fields must cover at least:

- `aggregation_rule`
- required spatial source fields
- validated-quality requirement
- explicit missing-numeric rule
- `weighted = false`
- `spatial_join_performed = false`
- `non_causal = true`
- `automatic_policy_recommendation = false`

Allowed generic aggregation rules are exactly:

- `count`
- `sum`
- `mean`
- `min`
- `max`

No weights, ranks, scores, thresholds, interpolation, imputation, geometry inference, distance, service areas or clustering.

Provide a deterministic pure helper, named `aggregate_numeric_values` or an equivalently explicit task-local name, that is used by production spatial aggregation and reference-calculation tests. The helper may only implement the five generic arithmetic rules above. Reject non-finite numeric evidence. Missing numeric evidence for non-count rules is excluded and counted explicitly; it is never silently replaced with zero.

### 6.2 Methodology authorization

Spatial aggregation is permitted only when the currently validated indicator methodology explicitly owns a strict block under its existing methodology metadata, for example `source_requirements["spatial_aggregation"]`, and that block validates as `ORDO-SPATIAL-AGGREGATION-v1`.

The processing service must not infer `sum`, `mean` or any other aggregation from an indicator name, unit or LLM output.

### 6.3 Governed inputs and exact spatial identity

Implement deterministic processing against a revalidated governed `OrdoAnalyticsRun` only.

Spatial source records must carry explicit identity fields sufficient to prove the target spatial unit, including:

- `indicator_code`
- `quality_status`
- `spatial_unit_key`
- `spatial_unit_type`
- `boundary_version`
- `crs`
- `value_numeric` where the chosen rule needs numeric values

The target `OrdoSpatialUnit` must:

- belong to the exact organization/workspace
- be `validated`
- have exact matching `spatial_unit_key`
- have exact matching `spatial_unit_type`
- have exact matching `boundary_version`
- have exact matching `crs`

Fail closed on cross-boundary-version, cross-CRS or cross-granularity evidence. Do not silently aggregate across incompatible spatial identities.

### 6.4 Persisted spatial run

Add `OrdoSpatialAggregationRun` to `analytics_models.py` and a matching table in migration 0031.

Persist at minimum:

- organization/workspace
- analytics run
- indicator and exact methodology identity
- methodology fingerprint or equivalent canonical immutable content fingerprint
- target spatial unit
- schema version
- aggregation rule
- exact boundary version / CRS / spatial-unit type
- canonical input snapshot SHA-256
- input record count
- matched record count
- dropped/missing numeric count
- aggregate numeric value
- unit
- deterministic computation trace
- deterministic run fingerprint
- creator and timestamp
- explicit false semantics for spatial join, forecast, causal claim and automatic policy recommendation

A successful spatial run is descriptive evidence only.

## 7. ORDO statistical-model contract - specification only

Create `src/domains/ordo/statistical_contracts.py` with a strict frozen Pydantic contract:

- class `OrdoStatisticalModelContractV1`
- schema version `ORDO-STATISTICAL-MODEL-CONTRACT-v1`
- canonical JSON serialization
- deterministic SHA-256 contract fingerprint

Add persisted entity `OrdoStatisticalModelContract` in `analytics_models.py` and migration 0031.

Each persisted contract is scoped to organization/workspace and bound to:

- exact target indicator
- exact currently validated indicator methodology ID/version
- deterministic fingerprint of the methodology content relevant to computation
- one governed/revalidated ORDO analytics run
- canonical input snapshot SHA-256
- stable `analysis_key`
- version number
- contract JSON/fingerprint
- lifecycle state `draft/proposed/validated/retired`
- proposal/approval/retirement human trace
- validation note
- validation evidence reference

A changed methodology or changed statistical specification requires a new contract version. Do not mutate a proposed/validated/retired contract in place.

### 7.1 Target semantics and family allowlist

Target semantics allowed in 24B:

- `continuous`
- `count`
- `proportion_rate`

Analysis structures:

- `cross_sectional`
- `panel`

Cross-sectional family allowlist by target semantics:

- continuous -> `linear_regression` or `robust_regression`
- count -> `poisson_glm` or `negative_binomial_glm`
- proportion_rate -> `fractional_logit` or `beta_regression`

Panel family allowlist:

- `fixed_effects`
- `mixed_effects`
- `hierarchical`

The contract must still preserve target semantic/response-family compatibility for panel analyses. Do not imply that any family is validated merely because it is allowed by the schema.

### 7.2 Statistical specification contents

The strict contract must include at least:

- analysis key/purpose
- target semantic
- analysis structure
- model family and response-family semantics
- feature specifications with stable feature key, role, source field, version identity, transformation and missing rule
- analysis window start/end/as-of
- assumptions
- required diagnostics
- limitations
- `non_causal = true`
- `automatic_policy_recommendation = false`

24B adds **no statistical fit/execution result table** and performs no model fitting. Do not import/use `statsmodels`, `sklearn`, `scipy`, Prophet, pmdarima or equivalent fitting libraries in the 24B code.

## 8. ORDO time-series specification/readiness contract - no forecast execution

Create `src/domains/ordo/time_series_contracts.py` with a strict frozen Pydantic contract:

- class `OrdoTimeSeriesSpecV1`
- schema version `ORDO-TIME-SERIES-SPEC-v1`
- canonical JSON serialization
- deterministic SHA-256 contract fingerprint

Add persisted entity `OrdoTimeSeriesSpec` in `analytics_models.py` and migration 0031.

Each spec is scoped to organization/workspace and bound to:

- exact indicator
- exact currently validated indicator methodology ID/version/fingerprint
- one governed/revalidated analytics run
- canonical input snapshot SHA-256
- stable series key
- version number
- contract JSON/fingerprint
- lifecycle `draft/proposed/validated/retired`
- human proposal/approval/retirement trace
- validation note/evidence reference

The strict spec must include at least:

- time index field
- frequency: `daily`, `weekly`, `monthly`, `quarterly`, or `annual`
- series key fields
- observation window start/end/as-of
- minimum history periods
- maximum missing ratio
- missing-data rule
- outlier policy
- revision policy
- comparability policy
- transformation: `none`, `log1p`, `difference`, or `seasonal_difference`
- trend requirement
- optional seasonality period
- candidate-family metadata only
- horizon/unit
- uncertainty-output requirement
- diagnostic requirements
- limitations

Candidate-family metadata allowlist:

- `naive`
- `seasonal_naive`
- `ets`
- `sarima`
- `sarimax`
- `count_time_series`

Temporal-validation planning must be represented as metadata only:

- `backtest_strategy = "rolling_origin_plan_only"`
- initial train periods
- step size
- horizon
- minimum origins
- required metrics selected only from target-appropriate canonical metrics such as MAE, RMSE, sMAPE, MASE, bias, interval coverage, interval width/sharpness and seasonal-baseline comparison

Mandatory locked booleans:

- `forecast_execution = false`
- `automatic_model_selection = false`
- `non_causal = true`

A validated 24B time-series spec means only that the human-approved **specification/readiness contract** is validated. It does not mean a forecast model was fit, backtested or promoted. 24C owns those runtime claims.

## 9. Migration 0031

Create:

`migrations/versions/20260916_0031_ordo_spatial_statistical_temporal_contracts.py`

Required header:

- revision: `20260916_0031`
- down_revision: `20260916_0030`

Upgrade must:

1. alter the ORDO indicator methodology status check to include `proposed`;
2. add proposal/retirement trace columns without fabricating historical proposal evidence;
3. create `ordo_spatial_aggregation_runs`;
4. create `ordo_statistical_model_contracts`;
5. create `ordo_time_series_specs`;
6. add appropriate FKs, checks and indexes;
7. preserve accepted 24A tables and scenario constraints.

Downgrade must be safe and explicit. Before restoring the historical three-state methodology constraint, any 24B `proposed` row must be mapped back to `draft`; then remove 24B-only trace columns/tables. Do not fabricate or mutate unrelated history.

## 10. Governance and Canonical System Inventory synchronization

Update governance in the same candidate.

### STATUS

Record:

- ISI-24A COMPLETE / CI_VERIFIED
- accepted SHA `04b0738933030f1d69de52f9260c7b2f11042d0e`
- accepted tree `6c688c698fb5bf9520e0a4437c5f372a9790df2c`
- exact-main run #85 / `35138374174` success
- current slice `ISI-24B - Spatial Processing + Statistical/Time-Series Contracts`
- overall ISI-24 remains IN PROGRESS
- server remains deferred/frozen

### tasks.json

Keep overall `ISI-24-ORDO-PRODUCTION-METHODOLOGY` as `in_progress`.

Record accepted 24A checkpoint, set 24B as current, and set the active spec to:

`automation/specs/ISI-24B-ORDO-SPATIAL-STATISTICAL-TEMPORAL-CONTRACTS.md`

### MasterPlan

Replace the stale wording `ISI-24A current governed slice` with an accepted 24A checkpoint and a new `ISI-24B current governed slice` section.

Add/update canonical system inventory so independently governed new components are represented. Use the next canonical IDs:

- `INV-C35` - ORDO spatial aggregation processing/run
- `INV-C36` - ORDO statistical model contract
- `INV-C37` - ORDO time-series specification

Update `INV-C28` to reference the new analytics contract modules/migration/test authority and the new 24B responsibility, while preserving 24A compatibility semantics.

Record the 2026-09-16 owner transition from accepted/CI-verified 24A to 24B. Do not mark the whole ISI-24 phase complete.

### Harness

Update `tests/test_isi_17_harness_contract.py` only as necessary to keep the canonical status/task/spec/harness contract synchronized. Do not weaken historical acceptance.

## 11. Required 24B tests

Create exactly these six new test authorities:

- `tests/test_isi_24b_methodology_lifecycle.py`
- `tests/test_isi_24b_spatial_processing_contract.py`
- `tests/test_isi_24b_statistical_contract.py`
- `tests/test_isi_24b_time_series_contract.py`
- `tests/test_isi_24b_governance_contract.py`
- `tests/test_isi_24b_reference_calculations.py`

Tests must cover at least:

- no draft -> validated skip;
- propose/validate/retire actor/trace behavior;
- truthful historical validated compatibility;
- exact spatial scope/lifecycle/boundary-version/CRS/granularity matching;
- no spatial join, weighting, hidden zero fill, causal or automatic recommendation semantics;
- deterministic arithmetic reference calculations for count/sum/mean/min/max;
- strict statistical family/target compatibility and fingerprints;
- statistical contracts bind exact validated methodology + governed analytics run;
- no statistical execution/result entity;
- strict time-series frequency/transformation/family/backtest-plan validation;
- `rolling_origin_plan_only` and mandatory `forecast_execution=false`;
- no automatic model selection;
- migration upgrade/downgrade contract;
- inventory/status/task/spec synchronization;
- accepted 24A scenario no-forecast boundary remains intact.

These reference calculations validate the generic deterministic processor only. They do **not** validate an ORDO indicator formula, destination score, ranking, threshold, forecast or policy conclusion.

## 12. Strict non-goals / forbidden implementation

The following are locked out of 24B:

- NO forecast execution
- NO ETS/SARIMA/SARIMAX fitting or prediction
- NO automatic model selection
- NO rolling-origin execution
- NO forecast backtest result execution
- NO forecast interval/result generation
- NO 24C runtime `NOT_ESTIMATED` completion
- NO causal impact estimator
- NO policy-effect estimator
- NO automatic policy recommendation
- NO citizen scoring
- NO eligibility logic
- NO arbitrary indicator formulas, weights, thresholds or rankings
- NO full GIS geometry engine
- NO PostGIS/GeoAlchemy/Shapely/GeoPandas dependency
- NO spatial joins
- NO distance/travel-time/service-area computation
- NO spatial clustering
- NO ORDO Help/User Guide completion
- NO ORDO XAI completion
- NO shared ISI-25 AI/MLOps promotion/champion logic
- NO new dependencies
- NO Streamlit/UI expansion
- NO server/DNS/ingress/SMTP/secrets/production-data mutation
- NO stage/commit/push

## 13. Acceptance gates

The candidate must satisfy all of the following without weakening existing tests:

```text
BASELINE_HEAD=PASS
ORIGIN_MAIN_BASELINE=PASS
BASELINE_TREE=PASS
LOCAL_BRANCH_MAIN=PASS
ONE_WORKTREE=PASS
CLEAN_PREIMAGE_WORKTREE=PASS
NO_STAGED_PREIMPLEMENTATION=PASS
EXACT_EXISTING_PREIMAGES_8=PASS
EXACT_NEW_PATHS_ABSENT_11=PASS
SOLE_MIGRATION_HEAD_20260916_0030=PASS

EXACT_ISI24B_DIRTY_SURFACE_20=PASS
NO_STAGED_POSTIMPLEMENTATION=PASS

METHODOLOGY_LIFECYCLE_CONTRACT=PASS
METHODOLOGY_PROPOSE_VALIDATE_RETIRE_API=PASS
HISTORICAL_METHOD_TRUTH=PASS
SPATIAL_AGGREGATION_CONTRACT=PASS
SPATIAL_IDENTITY_COMPATIBILITY=PASS
SPATIAL_REFERENCE_CALCULATIONS=PASS
NO_SPATIAL_JOIN_OR_WEIGHTING=PASS
STATISTICAL_MODEL_CONTRACT=PASS
STATISTICAL_FAMILY_TARGET_COMPATIBILITY=PASS
NO_STATISTICAL_EXECUTION=PASS
TIME_SERIES_SPEC_CONTRACT=PASS
ROLLING_ORIGIN_PLAN_ONLY=PASS
NO_FORECAST_EXECUTION=PASS
NO_AUTOMATIC_MODEL_SELECTION=PASS
SCENARIO_NO_FORECAST_BOUNDARY=PASS
TENANT_SCOPE_CONTRACT=PASS
CANONICAL_INVENTORY_SYNCHRONIZED=PASS
GOVERNANCE_24A_TO_24B_SYNCHRONIZED=PASS
HISTORICAL_24A_GOVERNANCE_TEST_MIGRATED=PASS

FOCUSED_ORDO_BACKWARD_COMPAT_AND_24B=PASS
POLICY=PASS
MIGRATION_OFFLINE=PASS
MIGRATION_LIVE=PASS
NATIVE_POSTGRES=PASS
PYTHON_COMPILE=PASS
RUFF_E9=PASS
MYPY=PASS
DIFF_CHECK=PASS
FULL_PYTHON_REGRESSION=PASS
CANDIDATE_MANIFEST_STABLE=PASS

CODEX_STAGE_COMMIT_PUSH=NO
SERVER_MUTATION=NO
READY_FOR_ISI24B_FINAL_REVIEW=PASS
```

## 14. Implementation-agent rules

- Read the complete repository MasterPlan and `AGENTS.md` before editing.
- Read this complete contract before editing.
- Inspect the accepted 24A implementation and existing SIMPA lifecycle/statistical contract patterns for architecture precedent, but do not copy SIMPA domain semantics into ORDO.
- Work only on canonical local `main`, exactly one worktree.
- Modify only the frozen 20 paths.
- Do not stage, commit or push.
- Do not run server/deployment operations.
- Do not change dependencies.
- Do not weaken tests or governance.
- If a contract requirement cannot be implemented inside the frozen surface, stop and explain the blocker instead of broadening scope.

## 15. Completion definition

The implementation agent is done only when an unstaged/uncommitted 20-path candidate exists and its own focused checks pass. The outer runner, independent analyzer, full regression, native PostgreSQL gate and assistant human review remain authoritative.

No commit/push is authorized by this contract.
