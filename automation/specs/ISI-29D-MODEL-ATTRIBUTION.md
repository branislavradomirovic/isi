# ISI-29D locked model attribution contract
Baseline: a77f9f0b4e43038554ee203a0c5ad22cd0b9e981 verified local/origin/direct main; clean single worktree and empty index/stash. Complete MasterPlan previously read in this conversation; canonical bootstrap and relevant code/contracts/ADR0025 reviewed. Hosted acceptance#96 success on predecessor374dda3 only, not this SHA. Owner standing29A-F implementation/verified commit/push and final acceptance/deployment authority persists.

Continuous OLS only, aggregate-only SIMPA. Persist domain-owned immutable attribution artifact (0036 additive migration) with exact result/run/scope, contract, source/input, background cohort and artifact fingerprints, author/time, schema/method/tolerance/unit. A request explicitly builds from stored coefficients and exact revalidated governed fit cohort; no model fitting, raw-source bypass, arbitrary user background, new feature scaling or future rows. Background is the exact complete-case training cohort, no subsampling. Fail closed if >512 selected records or >24 features, retired/unvalidated methodology/statistical contract, proposed execution, missing/fingerprint mismatch/invalidation, incompatible unit/engine/family, output numerical mismatch. Bounds are technical limits, not privacy/significance thresholds.

Use existing _prepare_input to preserve feature order, zero and complete-case handling; revalidate contract, run, ordered input-content fingerprint and stored detail result fingerprint. Compare reproduced predictions using stored parameters to stored fit metrics/counts with declared numerical tolerance (no refit). Derive exact interventional linear SHAP beta_j*(x_j-background_mean_j), base intercept+sum(beta*mean), independently verify additivity to direct prediction. Official SHAP LinearExplainer documented formula https://shap.readthedocs.io/en/latest/generated/shap.LinearExplainer.html ; independently enumerate coalition marginal contributions for small feature fixtures, deterministic test equivalence. No SHAP dependency needed for closed-form method, no dependency changes. Output scale identity / target methodology unit; background dependence and correlated-feature limitations visible; descriptive in-sample output explanation, not forecast, causal effect, generic confidence or LLM truth.

Scoped analysis.read checks before any read, analysis.run before creation (human click), existing full org/member/role/product/workspace boundary. Matrix contains only numerical aggregate model inputs and local pseudonymous row index/content digest, not names/source locators or arbitrary fields. Never external AI/provider/network call. Artifact JSON immutable at service boundary and fingerprint checked on every read with source/contract revalidation; underlying source invalidation blocks read even if artifact exists. Audit only fingerprints/state/actor, no inputs/matrix. Database JSON persistence is additive; no old result mutation/backfill.

UI existing statistical-result expander -> SHAP with explicit build/load, source/background/schema/unit notices, sample x feature matrix and heatmap, global mean-absolute ranking/chart, selected sample waterfall/table with base/input/contribution/output/additivity evidence. Bounds explicit and keyboard/data table fallback; safe fixed SVG escaped strings. Exact result/scoped widget keys, no cross-session cached matrices. ORDO current naive/seasonal-naive remains honestly unsupported with existing lag/backtest explanations; conditional additional execution model not selected because none meets execution/attribution prerequisite.

Tests: formula/coalition reference and correlated/zero/missing/order invariants; additive/sign/unit/finite/tolerance/parity failures; input/contract/source/result/metric tamper, scope/isolation and authorization; immutable persistence/native0036 upgrade/downgrade/reupgrade; UI/transport/matrix/waterfall/global parity and safe labels; no external network; full regression; synthetic desktop/mobile; independent analyzer twice + assistant exact review before standing-authorized main commit/push. No CI/server in29D. Inventory A11/A22/C45/M07/M22 and technical/Help/ledgers updated in same candidate. No production verification.

