# ISI-26A - Performance Contract + Deterministic Harness

## Status
`OWNER_APPROVED / SPEC_READY / FORMAL_COVERAGE_GATE`

> This specification remains the formal 26A coverage/gate identity. Repository implementation execution is grouped inside `ISI-26-R1-FULL-PERFORMANCE-LOAD-RESILIENCE.md`; that grouping removes the need for a separate 26A Codex invocation but does not supersede this formal gate.

Owner approval date: **2026-10-01**.

## Baseline
- Canonical repository: `branislavradomirovic/isi`
- Canonical branch: `main`
- Exact baseline SHA: `f37699224e2af01d4313b48f17de8607cb16e22e`
- Exact baseline tree: `e611b61210f9de09759a630e17e18d3abd242e90`
- Local owner evidence: `HEAD == origin/main`, ahead/behind `0/0`, clean index/worktree, empty stash, exactly one worktree.
- ISI-25A accepted on main SHA `f0047321ee4410522697144ecfa464087f1b83bc`.
- ISI-25B accepted on main SHA `7e11ee2a6f7546eacc3207e15cacfc35f6d04f3e`.
- ISI-25 hosted full acceptance was deliberately not run under the owner CI-cost policy; `CI_VERIFIED` is not claimed.
- Server/live-host verification remains `DEFERRED_SERVER_VERIFICATION`.

## Canonical bootstrap evidence
The 2026-10-01 ISI-26-B0 audit reviewed the complete MasterPlan/current governance, Technical Documentation, current task/status ledgers, relevant observability/recovery/AI runtime code, worker/queue contracts, server-shaped Compose resource limits and existing tests.

### ISI-26-B0 DONE / PARTIAL / MISSING / DRIFT

| Area | Classification | Evidence-backed state |
|---|---|---|
| HTTP telemetry | DONE | request count + latency instrumentation exists |
| worker telemetry | DONE | worker execution count + latency exists |
| AI telemetry | DONE | provider/model/prompt/product/outcome + latency exists |
| ingestion telemetry | DONE | duration/rows/columns exists |
| readiness | DONE | PostgreSQL, conditional Redis and storage readiness exist |
| data queue | DONE | inline/RQ with queue `isi-data` |
| AI queue | DONE | inline/RQ with queue `isi-ai` |
| data/AI RQ job timeout | PARTIAL | fixed `job_timeout=900` exists but is not an accepted capacity budget |
| AI provider timeout | PARTIAL | configurable; current default 120 seconds |
| AI circuit breaker | DONE foundation | deterministic closed/open/half-open + threshold/cooldown |
| recovery | DONE foundation | ISI-19 deterministic isolated recovery rehearsal |
| server-shaped memory limits | PARTIAL | limits exist but are not evidence-backed capacity budgets |
| performance workload catalogue | MISSING | no canonical workload IDs/profiles |
| deterministic performance harness | MISSING | no reusable percentile/throughput/correctness harness |
| performance budgets | MISSING | no canonical budget-state model or calibrated thresholds |
| API/auth load acceptance | MISSING | owned by ISI-26B |
| data/statistics/forecast/report scale acceptance | MISSING | owned by ISI-26C |
| AI concurrency/timeout/circuit load acceptance | MISSING | owned by ISI-26D |
| whole-phase closeout | MISSING | owned by ISI-26E |
| live server capacity / central ingress performance | DEFERRED | owner-approved ISI-28 only |

## Dependencies
- ISI-18 Observability & Operational Diagnostics
- ISI-19 Backup/Restore/DR
- ISI-20 Enterprise Security
- ISI-21 Data Governance/Privacy
- ISI-22 Industrial Data Platform
- ISI-23 SIMPA production methodology
- ISI-24 ORDO production methodology
- ISI-25A/25B AI/MLOps governance/runtime
- MasterPlan and Technical Documentation at the exact baseline SHA

## Objective
Create the canonical repository-side performance contract and deterministic measurement harness that later ISI-26 slices use to measure API, data, analytics, reporting and AI workloads without inventing production SLOs and without touching the live server.

