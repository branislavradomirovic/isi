# ISI-24D — ORDO Help Coverage + In-App User Guide + Forecast/Scenario XAI Presentation

Task ID: **ISI-24D**

Status of this document: **OWNER-SCOPE-FROZEN IMPLEMENTATION CONTRACT**

This document is the complete implementation authority for ISI-24D. Do not broaden it. Do not stage, commit, push, deploy, create branches/worktrees, use production secrets, or touch the server.

## 1. Immutable accepted baseline

- Repository: `branislavradomirovic/isi`
- Canonical local repository: `$HOME/Applications/Python/ISI`
- Branch: `main`
- Baseline commit: `76e4ca5265f48a096d2253c88898e1aaedbff991`
- Baseline tree: `0a6ec7b7ab4db5d43c570c714c065f8fef7093f4`
- Accepted exact-main workflow: `ISI required acceptance` run #87, run ID `35153774409`, completed/success
- Accepted Alembic sole head: `20260916_0032`
- ISI-24C is COMPLETE / CI_VERIFIED on this baseline.

## 2. Objective

Implement the ORDO Help/XAI and forecast-presentation slice required by MasterPlan 0.5A and ISI-24:

1. deliver detailed in-app ORDO Help / User Guide;
2. deliver repository `docs/help/ORDO-USER-GUIDE.md`;
3. make ORDO-owned material user actions VERIFIED in the canonical Help Coverage Matrix;
4. add deterministic, model-appropriate interpretation for persisted 24C forecast results;
5. add deterministic interpretation for scenario `NOT_ESTIMATED` semantics and preserve the scenario-versus-forecast boundary;
6. present persisted accepted 24C forecast results in Streamlit, including `ESTIMATED` / `NOT_ESTIMATED`, forecast intervals, rolling-origin/backtest evidence, diagnostics, warnings and provenance;
7. preserve bounded ORDO AI provenance/model/prompt/policy/human-review visibility without inventing shared ISI-25 evaluation/promotion semantics;
8. convert `INV-A19` from `PLANNED` to `CURRENT_AS_BUILT` only when the Help/User Guide/XAI implementation exists and its acceptance tests pass;
9. keep overall ISI-24 `IN PROGRESS`; ISI-24E remains final ORDO closeout.

## 3. Exact mutable surface — FROZEN 17

The complete ISI-24D candidate may modify/create exactly these paths and no others:

1. `automation/STATUS.md`
2. `automation/tasks.json`
3. `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
4. `docs/help/ISI-HELP-COVERAGE-MATRIX.md`
5. `src/streamlit_app/app.py`
6. `src/streamlit_app/ordo_workspace.py`
7. `src/streamlit_app/ordo_analytics_api.py`
8. `src/streamlit_app/ordo_analytics_workspace.py`
9. `tests/test_isi_24c_governance_contract.py`
10. `tools/ci/policy_check.py`
11. `tests/test_isi_17_harness_contract.py`
12. `automation/specs/ISI-24D-ORDO-HELP-XAI.md`
13. `docs/help/ORDO-USER-GUIDE.md`
14. `src/streamlit_app/ordo_help_workspace.py`
15. `src/domains/ordo/analytics_xai.py`
16. `tests/test_isi_24d_help_xai_contract.py`
17. `tests/test_isi_24d_forecast_xai.py`

Everything outside these 17 paths is immutable for ISI-24D.

### 3.1 Deterministic pre-implementation convergence subset

Before Codex is allowed, the outer package may deterministically mutate only these seven paths:

- `automation/STATUS.md`
- `automation/tasks.json`
- `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
- `src/streamlit_app/ordo_workspace.py`
- `tests/test_isi_24c_governance_contract.py`
- `tests/test_isi_17_harness_contract.py`
- `automation/specs/ISI-24D-ORDO-HELP-XAI.md`

This convergence step records accepted 24C history, makes 24D current, removes the stale ORDO phase caption and freezes this contract. It MUST NOT mark `INV-A19` current-as-built yet.

### 3.2 Later implementation subset

