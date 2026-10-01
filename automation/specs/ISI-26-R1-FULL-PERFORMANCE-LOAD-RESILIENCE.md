# ISI-26-R1 — Full Performance, Load & Resilience Implementation

## Status
`OWNER_APPROVED / LOCKED IMPLEMENTATION CONTRACT`

## Canonical baseline
- Repository: `branislavradomirovic/isi`
- Branch: `main`
- Exact baseline SHA: `5b2bf27e032d78f4ae5656f689819000da3cb207`
- Exact baseline tree: `9030bad7e7d8bda66dd7b85f8c09844d672bda18`
- Baseline state required: `HEAD == origin/main`, clean index/worktree, empty stash, exactly one worktree.
- Server verification: `DEFERRED_SERVER_VERIFICATION`.
- Hosted full CI: not authorized by this development package.

## Why R1 is a single larger implementation slice
The earlier ISI-26A/26B/26C/26D/26E decomposition is retained only as an internal coverage map. It is **not** the execution model. This R1 package supersedes the micro-task execution sequence and implements the full repository-side ISI-26 capability in one larger controlled ISI-26 implementation slice and one runner-mediated Codex implementation pass.

Internal coverage areas:
1. performance contract + deterministic harness;
2. API/auth/readiness load and dependency resilience;
3. ingestion/data/SIMPA/ORDO/report scale evidence;
4. AI queue/concurrency/timeout/circuit/fallback resilience;
5. governance/documentation reconciliation and whole-slice acceptance evidence.

A later recovery/closeout package is created only if deterministic evidence identifies a concrete remaining blocker. Do not pre-split the implementation into additional Codex micro-tasks.

## Canonical bootstrap result
ISI-26-B0 is CLOSED/PASS at the predecessor baseline. Repository truth already provides:
- bounded HTTP, worker, AI and ingestion telemetry;
- PostgreSQL/Redis/object-storage readiness;
- `isi-data` and `isi-ai` RQ queues;
- 900-second RQ job timeout;
- configurable AI timeout, current default 120 seconds;
- deterministic AI circuit-breaker/fallback governance;
- ISI-19 isolated recovery rehearsal;
- server-shaped memory limits which are configuration limits, **not** proven capacity budgets.

Missing before this R1 slice:
- canonical workload catalogue;
- deterministic percentile/throughput contract;
- repository-side load/resilience harness;
- API/auth/data/domain/report/AI scale acceptance;
- calibrated repository acceptance budgets;
- whole-phase performance evidence.

## Objective
Implement the complete **repository-side** ISI-26 Performance, Load & Resilience capability as one vertical slice, using synthetic/local evidence only, without touching the live server or shared infrastructure.

The candidate must establish:
- stable workload identities and synthetic fixtures;
- exact measurement semantics and evidence fingerprints;
- deterministic concurrent execution harness;
- bounded API/auth/readiness load profiles;
- controlled dependency-failure/resilience profiles;
- ingestion/data-worker scale profiles;
- SIMPA statistical workload profiles;
- ORDO forecast/backtest workload profiles;
- reporting/render/export scale profiles;
- AI stub/queue/concurrency/timeout/circuit/fallback profiles;
- hard correctness/security gates;
- evidence-backed local/repository calibration semantics;
- explicit separation between repository acceptance and live production capacity.

## Execution model
This contract is consumed only through the package runner.

Required flow:
`package SHA -> internal checksums -> selftest -> exact preflight -> install locked contract -> exactly one runner-mediated Codex implementation pass -> exact-surface validator -> focused/regression/native/full local acceptance -> candidate fingerprint -> independent analyzer -> assistant human review -> explicit owner staging/commit/push approval`.

Codex must not be invoked point-blank by the owner. The runner is the only implementation invocation authority for this R1 candidate.