ISI-26A must produce:
1. stable workload identities and phase ownership;
2. exact metric and percentile semantics;
3. explicit correctness, latency/throughput, resource and resilience budget classes;
4. explicit budget states `HARD_GATE`, `CALIBRATED`, `UNCALIBRATED`, `NOT_APPLICABLE`, `UNAVAILABLE`;
5. deterministic result/evidence schema and fingerprint;
6. a reusable pure-Python harness with injected callable/clock support for deterministic tests;
7. one bounded in-process smoke workload proving end-to-end harness behavior;
8. no runtime/product behavior change.

## Existing architecture
- FastAPI is backend/public/API authority.
- Streamlit is authenticated analytical UI.
- PostgreSQL is durable relational authority.
- Redis/RQ transports data and AI jobs.
- Data queue: `isi-data`; AI queue: `isi-ai`.
- Current RQ job timeout: 900 seconds.
- AI provider timeout is model/config driven; default is 120 seconds.
- Existing observability provides bounded counts and latency sums/counts but not canonical percentile/SLO acceptance.
- AI capability runtime already has deterministic circuit-breaker state and governed fallback evidence.
- Server-shaped Compose currently defines resource limits, but those limits are not proof of capacity.
- Current live-server/shared-edge verification is outside this task.

## Legacy/drift audit
1. `src/workers/worker.py` generic `default` queue worker:
   - classification: `REQUIRED_COMPATIBILITY`;
   - reason: retained for the simple development Compose path;
   - rule: it is not production concurrency authority and ISI-26A must not use it as the canonical worker topology.
2. `src/platform/ai/service.py` contains a historical comment saying persisted fallback edges are governance evidence only until ISI-25B:
   - classification: `REMOVE_IN_NAMED_PHASE(ISI-26D)`;
   - reason: runtime behavior is already 25B-aware and the stale comment is non-functional; 26D owns AI concurrency/circuit/fallback runtime inspection and will remove/reconcile that wording without broadening 26A.
3. Historical staging/precutover ingress assets:
   - classification: `LEGITIMATE_HISTORY / REQUIRED_COMPATIBILITY`;
   - rule: untouched by ISI-26A.
4. No `REMOVE_BEFORE_NEXT_SLICE` blocker remains after B0.

## ISI-26 phase decomposition
- **ISI-26A** - Performance Contract + Deterministic Harness
- **ISI-26B** - API/Auth/Readiness Load + Dependency Resilience
- **ISI-26C** - Data/Statistics/Forecast/Reporting Scale
- **ISI-26D** - AI Queue/Concurrency/Timeout/Circuit Resilience
- **ISI-26E** - Whole-Phase Performance & Resilience Closeout

## Exact mutable surface
Implementation may modify/create **only**:

### New tooling
- `tools/performance/__init__.py`
- `tools/performance/contracts.py`
- `tools/performance/harness.py`
- `tools/performance/workloads.py`
- `tools/performance/run_isi26a.py`

### New tests
- `tests/test_isi_26a_performance_contract.py`
- `tests/test_isi_26a_deterministic_harness.py`
- `tests/test_isi_26a_workload_catalog.py`

### Documentation / evidence
- `docs/ops/ISI-26-PERFORMANCE-CONTRACT.md`
- `automation/evidence/ISI-26A-PERFORMANCE-CONTRACT-DETERMINISTIC-HARNESS/**`