After assistant review of the convergence candidate, Codex may be authorized in a separate runner only for the remaining implementation paths plus any already-dirty allowed path that the outer runner explicitly permits. Generic `codex` remains forbidden; only `codex-isi` may be used.

## 4. Mandatory methodology and safety rules

- Forecast is not scenario.
- A scenario assumption is not evidence and is not a forecast.
- Scenario impact remains `NOT_ESTIMATED` with stable reason `NO_APPROVED_RESPONSE_MODEL` unless a separately approved response/impact methodology exists.
- `ESTIMATED` forecast means only that accepted 24C runtime produced persisted deterministic output under an exact validated time-series specification and governed input.
- `NOT_ESTIMATED` is a successful domain outcome, not zero and not a hidden failure.
- No automatic model selection or fallback may be implied.
- No causal interpretation may be added.
- No generic confidence score, feature importance, calibrated probability, ranking, winner, policy recommendation or causal impact may be fabricated.
- Forecast interval level is a configured interval level, not a generic probability that the forecast is correct.
- Rolling-origin metrics are historical backtest diagnostics; they do not prove future performance.
- Unsupported/unavailable metrics or explanations remain explicitly unavailable.
- Existing bounded AI output remains evidence synthesis requiring human review; shared champion/challenger/evaluation/promotion/fallback governance remains ISI-25.
- Server/DNS/ingress/SMTP/production secrets/data/server Ollama remain frozen until owner-approved ISI-28.

## 5. Forecast presentation boundary

24D consumes only the accepted 24C API/runtime truth already available at:

- `GET /api/v1/ordo/analytics/forecasts`
- `GET /api/v1/ordo/analytics/forecasts/{forecast_run_id}`

24D adds Streamlit client calls and read-only presentation/interpretation of persisted forecast runs.

24D MUST NOT add a manual raw-UUID forecast execution form or invent a time-series-spec discovery/authoring workflow that the accepted product API does not expose. The existing 24C `POST /forecasts` runtime remains intact and unchanged. A separate user-facing forecast configuration/execution workflow, if required for release, is an explicit ISI-24E gap-audit item and may not be silently invented inside Help/XAI work.

No backend forecast service, API route, schema, model, migration, forecast engine or dependency change is authorized in 24D.

## 6. Deterministic ORDO forecast XAI contract

Create `src/domains/ordo/analytics_xai.py` as a pure deterministic interpretation layer over persisted result dictionaries. It does not query databases, run models or call AI.

At minimum `build_forecast_xai(...)` must expose/explain:

- result status: `ESTIMATED` or `NOT_ESTIMATED`;
- stable `reason_code` and human-readable bounded interpretation;
- requested family vs executed family;
- engine key/version;
- interval method and interval level;
- observation/training window and horizon;
- rolling-origin plan;
- aggregate backtest metrics;
- metric availability, including explicit unavailable states;
- diagnostics and warnings without invented pass/fail thresholds;
- persisted forecast points only when `ESTIMATED`;
- exact time-series spec ID/version/fingerprint;
- exact target methodology ID/version/fingerprint;
- exact input snapshot SHA-256;
- explicit series identity;
- request/result fingerprints;
- `non_causal` semantics;
- `automatic_model_selection=false` semantics;
- `automatic_policy_recommendation=false` semantics;
- unsupported states for causal effect, feature importance, generic confidence score, prediction/ranking and automatic recommendation.

For `NOT_ESTIMATED`, no XAI function may create point estimates, intervals or replacement values.

## 7. Scenario XAI / interpretation contract

The same deterministic module must expose a bounded scenario interpretation helper for persisted scenario-assessment payloads:

- scenario is user-authored assumptions/measures, not a forecast;
- `forecast_performed=false` remains authoritative;
- `impact=NOT_ESTIMATED` is explained with its persisted reason code;
- `NO_APPROVED_RESPONSE_MODEL` means the system intentionally did not estimate causal/predictive impact;
- legacy `LEGACY_NOT_EVALUATED` remains historical truth and must not be rewritten as a later execution event;
- no numeric impact or confidence may be invented when absent.

## 8. Streamlit presentation contract