## Architecture invariants
- FastAPI remains backend/API authority.
- Streamlit remains authenticated analytical UI.
- PostgreSQL remains durable relational authority.
- Redis/RQ remains job transport, not business truth.
- MinIO/S3-compatible storage boundary remains unchanged.
- SIMPA and ORDO remain domain-isolated.
- deterministic analytics remain numerical authority.
- LLM/VLM remain bounded synthesis/explanation, never silent numerical/state authority.
- central Nginx/shared-host deployment truth remains documentation only for ISI-26; no live ingress operation is authorized.
- Krcuga and OralScanXAI are strict non-target systems.

## Performance evidence semantics

### Budget classes
Exactly:
- `CORRECTNESS`
- `LATENCY_THROUGHPUT`
- `RESOURCE`
- `RESILIENCE`

### Budget states
Exactly:
- `HARD_GATE`
- `CALIBRATED`
- `UNCALIBRATED`
- `NOT_APPLICABLE`
- `UNAVAILABLE`

`CALIBRATED` means a repository/local acceptance threshold backed by accepted synthetic/local evidence. It must never be represented as live production/server capacity proof.

### Percentiles
Nearest-rank only:
- sort non-negative samples ascending;
- `rank = ceil(q * N)` for `q in (0, 1]`;
- selected index `rank - 1`;
- empty set -> unavailable, never zero.

### Throughput
`completed measured operations / measured wall duration`.
- warmups excluded;
- failed measured operations remain in denominator;
- non-positive duration is invalid evidence.

### Correctness
Timing never decides correctness. Correctness/security/resilience blockers are non-compensable.

## Canonical workload catalogue
The implementation must define and exercise these versioned workload identities in the same R1 slice:

1. `api.health.read.v1`
2. `api.authenticated.context.v1`
3. `api.authenticated.navigation.v1`
4. `api.readiness.synthetic.v1`
5. `data.ingestion.synthetic.v1`
6. `simpa.analytics.synthetic.v1`
7. `ordo.forecast.synthetic.v1`
8. `report.render.synthetic.v1`
9. `ai.stub.synthetic.v1`
10. `ai.circuit.synthetic.v1`

Every profile must declare:
- workload ID/version;
- title/category;
- execution mode;
- synthetic fixture/version;
- warmup count;
- measured sample count;
- requested concurrency;
- correctness gates;
- required metrics;
- budget states and optional thresholds;
- privacy/security classification;
- expected failure semantics;
- contract fingerprint fields.

## Repository-only environment classes
Allowed:
- `LOCAL_REPOSITORY`
- `LOCAL_DISPOSABLE_POSTGRES`
- `LOCAL_DISPOSABLE_SERVICES` only where an existing repository acceptance tool already provides it.

Forbidden in this package:
- production host;
- public ISI endpoint;
- current server;
- central-ingress benchmarking;
- Krcuga/OralScanXAI endpoints.

Every evidence record must explicitly contain:
- `PRODUCTION_CAPACITY_VERIFIED=false`
- `SERVER_VERIFIED=false`

## Required implementation behavior

### A. Core performance contract and harness
Create a pure-Python reusable harness using standard library + existing dependencies only.

Required capabilities:
- immutable workload/metric/result contracts;
- exact budget state validation;
- nearest-rank p50/p95/p99;
- warmup exclusion;
- bounded standard-library concurrency;
- injected callable;
- injected/fake clock or deterministic metric input for unit tests;
- exact success/failure/correctness counts;
- bounded failure reason codes only;
- no raw exception text in canonical evidence;
- stable sorted JSON;
- canonical SHA-256 contract fingerprint independent of timing values;
- measured timing fingerprint/evidence may vary but cannot alter correctness authority;
- zero/non-positive measured duration fails closed.

### B. API/auth/readiness workloads
Use in-process FastAPI/TestClient or equivalent repository-local test surfaces only.

At minimum verify under bounded repeated/concurrent execution:
- `/api/v1/health` exact contract;
- authenticated app-context path using synthetic local auth/test fixtures already supported by repository tests;
- authenticated navigation/app-shell path using synthetic test fixtures;
- readiness behavior with synthetic injected component health/failure, not production dependencies.