### Closure-only synchronized governance updates
- `automation/STATUS.md`
- `automation/tasks.json`
- `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
- `TECHNICAL_DOCUMENTATION.md`

Everything else is immutable for ISI-26A unless the owner explicitly approves a scope change.

## Canonical system inventory impact
No new customer-facing product capability is introduced.

At implementation closeout:
- observability/performance tooling inventory rows must reference the canonical performance contract/harness as repository test/acceptance authority;
- runtime, deployment, AI provider, worker and ingress ownership must remain unchanged;
- no CURRENT_AS_BUILT production component may be added merely because a measurement harness exists.

## Implementation-tool authority
Codex is allowed **only for the later implementation candidate**, after this spec is committed and the owner local baseline is synchronized.

Implementation invocation rules:
- standard `codex` CLI only;
- canonical repository/worktree only;
- one locked implementation invocation for the initial candidate;
- no stage/commit/push/deploy;
- no GitHub Actions dispatch;
- no server access;
- outer deterministic runner and independent analyzer own acceptance.

This specification/governance lock itself does not require Codex.

## Locked boundaries
- No new runtime dependency.
- No `pyproject.toml`, `requirements*.lock` or dependency upgrade.
- No application/runtime source changes under `src/**`.
- No migrations/database schema changes.
- No API/UI/worker behavior changes.
- No Compose changes.
- No central Nginx, Caddy, DNS, TLS, server, SMTP, Ollama or production-data mutation.
- No calls to `https://isi.opus.rs:8445/` or any production host.
- Krcuga and OralScanXAI are strict non-target systems.
- No tenant/product authorization weakening.
- No use of real customer/institution data in performance fixtures.
- No performance optimization is allowed before a measured bottleneck exists.

## Required behavior

### 1. Canonical workload contract
Every workload definition must include at minimum:
- `workload_id`;
- title/description;
- owner phase;
- surface/category;
- execution mode;
- synthetic fixture identity/version;
- warmup count;
- measured sample count;
- requested concurrency;
- correctness gates;
- required metrics;
- budget state per metric;
- security/privacy classification;
- expected failure semantics;
- evidence/fingerprint metadata.

Workload IDs are immutable once accepted. Changed semantics require a new workload version.

### 2. Canonical workload catalogue
ISI-26A must register these planned workload identities without falsely claiming later-phase acceptance:

- `api.health.read.v1` - ISI-26A smoke / ISI-26B calibration
- `api.authenticated.context.v1` - ISI-26B
- `api.authenticated.navigation.v1` - ISI-26B
- `data.ingestion.synthetic.v1` - ISI-26C
- `simpa.analytics.synthetic.v1` - ISI-26C
- `ordo.forecast.synthetic.v1` - ISI-26C
- `report.render.synthetic.v1` - ISI-26C
- `ai.stub.synthetic.v1` - ISI-26D
- `ai.circuit.synthetic.v1` - ISI-26D

Only `api.health.read.v1` and internal harness self-tests may execute as measured smoke in 26A. All other workload profiles remain declared/un-calibrated until their owning slice.

### 3. Metric semantics
The harness must support at minimum:
- sample count;
- success/failure count;
- correctness failure count;
- elapsed duration;
- latency minimum/maximum;
- p50/p95/p99 latency;
- throughput;
- optional queue-wait duration;
- optional execution duration;
- optional resource observations;
- bounded failure-code counts.

No raw exception text, secrets, request bodies, prompts, uploaded data, customer identifiers or tenant identifiers may be written to result evidence.

### 4. Exact percentile rule
Use a deterministic nearest-rank percentile:
- sort non-negative latency samples ascending;
- for percentile `q` in `(0,1]`, rank = `ceil(q * N)`;
- selected sample index = `rank - 1`;
- empty sample sets produce `UNAVAILABLE`, never zero.

The same algorithm must be used by tests and evidence rendering.

### 5. Throughput semantics
For a measured workload:
- throughput = completed measured operations / measured wall duration;
- warmup operations are excluded;
- failed measured operations remain in the denominator;
- zero/non-positive measured duration must fail closed as invalid evidence.

Throughput is measurement evidence, not automatically a pass/fail production SLO.

### 6. Budget classes
The contract must distinguish:

**Correctness gates**
- hard blocker;
- examples: unexpected status/result, cross-scope leakage, corrupted fingerprint/result, job loss, unexpected exception.

**Latency/throughput budgets**
- p50/p95/p99, throughput, queue wait, execution duration.

**Resource budgets**
- memory/process/resource observations where the owning slice can measure them safely.

**Resilience budgets**
- bounded timeout, expected dependency failure, circuit transition, retry/fallback/recovery semantics.

### 7. Budget-state model
Every budget is exactly one of:
- `HARD_GATE` - deterministic correctness/security/resilience invariant;
- `CALIBRATED` - numeric threshold backed by accepted measurement evidence;
- `UNCALIBRATED` - metric is collected but has no accepted pass/fail numeric threshold yet;
- `NOT_APPLICABLE`;
- `UNAVAILABLE` - measurement cannot be produced and reason code is explicit.

26A must **not** invent production p95/p99/throughput/resource thresholds.

### 8. Correctness hard gates
For every measured workload:
- no unexpected exception;
- no unexpected status/result;
- no correctness mismatch;
- no synthetic tenant/product boundary violation;
- no missing result record;
- evidence fingerprint must be reproducible for the canonical non-timing contract fields.

Timing values themselves are not required to be byte-identical between runs.

### 9. Result schema
Each run result must include:
- repository SHA;
- workload ID/version;
- synthetic fixture identity;
- environment class (`LOCAL_REPOSITORY` only in 26A);
- warmup/measured sample counts;
- requested/effective concurrency;
- metric values and states;
- correctness gate results;
- bounded reason codes;
- start/end monotonic-derived duration;
- canonical contract fingerprint;
- explicit `PRODUCTION_CAPACITY_VERIFIED=false`;
- explicit `SERVER_VERIFIED=false`.

Do not persist hostname, username, home path, IP address or secrets in canonical evidence.

### 10. Deterministic harness design
The harness must:
- be pure Python using standard library + already-installed project dependencies only;
- accept an injected callable;
- support injected/fake clock or deterministic metric input for unit tests;
- separate warmup from measured samples;
- support bounded concurrency through standard-library primitives;
- capture only bounded reason codes for failures;
- never suppress correctness errors to improve performance numbers;
- never turn a timeout/error into success;
- render stable sorted JSON for evidence;
- never contact external/public network targets in 26A.

### 11. 26A smoke workload
Implement one bounded in-process health workload against the FastAPI application/test surface:
- no external network;
- no Docker requirement;
- no production configuration;
- verifies expected health response;
- proves warmup/measurement/result rendering/fingerprint path;
- latency metrics collected as `UNCALIBRATED`;
- correctness is `HARD_GATE`.

### 12. Performance evidence contract
`docs/ops/ISI-26-PERFORMANCE-CONTRACT.md` must explain:
- workload catalogue;
- metric semantics;
- percentile rule;
- budget states;
- calibration lifecycle;
- environment classes;
- security/privacy rules;
- why repository measurements are not live production capacity proof;
- handoff from 26A -> 26B/26C/26D -> 26E -> ISI-27;
- live-server capacity verification remains ISI-28.

## Impact
- Database/migrations: **NONE**
- API: **NONE**
- UI: **NONE**
- Workers: **NONE**
- Runtime configuration: **NONE**
- Dependencies: **NONE**
- Compose: **NONE**
- Production/server: **NONE**
- Repository tooling/tests/docs: **YES**

## Security and privacy
- synthetic fixtures only;
- no raw auth/session headers/cookies/tokens;
- no prompt/output/body logging;
- no customer/institution data;
- no tenant/user identifiers in evidence;
- failure detail is bounded reason-code only;
- cross-tenant/product correctness remains a hard gate when such workloads are added in later slices;
- timing evidence must not weaken authorization/security controls.

## Tests

### New exact test files
1. `tests/test_isi_26a_performance_contract.py`
2. `tests/test_isi_26a_deterministic_harness.py`
3. `tests/test_isi_26a_workload_catalog.py`

### Required test coverage
**Contract**
- workload IDs/version required and stable;
- invalid sample/concurrency values fail closed;
- exact budget-state vocabulary enforced;
- no CALIBRATED metric without explicit numeric threshold/evidence metadata;
- UNCALIBRATED timing metric accepted without threshold;
- production/server verification flags false in 26A;
- evidence schema rejects secrets/unsafe identity fields.

**Harness**
- warmups excluded;
- success/failure/correctness accounting exact;
- nearest-rank p50/p95/p99 exact;
- empty samples -> UNAVAILABLE;
- throughput includes measured failures in denominator;
- zero duration invalid;
- deterministic fake-clock test;
- bounded concurrency;
- exceptions become bounded failure codes;
- stable non-timing contract fingerprint;
- no timing value is used as correctness authority.

**Workload catalogue**
- exact required workload IDs present;
- owner phases correct;
- only 26A health workload marked executable/calibratable in 26A;
- later workloads remain UNCALIBRATED/not executed;
- no production URL/host;
- no Krcuga/OralScan endpoint;
- no external network invocation;
- health smoke passes in-process.

### Regression coverage
Run at minimum:
- `tests/test_isi_18_observability.py`
- `tests/test_isi_18_readiness.py`
- `tests/test_isi_19_recovery_rehearsal.py`
- `tests/test_isi_25b_capability_runtime.py`
- `tests/test_isi_25b_monitoring_xai_help.py`
- `tests/test_isi_production_workflow_lock.py`

## Exact acceptance commands
The implementation package must provide a deterministic outer runner that performs, in order:

1. exact baseline/main/origin/one-worktree/clean-index preflight;
2. verify no dependency files changed;
3. verify no `src/**`, migration, Compose, workflow or deployment files changed;
4. compile new tooling/tests;
5. focused 26A tests;
6. listed regression tests;
7. policy check;
8. Ruff on mutable Python surface;
9. `git diff --check`;
10. run `tools/performance/run_isi26a.py` in repository-local synthetic mode;
11. validate evidence JSON schema/content;
12. independent analyzer over exact mutable surface;
13. final clean index / unstaged candidate guard;
14. prove no server/network/GitHub Actions mutation occurred.

No hosted GitHub Actions are authorized for 26A development acceptance.

## Evidence
Required evidence directory:
`automation/evidence/ISI-26A-PERFORMANCE-CONTRACT-DETERMINISTIC-HARNESS/`

Minimum evidence:
- `manifest.json`
- `acceptance.txt`
- `performance-smoke.json`
- `candidate-files.txt`
- `candidate-diff.sha256`
- `independent-analysis.txt`

Evidence must state:
- `PRODUCTION_CAPACITY_VERIFIED=false`
- `SERVER_VERIFIED=false`
- `GITHUB_ACTIONS_DISPATCH=NO`
- `SERVER_MUTATION=NO`

## Non-goals
- production load test;
- current-server capacity measurement;
- central-Nginx benchmarking;
- DNS/TLS benchmarking;
- performance tuning;
- worker replica/scaling changes;
- DB pool tuning;
- Redis tuning;
- MinIO tuning;
- Ollama/model tuning;
- API behavior changes;
- new scheduler;
- new monitoring backend;
- Prometheus/Grafana/Loki/OpenTelemetry deployment;
- customer-facing UI;
- production SLO/SLI commitment.

## Forbidden changes
- no server/SSH/SCP/rsync/deployment;
- no calls to production/public ISI endpoint;
- no Krcuga or OralScanXAI mutation/contact;
- no central-ingress mutation;
- no Caddy work;
- no dependency additions/upgrades;
- no `src/**` changes;
- no Compose changes;
- no migrations;
- no GitHub workflow changes/dispatch;
- no stage/commit/push by Codex;
- no weakening/skipping/xfail of tests;
- no invented latency/throughput/resource threshold labeled production-ready.

## Human review and owner gate
A passing implementation candidate remains unstaged/uncommitted. Assistant human review must verify:
- exact mutable surface;
- contract semantics;
- percentile/throughput math;
- no false calibrated/production claim;
- no server/public network path;
- no regression/security weakening;
- stable evidence fingerprint.

Exact-file staging/commit/push requires separate explicit owner approval after review.

## Completion definition
`IMPLEMENTED` requires local runner/analyzer PASS on the unstaged candidate.

Expected terminal closure markers:

```text
ISI26A_EXACT_MUTABLE_SURFACE=PASS
ISI26A_NO_RUNTIME_OR_DEPENDENCY_CHANGE=PASS
ISI26A_CONTRACT_TESTS=PASS
ISI26A_HARNESS_TESTS=PASS
ISI26A_WORKLOAD_CATALOG=PASS
ISI26A_REGRESSION_SET=PASS
ISI26A_SYNTHETIC_SMOKE=PASS
ISI26A_EVIDENCE_SCHEMA=PASS
ISI26A_NO_PRODUCTION_THRESHOLDS_INVENTED=PASS
PRODUCTION_CAPACITY_VERIFIED=NO
SERVER_VERIFIED=NO
GITHUB_ACTIONS_DISPATCH=NO
SERVER_MUTATION=NO
READY_FOR_ISI26A_HUMAN_REVIEW=PASS
```

`REVIEW_VERIFIED` requires assistant review with no unresolved blocker.

Commit/push requires separate owner approval.

`CI_VERIFIED` is not required for this development slice unless the owner separately authorizes a hosted acceptance checkpoint.

ISI-26A is complete when the accepted main commit contains the contract/harness/tooling/tests/docs and synchronized governance, while production capacity remains explicitly unverified.

## Deferred server verification
`DEFERRED_SERVER_VERIFICATION`

Current server, DNS, certificates, shared central Nginx, production SMTP/secrets/data and server Ollama remain exclusive to owner-approved ISI-28.
