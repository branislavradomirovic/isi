# ISI-25A — AI/MLOps Governance + Evaluation Foundation

## Status

Owner-approved macro-slice for implementation, including the consolidated R4 human-review remediation. This is one indivisible ISI-25A implementation slice, not a collection of microtasks. ISI-25 remains globally IN PROGRESS after this slice because ISI-25B is still required. GitHub-hosted CI is intentionally not part of ISI-25A development acceptance.

Owner approval phrase already granted for scope design:

`ODOBRENO ISI-25A AI/MLOPS GOVERNANCE + EVALUATION FOUNDATION SCOPE`

Implementation becomes an accepted main checkpoint only after deterministic local validation, assistant human review, and a separate owner-approved exact-candidate commit/push. No GitHub Actions acceptance is expected until the controlled final RC checkpoint in ISI-27.

## Baseline

Exact implementation baseline:

- repository: `branislavradomirovic/isi`
- branch: `main`
- HEAD: `7e4db145c285aaff7a96f9c37279c44477f4432f`
- tree: `ae6dd9913a842ffdf548a90c48e53074f7914546`
- origin/main: same exact SHA before implementation
- Alembic sole head before implementation: `20260916_0032`
- expected new Alembic sole head after implementation: `20260917_0033`
- pre-implementation worktree: clean, unstaged, no untracked files

Any baseline mismatch is STOP, not an invitation to rebase, merge, reset, stash, clean, amend or improvise.

## Canonical bootstrap evidence

Before editing, implementation authority must read completely:

1. `AGENTS.md`
2. `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
3. `docs/roadmap/ISI-AI-MODEL-EVALUATION-PROTOCOL-v1.md`
4. `automation/specs/ISI-24E-ORDO-FINAL-CLOSEOUT.md`
5. existing `src/platform/ai/**`
6. existing `src/api/ai_routes.py`
7. current access/RBAC catalog
8. current Alembic chain through `20260916_0032`

The full MasterPlan, AGENTS and accepted as-built code outrank assumptions in this task. If the exact baseline reveals a contradiction that cannot be resolved inside the frozen mutable surface while preserving the locked boundaries below, STOP and report the contradiction.

## Dependencies

Depends on accepted ISI-17 through ISI-24 and the current manual-only CI governance already present on `main`.

Uses the existing shared AI provider/gateway/job/attempt/audit/embedding/namespace/policy architecture. This slice MUST extend it; it MUST NOT create a parallel AI platform.

## Objective

Implement the complete ISI-25A foundation in one macro-slice:

- unified capability/model governance registry across statistical/ML, embedding, LLM and VLM capabilities;
- immutable/versioned model identity and provenance;
- candidate/challenger/champion/retired lifecycle vocabulary without authorizing 25B promotion;
- explicit persisted fallback relationships as foundation evidence, with no heuristic or registered cross-model runtime fallback activation in 25A;
- prompt rollback identity layered on the existing prompt/version registry;
- frozen/versioned `SIMPA-EVAL-v1` and `ORDO-EVAL-v1` evaluation dataset contracts using non-production fixture content;
- persisted evaluation dataset/run/result/review/provenance foundation for the evaluators implemented later in 25B;
- human-review evidence;
- controlled API inspection/mutation using existing permissions;
- additive PostgreSQL migration and regression coverage;
- canonical documentation/status/inventory updates that keep global ISI-25 IN PROGRESS and 25B pending.

## Existing architecture

Preserve and extend, rather than replace:

- `src/platform/ai/models.py` — existing AIModel/AIPrompt/AIPromptVersion/AIPolicyProfile/AIJob/AIJobAttempt/AIAuditEvent/AIEmbedding persistence;
- `src/platform/ai/gateway.py` and `providers.py` — single provider invocation boundary;
- `src/platform/ai/policy.py` — provider/data policy and sensitive SIMPA local-only rules;
- `src/platform/ai/service.py` — current job creation, provider candidate handling and execution integration;
- `src/platform/ai/namespaces.py` and embeddings — tenant/product/private namespace isolation;
- `src/api/ai_routes.py` — current scoped AI API;
- central RBAC — existing permissions only. Do not add a new `ai.manage` permission in 25A.

The existing runtime AIModel remains the provider/runtime configuration entity. The MLOps governance layer may add capability/model-registration entities that reference existing AIModel where appropriate and also represent deterministic/statistical artifacts that do not use a provider gateway.

## Canonical system inventory impact

Update the MasterPlan SYSTEM INVENTORY to describe the actual 25A as-built foundation without rewriting unrelated historical rows. The resulting inventory must make these truths explicit:

- the provider gateway remains the single provider boundary;
- the existing runtime AI model/prompt/policy registry remains part of the shared AI substrate;
- the 25A capability/model governance registry is the authority for lifecycle identity and persisted fallback relations, while cross-model runtime activation remains deferred to 25B;
- evaluation dataset/run/result/review entities are current as-built foundation after this slice;
- `SIMPA-EVAL-v1` and `ORDO-EVAL-v1` are frozen evaluation CONTRACT/FIXTURE baselines, not proof of production quality;
- promotion winner selection, evaluator engines, circuit breaker, drift jobs and dashboards remain 25B;
- dedicated Vision and Audio services remain NOT_PRESENT;
- no production model promotion occurs in 25A.

Prefer additive inventory rows after current C39 and/or precise updates to E05/E06 rather than repurposing unrelated inventory IDs.

## Legacy/drift audit

Treat these as existing assets to preserve:

- current AIModel provider configuration;
- current prompt/version records and checksum semantics;
- current policy profiles and sensitive SIMPA local-only restrictions;
- current AI job/attempt/audit trail;
- current embedding provenance and namespace isolation;
- current ORDO 24C/24E semantics.

Known drift to resolve in 25A:

1. existing fallback candidate scanning was policy-constrained but not capability-registry-governed; 25A removes all cross-model runtime scanning because `AIJob` lacks an unambiguous capability/registration binding;
2. current AI registry lacks formal capability/family/version/fingerprint lifecycle evidence across statistical/ML, embedding, LLM and VLM;
3. prompt versions lack explicit governed rollback-target identity;
4. no canonical persisted evaluation dataset/run/result/review foundation exists;
5. no frozen `SIMPA-EVAL-v1` / `ORDO-EVAL-v1` contract artifacts exist.

Do not interpret those findings as permission to rewrite the provider, queue, worker, domain analytics or embedding subsystems.

## Exact mutable surface

### FROZEN 19 paths

Exactly these 19 repository paths may differ from the baseline after the Codex implementation. No other repository path may be created, modified, renamed or deleted.

1. `automation/STATUS.md`
2. `automation/tasks.json`
3. `automation/specs/ISI-25A-AI-MLOPS-GOVERNANCE-EVALUATION-FOUNDATION.md`
4. `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
5. `docs/roadmap/ISI-25-MODEL-REGISTRY.md`
6. `docs/roadmap/ISI-25-PROMOTION-POLICY.md`
7. `migrations/versions/20260917_0033_ai_mlops_governance_evaluation_foundation.py`
8. `src/platform/ai/models.py`
9. `src/platform/ai/schemas.py`
10. `src/platform/ai/service.py`
11. `src/platform/ai/governance.py`
12. `src/platform/ai/evaluation.py`
13. `src/api/ai_routes.py`
14. `tests/evals/SIMPA-EVAL-v1.json`
15. `tests/evals/ORDO-EVAL-v1.json`
16. `tests/test_isi_25a_model_registry.py`
17. `tests/test_isi_25a_eval_foundation.py`
18. `tests/test_isi_25a_api_contract.py`
19. `tests/test_isi_25a_governance_contract.py`

All 19 paths must be present in the final dirty surface. Existing paths must be meaningfully updated for the 25A contract; new paths must be created. If implementation would require a 20th path, STOP rather than expanding scope.

For the R4 remediation pass, only these 11 paths may change relative to the exact R3 preimage: `automation/STATUS.md`, `automation/tasks.json`, this specification, the MasterPlan, both ISI-25 roadmap documents, `src/api/ai_routes.py`, `src/platform/ai/service.py`, `tests/test_isi_25a_api_contract.py`, `tests/test_isi_25a_model_registry.py` and `tests/test_isi_25a_governance_contract.py`. The other eight R3 candidate paths remain byte-identical.

In particular, `.github/workflows/**`, `AGENTS.md`, access/RBAC catalog files, worker files, provider/gateway files, requirements/lock files, Docker/deployment files and all production/server artifacts are immutable in this slice.

## Implementation-tool authority

The original outer deterministic runner installed the 25A contract before the R3 implementation. The owner-authorized R4 pass explicitly permits this specification to be updated inside the locked 11-path remediation surface so it records the reviewed runtime and authority truth. No path outside that surface may be changed.

Generic `codex` is forbidden. The runner invokes:

`codex-isi --ask-for-approval never exec --sandbox workspace-write ...`

Codex must not stage, commit, push, invoke GitHub Actions, mutate server state or broaden the mutable surface. The outer deterministic runner owns validation after Codex exits.

## Locked boundaries

### One macro-slice, no microtasks

Implement the entire 25A scope in one Codex execution. Do not split registry, migration, prompt governance, eval manifests or tests into separately approved tasks/checkpoints.

### GitHub cost boundary

- no `gh workflow run`;
- no GitHub Actions dispatch;
- no automatic hosted CI trigger additions;
- `.github/workflows/ci.yml` is immutable and must remain manual `workflow_dispatch` only;
- no push/PR/schedule/workflow_run/merge_group trigger may be introduced.

### Server boundary

No SSH/SCP/rsync, DNS, ingress, SMTP, production secret, production data, production Ollama/model, container deployment or server mutation. Production remains frozen until explicit ISI-28.

### Product/domain boundary

ISI contains only SIMPA and ORDO. No COSMOS or new product/domain is introduced.

### ORDO 24C/24E semantic lock

Absolutely preserve:

- scenario != forecast;
- `forecast_performed=false` remains authoritative for scenario flow;
- scenario `NOT_ESTIMATED` + `NO_APPROVED_RESPONSE_MODEL` means intentionally unestimated impact, never zero/failure;
- `LEGACY_NOT_EVALUATED` remains historical compatibility truth;
- forecast `ESTIMATED` remains limited to accepted deterministic 24C runtime under exact validated specification/input;
- forecast `NOT_ESTIMATED` remains a successful bounded outcome;
- no automatic ORDO model selection;
- no ORDO fallback between forecast families;
- no scenario automatic impact estimation;
- no causal claim, policy recommendation, ranking/winner, generic confidence, feature importance or calibrated-probability invention;
- interval and backtest meanings remain unchanged.

The new MLOps registry MUST NOT silently become numerical/domain authority over accepted deterministic SIMPA/ORDO analytics.

## Required behavior

### 1. Capability/model governance registry

Add a shared governance layer inside `src/platform/ai/**` that can represent:

- `capability_key`;
- product scope: SHARED/SIMPA/ORDO;
- family/modality: at least `statistical_ml`, `embedding`, `llm`, `vlm`;
- model/artifact identity;
- optional reference to existing runtime `AIModel` for provider-backed capabilities;
- provider/runtime name where relevant;
- version/tag/revision;
- artifact/checksum identity where available;
- deterministic registry fingerprint;
- lifecycle vocabulary: `candidate`, `challenger`, `champion`, `retired`;
- enabled/disabled state;
- creation actor/timestamps/provenance.

Do NOT hard-code a permanent champion. Existing runtime models must not be silently backfilled as champion.

25A MUST NOT expose an executable promotion-to-champion operation. If the DB vocabulary includes `champion` for forward compatibility, service/API mutation to champion must fail closed with a stable reason indicating promotion belongs to 25B and requires evaluation/approval evidence.

Candidate/challenger registration and retirement are allowed where permissions and invariants are met.

### 2. Persisted fallback governance and selected-model-only runtime

Add explicit, persisted fallback relationships between compatible registered model/capability identities.

Required invariants:

- source and target must be valid registered identities;
- fallback cannot self-reference;
- fallback graph cannot contain cycles;
- fallback cannot cross product/capability boundaries unless the registry explicitly defines compatible SHARED scope and existing policy still permits it;
- fallback target cannot bypass sensitive/local-only policy;
- deterministic priority/order;
- no implicit fallback candidate may be used merely because another enabled model exists.

The fallback graph is 25A foundation evidence only. `src/platform/ai/service.py` must fail closed to the explicitly selected/default runtime model, subject to existing product/provider policy, even when a persisted edge exists. It must not call or otherwise wire `authorized_runtime_fallbacks` or `runtime_fallback_allows_error`, and it must not scan other enabled models. Existing selected-model attempt/failure/audit behavior remains intact.

An `AIJob` has no capability/registration binding, and one runtime model may validly have multiple capability registrations. Capability-bound registered fallback execution is therefore deferred to ISI-25B, which must bind execution to one unambiguous capability/registration and enforce trigger, semantic-equivalence and human-review edge declarations. In 25A, `semantically_equivalent` and `requires_human_review` are persisted contract metadata rather than executable gates. No route or runtime path claims a fallback edge is production-executable.

Do not implement 25B winner selection, automatic promotion, traffic splitting or circuit breaker here.

### 3. Prompt rollback identity

Preserve existing AIPrompt/AIPromptVersion semantics and checksums.

Add governed rollback-target identity so a prompt/version can reference an explicit prior target without rewriting old prompt versions. Required invariants:

- source and target versions belong to the same prompt;
- no self-target;
- target checksum/version identity remains immutable;
- rollback registration is audited/provenanced;
- no silent unversioned prompt update;
- registering a rollback target does not automatically execute a rollback or change active production behavior in 25A.

### 4. Frozen evaluation dataset contracts

Create exactly:

- `tests/evals/SIMPA-EVAL-v1.json`
- `tests/evals/ORDO-EVAL-v1.json`

They must be deterministic, UTF-8 JSON, non-production fixtures/contracts, with no secrets or personal data.

Each manifest/dataset must contain at least:

- dataset key;
- version;
- product code;
- schema version;
- capability/task coverage declaration;
- deterministic `cases_sha256`, computed as SHA-256 over UTF-8 JSON serialization of the `cases` array with `ensure_ascii=false`, sorted keys and compact separators `(",", ":")`;
- case count;
- source provenance description;
- sensitivity classification;
- frozen flag/timestamp or immutable version identity;
- owner/approval state;
- explicit `foundation_only_not_production_promotion_evidence` truth;
- a small deterministic synthetic case set sufficient to prove loader/persistence contracts, not to claim production model quality.

Persist corresponding dataset registry identities in PostgreSQL through the new evaluation foundation. Dataset content/version/hash becomes immutable once frozen/approved. Changed content requires a new dataset version.

### 5. Evaluation run/result persistence foundation

Add shared persistence/service contracts for future 25B evaluator engines.

Evaluation run identity must support at least:

- run UUID;
- dataset registry/version/hash identity;
- capability/model registration under test;
- optional baseline/champion reference, without implying a current champion exists;
- optional prompt-version identity;
- policy-profile identity where relevant;
- input/provenance fingerprint;
- environment/config fingerprint;
- started/completed timestamps;
- bounded status lifecycle;
- immutable terminal result fingerprint.

Result/evidence persistence must support future metric/safety/reliability/provenance records without calculating those metrics in 25A. A generic typed JSON evidence/result row is acceptable if it is deterministic, fingerprinted and immutable after terminal completion.

Do NOT implement nDCG/MRR/Recall scoring, factuality scoring, Serbian quality scoring, VLM scoring, adversarial scoring, drift calculation, automated promotion or winner ranking in 25A.

### 6. Human-review evidence

Persist human-review evidence for evaluation/promotion readiness foundation with at least:

- evaluation run identity;
- reviewer membership identity;
- bounded decision/status;
- timestamp;
- notes/evidence reference;
- immutable reviewer/decision trace once final.

No broad bypass/override flag. No review record may itself promote a model in 25A.

### 7. API/admin integration using existing permissions

Extend the existing `/api/v1/ai` boundary. Do not create a new router/subsystem unless impossible inside the frozen surface.

Use existing permissions only:

- privileged global/shared registry, fallback, prompt-rollback-target and dataset mutation: existing `User.is_platform_admin` authority after normal organization/product/workspace scope resolution; no new permission code;
- evaluation inspection, including review inspection: existing `analysis.read` and/or `audit.read` as appropriate;
- creating evaluation-run foundation records: existing `analysis.run` where appropriate;
- evaluation review writes: existing `report.publish` sign-off authority;
- ordinary AI execution remains `ai.run`.

Required API capabilities:

- inspect capability/model registrations;
- create candidate/challenger registration;
- retire registration;
- register/list fallback relationships;
- register/list prompt rollback targets;
- inspect/register frozen evaluation datasets;
- create/read evaluation-run foundation records;
- append/read deterministic result/evidence rows while run is mutable;
- complete/fail a run into immutable terminal state;
- append/read human review subject to rules.

No API endpoint may select a winner, promote to champion, change production deployment, activate a model on server, or execute domain forecasts/scenario impacts.

All routes must preserve tenant/product/workspace boundaries where those scopes apply and fail closed on unauthorized access.

### 8. Migration

Create one additive migration only:

`migrations/versions/20260917_0033_ai_mlops_governance_evaluation_foundation.py`

Requirements:

- `down_revision = "20260916_0032"`;
- one sole head after change: `20260917_0033`;
- PostgreSQL-compatible constraints/indexes/FKs;
- additive schema only except tightly scoped additive columns/constraints needed for prompt rollback/runtime registry integration;
- no destructive historical rewrite;
- no production data seed;
- no dependency upgrade;
- downgrade must reverse only 25A schema changes.

### 9. Documentation and state

`docs/roadmap/ISI-25-MODEL-REGISTRY.md` must document exact registry identity, lifecycle, fallback, prompt rollback, provenance and 25A/25B boundary.

`docs/roadmap/ISI-25-PROMOTION-POLICY.md` must document the future promotion gate, while stating promotion execution/winner selection is NOT IMPLEMENTED in 25A. It must require frozen eval evidence, safety/provenance, human review and rollback before 25B promotion can be considered.

Update MasterPlan inventory/current-state text precisely. Keep global ISI-25 IN PROGRESS and ISI-26/27/28 unchanged in sequence.

Update STATUS/tasks so ISI-25 is the active phase, 25A foundation is the current implementation checkpoint/candidate, 25B remains required next, and no GitHub acceptance claim is made.

## Impact

This slice establishes governance identities and persistence contracts. It must not alter accepted deterministic domain calculations, add new production provider infrastructure or declare any model production-ready.

The expected runtime behavior change is intentionally narrow: the explicitly selected/default model is the only 25A runtime candidate. Neither heuristic nor persisted-edge cross-model fallback executes. Existing provider/data policy and selected-model attempt/audit history remain authoritative; sensitive SIMPA local-only policy remains stricter.

## Security and privacy

- preserve SIMPA sensitive local-only behavior;
- no external provider enablement;
- no production data in eval fixtures;
- no PII/secrets in manifests or evidence fixtures;
- preserve tenant/product/workspace isolation;
- immutable hashes/fingerprints for registry/eval identities;
- reviewer membership references use existing membership model;
- no model/prompt/fallback relation may weaken provider/data policy;
- no server/model runtime mutation.

## Tests

Create the four new 25A test authorities in the frozen surface.

### `tests/test_isi_25a_model_registry.py`

Cover at minimum:

- capability/model registration identity/fingerprint;
- supported families;
- candidate/challenger/retired lifecycle;
- champion mutation forbidden in 25A;
- no hard-coded champion;
- persisted fallback graph invariants, with all cross-model runtime activation deferred;
- fallback self-reference/cycle/product/capability mismatch rejected;
- policy remains stricter than the selected model;
- no registered or unregistered model substitution;
- the same runtime model may have multiple capability registrations without 25A choosing one implicitly;
- existing AI attempt/audit semantics preserved;
- prompt rollback same-prompt requirement/no self-target/immutable identity.

### `tests/test_isi_25a_eval_foundation.py`

Cover at minimum:

- load/validate SIMPA-EVAL-v1 and ORDO-EVAL-v1;
- deterministic dataset hash/fingerprint;
- frozen dataset immutability;
- dataset version identity;
- evaluation run/result/evidence persistence;
- terminal run immutability;
- result fingerprint;
- human-review evidence and final-review immutability;
- no scoring/promotion side effect.

### `tests/test_isi_25a_api_contract.py`

Cover at minimum:

- permitted reads/mutations;
- platform-admin-only global governance/dataset mutation after normal scope resolution;
- review POST requires `report.publish` while GET inspection retains `analysis.read`;
- existing permission enforcement with no new taxonomy;
- cross-tenant/product denial;
- champion/promotion operation unavailable/forbidden;
- no deploy/server endpoint;
- fallback and prompt rollback API invariants;
- evaluation foundation API lifecycle.

### `tests/test_isi_25a_governance_contract.py`

Cover at minimum:

- exact documentation artifacts and phase boundary;
- SYSTEM INVENTORY truth;
- `SIMPA-EVAL-v1` / `ORDO-EVAL-v1` contract markers;
- no current permanent champion;
- 25B evaluator/promotion/circuit-breaker scope remains deferred;
- 24C/24E ORDO semantic markers remain intact;
- `.github/workflows/ci.yml` remains manual-only and unchanged from baseline content semantics;
- server/deployment boundary remains frozen.

Also run existing compatibility tests for shared AI, namespaces/policy and ORDO 24C/24E semantics.

## Exact acceptance commands

The outer package runner, not Codex, owns the final sequence:

1. package checksum + selftest;
2. exact clean-baseline preflight and `git fetch origin main` verification;
3. pre-implementation repository policy check;
4. one `codex-isi` implementation invocation for the complete 25A scope;
5. independent structural analyzer;
6. Alembic sole-head/offline migration validation;
7. focused 25A + AI + ORDO compatibility tests;
8. targeted Ruff plus E9 repository guard;
9. full mypy;
10. repository policy check;
11. `git diff --check`;
12. local isolated native PostgreSQL 17 acceptance via existing `tools/ci/native_postgres_tests.sh`;
13. one full local Python regression suite at the end;
14. final independent analyzer and deterministic candidate fingerprint.

No GitHub Actions are dispatched.

## Evidence

Required final runner evidence includes:

- baseline HEAD/tree/origin verification PASS;
- baseline/final Alembic head markers;
- exact 19-path final dirty surface;
- no staged files;
- no unexpected untracked files;
- manual-only CI policy preserved;
- 25A analyzer PASS;
- focused tests PASS;
- Ruff/mypy/policy/diff PASS;
- native PostgreSQL 17 acceptance PASS;
- full local regression PASS;
- stable deterministic candidate fingerprint;
- `CODEX_EXECUTED=YES_VIA_CODEX_ISI`;
- `STAGE_COMMIT_PUSH=NO`;
- `GITHUB_ACTIONS_DISPATCH=NO`;
- `SERVER_MUTATION=NO`;
- `READY_FOR_ISI25A_HUMAN_REVIEW=PASS`.

## Non-goals

Explicitly deferred to ISI-25B or later:

- nDCG/MRR/Recall evaluator implementation;
- statistical/ML scoring engine comparison;
- LLM factuality/structured-output/Serbian-quality evaluator engines;
- VLM/image evaluation engine;
- adversarial prompt-injection/PII/unsafe-context scoring;
- circuit breaker;
- drift monitoring/jobs;
- latency/resource benchmark promotion thresholds beyond persistence fields;
- champion selection/promotion/winner ranking;
- traffic splitting/A-B deployment;
- production rollback execution;
- production model download/activation;
- scheduled nightly/weekly evaluation jobs;
- dashboards/final XAI closeout;
- global Help F08 closeout where assigned to ISI-27;
- GitHub hosted acceptance before final controlled ISI-27 RC;
- ISI-26 load/resilience implementation;
- ISI-27 RC packaging;
- ISI-28 server deployment.

## Forbidden changes

- any path outside the frozen 19;
- `.github/workflows/**`;
- `AGENTS.md`;
- RBAC/access catalog changes or new permission codes;
- requirements/lock/dependency changes;
- Docker/deployment/server config;
- provider/gateway rewrite;
- worker/queue architecture rewrite;
- new scheduler;
- dedicated Vision or Audio service;
- production secrets/data/model runtime;
- automatic GitHub triggers;
- GitHub Actions dispatch;
- stage/commit/push;
- server access/mutation;
- hard-coded champion;
- automatic model/prompt promotion;
- ranking/winner output;
- ORDO automatic model selection/fallback or scenario impact estimation;
- causal/policy claims.

## Human review and owner gate

The runner stops with a dirty, unstaged, locally validated candidate. The assistant must review the exact diff and analyzer evidence before any commit.

This scope approval does NOT authorize commit/push and does NOT authorize GitHub Actions.

A separate owner approval is required to stage and commit/push the exact reviewed candidate. No content-changing closeout microtask should be introduced solely to manufacture another checkpoint; the phase remains ISI-25 IN PROGRESS because 25B follows.

## Completion definition

ISI-25A R4 implementation candidate is ready for final human review only when every local gate passes, the exact 19-path surface is stable, the eight non-remediation R3 paths remain byte-identical, and runtime/authority documentation tells the selected-model-only and platform-admin/reviewer truth.

After assistant human review plus separate owner-approved exact-candidate commit/push, 25A may be treated as the accepted foundation checkpoint inside globally IN-PROGRESS ISI-25. GitHub CI verification remains intentionally deferred to the single controlled final RC acceptance at ISI-27.

ISI-25 itself is NOT complete until 25B is accepted.

## Deferred server verification

All production deployment/server/DNS/ingress/SMTP/secrets/data/Ollama/model-runtime verification and mutation remain frozen until explicit ISI-28 after ISI-27 and explicit GO.