Hard gates:
- zero unexpected 5xx;
- zero unexpected authorization success;
- zero cross-scope leakage;
- no raw auth/session data in evidence;
- controlled dependency failure returns bounded/safe state.

### C. Data/ingestion scale workloads
Exercise deterministic synthetic CSV/JSON/XLSX-compatible repository surfaces as supported by existing code/tests.

At minimum cover:
- small and bounded larger synthetic record counts;
- row/column/sheet accounting;
- XLSX uncompressed-size guard behavior;
- repeated ingestion/inspection path;
- deterministic failure reason for guard breach;
- no raw filename/storage-key/customer data in canonical evidence.

Do not weaken current upload/uncompressed guards just to improve numbers.

### D. SIMPA analytics scale workload
Use only synthetic aggregate/system-level data already consistent with accepted SIMPA contracts.

Required:
- deterministic repeated analytical/statistical execution;
- result fingerprint/correctness preservation under repeated runs;
- bounded latency evidence;
- no citizen-level data;
- no new LISI formula/weight/threshold;
- no causal claim.

### E. ORDO forecast scale workload
Use accepted deterministic naive/seasonal-naive/rolling-origin boundaries and synthetic data.

Required:
- repeated forecast/backtest execution;
- exact forecast metric/result correctness remains unchanged;
- `NOT_ESTIMATED` semantics preserved;
- scenario != forecast;
- no automatic family selection/fallback;
- no causal impact claim.

### F. Reporting scale workload
Exercise deterministic persisted-data renderer/service surfaces with synthetic reports.

Required:
- repeated JSON/Markdown/HTML rendering where supported;
- checksum/result stability;
- larger bounded synthetic section/item counts;
- no new PDF/document-conversion dependency;
- no AI inference inside reporting benchmark.

### G. AI resilience/load workload
Use deterministic local development stub/test doubles and existing in-memory/local DB test paths. Do not invoke real Ollama/server models.

Required:
- queue dispatch contract evidence;
- bounded concurrent synthetic AI jobs/operations;
- provider timeout error semantics;
- circuit closed -> open -> half_open -> closed deterministically without sleeps;
- valid registered fallback gates preserved;
- sensitive SIMPA local-only boundary preserved;
- review-required fallback remains review-required;
- no heuristic registration scan;
- no model installation/deployment;
- no online learning/silent promotion/silent rollback.

### H. Resource evidence
Repository/local resource evidence may be collected only where deterministic and portable enough for acceptance.

Rules:
- existing Compose `mem_limit` values are configuration facts, not capacity proof;
- host-specific absolute RSS/CPU thresholds must not become hard gates in this slice unless evidence is demonstrably portable;
- resource observations that cannot be made portably are `UNAVAILABLE`/`UNCALIBRATED`, never fabricated;
- performance acceptance must not depend on user name, host name, IP or machine path.

## Calibration policy
R1 may set **repository acceptance** thresholds only when:
1. workload is fully synthetic/local;
2. metric is stable enough under deterministic repeated local execution;
3. threshold includes documented safety margin;
4. threshold failure does not invite weakening correctness/security;
5. documentation explicitly says it is not a live production SLO.

If those conditions are not satisfied, state remains `UNCALIBRATED`.

## Exact mutable surface
Codex may modify/create only the following paths.

