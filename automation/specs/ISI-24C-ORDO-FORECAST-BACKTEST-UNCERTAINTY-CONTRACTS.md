# ISI-24C — ORDO Forecast Engine + Rolling-Origin Backtesting + Uncertainty/Diagnostics + NOT_ESTIMATED Runtime Semantics

Task ID: **ISI-24C**

Status of this document: **OWNER-SCOPE-FROZEN IMPLEMENTATION CONTRACT**

This document is the complete implementation authority for this slice. Do not broaden it. Do not stage, commit, push, deploy, create branches/worktrees, use production secrets, or touch the server.

## 1. Immutable accepted baseline

- Repository: `branislavradomirovic/isi`
- Canonical local repository: `$HOME/Applications/Python/ISI`
- Branch: `main`
- Baseline commit: `0ad913db23cea44033e8adf693eb179edfa8fb5d`
- Baseline tree: `1008022ebe4cf95b4d45a12ff746188e6c8efa11`
- Accepted exact-main workflow: `ISI required acceptance` run #86, run ID `35147730914`, completed/success
- Accepted Alembic sole head: `20260916_0031`
- ISI-24B is COMPLETE / CI_VERIFIED on this baseline.

## 2. Objective

Implement the first governed ORDO forecast execution slice:

**ISI-24C — Forecast Engine + Rolling-Origin Backtesting + Uncertainty/Diagnostics + NOT_ESTIMATED Runtime Semantics**

24C turns the accepted 24B time-series specification into a reproducible execution authority without inventing model parameters that 24B did not define.

24C MUST preserve:
- forecast != scenario;
- explicit human-approved time-series specification;
- exact governed analytical input;
- no automatic model selection;
- no random split;
- no future leakage;
- no fabricated intervals;
- no causal claim;
- no automatic policy recommendation;
- `NOT_ESTIMATED` instead of invented results.

## 3. Exact mutable surface — FROZEN 21

The implementation may modify/create exactly these paths and no others:

1. `automation/STATUS.md`
2. `automation/specs/ISI-24C-ORDO-FORECAST-BACKTEST-UNCERTAINTY-CONTRACTS.md`
3. `automation/tasks.json`
4. `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
5. `migrations/versions/20260916_0032_ordo_forecast_backtest_uncertainty.py`
6. `src/api/ordo_analytics_routes.py`
7. `src/domains/ordo/analytics_models.py`
8. `src/domains/ordo/analytics_schemas.py`
9. `src/domains/ordo/analytics_service.py`
10. `src/domains/ordo/forecast_metrics.py`
11. `src/domains/ordo/forecasting.py`
12. `tests/test_isi_17_harness_contract.py`
13. `tests/test_isi_24b_governance_contract.py`
14. `tests/test_isi_24c_api_contract.py`
15. `tests/test_isi_24c_forecast_engine.py`
16. `tests/test_isi_24c_governance_contract.py`
17. `tests/test_isi_24c_migration_contract.py`
18. `tests/test_isi_24c_not_estimated_semantics.py`
19. `tests/test_isi_24c_reference_forecasts.py`
20. `tests/test_isi_24c_rolling_origin.py`
21. `tests/test_isi_24c_uncertainty_diagnostics.py`

Everything outside these 21 paths is immutable for ISI-24C.

Explicitly DO NOT modify:
- `src/domains/ordo/time_series_contracts.py`
- `src/domains/ordo/statistical_contracts.py`
- `src/domains/ordo/spatial_processing.py`
- `src/domains/ordo/models.py`
- `src/domains/ordo/schemas.py`
- `src/domains/ordo/service.py`
- `pyproject.toml`
- `requirements.lock`
- any Streamlit/UI file
- any CI workflow
- server/deployment files.

`statsmodels` is already an accepted dependency. This slice must not change dependencies.

If another path is genuinely required, STOP and report the blocker. Do not silently expand scope.

## 4. 24B authority remains immutable

`OrdoTimeSeriesSpecV1` remains the human-approved specification authority.

Its accepted semantics remain:
- `backtest_strategy = "rolling_origin_plan_only"`
- `forecast_execution = false`
- `automatic_model_selection = false`
- `non_causal = true`

Those booleans describe the 24B specification object. Do NOT mutate the 24B spec to pretend execution occurred.

24C creates a separate runtime forecast entity. A validated time-series spec is necessary but not sufficient for an estimated forecast.

## 5. Executable family boundary

24B recognizes metadata families:

- `naive`
- `seasonal_naive`
- `ets`
- `sarima`
- `sarimax`
- `count_time_series`

24C executable families are **exactly**:

- `naive`
- `seasonal_naive`

This is deliberate.

24C MUST NOT invent:
- ETS trend/seasonal/damping configuration;
- SARIMA order or seasonal order;
- SARIMAX exogenous-variable identity, future values or provenance;
- a count-time-series parameterization.

If execution explicitly requests `ets`, `sarima`, `sarimax`, or `count_time_series`, and the requested family is allowed by the validated spec, persist a successful domain outcome:

- `result_status = "NOT_ESTIMATED"`
- `reason_code = "EXECUTABLE_FAMILY_NOT_DEFINED_24C"`

Do not treat that outcome as zero, forecast failure, or model selection.

If the requested family is not listed in the validated spec, reject the request fail-closed with stable error:
`forecast_family_not_in_validated_spec`.

There is NO automatic fallback from one requested family to another.

## 6. Forecast execution request

Add strict Pydantic request type `ForecastExecutionRequest`.

Minimum fields:

- `organization_id`
- `workspace_id`
- `time_series_spec_id`
- `requested_family`
- `series_identity`
- `interval_level`

`requested_family` uses the complete 24B family vocabulary, but only the two families above are executable in 24C.

`series_identity` is an explicit mapping whose keys must equal the validated spec's `series_key_fields` exactly. Values must be JSON scalar values. No hidden default, fuzzy matching, or inferred dimension is allowed.

`interval_level` is explicitly user/request supplied and must be exactly one of:
- `0.80`
- `0.90`
- `0.95`

Persist it exactly.

The request does not choose an analytics run. The validated `OrdoTimeSeriesSpec` already binds the exact governed analytics run and input snapshot.

## 7. Execution authority and revalidation

Execution requires ALL of:

1. exact organization/workspace scope;
2. existing `OrdoTimeSeriesSpec`;
3. spec status exactly `validated`;
4. exact validated spec fingerprint;
5. exact target methodology ID/version/fingerprint still valid;
6. exact bound governed analytics run still revalidates;
7. exact input snapshot SHA-256 still matches;
8. requested family is present in the validated spec;
9. exact series identity is supplied;
10. actor is traceable through existing authenticated `analysis.run` permission.

Do not execute a draft, proposed or retired spec.

Stable fail-closed errors should include:
- `time_series_spec_not_found`
- `time_series_spec_not_validated`
- `time_series_spec_binding_invalid`
- `forecast_family_not_in_validated_spec`
- `forecast_series_identity_invalid`

## 8. Governed series extraction

Use only the exact governed/revalidated analytical input bound to the spec.

The extracted records must match:
- the target indicator code;
- `quality_status == "validated"`;
- every explicit `series_identity` key/value;
- the spec observation window;
- the spec as-of boundary.

Required source evidence includes:
- target indicator identity;
- quality state;
- spec time-index field;
- every series-key field;
- `value_numeric`.

No text-to-number inference.

Time values must be deterministically parseable as ISO date/datetime values.

After filtering:
- sort strictly by time;
- duplicate time index => `NOT_ESTIMATED / DUPLICATE_TIME_INDEX`;
- invalid/non-finite value => `NOT_ESTIMATED / INVALID_SERIES_VALUE`;
- no evidence => `NOT_ESTIMATED / SERIES_EVIDENCE_NOT_FOUND`.

Target-value constraints:
- `continuous`: any finite numeric value;
- `count`: finite, non-negative, integer-valued numeric evidence;
- `proportion_rate`: finite value in `[0, 1]`.

24C supports execution only for `transformation = "none"`.
For `log1p`, `difference`, or `seasonal_difference`, return:
`NOT_ESTIMATED / TRANSFORMATION_EXECUTION_NOT_DEFINED_24C`.

Do not invent inverse-transform or bias-correction semantics.

## 9. Frequency and missing-period contract

24C baseline execution requires a regular complete calendar series.

Support the existing frequencies:
- daily
- weekly
- monthly
- quarterly
- annual

Determine expected successive periods deterministically.

If the observation window contains a missing expected period or an irregular step, return:

`NOT_ESTIMATED / IRREGULAR_OR_MISSING_PERIODS`

Do not silently compress time, interpolate, impute, forward-fill, backward-fill or convert missing periods to zero.

The existing 24B missing-data metadata remains preserved, but the 24C baseline engine is intentionally stricter for execution.

If observed history is below `minimum_history_periods`, return:
`NOT_ESTIMATED / INSUFFICIENT_HISTORY`.

## 10. Pure forecast engines

Create `src/domains/ordo/forecasting.py`.

Provide deterministic pure helpers for:

### 10.1 Naive

For horizon `h`, every future point equals the final training observation.

No parameter fitting.

### 10.2 Seasonal naive

Requires `seasonality_period`.

Forecasts repeat the most recent complete seasonal cycle recursively across the requested horizon.

If seasonality metadata is absent:
`NOT_ESTIMATED / SEASONAL_PERIOD_REQUIRED`.

If training history is insufficient for one complete seasonal cycle:
`NOT_ESTIMATED / SEASONAL_HISTORY_INSUFFICIENT`.

No hidden fallback to naive.

All forecast values must preserve target-domain constraints.

## 11. Rolling-origin execution

Create an explicit deterministic rolling-origin engine.

Given the validated plan:
- `initial_train_periods`
- `step_size`
- `horizon`
- `minimum_origins`

Construct origins only in chronological order:

`train[0:train_end] -> test[train_end:train_end+horizon]`

Start at `initial_train_periods`, advance by `step_size`, and include an origin only when the complete test horizon exists.

Never:
- randomize;
- shuffle;
- fit on a test value;
- use a future origin to fit an earlier origin;
- use the final future horizon in backtesting.

Require origin count >= validated `minimum_origins`.
Otherwise:
`NOT_ESTIMATED / INSUFFICIENT_ROLLING_ORIGINS`.

For uncertainty interval calibration, require at least **3 completed historical rolling-origin residuals per horizon step** for the final forecast interval.

If this cannot be satisfied:
`NOT_ESTIMATED / INSUFFICIENT_INTERVAL_CALIBRATION`.

## 12. Forecast metrics authority

Create `src/domains/ordo/forecast_metrics.py`.

Use these exact definitions.

Define point error:
`error = forecast - actual`.

### MAE
mean absolute error.

### RMSE
square root of mean squared error.

### bias
mean signed `forecast - actual`.

### sMAPE
`200 * abs(forecast - actual) / (abs(actual) + abs(forecast))`.

When actual and forecast are both zero, that point contributes `0`.

### MASE

For each rolling origin, calculate scaling denominator from that origin's TRAINING DATA ONLY.

Lag:
- `seasonality_period` when present;
- otherwise `1`.

Scale is mean absolute lagged difference.

A zero/non-finite scale makes MASE unavailable for that origin.
If MASE is required by the validated spec and cannot be produced for every scored origin, the run is:
`NOT_ESTIMATED / REQUIRED_BACKTEST_METRIC_UNAVAILABLE`.

### seasonal_baseline_comparison

Compare aggregate selected-family MAE to seasonal-naive MAE over the exact same eligible rolling origins.

Requires valid `seasonality_period` and sufficient training data at every scored origin.

Persist ratio:
`selected_mae / seasonal_naive_mae`.

Do not label it winner/loser and do not promote a model.

If baseline MAE is zero, the comparison is unavailable; if it is required, use:
`NOT_ESTIMATED / REQUIRED_BACKTEST_METRIC_UNAVAILABLE`.

## 13. Uncertainty intervals — empirical and leakage-safe

No arbitrary percentage band is allowed.

24C interval method is exactly:

`rolling_origin_empirical_residual_quantile_v1`

Residual for interval calibration:
`residual = actual - forecast`.

For a requested interval level `L`:
- `alpha = 1 - L`
- lower residual quantile = `alpha / 2`
- upper residual quantile = `1 - alpha / 2`

### Backtest interval diagnostics

For backtest coverage, each origin may use ONLY residuals from strictly EARLIER origins at the same horizon step.

Never use residuals from the origin being scored or any future origin.

Require at least 3 prior residuals at that horizon step before an interval is scored.

### Final future interval

For each horizon step, use all completed historical rolling-origin residuals for that horizon step.

Require at least 3 residuals.

Future interval:
- `lower = point_forecast + lower_residual_quantile`
- `upper = point_forecast + upper_residual_quantile`

Target-domain clipping:
- count: lower bound cannot be below `0`;
- proportion_rate: bounds clipped to `[0, 1]`;
- continuous: no clipping except finite-value validation.

Persist:
- interval method;
- requested interval level;
- calibration residual count by horizon;
- lower/upper value for every estimated point.

Do not call these intervals calibrated probabilities beyond the empirical method actually implemented.

## 14. Interval metrics

### interval_coverage

Compute only over backtest points for which leakage-safe prequential intervals were available.

`covered_count / eligible_interval_point_count`.

### interval_width_sharpness

Mean `upper - lower` over those same eligible points.

If either metric is required by the validated spec and there are no eligible interval-scored points:
`NOT_ESTIMATED / REQUIRED_BACKTEST_METRIC_UNAVAILABLE`.

Persist explicit metric availability and denominator counts.

## 15. Persisted forecast runtime entity

Add `OrdoForecastRun` in `analytics_models.py` and migration 0032.

One row represents one exact execution attempt/outcome.

Persist at minimum:

- organization/workspace;
- bound analytics run ID;
- time-series spec ID/version/fingerprint;
- target indicator ID;
- target methodology ID/version/fingerprint;
- input snapshot SHA-256;
- explicit `series_identity`;
- request fingerprint;
- requested family;
- executed family nullable;
- engine key/version;
- interval method/level;
- result status;
- stable reason code;
- observation/training window;
- horizon;
- rolling-origin plan;
- per-origin backtest records;
- aggregate backtest metrics;
- metric availability;
- diagnostics;
- warnings;
- forecast points;
- result fingerprint;
- `non_causal = true`;
- `automatic_model_selection = false`;
- `automatic_policy_recommendation = false`;
- creator/timestamp.

Schema version:
`ORDO-FORECAST-RUN-v1`.

Result status is exactly:
- `ESTIMATED`
- `NOT_ESTIMATED`

`NOT_ESTIMATED` rows must have no fabricated point/interval values.

`ESTIMATED` rows require:
- executed family;
- complete horizon forecast points;
- finite point estimates;
- finite lower/upper intervals;
- successful rolling-origin acceptance;
- all metrics required by the validated spec either present or explicitly valid under the contract.

Use deterministic canonical JSON + SHA-256 for request/result fingerprints.

Repeated identical requests may produce another audit row, but deterministic inputs must produce the same result fingerprint. Do not silently mutate an old run.

## 16. Stable NOT_ESTIMATED reason codes

Implement at least these exact codes:

- `EXECUTABLE_FAMILY_NOT_DEFINED_24C`
- `TRANSFORMATION_EXECUTION_NOT_DEFINED_24C`
- `SERIES_EVIDENCE_NOT_FOUND`
- `DUPLICATE_TIME_INDEX`
- `INVALID_SERIES_VALUE`
- `IRREGULAR_OR_MISSING_PERIODS`
- `INSUFFICIENT_HISTORY`
- `INSUFFICIENT_ROLLING_ORIGINS`
- `SEASONAL_PERIOD_REQUIRED`
- `SEASONAL_HISTORY_INSUFFICIENT`
- `INSUFFICIENT_INTERVAL_CALIBRATION`
- `REQUIRED_BACKTEST_METRIC_UNAVAILABLE`

These are domain outcomes. They are not zeros and must not be presented as forecasts.

Unexpected infrastructure/programming failures remain technical failures and must not be converted to `NOT_ESTIMATED`.

## 17. Scenario runtime NOT_ESTIMATED semantics

Preserve the scenario/forecast separation and DB constraint:
`forecast_performed = false`.

Add first-class scenario-impact persistence fields sufficient to represent:

- `impact_estimation_status`
- `impact_estimation_reason_code`
- `impact_estimate_numeric`
- `impact_estimate_unit`
- `impact_model_reference`

Allowed status:
- `LEGACY_NOT_EVALUATED`
- `NOT_ESTIMATED`
- `ESTIMATED`

Migration truth:
- existing 24A/24B rows become `LEGACY_NOT_EVALUATED`;
- do NOT fabricate historical `NOT_ESTIMATED` execution events.

New scenario assessments created in 24C MUST persist:

- `impact_estimation_status = "NOT_ESTIMATED"`
- `impact_estimation_reason_code = "NO_APPROVED_RESPONSE_MODEL"`
- `impact_estimate_numeric = NULL`
- empty/no impact model reference
- `forecast_performed = false`

The API/assessment payload must explicitly expose:

`impact = NOT_ESTIMATED`

with the stable reason code.

24C MUST NOT implement an `ESTIMATED` scenario-impact path. That remains unavailable until a separate evidence-backed response/impact methodology exists.

## 18. API

Add forecast routes under existing:

`/api/v1/ordo/analytics`

Minimum routes:

- `POST /forecasts`
- `GET /forecasts`
- `GET /forecasts/{forecast_run_id}`

Use existing scope/permission model:
- execute: `analysis.run`
- read: `analysis.read`

Responses must expose:
- result status;
- reason code;
- requested/executed family;
- exact spec/methodology/input identities;
- series identity;
- interval method/level;
- forecast points;
- aggregate metrics;
- metric availability;
- diagnostics/warnings;
- non-causal / no-auto-selection semantics;
- fingerprints.

Do not add Streamlit/UI in 24C. ORDO UI/Help/XAI remains 24D.

## 19. Migration 0032

Create:

`migrations/versions/20260916_0032_ordo_forecast_backtest_uncertainty.py`

Required:
- revision: `20260916_0032`
- down_revision: `20260916_0031`

Upgrade:
1. create `ordo_forecast_runs`;
2. add scenario impact-estimation fields;
3. backfill historical scenario rows to `LEGACY_NOT_EVALUATED`;
4. preserve `ck_ordo_scenario_assessment_no_forecast`;
5. add checks/indexes for forecast result state, fingerprints, booleans and scope.

Downgrade:
- remove forecast runtime table;
- remove 24C scenario-impact fields;
- do not mutate unrelated historical content.

## 20. Governance synchronization

### STATUS

Record:
- ISI-24B COMPLETE / CI_VERIFIED;
- SHA `0ad913db23cea44033e8adf693eb179edfa8fb5d`;
- tree `1008022ebe4cf95b4d45a12ff746188e6c8efa11`;
- run #86 / `35147730914` success;
- current slice `ISI-24C - Forecast Engine + Rolling-Origin Backtesting + Uncertainty/Diagnostics + NOT_ESTIMATED Runtime Semantics`;
- overall ISI-24 remains IN PROGRESS;
- server remains deferred/frozen.

### tasks.json

Keep `ISI-24-ORDO-PRODUCTION-METHODOLOGY` as `in_progress`.
Record 24B accepted checkpoint.
Set 24C current.
Set active spec to:

`automation/specs/ISI-24C-ORDO-FORECAST-BACKTEST-UNCERTAINTY-CONTRACTS.md`

### MasterPlan

Convert 24B current wording to accepted 24B checkpoint and add 24C current governed slice.

Add next canonical inventory IDs:
- `INV-C38` — ORDO forecast execution/runtime result authority;
- `INV-C39` — ORDO forecast/backtest metrics + uncertainty authority.

Update relevant existing ORDO analytics/scenario/time-series inventory rows without deleting accepted history.

Do not mark overall ISI-24 complete.

### Historical 24B governance test

Migrate `tests/test_isi_24b_governance_contract.py` from live-current-24B assertions to accepted 24B checkpoint assertions.

It must preserve:
- 24B migration truth;
- 24B inventory IDs `INV-C35/C36/C37`;
- accepted 24B SHA/tree/run evidence;
- scenario no-forecast boundary;
- 24B time-series plan-only semantics.

It must no longer require live STATUS/tasks to claim 24B is current.

### Harness

Update `tests/test_isi_17_harness_contract.py` only as needed for current 24C status/spec synchronization.
Do not weaken prior accepted checkpoints.

## 21. New 24C test authorities

Create exactly these eight tests:

- `tests/test_isi_24c_api_contract.py`
- `tests/test_isi_24c_forecast_engine.py`
- `tests/test_isi_24c_rolling_origin.py`
- `tests/test_isi_24c_uncertainty_diagnostics.py`
- `tests/test_isi_24c_not_estimated_semantics.py`
- `tests/test_isi_24c_migration_contract.py`
- `tests/test_isi_24c_governance_contract.py`
- `tests/test_isi_24c_reference_forecasts.py`

Coverage must include:
- spec must be validated;
- exact binding revalidation;
- family must be explicitly requested and present in spec;
- no automatic selection/fallback;
- only naive/seasonal-naive execution;
- unsupported executable family => NOT_ESTIMATED;
- deterministic reference forecasts;
- exact rolling-origin splits and no leakage;
- missing/duplicate/invalid evidence;
- minimum history/origins;
- deterministic metrics;
- leakage-safe empirical interval calibration;
- interval target-domain clipping;
- required-metric unavailability;
- deterministic request/result fingerprints;
- scenario `NOT_ESTIMATED` runtime semantics;
- historical scenario legacy truth;
- migration upgrade/downgrade;
- accepted 24B checkpoint and current 24C governance;
- accepted 24A scenario no-forecast boundary remains intact.

Reference forecasts validate generic forecast machinery only. They do NOT validate a destination forecast methodology, policy conclusion or normative destination ranking.

## 22. Strict non-goals

Locked out of ISI-24C:

- NO automatic model selection
- NO model ranking/winner label
- NO champion/challenger promotion/model registry (ISI-25)
- NO ETS execution
- NO SARIMA execution
- NO SARIMAX execution
- NO count-time-series execution
- NO invented SARIMA orders
- NO invented future exogenous values
- NO invented count-model structure
- NO random train/test split
- NO future leakage
- NO interpolation/imputation/hidden zero fill
- NO fabricated interval percentage
- NO causal impact estimator
- NO policy-effect estimator
- NO automatic policy recommendation
- NO citizen scoring
- NO eligibility logic
- NO normative destination ranking
- NO scenario-as-forecast
- NO estimated scenario impact without approved response model
- NO Monte Carlo
- NO Streamlit/UI expansion
- NO ORDO Help/User Guide completion
- NO ORDO XAI completion
- NO shared ISI-25 AI/MLOps promotion logic
- NO dependency changes
- NO server/DNS/ingress/SMTP/secrets/production-data mutation
- NO stage/commit/push

## 23. Required acceptance gates

The candidate must satisfy:

```text
BASELINE_HEAD=PASS
ORIGIN_MAIN_BASELINE=PASS
BASELINE_TREE=PASS
LOCAL_BRANCH_MAIN=PASS
ONE_WORKTREE=PASS
NO_STAGED_PREIMPLEMENTATION=PASS
CLEAN_PREIMAGE_WORKTREE=PASS

