# ISI-25B — Evaluation + Promotion Runtime

## Status and owner approval

Owner-approved single macro-slice for implementation.

Approved owner phrase:

`ODOBRENO ISI-25B EVALUATION + PROMOTION RUNTIME SCOPE`

This is one indivisible implementation slice. Do not split it into evaluator, fallback, promotion, monitoring, Help, or bookkeeping microtasks. ISI-25A is already accepted and committed. ISI-25 remains globally IN PROGRESS until this 25B candidate passes deterministic local acceptance, independent analysis, assistant human review, and a later separate owner-approved exact-candidate commit/push.

GitHub-hosted CI is intentionally excluded from this development slice. No production/server mutation is authorized.

## Exact accepted baseline

- repository: `branislavradomirovic/isi`
- canonical local repository: `$HOME/Applications/Python/ISI`
- branch: `main`
- HEAD: `f0047321ee4410522697144ecfa464087f1b83bc`
- tree: `06e419ec656ee2fb0bfb74b4a6b10d42ef275f25`
- origin/main: `f0047321ee4410522697144ecfa464087f1b83bc` before implementation
- accepted ISI-25A commit subject: `Complete ISI-25A AI/MLOps governance and evaluation foundation`
- pre-implementation Alembic sole head: `20260917_0033`
- expected post-implementation Alembic sole head: `20260918_0034`
- worktree/index before implementation: clean/unstaged
- GitHub Actions for `f0047321ee4410522697144ecfa464087f1b83bc`: zero hosted runs
- canonical workflow remains manual-only and remotely `disabled_manually`

Any baseline mismatch is a hard STOP. Do not rebase, merge, reset, stash, clean, amend, branch, create another worktree, or improvise around it.

## Canonical authorities that must be read before editing