### Locked spec/governance
- `automation/specs/ISI-26-R1-FULL-PERFORMANCE-LOAD-RESILIENCE.md` (installed byte-for-byte by runner; Codex must not edit it)
- `automation/specs/ISI-26A-PERFORMANCE-CONTRACT-DETERMINISTIC-HARNESS.md` (may only mark historical/superseded execution decomposition; preserve technical content as history)
- `automation/STATUS.md`
- `automation/tasks.json`
- `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
- `TECHNICAL_DOCUMENTATION.md`

### Performance tooling
- `tools/performance/__init__.py`
- `tools/performance/contracts.py`
- `tools/performance/harness.py`
- `tools/performance/workloads.py`
- `tools/performance/scenarios.py`
- `tools/performance/evidence.py`
- `tools/performance/run_isi26.py`

### Performance documentation
- `docs/ops/ISI-26-PERFORMANCE-LOAD-RESILIENCE.md`

### Exact new tests
- `tests/test_isi_26_performance_contract.py`
- `tests/test_isi_26_api_resilience.py`
- `tests/test_isi_26_data_scale.py`
- `tests/test_isi_26_domain_scale.py`
- `tests/test_isi_26_reporting_scale.py`
- `tests/test_isi_26_ai_resilience.py`
- `tests/test_isi_26_governance_contract.py`

### Narrow existing runtime/telemetry surface — modify only if evidence requires it
- `src/platform/observability/metrics.py`
- `src/platform/observability/telemetry.py`
- `src/platform/observability/readiness.py`
- `src/platform/data/queue.py`
- `src/platform/ai/queue.py`
- `src/workers/data_jobs.py`
- `src/workers/ai_jobs.py`
- `src/platform/ai/service.py`

No other path is mutable. If a required fix lies outside this surface, stop with a blocker; do not broaden scope autonomously.

## Required governance reconciliation
The candidate must:
- change parent ISI-26 to `IN PROGRESS / R1 FULL IMPLEMENTATION CANDIDATE`;
- mark 26A/26B/26C/26D child task execution decomposition as `SUPERSEDED_BY_R1_FULL_SLICE` or equivalent non-active history;
- retain 26E only as a whole-phase closeout concept, not a pre-authorized separate Codex implementation task;
- state that recovery/closeout work is created only from evidence after R1 review;
- keep ISI-27 next only after ISI-26 whole-phase acceptance;
- keep ISI-28 as exclusive live-server mutation phase.

## Database/migration boundary
No schema change is planned or authorized.
- No Alembic migration may be created.
- Existing DB behavior may be exercised by tests/native PostgreSQL.
- If a schema change appears necessary, stop and report blocker.

## Dependency boundary
No new dependency and no dependency upgrade.
Immutable:
- `pyproject.toml`
- `requirements.lock`
- `requirements.runtime.lock`

## Deployment boundary
Immutable:
- all `docker-compose*.yml`;
- `docker/**`;
- `deploy/**`;
- `.github/**`;
- central ingress configuration;
- server configuration.

No SSH/SCP/rsync/curl/wget/request to production/public ISI/Krcuga/OralScanXAI endpoints.

## Security/privacy hard gates
- synthetic fixtures only;
- no real customer/institution records;
- no raw passwords/tokens/cookies/authorization headers;
- no raw AI prompt/output in canonical performance evidence;
- no tenant/user identifiers in evidence;
- no cross-product/cross-tenant leakage;
- no security-control disabling to improve performance;
- no unsafe exception/string dump in evidence.

## Required new test coverage

### Performance contract
- exact enums/states/classes;
- invalid values fail closed;
- nearest-rank exact math;
- empty set unavailable;
- calibrated threshold requires evidence metadata;
- canonical fingerprint excludes timing noise;
- unsafe identity/secret fields rejected.

### API/auth/readiness
- repeated/concurrent health exactness;
- authenticated synthetic context/navigation correctness;
- authorization failure remains failure;
- dependency failure returns safe bounded readiness state;
- no raw auth/session evidence.

### Data scale
- deterministic synthetic small/larger inputs;
- guards preserved;
- repeated output/correctness evidence;
- bounded failure codes.

### Domain scale
- SIMPA deterministic analytics repeated correctness;
- ORDO forecast/backtest repeated correctness;
- non-causal/scenario/NOT_ESTIMATED boundaries preserved.

### Reporting
- JSON/Markdown/HTML deterministic output/checksum;
- bounded larger synthetic report structures;
- no external converter/AI inference.

### AI resilience
- concurrent synthetic/stub operations;
- timeout bounded failure;
- circuit state transitions deterministic;
- fallback/review/local-only gates preserved;
- no server/model mutation.

### Governance contract
- R1 full-slice is active authority;
- micro-slice execution decomposition is no longer active;
- no false production-capacity claim;
- server remains ISI-28;
- Krcuga/OralScanXAI non-target;
- full CI remains manual/undispatched.

## Regression acceptance set
At minimum include focused regressions for:
- ISI-18 observability/readiness;
- ISI-19 recovery;
- ISI-20 security/assurance contracts relevant to auth/performance;
- ISI-22G governed domain consumption/synthetic E2E;
- ISI-23E SIMPA closeout/synthetic E2E;
- ISI-24C/24E forecast/workflow semantics;
- ISI-25B capability runtime/promotion/monitoring/XAI;
- production workflow lock;
- server deployment contract as a no-mutation regression.

## Local acceptance gates
The package runner owns:
1. archive/internal integrity and package selftest;
2. exact baseline/main/origin/one-worktree/clean/stash preflight;
3. locked contract installation;
4. exactly one standard `codex` implementation invocation;
5. exact mutable-surface validator;
6. no dependency/migration/deployment/workflow drift;
7. compile;
8. Ruff;
9. mypy;
10. focused ISI-26 tests;
11. required regression set;
12. policy check;
13. `git diff --check`;
14. local synthetic performance suite and evidence schema validation;
15. local native PostgreSQL acceptance using existing repository tooling;
16. exactly one final full local `pytest -q -p no:cacheprovider`;
17. candidate fingerprint;
18. final guard that HEAD/origin remain baseline and index remains unstaged.

The runner must not stage/commit/push.

## Independent analyzer
Runs only after runner PASS. It is read-only and must verify:
- exact candidate surface;
- locked contract byte identity;
- no dependency/migration/deployment/workflow drift;
- no public/server network path in performance tooling/tests;
- workload catalogue exactness;
- percentile/throughput correctness;
- no false production SLO/capacity language;
- governance reconciliation from micro decomposition to R1 full slice;
- server/Krcuga/OralScanXAI protections;
- candidate fingerprint reproducibility.

## Non-goals / forbidden outcomes
- no server load test;
- no live `isi.opus.rs:8445` benchmark;
- no central-Nginx benchmark/change;
- no Krcuga or OralScanXAI contact/change;
- no DNS/TLS/SMTP/server-Ollama action;
- no dependency additions/upgrades;
- no migration;
- no new scheduler;
- no external load tool dependency;
- no automatic model installation/training/promotion/rollback;
- no methodology invention;
- no production SLO claim from local evidence;
- no branch/PR/worktree;
- no GitHub Actions dispatch;
- no stage/commit/push by Codex or runner.

## Candidate completion markers
A valid runner PASS must emit all of:

```text
ISI26_R1_PACKAGE_INTEGRITY=PASS
ISI26_R1_BASELINE=PASS
ISI26_R1_CODEX_CALLS=1
ISI26_R1_EXACT_SURFACE=PASS
ISI26_R1_NO_DEPENDENCY_DRIFT=PASS
ISI26_R1_NO_MIGRATION=PASS
ISI26_R1_NO_DEPLOYMENT_DRIFT=PASS
ISI26_R1_FOCUSED_TESTS=PASS
ISI26_R1_REGRESSION_SET=PASS
ISI26_R1_LOCAL_PERFORMANCE_EVIDENCE=PASS
ISI26_R1_NATIVE_POSTGRES=PASS
ISI26_R1_FULL_LOCAL_REGRESSION=PASS
ISI26_R1_CANDIDATE_FINGERPRINT=PASS
PRODUCTION_CAPACITY_VERIFIED=NO
SERVER_VERIFIED=NO
GITHUB_ACTIONS_DISPATCH=NO
SERVER_MUTATION=NO
STAGE_COMMIT_PUSH=NO
READY_FOR_ISI26_R1_INDEPENDENT_ANALYSIS=PASS
```

After a separate analyzer PASS and assistant human review, exact-file staging/commit/push requires a separate explicit owner approval/finalizer.
