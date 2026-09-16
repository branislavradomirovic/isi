# ISI-23D — SIMPA Help Coverage + In-App User Guide + Statistical XAI

Status: OWNER-LOCKED IMPLEMENTATION CONTRACT
Baseline main SHA: `a49b3faf171dfdbcf9306cfbe50fdc6ad1aabbff`
Execution model: deterministic package apply + independent analyzer; no Codex; no stage/commit/push; no server mutation.

## Objective

Implement the ISI-23D Help/XAI slice required by MasterPlan 0.5A and ISI-23:

1. establish the canonical repository Help Coverage Matrix;
2. deliver detailed in-app SIMPA Help / User Guide;
3. deliver repository SIMPA User Guide documentation;
4. make deterministic statistical results model-appropriate and interpretable for OLS, Poisson GLM, Binomial/Logit and Fractional Logit;
5. expose coefficient estimate, standard error, confidence interval and model-produced p-value where available;
6. explain diagnostics, calibration/error summaries, complete-case missing/dropped behavior, fingerprints/provenance and `production_eligible` without inventing thresholds/confidence/causality;
7. preserve bounded AI provenance/model/policy/prompt/human-review visibility while leaving shared AI/MLOps promotion/fallback evaluation to ISI-25;
8. synchronize MasterPlan / STATUS / tasks from accepted ISI-23C to current ISI-23D.

## Mandatory safety / methodology rules

- No citizen scoring, eligibility automation, risk labels, benefit decisions or punitive decisioning.
- No LISI formula, weight, threshold or class-band invention.
- No causal claim from ordinary regression/association.
- No fabricated feature importance, generic confidence score, calibrated probability, policy conclusion or unsupported attribution.
- `DRAFT`, `PROPOSED`, `VALIDATED`, `RETIRED`, reference-suite PASS and human validation remain distinct.
- `production_eligible=true` means the executed statistical contract was `VALIDATED`; it is not champion/performance certification.
- Complete-case handling must state that missing target/feature records are dropped and numerical zero is preserved.
- Existing immutable statistical results without p-values remain immutable; UI must show p-value unavailable for legacy result rather than reconstructing it.
- P-values are model-based association inference only, not practical significance, policy significance or causality; no multiplicity adjustment is implied by the v1 contract.
- Diagnostics expose raw supported outputs only; no universal pass/fail threshold may be invented.
- Calibration status `not_applicable` must be displayed as such, not as missing. Binomial/Fractional calibration-error summaries must not be called proof of calibrated confidence.
- Server/DNS/ingress/SMTP/production secrets/data/server Ollama remain frozen until owner-approved ISI-28.

## Exact mutable surface

Existing paths:

1. `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
2. `automation/STATUS.md`
3. `automation/tasks.json`
4. `src/streamlit_app/app.py`
5. `src/streamlit_app/simpa_analytics_workspace.py`
6. `src/domains/simpa/statistical_models.py`
7. `tests/test_isi_23c_api_ui_contract.py`
8. `tools/ci/policy_check.py`
9. `tests/test_isi_17_harness_contract.py`
10. `tests/test_isi_23a_ui_contract.py`
11. `tests/test_isi_23b_api_ui_contract.py`

New paths:

12. `automation/specs/ISI-23D-SIMPA-HELP-XAI.md`
13. `docs/help/ISI-HELP-COVERAGE-MATRIX.md`
14. `docs/help/SIMPA-USER-GUIDE.md`
15. `src/streamlit_app/simpa_help_workspace.py`
16. `src/domains/simpa/statistical_xai.py`
17. `tests/test_isi_23d_help_xai_contract.py`
18. `tests/test_isi_23d_statistical_xai.py`

Any other repository mutation is a hard failure.

## Canonical system inventory impact

- `INV-A18 SIMPA Help, User Guide and XAI interpretation`: `PLANNED -> CURRENT_AS_BUILT`, canonical paths/test authority updated.
- `INV-A21 Cross-product Help Coverage Matrix`: `PLANNED -> CURRENT_AS_BUILT`, while non-SIMPA/shared/ORDO rows may honestly remain `MISSING`/`PARTIAL` until their owning phases.
- No new domain/service/database/worker/provider inventory unit is introduced.
- `tools/ci/policy_check.py` and `tests/test_isi_17_harness_contract.py` are synchronized to the owner-approved 23D inventory/task state; stale `INV-A18=PLANNED` and `Current/next=ISI-23C` sentinels are forbidden.
- `tests/test_isi_23a_ui_contract.py` and `tests/test_isi_23b_api_ui_contract.py` retain their phase-specific lifecycle/reference-provenance checks but no longer freeze the later global Help state as PLANNED; Help completeness is owned by the dedicated ISI-23D Help/XAI authority.

## Help contract

Every SIMPA material Help topic must provide all MasterPlan 0.5A items:

1. what it does;
2. when to use it;
3. role/permission boundary;
4. exact steps;
5. fields/status/result semantics;
6. representative non-sensitive example;
7. explicit non-goals;
8. common errors and safe recovery;
9. security/privacy/methodological/regulatory limitations;
10. provenance/version/quality/human-review requirements.

SIMPA domain material actions must be `VERIFIED` in the matrix and cross-linked to the in-app topic and repository User Guide. Other products/shared surfaces must not be falsely upgraded to VERIFIED.

## Statistical XAI contract

The presentation/XAI layer is deterministic and consumes only stored result/contract/provenance fields. It must support:

- continuous -> OLS;
- count -> Poisson GLM;
- binary system state -> Binomial/Logit;
- proportion/rate -> Fractional Logit.

For each result expose/explain:

- target semantic and model family;
- coefficient scale and direction caveat appropriate to the family;
- estimate, standard error, confidence interval and p-value status/value;
- sample size / selected count / dropped-missing count;
- fit/error metrics;
- diagnostics with no invented pass/fail threshold;
- calibration status/measure where actually present;
- engine schema and statsmodels version;
- statistical contract/methodology/artifact/dataset/input/result fingerprints;
- `production_eligible` semantics;
- explicit unsupported states for causal effect, generic confidence score, feature importance, prediction threshold and policy recommendation.

## Legacy/drift classification

- `automation/STATUS.md`, `automation/tasks.json` and the ISI-23 MasterPlan status still naming 23C as current: `REMOVE_BEFORE_NEXT_SLICE` governance drift; synchronize in this candidate.
- `simpa_analytics_workspace.py` caption saying detailed Help remains planned for ISI-23E: `REMOVE_BEFORE_NEXT_SLICE` stale UI text.
- 23C historical test assertions that globally freeze Help as PLANNED / require the stale 23E caption: `REMOVE_BEFORE_NEXT_SLICE`; retain 23C technical invariants but stop freezing future global state.
- historical immutable statistical result rows without p-values: `REQUIRED_COMPATIBILITY`; do not rewrite them.

## Non-goals

- No ORDO Help/XAI implementation.
- No new LISI methodology/formula/weights/thresholds.
- No classification thresholds/classes.
- No new forecast/causal model.
- No statistical-to-AI synthesis integration.
- No shared AI champion/challenger/evaluation/promotion/fallback implementation (ISI-25).
- No schema migration.
- No dependency change.
- No deployment/server mutation.

## Acceptance

Required local gates:

- exact baseline and exact preimage verification;
- exact 18-path dirty surface;
- independent Help/XAI analyzer;
- focused ISI-23D tests;
- 23C compatibility tests;
- policy check;
- `git diff --check`;
- full Python regression;
- final exact analyzer;
- HEAD and `origin/main` remain baseline;
- candidate remains unstaged/uncommitted.

Only after assistant review and explicit owner approval may a separate exact commit/push package be created.