### Navigation

When product code is ORDO, `app.py` adds an `ordo_help` navigation entry analogous to the accepted SIMPA Help pattern, while preserving product isolation.

### Forecast presentation

`ordo_analytics_api.py` adds read-only wrappers for the accepted forecast list/detail endpoints.

`ordo_analytics_workspace.py` adds a forecast-results section that:

- lists persisted forecast runs for the active organization/workspace;
- clearly separates `ESTIMATED` from `NOT_ESTIMATED`;
- shows requested/executed family and reason code;
- shows forecast points/intervals only for `ESTIMATED`;
- shows rolling-origin/backtest metrics, diagnostics, warnings and provenance;
- renders deterministic forecast XAI;
- never labels scenario output as forecast;
- never invents missing values, confidence or model quality labels;
- does not provide a raw-UUID execution form.

Existing scenario assessments must display explicit impact state/reason and deterministic scenario interpretation rather than a bare table where practical.

Existing bounded ORDO AI cards must retain provider/model/policy/prompt/human-review provenance and must not gain invented shared ISI-25 quality claims.

## 9. ORDO Help contract

Create `src/streamlit_app/ordo_help_workspace.py` and `docs/help/ORDO-USER-GUIDE.md`.

Every material ORDO Help topic must satisfy all ten MasterPlan 0.5A fields:

1. what the function does;
2. when it should be used;
3. role/permission boundary;
4. exact user steps;
5. fields/status/result semantics;
6. representative non-sensitive example;
7. explicit non-goals;
8. common errors and safe recovery;
9. security/privacy/methodological/regulatory limitations;
10. provenance/version/quality/human-review requirements.

Minimum topic coverage:

- `ORDO-H01` access and workspace context;
- `ORDO-H02` destination profile/resources/stakeholders;
- `ORDO-H03` monitoring cycles;
- `ORDO-H04` indicator registry, observations and methodology status;
- `ORDO-H05` governed analytical artifacts and evidence-quality snapshot;
- `ORDO-H06` methodology lifecycle and human approval boundaries;
- `ORDO-H07` analytics snapshots and provenance;
- `ORDO-H08` development goals and scenarios;
- `ORDO-H09` evidence-only scenario assessment and `NOT_ESTIMATED` impact;
- `ORDO-H10` persisted forecasts, rolling-origin backtesting, intervals, diagnostics and forecast `NOT_ESTIMATED`;
- `ORDO-H11` bounded local AI synthesis, provenance and human review;
- `ORDO-H12` Help/User Guide usage and limitations.

## 10. Help Coverage Matrix and inventory

On successful 24D implementation:

- `INV-A12 ORDO indicators` -> `VERIFIED` Help coverage;
- `INV-A13 ORDO analytics and scenarios` -> `VERIFIED` Help coverage for its implemented user-facing actions, including persisted forecast presentation;
- `INV-A19 ORDO Help, User Guide and XAI interpretation` -> inventory status `CURRENT_AS_BUILT` and Help coverage `VERIFIED`;
- `INV-A21 Cross-product Help Coverage Matrix` remains `PARTIAL` globally until all shared production-critical surfaces owned by later release work are verified;
- shared surfaces such as Login/Data/AI/Reporting/Administration/Security must not be falsely promoted by ORDO domain Help;
- `tools/ci/policy_check.py` and the harness change the `INV-A19` sentinel only when implementation exists and 24D tests prove it.

No new independent inventory ID is required: 24D realizes the already-planned `INV-A19` and extends presentation/test authority of existing ORDO rows.

## 11. Governance synchronization

The pre-implementation convergence step records:

- accepted 24C SHA `76e4ca5265f48a096d2253c88898e1aaedbff991`;
- accepted tree `0a6ec7b7ab4db5d43c570c714c065f8fef7093f4`;
- exact-main run #87 / `35153774409` success;
- 24C as accepted historical checkpoint;
- 24D as current governed slice;
- overall ISI-24 remains `IN PROGRESS`;
- server remains frozen/deferred.