EXACT_EXISTING_PREIMAGES_9=PASS
EXACT_NEW_PATHS_ABSENT_12=PASS
SOLE_MIGRATION_HEAD_20260916_0031=PASS

EXACT_ISI24C_DIRTY_SURFACE_21=PASS
ISI24C_ANALYZER=PASS

FORECAST_EXECUTABLE_FAMILY_BOUNDARY=PASS
NO_AUTOMATIC_MODEL_SELECTION=PASS
ROLLING_ORIGIN_NO_LEAKAGE=PASS
UNCERTAINTY_INTERVAL_CONTRACT=PASS
NOT_ESTIMATED_RUNTIME_CONTRACT=PASS
SCENARIO_NO_FORECAST_BOUNDARY=PASS
HISTORICAL_24B_CHECKPOINT=PASS
DEPENDENCY_SURFACE_UNCHANGED=PASS

FOCUSED_ORDO_BACKWARD_COMPAT_AND_24C=PASS
POLICY=PASS
MIGRATION_OFFLINE=PASS
PYTHON_COMPILE=PASS
RUFF_E9=PASS
MYPY=PASS
DIFF_CHECK=PASS
FULL_PYTHON_REGRESSION=PASS
NATIVE_POSTGRES=PASS
MIGRATION_LIVE=PASS

CANDIDATE_MANIFEST_STABLE=PASS

CODEX_STAGE_COMMIT_PUSH=NO
SERVER_MUTATION=NO
READY_FOR_ISI24C_FINAL_REVIEW=PASS
```

No gate may be weakened merely to make the task green.