## Reconciliation / legacy audit
DONE29A/B/C exact approved file hashes/commits; PARTIAL real institutional GIS sources; MISSING29D/E/F runtime. DRIFT top task next/current baseline29C is REMOVE_BEFORE_NEXT_SLICE in this candidate. Historical29A/B/C candidate notes LEGITIMATE_HISTORY; existing statistical regression unsupported states REQUIRED_COMPATIBILITY for old coefficient read model, new SHAP separate panel. Existing historical Alembic tests bind their own revisions, no global-head freeze found. No new dependency, provider, numerical model family, worker or ingress; raw-source bypass prohibited. Browser recapture previously blocked by exhausted review credits; do not bypass; browser acceptance required before phase closeout. Native disposable loopback DB allowed for tests, no server.

## Exact mutable surface
- `TECHNICAL_DOCUMENTATION.md`
- `automation/STATUS.md`
- `automation/tasks.json`
- `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
- `docs/roadmap/ISI-29-XAI-GIS-ENTITY-FINDINGS-PLAN.md`
- `docs/help/ISI-HELP-COVERAGE-MATRIX.md`
- `docs/help/ISI-SHAP-GUIDE.md`
- `automation/specs/ISI-29D-MODEL-ATTRIBUTION.md`
- `src/domains/simpa/analytics_models.py`
- `src/domains/simpa/statistical_attribution.py`
- `src/domains/simpa/attribution_service.py`
- `src/api/simpa_analytics_routes.py`
- `src/streamlit_app/simpa_analytics_api.py`
- `src/streamlit_app/simpa_analytics_workspace.py`
- `src/streamlit_app/attribution_view.py`
- `migrations/versions/20261008_0036_simpa_attribution.py`
- `tests/test_isi_29d_attribution_engine.py`
- `tests/test_isi_29d_attribution_service.py`
- `tests/test_isi_29d_attribution_ui_api.py`
- `tests/test_isi_29d_native_postgres.py`
- `tools/qa/run_isi29d.py`
- `tools/qa/analyze_isi29d.py`

All other tracked files frozen. Canonical inventory impact A11/A22/C45/M07/M22 as above; no shared AI authority changes. Existing ORDO unavailable SHAP meaning retained. Evidence automation/evidence/ISI-29D. Technical absolute/relative tolerance1e-8, finite identity output, no domain threshold. Creation requires explicit human analysis.run click plus analysis.read; audit bounded fingerprint only. Migration upgrade/downgrade/reupgrade mandatory; no CI/server this slice.

Final review lock clarification before correction: fingerprint includes artifact creation UUID/actor/UTC timestamp and compares them to immutable relational metadata on read; no active-creator requirement after creation. Attribution implementation and input-reconstruction source SHA256 are recorded, alongside stored model engine/schema/library version. Original fit code SHA was not stored by legacy results, explicitly NOT_RECORDED_LEGACY_RESULT (never invented). Closed-form deterministic explainer has seed NOT_APPLICABLE, no sampling. UI distinguishes unavailable generic classical feature-importance state from separately available SHAP artifact. Exact gates repeat after correction.

Final UI review: exact-zero contributions are neutral gray markers, never negative bars; create keeps explicit loaded state through sample selection reruns. Dynamic feature/unit labels render as plain text (not Markdown). Reported additivity error is computed from normalized serialized matrix/baseline/output, not an earlier unrounded intermediate. Functional AppTest covers viewer load and analyst creation/rerun; it does not replace browser acceptance.

Browser acceptance correction: the shared legacy coefficient/forecast renderer adds a truthful non-SHAP unavailable caption for its original surfaces. The new verified SHAP panel renders its fixed escaped charts with a dedicated non-causal caption instead; legacy renderer/tests stay unchanged. AppTest rejects the contradictory unavailable caption. Exact 22-file mutable scope unchanged; rerun all gates and browser acceptance against revised fingerprint.

Release review correction: the new native test must participate in the existing hosted ISI_RUN_NATIVE_DB_TESTS lane using loopback isi_ci, in addition to explicit local isi29d_synthetic. The test retains owned random-schema isolation and cleanup; no native skip is permitted in release evidence. No workflow/triggers or broader mutable surfaces change.