1. `AGENTS.md`
2. `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
3. `docs/roadmap/ISI-AI-MODEL-EVALUATION-PROTOCOL-v1.md`
4. `docs/roadmap/ISI-25-MODEL-REGISTRY.md`
5. `docs/roadmap/ISI-25-PROMOTION-POLICY.md`
6. `automation/specs/ISI-25A-AI-MLOPS-GOVERNANCE-EVALUATION-FOUNDATION.md`
7. current `src/platform/ai/**`, `src/api/ai_routes.py`, access/RBAC authorities, migration chain and relevant tests
8. `docs/help/ISI-HELP-COVERAGE-MATRIX.md`

The MasterPlan, evaluation protocol, accepted 25A code and current owner instructions outrank assumptions in this contract. If an irreconcilable contradiction is discovered inside the locked mutable surface, STOP and report it. Do not broaden scope.

## Bootstrap / DONE-PARTIAL-MISSING-DRIFT truth

Accepted ISI-25A provides:

- DONE: shared capability/model registration across `statistical_ml`, `embedding`, `llm`, `vlm`;
- DONE: immutable registry identity/fingerprint and candidate/challenger/retired lifecycle;
- DONE: champion vocabulary but champion mutation intentionally fail-closed;
- DONE: persisted fallback graph with priority, trigger codes, semantic-equivalence and human-review declarations;
- DONE: prompt rollback target identity;
- DONE: frozen synthetic `SIMPA-EVAL-v1` and `ORDO-EVAL-v1` CONTRACT/FIXTURE datasets;
- DONE: evaluation dataset/run/result/review persistence foundation;
- DONE: platform-admin-only shared governance mutation and `report.publish` evaluation-review write boundary;
- DONE: selected/default-model-only 25A runtime, preventing ambiguous fallback.

25B must close:

- MISSING: unambiguous capability/registration-bound runtime execution;
- MISSING: executable registered fallback with trigger, semantic, review and provider-policy enforcement;
- MISSING: promotion-grade frozen benchmark identity distinct from 25A foundation fixtures;
- MISSING: deterministic evaluator engines for statistical/ML, embeddings/RAG, LLM and VLM evidence;
- MISSING: factuality/hallucination, structured-output, provenance, Serbian/human-rubric, retrieval and adversarial/safety metrics;
- MISSING: baseline/challenger comparison and capability-specific threshold profiles;
- MISSING: evidence-gated champion promotion and governed rollback execution identity;
- MISSING: circuit-breaker state and deterministic request-time enforcement;
- MISSING: drift snapshots/read model; no scheduler or online learning;
- MISSING/PARTIAL: shared AI XAI / Help / evaluation interpretation;
- DRIFT: `automation/STATUS.md` and `automation/tasks.json` still describe accepted 25A as an unstaged candidate rather than accepted `f0047321ee4410522697144ecfa464087f1b83bc`.

The status drift is absorbed into this macro-slice. Do not create a separate bookkeeping commit.

## Mandatory legacy/drift classifications

The implementation must record these classifications in canonical docs/status where appropriate:

1. 25A selected-model-only runtime: `REQUIRED_COMPATIBILITY` for jobs without explicit registration binding.
2. 25A ambiguous helper behavior that infers a registration from `runtime_model_id` using first-created ordering: `REMOVE_BEFORE_NEXT_SLICE`; 25B execution may not use it.
3. `SIMPA-EVAL-v1` / `ORDO-EVAL-v1`: `REQUIRED_COMPATIBILITY`; they remain foundation-only forever and are not retroactively converted to promotion evidence.
4. Historical 25A tests that assert 25A current-global runtime forever: `REMOVE_BEFORE_NEXT_SLICE`; rewrite them to assert the accepted 25A historical contract without freezing 25B current behavior.
5. F08 / global Help gaps outside ISI-25 ownership: `REMOVE_IN_NAMED_PHASE(ISI-27)`; 25B closes only shared AI/model evaluation/provenance/promotion/fallback interpretation it owns.
6. No application-owned scheduler exists: `REQUIRED_COMPATIBILITY`; drift monitoring is explicit/on-demand and persisted, never a new hidden scheduler.

## Original implementation mutable surface — 27 paths

The original implementation authorization was exactly these 27 repository paths relative to `f0047321ee4410522697144ecfa464087f1b83bc`. This list remains the immutable implementation-scope record for the 25B build phase; it is not a requirement that a committed clean checkout remain dirty.

1. `automation/STATUS.md`
2. `automation/tasks.json`
3. `automation/specs/ISI-25B-EVALUATION-PROMOTION-RUNTIME.md`
4. `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
5. `docs/roadmap/ISI-25-MODEL-REGISTRY.md`
6. `docs/roadmap/ISI-25-PROMOTION-POLICY.md`
7. `docs/help/ISI-HELP-COVERAGE-MATRIX.md`
8. `docs/help/ISI-AI-USER-GUIDE.md`
9. `migrations/versions/20260918_0034_ai_evaluation_promotion_runtime.py`
10. `src/platform/ai/models.py`
11. `src/platform/ai/schemas.py`
12. `src/platform/ai/service.py`
13. `src/platform/ai/governance.py`
14. `src/platform/ai/evaluation.py`
15. `src/platform/ai/promotion.py`
16. `src/platform/ai/monitoring.py`
17. `src/platform/ai/xai.py`
18. `src/api/ai_routes.py`
19. `tests/test_isi_25b_capability_runtime.py`
20. `tests/test_isi_25b_evaluation_engines.py`
21. `tests/test_isi_25b_promotion.py`
22. `tests/test_isi_25b_safety_retrieval.py`
23. `tests/test_isi_25b_monitoring_xai_help.py`
24. `tests/test_isi_25b_governance_contract.py`
25. `tests/test_isi_25a_model_registry.py`
26. `tests/test_isi_25a_api_contract.py`
27. `tests/test_isi_25a_governance_contract.py`

### Owner-approved Final Human Review recovery overlay — effective final acceptance surface 28 paths

Final Human Review recovery found one historical Help/XAI compatibility test whose accepted ISI-24D expectation had to be aligned with the ISI-25 shared AI Help/XAI ownership already implemented inside the original 27-path feature scope:

28. `tests/test_isi_24d_help_xai_contract.py`

This is the sole owner-approved validation-alignment addition. The effective ISI-25B final acceptance surface is therefore the original 27 implementation paths plus this one historical compatibility-test path: exactly 28 repository paths. No 29th path is authorized.

The recovery governance test must be valid both for the reviewed unstaged candidate and for the later clean committed checkout. It may verify the static exact-28 partition and frozen recovery bytes, but it must not require `git status` itself to remain dirty after acceptance commit.

### Frozen outside the effective final acceptance 28 paths

In particular, these are immutable:

- `.github/workflows/**`;
- `AGENTS.md`;
- access/RBAC catalog/model/service files and permission taxonomy;
- `docs/roadmap/ISI-AI-MODEL-EVALUATION-PROTOCOL-v1.md`;
- accepted `migrations/versions/20260917_0033_ai_mlops_governance_evaluation_foundation.py`;
- `tests/evals/SIMPA-EVAL-v1.json` and `tests/evals/ORDO-EVAL-v1.json`;
- provider/gateway files;
- worker/RQ files;
- dependency/requirements/lock files;
- Docker/deployment/server/Caddy/SMTP/secrets/data/model-installation files;
- SIMPA/ORDO domain numerical runtime files, including accepted ORDO forecast implementation;
- production/server state.

No 29th repository path is authorized for ISI-25B final acceptance. Any further path requirement is a hard STOP and requires a new explicit owner scope decision.

## Implementation authority

Exactly one implementation-model invocation is authorized:

`codex-isi --ask-for-approval never exec --sandbox workspace-write ...`

Generic `codex` is forbidden. The outer runner installs this canonical contract byte-for-byte before Codex executes and owns all final acceptance after Codex exits.

Codex may run focused tests while implementing, but must not run the repository-wide full suite. The outer runner owns exactly one final full `pytest` regression.

Codex must not stage, commit, push, dispatch/enable GitHub Actions, create branches/worktrees, deploy, touch the server, install models, mutate production secrets/data, or broaden the owner-approved effective 28-path final acceptance surface.

## Hard architecture boundaries

### GitHub / CI cost boundary

- workflow remains `workflow_dispatch` only;
- remote workflow remains disabled during 25B development;
- no `push`, PR, schedule, workflow_run or merge_group trigger;
- no hosted Actions run in 25B;
- commit/push, when later separately owner-approved after human review, remains separate from hosted CI authorization;
- hosted final RC acceptance is reserved for ISI-27.

### Server / deployment boundary

No SSH, SCP, rsync, DNS, Caddy/ingress, SMTP, production DB/data/object storage, production secrets, server Ollama, Docker deployment or service mutation. Server remains frozen through ISI-27. ISI-28 is the only deployment phase.

### Domain and methodology boundary

- SIMPA and ORDO remain the only products.
- MLOps never becomes SIMPA or ORDO numerical/methodology authority.
- Sensitive SIMPA remains local-only.
- No citizen-level scoring, eligibility, institutional decision automation, unapproved LISI formula/weight/threshold, or policy conclusion.
- Preserve ORDO: scenario != forecast; `forecast_performed=false`; scenario `NOT_ESTIMATED` + `NO_APPROVED_RESPONSE_MODEL` is intentional unestimation, never zero/failure; `LEGACY_NOT_EVALUATED` remains historical truth; forecast ESTIMATED remains accepted deterministic runtime only; no automatic forecast-family selection/fallback; no scenario impact auto-estimation; no causal/policy/ranking claims.
- No generic confidence, probability, feature importance, SHAP/attribution, calibration or uncertainty claim unless a specific evaluator/result actually supports its semantics.
- No online learning, self-training, silent model replacement or silent rollback.

## Required implementation

### 1. Canonical 25A acceptance bookkeeping + 25B activation

Update `automation/STATUS.md`, `automation/tasks.json`, MasterPlan and ISI-25 docs so repository truth is explicit:

- ISI-25A accepted main SHA `{BASELINE_SHA}`;
- accepted tree `{BASELINE_TREE}`;
- 25A local deterministic acceptance + assistant human review completed;
- no hosted GitHub acceptance was run for 25A under current owner policy; do NOT label it `CI_VERIFIED`;
- ISI-25B is the active implementation checkpoint;
- overall ISI-25 remains `IN PROGRESS` until 25B acceptance;
- server remains `DEFERRED_SERVER_VERIFICATION` / frozen;
- ISI-26 remains next only after 25B acceptance.

Historical accepted 25A implementation behavior remains traceable and must not be rewritten as if 25B existed in that checkpoint.

### 2. Additive Alembic 0034 runtime/evaluation/promotion layer

Create exactly `migrations/versions/20260918_0034_ai_evaluation_promotion_runtime.py` with:

- `revision = "20260918_0034"`;
- `down_revision = "20260917_0033"`;
- one additive/reversible schema evolution;
- no seed of a champion, no model installation, no production data mutation.

Required schema capabilities:

#### 2.1 AIJob / AIJobAttempt binding

Add nullable backward-compatible fields so a job may be explicitly bound to a governance registration and each attempt/fallback is auditable:

- `core_ai_jobs.model_registration_id` -> `core_ai_model_registrations.id` (nullable for legacy selected-only jobs);
- `core_ai_job_attempts.model_registration_id` -> registration identity (nullable only for legacy attempts);
- `core_ai_job_attempts.fallback_edge_id` -> `core_ai_model_fallbacks.id` (nullable);
- `core_ai_job_attempts.is_fallback` boolean, default false;
- enough persisted evidence to establish whether successful fallback output requires human review. This may be a dedicated boolean column or an equivalent immutable/auditable field, but it must not be inferred only from current mutable edge state after execution.

Do not rewrite historical jobs/attempts to guess a registration.

#### 2.2 Promotion-grade benchmark registry

Preserve `core_ai_evaluation_datasets` and the two v1 foundation fixtures unchanged in meaning.

Add `core_ai_evaluation_benchmarks` / `AIEvaluationBenchmark` as a separate frozen benchmark authority for promotion evidence. It must persist at least:

- dataset key/version;
- product code;
- capability key;
- model family;
- schema version;
- case count;
- deterministic cases SHA-256;
- immutable manifest fingerprint;
- source provenance;
- sensitivity class;
- methodology version where applicable;
- frozen/approved state and owner;
- full manifest JSON;
- actor/timestamps.

Cases must have stable IDs and the metadata required by the canonical evaluation protocol. Changed content under the same key/version is forbidden; a new version is required.

Add nullable `benchmark_id` to `core_ai_evaluation_runs`. Foundation runs may keep `benchmark_id=NULL`; promotion eligibility requires a frozen approved benchmark. Existing `dataset_id` semantics remain intact and may continue to identify the 25A contract/fixture foundation.

#### 2.3 Capability threshold profiles

Add `core_ai_capability_thresholds` / `AICapabilityThreshold` with immutable/versioned identity for:

- product scope + capability key + model family;
- version;
- required metric definitions and directions;
- minimum absolute thresholds;
- minimum challenger-vs-baseline deltas where applicable;
- safety/provenance/structured-output hard gates;
- latency/resource limits where applicable;
- circuit-breaker policy (`failure_threshold`, `cooldown_seconds`) or equivalent explicit versioned runtime policy;
- fingerprint, enabled state, provenance, actor/timestamps.

There is no generic weighted winner score. Safety/privacy/provenance blockers are non-compensable.

#### 2.4 Promotion decisions

Add `core_ai_promotion_decisions` / `AIPromotionDecision` with immutable decision evidence including:

- product/capability/family;
- challenger/candidate registration;
- baseline registration;
- candidate and baseline evaluation runs;
- benchmark identity;
- threshold profile identity;
- rollback registration;
- deterministic comparison/result evidence and fingerprint;
- decision status and blocker reasons;
- final authorized review evidence;
- explicit owner-approval reference when execution would materially change the governed champion;
- actor/timestamps.

A promotion record must never claim deployment/server activation.

#### 2.5 Capability runtime / circuit state

Add `core_ai_capability_runtime_states` / `AICapabilityRuntimeState` with one deterministic runtime state per product scope/capability, including:

- current champion registration (nullable until a promotion is executed);
- rollback registration;
- circuit state: `closed`, `open`, `half_open`;
- consecutive failure count;
- configured failure threshold and cooldown copied from approved runtime policy/threshold profile;
- opened/last failure/last success timestamps;
- version/audit identity and actor where applicable.

No state may silently install/enable a provider model.

#### 2.6 Drift snapshots

Add `core_ai_drift_snapshots` / `AIDriftSnapshot` with scoped capability/registration/time-window identity, deterministic metrics JSON/fingerprint and bounded status such as `ok`, `warning`, `blocker`, `insufficient_evidence`.

No application-owned scheduler is introduced. Drift collection/evaluation is explicit/on-demand or uses already existing job infrastructure without adding a new worker/scheduler path.

### 3. Capability/registration-bound AI runtime

Extend current AI job request/response schemas and service without breaking legacy callers.

#### 3.1 Backward compatibility

If no governance registration is explicitly bound, current accepted 25A behavior remains: selected/default model only, no cross-model scan, no registered fallback activation.

#### 3.2 Bound execution

An explicitly bound request must identify one exact `AIModelRegistration` (e.g. `model_registration_id`) and may not infer “the first” registration for a runtime model. The registration must:

- be enabled and non-retired;
- be visible to the product;
- have a provider-backed runtime model for LLM/VLM/embedding execution;
- match the requested/selected runtime identity if both are supplied;
- establish one unambiguous capability key and family.

Persist the registration on the job and attempt.

#### 3.3 Executable fallback rules

For a bound job only, registered cross-model fallback may be attempted after a qualifying failure and only when all are true:

- source registration is the exact bound registration;
- edge is registered and ordered by deterministic priority;
- source/target capability and family are identical and product scope is compatible;
- target is enabled/non-retired and has an enabled compatible runtime;
- error code matches edge trigger (`*` may be supported explicitly);
- `semantically_equivalent=true` for automatic fallback;
- existing provider/data policy allows the target;
- sensitive SIMPA cannot escape local-only policy;
- circuit policy allows the attempt;
- every attempt records registration and fallback edge evidence.

`semantically_equivalent=false` may remain visible governance evidence but is not automatically executable.

If a successful edge has `requires_human_review=true`, the job must finish in a bounded review-required state with `human_review_status=pending`; do not present it as ordinary final success.

Remove or stop using any 25A helper behavior that picks a source registration by `runtime_model_id` plus first-created ordering. New runtime helpers must take the exact source registration identity.

#### 3.4 Circuit breaker

Circuit breaker is deterministic and capability-bound:

- qualifying failures increment persisted state;
- reaching the approved failure threshold opens the circuit;
- open circuit prevents repeated direct use until cooldown/explicit reset semantics allow `half_open` probe;
- successful probe/request closes circuit and resets failures;
- circuit state may permit an otherwise valid registered fallback if trigger/policy/semantic gates also permit it;
- circuit state must never arbitrarily choose another enabled model;
- no background scheduler is introduced.

Tests must control time deterministically; no flaky sleeps.

### 4. Promotion-grade benchmark contract

Implement validation/registration for promotion benchmarks separately from foundation fixtures.

Minimum benchmark case metadata follows the canonical evaluation protocol and must include stable `case_id`, product/domain, capability, language, input/evidence version, expected contract/gold reference, source refs, sensitivity, methodology version/human-gold state where applicable, and notes.

A benchmark must be:

- frozen;
- approved;
- versioned and hash-addressed;
- immutable under its key/version;
- product/capability/family scoped;
- free of embedded secrets;
- privacy/sensitivity classified.

Do not create or claim a production-quality SIMPA/ORDO gold benchmark in this task unless such evidence already exists in repository truth. The implementation provides the governed mechanism and synthetic deterministic tests; it must not fabricate human-approved gold labels.

### 5. Deterministic evaluator engines

Implement actual deterministic evaluator functions in `src/platform/ai/evaluation.py`. They evaluate explicit expected/gold/evidence and actual model/runtime outputs; they do not use an LLM judge as hidden authority.

#### 5.1 Shared result contract

Each evaluator returns/persists typed metric/safety/provenance/evidence rows with:

- metric key;
- value and denominator/support where meaningful;
- direction/interpretation metadata;
- unavailable/not-applicable state instead of fabricated values;
- source/evidence/case references;
- deterministic fingerprint.

#### 5.2 Statistical/ML metrics

Provide dependency-free deterministic primitives appropriate to explicit inputs, including where relevant:

- MAE;
- RMSE;
- optional bias;
- precision/recall/F1;
- Brier score;
- enough typed evidence to compare a challenger with a registered baseline.

Do not recompute or override accepted SIMPA/ORDO domain methodology; evaluators consume explicit gold/prediction arrays/evidence supplied by a benchmark/run.

#### 5.3 Embedding/RAG metrics

Implement at least:

- Recall@k;
- MRR;
- nDCG@k;
- optional precision@k/context evidence where explicitly supplied;
- namespace-isolation pass/fail evidence.

Mandatory negative evaluation supports:

- SIMPA private query must not retrieve ORDO private context;
- ORDO private query must not retrieve SIMPA private context;
- organization A must not retrieve organization B private context;
- public/private namespace boundaries remain enforced.

Do not weaken existing namespace enforcement.

#### 5.4 LLM metrics

Implement deterministic evaluation of explicit adjudication/evidence for:

- grounded factuality / supported atomic claims;
- hallucination/unsupported claim rate;
- structured-output parse/schema/required-field/enum compliance where schema is supplied;
- provenance/source-reference compliance;
- instruction/refusal contract;
- latency/token/resource/failure evidence;
- Serbian-language quality through an explicit authorized human rubric/evidence input when deterministic language scoring is not justified.

Do not invent a “Serbian quality AI score.” Human rubric values are validated, preserved and aggregated transparently.

#### 5.5 VLM/document metrics

Implement deterministic primitives for supplied gold/extracted structures, such as normalized field accuracy, numeric transcription accuracy and structured-output/provenance status. OCR/table/chart metrics may be unavailable unless sufficient expected evidence exists.

There is no requirement to install or invoke a VLM on the server. If no registered executable VLM/evidence is available, surface bounded `unavailable` / `insufficient_evidence`, never a fake score.

#### 5.6 Adversarial/safety evidence

Support explicit case outcomes for:

- missing/contradictory/stale evidence;
- prompt injection / instructions embedded in retrieved content;
- PII/sensitivity boundary;
- cross-product/cross-tenant attempts;
- unsupported causal conclusions;
- unsupported forecasts/scenario impacts;
- fabricated score/threshold requests;
- human-review bypass attempts.

Safety blocker evidence is non-compensable in promotion logic.

### 6. Deterministic comparison and promotion criteria

Implement comparison without a generic ranking score.

A challenger can be promotion-eligible only if:

1. both candidate and baseline registrations match capability/family/product scope;
2. both evaluation runs are terminal `completed` and reference the same frozen approved promotion benchmark;
3. required prompt/policy/methodology identities are compatible according to the threshold contract;
4. every required metric exists with acceptable evidence state;
5. absolute thresholds pass;
6. required challenger-vs-baseline minimum deltas pass in the configured direction;
7. structured-output/provenance/safety/privacy gates pass;
8. latency/resource gates pass when required;
9. candidate has final authorized `approved` evaluation review evidence;
10. rollback registration is compatible, enabled and explicitly recorded;
11. explicit owner-approval reference is present when executing promotion;
12. no unresolved blocker remains.

Improvement in one metric can never offset a safety/privacy/provenance blocker.

No source code may preselect a model family/name as champion or encode an eternal winner.

### 7. Evidence-gated champion promotion

Implement promotion service in `src/platform/ai/promotion.py` and bounded API under existing `/api/v1/ai` boundary.

Promotion mutation must require:

- normal organization/product/workspace scope resolution;
- platform-admin authority for global registry mutation;
- existing `report.publish` sign-off permission;
- explicit promotion decision/evidence satisfying section 6.

Execution is an atomic DB governance transaction:

- candidate becomes `champion`;
- any current champion for the same product-scope/capability becomes a non-champion compatible lifecycle state (prefer `challenger`, not silent retirement unless explicitly intended);
- capability runtime state pins champion + rollback registration + approved circuit policy;
- immutable audit/promotion evidence is persisted.

Promotion does NOT install a model, modify Ollama, change server configuration, deploy code, change DNS, or silently rewrite the legacy default runtime model.

Enforce at most one enabled champion per exact product-scope/capability through DB/service invariants where safely possible.

### 8. Governed rollback

Rollback is explicit and auditable, not silent.

A rollback operation may restore the registered compatible rollback registration only when:

- runtime state has a valid rollback target;
- target is enabled/non-retired and same capability/family/product scope;
- actor has the same strong promotion authority;
- reason/evidence reference is supplied;
- audit + promotion/runtime state is updated atomically.

Rollback changes registry/runtime governance state only. It does not install software/models or mutate the server.

Prompt rollback execution is not required unless it can be safely implemented inside the original 27 implementation paths without conflating model and prompt lifecycle; prompt rollback identity from 25A must remain preserved and visible.

### 9. Drift monitoring and operational read model

Implement `src/platform/ai/monitoring.py` without scheduler/dependency additions.

Required behavior:

- create deterministic drift snapshots from explicit observed/reference metric windows;
- classify `ok`, `warning`, `blocker`, `insufficient_evidence` using versioned capability threshold/runtime policy evidence;
- persist fingerprints/provenance;
- expose read-only capability status containing champion/challenger identities, latest evaluation evidence, promotion/rollback state, circuit state, latest drift status, fallback availability and human-review requirements;
- drift/circuit evidence may block promotion or runtime use according to explicit policy, but never triggers online training or silent replacement.

### 10. Shared AI XAI / interpretation contract

Implement `src/platform/ai/xai.py` as a deterministic presentation/read-model helper, not a second AI model.

For a governed AI/evaluation result it must expose where available:

- product/capability/model registration identity and version/fingerprint;
- lifecycle/champion state;
- prompt/policy identity;
- benchmark/evaluation run/result fingerprints;
- governed evidence/source provenance;
- structured-output validation state;
- metric interpretation with explicit direction/support;
- fallback edge/attempt and review-required state;
- circuit/drift state;
- final human review evidence;
- rollback identity;
- distinction between deterministic numerical authority and generative synthesis.

For unsupported feature importance, SHAP/attribution, probability/confidence, calibration or uncertainty, return explicit `unavailable`/not-applicable text/state rather than inventing data.

### 11. API boundaries

Extend only `src/api/ai_routes.py`; do not create a parallel API stack.

Provide bounded endpoints/read models for:

- promotion benchmark registration/listing;
- threshold profile registration/listing;
- deterministic evaluation execution/evidence append over scoped runs;
- comparison/promotion eligibility preview;
- explicit promotion execution;
- explicit rollback execution;
- capability runtime/circuit state inspection and bounded reset/probe authority if needed;
- drift snapshot creation/listing;
- governance/evaluation/XAI status read model.

Permissions must use existing taxonomy only:

- ordinary AI execution: `ai.run`;
- evaluation execution/evidence: `analysis.run`;
- inspection/read model: `analysis.read`;
- final review/sign-off: `report.publish`;
- global benchmark/threshold/promotion/rollback governance mutation: platform admin after normal scope resolution, with `report.publish` additionally required for promotion/rollback execution.

Do not add `ai.manage` or any new permission.

### 12. Help / User Guide / coverage matrix

Create `docs/help/ISI-AI-USER-GUIDE.md` and update the Help Coverage Matrix for ISI-25-owned shared AI actions.

The guide must satisfy MasterPlan 0.5A for material actions, including:

- what registry/evaluation/promotion/fallback/circuit/drift functions do;
- when each is used;
- roles/permissions;
- exact conceptual workflow;
- meaning of lifecycle states, benchmark/run/result/review states, circuit/drift states and review-required fallback;
- synthetic example(s);
- non-goals and explicit absence of automatic deployment/online learning;
- common failure/blocker states and recovery;
- privacy/security/methodology limitations;
- model/prompt/policy/benchmark/evidence/provenance/fingerprint/human-review interpretation;
- unsupported XAI shown as unavailable.

Close the ISI-25-owned AI evaluation/provenance/promotion/fallback interpretation portion of INV-A09, INV-A18/INV-A19 shared-AI guidance and INV-A21. Do not falsely claim Login/Reporting/Admin/Security/shared release Help owned by ISI-27 is complete.

### 13. Historical 25A test convergence

The following accepted 25A tests are in the mutable surface only because they currently assert mutable current-global behavior that 25B intentionally supersedes:

- `tests/test_isi_25a_model_registry.py`;
- `tests/test_isi_25a_api_contract.py`;
- `tests/test_isi_25a_governance_contract.py`.

Rewrite only the assertions necessary so they test the historical 25A contract/foundation rather than forbidding 25B forever. Preserve all immutable 25A truths: foundation fixtures, 0033 identity, 25A selected-only historical boundary, platform-admin authority, ORDO locks, no production deployment in 25A.

Do not weaken tests merely to get green. Add 25B tests for the new current behavior.

## Exact new 25B tests

Create exactly these six test files:

1. `tests/test_isi_25b_capability_runtime.py`
2. `tests/test_isi_25b_evaluation_engines.py`
3. `tests/test_isi_25b_promotion.py`
4. `tests/test_isi_25b_safety_retrieval.py`
5. `tests/test_isi_25b_monitoring_xai_help.py`
6. `tests/test_isi_25b_governance_contract.py`

### Required test coverage

#### Capability runtime

- legacy no-registration job remains selected-only;
- bound job persists exact registration;
- same runtime model registered for two capabilities cannot create ambiguity because source registration is explicit;
- unregistered enabled models are never scanned;
- only matching trigger executes fallback;
- semantic-equivalence false blocks automatic fallback;
- policy/local-only blocks target;
- sensitive SIMPA external fallback blocked;
- requires-human-review edge yields review-required/pending outcome;
- attempt audit pins source/target registration and edge;
- circuit open/half-open/close behavior deterministic without sleeps.

#### Evaluation engines

- MAE/RMSE/bias deterministic;
- classification precision/recall/F1/Brier deterministic;
- Recall@k/MRR/nDCG deterministic with zero/empty edge cases bounded;
- factuality/hallucination support accounting;
- structured-output validity;
- provenance compliance;
- human Serbian rubric transparent and bounded;
- VLM normalized field/numeric accuracy plus unavailable behavior;
- latency/resource evidence typed, not a quality substitute.

#### Promotion

- benchmark immutability/new-version requirement;
- foundation v1 datasets cannot satisfy promotion benchmark requirement;
- same benchmark/capability/family required;
- missing metric fails closed;
- absolute threshold failure blocks;
- minimum delta failure blocks;
- safety/provenance blocker is non-compensable;
- approved final review required;
- rollback required;
- owner approval reference required;
- no generic winner score;
- atomic champion transition and one-champion invariant;
- no server/model installation side effect;
- explicit rollback restores governed state and audits it.

#### Safety/retrieval

- cross-product private retrieval negative case;
- cross-tenant private retrieval negative case;
- public/private isolation;
- prompt injection/unsafe context evidence blocker;
- PII/sensitivity blocker;
- unsupported causal/forecast/scenario-impact/human-review-bypass evidence blocker;
- ORDO forecast-family runtime remains untouched/no MLOps fallback route.

#### Monitoring/XAI/Help

- drift statuses deterministic and fingerprinted;
- no scheduler/online learning/silent replacement path;
- read model exposes provenance/lifecycle/review/fallback/circuit/drift/rollback;
- unsupported confidence/calibration/feature importance/SHAP explicitly unavailable;
- AI User Guide and Help matrix contain the mandatory coverage semantics without overclaiming ISI-27-owned areas.

#### Governance contract

- exact 0034/down_revision;
- accepted 25A SHA/tree and no `CI_VERIFIED` false claim;
- manual-only workflow preserved;
- no new permission taxonomy;
- no dependency/provider/worker/server changes;
- 25B current, ISI-25 IN PROGRESS until acceptance;
- evaluation protocol file unchanged;
- v1 foundation fixture semantics unchanged;
- ORDO 24C/24E semantics preserved.

## Focused compatibility tests owned by outer runner

Outer runner will run new 25B tests plus:

- all four `tests/test_isi_25a_*.py` files;
- `tests/test_isi_07_models_contract.py`;
- `tests/test_isi_07_policy.py` if present;
- `tests/test_isi_24e_closeout_contract.py`;
- `tests/test_isi_24e_forecast_workflow_api.py`;
- `tests/test_isi_24e_forecast_workflow_ui.py`.

## Acceptance sequence owned by outer runner

1. package selftest;
2. exact baseline / origin / one-worktree / clean-index preflight;
3. read-only GitHub workflow state = `disabled_manually` and zero runs for baseline SHA;
4. pre-head `{PRE_HEAD}`;
5. current policy check;
6. install this canonical spec byte-for-byte;
7. exactly one `codex-isi` implementation invocation;
8. independent exact-28 final-acceptance structural/semantic analyzer;
9. sole Alembic head `{POST_HEAD}` + offline migration validation;
10. focused 25B + compatibility tests;
11. compile/Ruff/mypy/pip/policy/diff quality;
12. local native PostgreSQL 17 acceptance including existing recovery rehearsal;
13. fail-closed cleanup of only proven untracked `test-results/native-postgres/**` harness output;
14. exactly one final full local `pytest -q -p no:cacheprovider`;
15. final independent analyzer and candidate fingerprint;
16. final guard: HEAD/origin remain `{BASELINE_SHA}`, index empty, exact 28 final-acceptance candidate surface locked, workflow untouched, server untouched.

No staging, commit or push is authorized by this runner. A passing candidate goes to assistant human review and then requires separate owner approval for exact-file commit/push.

## Non-goals / forbidden outcomes

- no automatic hosted CI;
- no GitHub workflow enable/dispatch;
- no branch/PR/worktree;
- no server/deployment action;
- no dependency additions/upgrades;
- no provider/gateway rewrite;
- no new worker/scheduler;
- no model download/install;
- no hard-coded champion/winner;
- no automatic production champion without explicit promotion transaction/evidence;
- no online learning/self-training;
- no silent fallback/rollback/replacement;
- no external provider fallback for sensitive SIMPA;
- no ORDO forecast-family automatic selection/fallback;
- no scenario impact automation;
- no causal/policy/ranking claims;
- no fabricated confidence/calibration/feature importance/XAI;
- no retroactive conversion of `SIMPA-EVAL-v1` / `ORDO-EVAL-v1` into promotion evidence;
- no `CI_VERIFIED` claim for 25A/25B without an actual hosted acceptance run.

## Completion definition

A candidate is ready for final human review only when the outer runner prints all of:

```text
ISI25B_EXACT_28_CANDIDATE_SURFACE=PASS
ALEMBIC_0034_SINGLE_HEAD=PASS
NATIVE_POSTGRES_LOCAL_ACCEPTANCE=PASS
FULL_LOCAL_REGRESSION=PASS
CANDIDATE_FINGERPRINT_STABLE=PASS
CODEX_EXECUTED=YES_VIA_CODEX_ISI
STAGE_COMMIT_PUSH=NO
GITHUB_ACTIONS_DISPATCH=NO
SERVER_MUTATION=NO
ISI25_GLOBAL_STATE=IN_PROGRESS_25B_CANDIDATE
READY_FOR_ISI25B_FINAL_HUMAN_REVIEW=PASS
```

Passing this runner is not commit authorization and is not production/deployment authorization.