During the implementation candidate, do **not** claim 24D `COMPLETE / CI_VERIFIED` and do not make 24E current before exact-main CI has actually passed. After accepted 24D exact-main CI, a separate deterministic closeout/transition step must synchronize 24D accepted evidence and activate 24E. This prevents recurrence of the stale-current drift detected after 24C.

## 12. Legacy/drift classification

- live governance still calling 24C current after exact-main run #87: `REMOVE_BEFORE_NEXT_SLICE`; fixed by the deterministic convergence step before Codex;
- `tests/test_isi_24c_governance_contract.py` freezing 24C as live-current: `REMOVE_BEFORE_NEXT_SLICE`; convert it to accepted-checkpoint history while preserving 24C technical/scope invariants;
- ORDO indicator caption saying formulas/scenarios/models arrive in ISI-11: `REMOVE_BEFORE_NEXT_SLICE`; replace with timeless as-built wording before Codex;
- `INV-A19=PLANNED` in MasterPlan/policy/harness: valid **pre-implementation state**, classified `REMOVE_IN_NAMED_PHASE(ISI-24D)`; change only when Help/XAI is actually implemented and tested;
- ORDO rows `MISSING` in Help Coverage Matrix: valid pre-24D truth, classified `REMOVE_IN_NAMED_PHASE(ISI-24D)`;
- historical forecast/scenario rows and accepted 24A-24C contracts: `LEGITIMATE_HISTORY` / `REQUIRED_COMPATIBILITY`; never rewrite to simulate later evidence.

## 13. Strict non-goals

- NO backend forecast engine change
- NO new forecast model family
- NO automatic model selection/fallback
- NO new time-series-spec authoring/discovery API
- NO raw UUID execution form
- NO forecast execution semantics change
- NO new scenario impact estimator
- NO causal claim
- NO policy recommendation
- NO ranking/winner label
- NO generic confidence score
- NO fabricated feature importance/attribution
- NO new ORDO formula/weight/threshold
- NO shared AI champion/challenger/evaluation/promotion/fallback implementation
- NO DB migration
- NO dependency change
- NO CI workflow change
- NO server/deployment mutation
- NO stage/commit/push

## 14. Required tests

Create exactly these new 24D test authorities:

- `tests/test_isi_24d_help_xai_contract.py`
- `tests/test_isi_24d_forecast_xai.py`

Coverage must prove at minimum:

- ORDO Help nav is product-scoped and SIMPA/ORDO Help remain isolated;
- every ORDO topic has all ten required Help fields;
- ORDO User Guide exists and covers scenario-versus-forecast, `NOT_ESTIMATED`, backtesting, intervals, provenance, permissions, errors/recovery, non-goals and human review;
- Help Coverage Matrix has honest VERIFIED ORDO rows/actions without falsely promoting shared later-phase surfaces;
- `INV-A19` becomes CURRENT_AS_BUILT only with implementation/test authority;
- forecast client uses accepted GET endpoints;
- forecast XAI is deterministic and does not fabricate values;
- `NOT_ESTIMATED` never becomes zero or a forecast;
- backtest metrics/interval level/diagnostics are explained without invented quality thresholds/confidence;
- forecast provenance/fingerprints are preserved;
- scenario `NO_APPROVED_RESPONSE_MODEL` and `forecast_performed=false` remain explicit;
- legacy scenario state remains distinct;
- AI provenance and human-review boundaries remain visible;
- accepted 24C runtime/API semantics remain compatible;
- no backend/migration/dependency expansion occurred.

## 15. Acceptance gates

The final 24D candidate must satisfy:

- exact baseline/preimage control;
- total dirty surface exactly within the frozen 17 paths;
- no staged files;
- HEAD and `origin/main` remain the accepted 24C baseline until owner-approved commit;
- independent analyzer PASS;
- new 24D focused tests PASS;
- relevant 24A/24B/24C compatibility tests PASS;
- policy check PASS;
- `git diff --check` PASS;
- full Python regression PASS;
- no migration head change from `20260916_0032`;
- no dependency change;
- no server mutation;
- no stage/commit/push.

Only after assistant human review and explicit owner approval may an exact commit/push package be created.
