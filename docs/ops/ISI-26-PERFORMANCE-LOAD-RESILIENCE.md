# ISI-26 R1 repository performance and resilience

Status: **IMPLEMENTATION COMPLETE / ACCEPTED ON MAIN / NOT CI_VERIFIED**. R1 is accepted on main SHA `e4b5b7f5927bc553fd616800d37beb5d115bb46e`
(tree `9a30b280ba44798b987167c155f0be6ccc13776e`) from human-reviewed candidate fingerprint
`98653d20a5223d4f6be66f3ee2017f998865b00ecb08a0950c07123d60dc2e24`. ISI-26A/26B/26C/26D remain formal coverage/gate identities
and are accepted through the grouped R1 implementation; R1 superseded only the
micro-task execution cadence. ISI-26E closes the whole-phase audit. ISI-27 is
current/next for a fresh release-candidate bootstrap.

## Bootstrap and inventory reconciliation

Baseline `5b2bf27e032d78f4ae5656f689819000da3cb207`, tree
`9030bad7e7d8bda66dd7b85f8c09844d672bda18`: canonical main equals local
origin/main, one worktree, empty stash and index. The installed R1 contract was
the sole untracked file before implementation. No fetch or hosted dispatch was
performed. The recorded latest hosted acceptance is Phase-24 run #90,
`35238623960`, attempt 2, success on `5937daa2ea7ff9c476bd6a05a04841d1534aefe2`.
ISI-25A/25B are accepted on main without hosted acceptance. There is no exact-R1
baseline CI_VERIFIED claim.

| Area | Bootstrap state | R1 reconciliation |
|---|---|---|
| INV-B25 observability/readiness | DONE | Existing bounded telemetry and injected component checks preserved |
| INV-D01/D03 queues | DONE foundation | RQ name/target/900-second dispatch contract tested with doubles |
| INV-D02/D04 workers | PARTIAL capacity evidence | Real ingestion worker and AI execution service run on isolated synthetic SQLite; shared transport contention unmeasured |
| INV-C38/C39 forecast authority | DONE | Explicit naive/seasonal-naive and chronological backtests exercised |
| INV-E05 fallback/circuit | DONE runtime, DRIFT comment | Exact-registration gates exercised; obsolete pre-25B comment corrected |
| INV-F04 renderer | DONE | Persisted synthetic drafts rendered in JSON/Markdown/HTML |
| Workloads/harness/evidence | MISSING | New development-only inventory row INV-M19 |
| Portable timing/resource thresholds | MISSING | Timing UNCALIBRATED; resource UNAVAILABLE |
| Live capacity | Deferred | ISI-28 only |

Legacy audit classifications:

- Obsolete active 26A–26D sequence: `REMOVE_BEFORE_NEXT_SLICE`, resolved by R1
  reconciliation; preserved 26A specification becomes `LEGITIMATE_HISTORY`.
- Stale fallback comment: `REMOVE_BEFORE_NEXT_SLICE`, resolved within the allowed
  service file. Runtime behavior is unchanged.
- Generic development worker/default queue: `REQUIRED_COMPATIBILITY`; not used as
  production scaling authority.
- Pre-cutover edge/Compose compatibility: `REQUIRED_COMPATIBILITY`; historical
  deployment runbooks and old accepted checkpoint text: `LEGITIMATE_HISTORY`.
- Shared/global Help gaps: `REMOVE_IN_NAMED_PHASE(ISI-27)`, unchanged release gate.
- No added branch/worktree, dependency, migration, deployment path, generated
  runtime dependency, bypass, feature flag or CI exemption. The local test lane
  does not replace governed domain consumption; ISI-22G/23E regressions retain
  that authority.

Canonical system inventory impact: new INV-M19 repository test authority only.
No customer-facing workflow or Help/XAI boundary changes; no new production
service, provider, storage or model family. Existing tenant/product/workspace,
privacy, methodology and human-review authorities remain unchanged.

## Versioned workloads

Each immutable profile records identity/version, title/category, execution mode,
fixture version and implementation digest, warmups, measured samples, requested
concurrency, correctness gates, required metric budgets, privacy classification,
expected failures and environment. Defaults are one warmup, eight measured
operations, two concurrent lanes. Limits are 100 warmups, 1024 samples and 16
threads. One operation is the complete bundle below, not an individual SQL
query, request, record, model token or report item.

| ID | Measured operation bundle |
|---|---|
| api.health.read.v1 | Real health route and exact response |
| api.authenticated.context.v1 | Real session validation/context, missing/invalid auth, foreign workspace and denied product |
| api.authenticated.navigation.v1 | Real app-shell with equivalent authorization/isolation checks |
| api.readiness.synthetic.v1 | Real readiness HTTP 200/503, independent PostgreSQL/Redis/storage failures and sanitized thrown check failure |
| data.ingestion.synthetic.v1 | CSV/JSON/XLSX inspection at 8/512 rows, CSV/JSON materialization, member/aggregate ZIP guards, six persisted inspection jobs and terminal replay |
| simpa.analytics.synthetic.v1 | Aggregate synthetic OLS at 16/256 observations, known slope, sample accounting and non-causal result |
| ordo.forecast.synthetic.v1 | Explicit naive/seasonal-naive at 16/128 periods, three-step forecast, rolling origins and exact metrics, unsupported-family/seasonality failure |
| report.render.synthetic.v1 | Two persisted synthetic draft versions, 2/32 sections with 32 items each, all three renderers and HTML escaping |
| ai.stub.synthetic.v1 | Local stub job plus unbound timeout with no heuristic fallback; sensitive local-only policy and exact fallback registration checks |
| ai.circuit.synthetic.v1 | Registered timeout/fallback with pending human review, unbound timeout failure and deterministic closed/open/half_open/closed |

Fixture/reference construction and RQ dispatch-contract preflights are outside measurement. Dispatch success/persisted queue identity, 900-second timeout and safe enqueue failure are mandatory before data/AI profiles run; their bounded preflight digest is included in every result fingerprint. Each lane owns its own
SQLite database and session/client lifecycle, with foreign keys enabled. No
SQLAlchemy session is shared concurrently. The reference digest excludes raw
API/session/tenant identity and AI text; actual outputs must match it while
independent semantic assertions enforce correctness. Tests also cover safe HTTP
503/recovery mapping, RQ dispatch failure, timeout translation through a mocked
HTTP transport, scenario != forecast and NOT_ESTIMATED impact.

Patches are installed before concurrent work and restored on exit. Workload
profiles execute serially within the suite; independent operations within a
profile execute concurrently. Run this isolated suite as a separate process,
not concurrently with application traffic in the same Python process.

## Measurement and evidence

Nearest-rank percentile: sort finite non-negative samples, choose index
`ceil(q * N) - 1`, for `0 < q <= 1`. Empty input is unavailable (`None`), never
zero. p50/p95/p99 use exactly this rule. Measured elapsed wall time must be finite
and strictly positive. Throughput is **all completed measured operations / wall
seconds**, including failed operations. Warmups are excluded from timing/count
metrics; any warmup correctness failure still blocks acceptance. Latency starts
inside the worker and includes the operation bundle; wall duration also includes
executor scheduling. This is not external queue-wait measurement.

Success, expected failure and correctness are separate. Unexpected exceptions
become only `unexpected_exception`; raw exception text is never serialized.
Expected operation failures require a declared bounded code and correct failure
semantics. Current bundles verify expected failures internally and return success
only when the entire bundle passes. A mismatch, missing sample, invalid duration,
authorization success or leaked scope cannot be offset by faster timing.

Budget classes are exactly CORRECTNESS, LATENCY_THROUGHPUT, RESOURCE, RESILIENCE.
States are HARD_GATE, CALIBRATED, UNCALIBRATED, NOT_APPLICABLE, UNAVAILABLE.
Correctness and resilience failure budgets are zero HARD_GATE. Timing remains
UNCALIBRATED. Resource is UNAVAILABLE (`not_portable`); no absolute RSS/CPU gate is
claimed. Compose memory limits are configuration facts only.

CALIBRATED means repository acceptance only. It requires accepted synthetic
measurement and contract digests, at least three repeated runs, an observed
bound and a safety margin greater than one. Upper latency thresholds equal
observed bound times margin; lower throughput thresholds divide by margin.
A later accepted calibration must demonstrate stability and document its
provenance. The schema validates metadata, not human approval authenticity.
The R1 candidate does not invent an acceptance threshold from one machine run.

Canonical evidence is stable sorted JSON. Contract SHA-256 excludes measured
timing; the evidence SHA-256 includes measurements and derived summary. Validation
recomputes fingerprints, counts, quantiles and acceptance. Closed models forbid
arbitrary metadata, free-form failure strings and identity/secret fields.
Repository SHA identifies committed source; the outer runner's candidate
fingerprint identifies the complete unstaged candidate. Fixture digests also
bind the scenario implementation. No host/user/IP/path is in canonical evidence.
Every record explicitly contains:

```text
PRODUCTION_CAPACITY_VERIFIED=false
SERVER_VERIFIED=false
```

## Local execution and acceptance ownership

From the canonical repository, using the existing environment:

```sh
.venv/bin/python -m tools.performance.run_isi26 > /tmp/isi26-performance.jsonl
.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_isi_26_*.py
.venv/bin/ruff check tools/performance tests/test_isi_26_*.py
.venv/bin/python tools/ci/policy_check.py
git diff --check
```

The CLI validates every emitted evidence record and exits nonzero for failed
correctness or calibrated budgets. stdout is canonical JSONL; runtime diagnostics
remain on stderr. Evidence output is external to the exact repository mutable
surface. The package runner owns final compile/Ruff/mypy, regression set, native
PostgreSQL acceptance, exactly one full local pytest run, surface/locked-contract
verification and candidate fingerprint. Independent analysis and human review
follow runner PASS. This candidate does not self-issue runner/analyzer markers.

Required regressions retain ISI-18/19/20, ISI-22G/23E governed synthetic E2E,
ISI-24C/24E forecast/workflow, ISI-25B runtime/promotion/XAI, production workflow
lock and server deployment no-mutation contracts. Native PostgreSQL and recovery
rehearsal remain runner gates; isolated SQLite is not substitute evidence.

## Limits and protected boundaries

These measurements do not prove production SLOs, shared DB/Redis contention,
real provider throughput, queue wait, live storage latency, recovery RPO/RTO or
server capacity. Reports are persisted synthetic drafts, not institutional
publication approval. Synthetic OLS is an engine test, not a newly validated
methodology or LISI formula. Forecast families are explicit; unsupported effects
remain NOT_ESTIMATED. AI fallback remains review-required, sensitive SIMPA remains
local-only, and no real Ollama model is called.

Allowed evidence environments are LOCAL_REPOSITORY, LOCAL_DISPOSABLE_POSTGRES,
and LOCAL_DISPOSABLE_SERVICES only through existing acceptance tooling. The CLI
uses LOCAL_REPOSITORY. ISI-28 exclusively owns live-server mutation and capacity
verification. Central ingress, public endpoint, Krcuga and OralScanXAI are strict
non-targets. Hosted full CI remains manual/undispatched. No dependency, migration,
Compose, deploy or .github changes are authorized.

```text
R1_STAGE_COMMIT_PUSH=PASS
R1_REMOTE_EQUALITY=PASS
GITHUB_ACTIONS_DISPATCH=NO
SERVER_MUTATION=NO
CI_VERIFIED=NO
PRODUCTION_CAPACITY_VERIFIED=NO
SERVER_VERIFIED=NO
```

The pre-finalizer candidate previously carried `STAGE_COMMIT_PUSH=NO`; that marker is retained only as historical candidate evidence, not as the current accepted-main state.

## Historical governance regression recovery

The initial R1 regression gate found three historical governance assertions that also failed on the exact untouched baseline. The original blocker classification remains valid as evidence, but the correction is now explicitly authorized through `ISI-26-R1-R1`.

Recovery semantics:

- `tests/test_isi_24e_closeout_contract.py` reads its transition-state evidence from the accepted Phase-24 closeout bookkeeping checkpoint `7e4db145c285aaff7a96f9c37279c44477f4432f`;
- `tests/test_isi_25b_governance_contract.py` reads its 25B-candidate/FHR1 mutable status and frozen-byte evidence from `7e11ee2a6f7546eacc3207e15cacfc35f6d04f3e`;
- all fourteen original `FROZEN_FHR1_SHA256` constants remain unchanged;
- current live status/task/MasterPlan/runtime bytes are no longer incorrectly required to equal an old recovery snapshot;
- no test is skipped, xfailed, deleted or weakened;
- no runtime behavior is changed by this recovery;
- no Codex, server, hosted CI, staging, commit or push is authorized.

The recovery package must re-run the formerly failing assertions, both complete historical test files, the original R1 regression set, native PostgreSQL acceptance and one full local regression before R1 may proceed to independent analysis.


## Human-review hosted-CI portability recovery

R1-R1C completed the local acceptance lane: focused/regression checks, synthetic performance evidence, native PostgreSQL acceptance and the final full local regression passed. Assistant human review then identified one repository-test portability blocker: the historical governance recovery used ancestor `git show`/historical-diff reads, but the hosted `tests` job uses the default shallow `actions/checkout@v4`. A later manual hosted acceptance could therefore fail despite a correct current candidate.

`ISI-26-R1-R1D` resolves that blocker without changing workflow/runtime behavior. Historical Phase-24 transition evidence and FHR1/25B candidate-state evidence are materialized in `automation/specs/ISI-26-R1-HISTORICAL-GOVERNANCE-EVIDENCE.json`. The manifest records the already verified authority SHAs, the original fourteen FHR1 SHA-256 values and accepted 25A foundation artifact hashes. Governance tests consume that repository evidence directly and therefore remain valid in shallow checkouts. No skip/xfail, workflow fetch-depth change, current-state rollback, runtime change, dependency, migration, server, staging, commit or push is authorized.

The R1-R1A native PostgreSQL PASS and synthetic performance PASS are inherited because R1-R1D changes only tests/documentation/evidence. One complete local regression is required after the recovery before renewed human review.


## R1-R1D manifest transcription recovery

The R1-R1D targeted governance gate validated the self-contained evidence approach and shallow-checkout portability, then exposed two package-only defects before full-regression continuation: the Phase-24 closeout test retained one final live-MasterPlan assertion for a historical phrase, and the evidence manifest mistyped exactly one FHR1 SHA256 (`src/platform/ai/models.py`).

`ISI-26-R1-R1E` corrects those two defects only. The historical Phase-24 overall-state marker is stored in the same self-contained evidence record, and the FHR1 hash is restored to the original accepted/test value `2ef6b8bc8d8bcefbdeaccfec6f1c229eb5980e81ff49b624b64620bbbe87b86f`. The other thirteen FHR1 hashes and all accepted 25A foundation hashes remain unchanged. No runtime, dependency, migration, workflow, deployment or server behavior is changed. One complete local regression is required before renewed human review.


## R1-R1F human-review governance/provenance recovery

Renewed human review after R1-R1E found two non-runtime blockers. First, the self-contained historical governance JSON was written below `automation/evidence/`, but the repository `evidence/` ignore rule hides new files there from Git status, candidate fingerprinting and review packaging. R1-R1F moves the unchanged verified record to `automation/specs/ISI-26-R1-HISTORICAL-GOVERNANCE-EVIDENCE.json` and updates all test/document consumers; the ignored local copy is removed.

Second, the R1 execution contract intentionally grouped 26A-D implementation into one large execution slice, but canonical live governance had incorrectly converted that execution grouping into task supersession. R1-R1F restores ISI-26A through 26E as formal coverage/gate checkpoint identities. R1 remains the grouped implementation execution candidate and removes the need for one Codex invocation per child gate; it does not erase or supersede the formal gates. ISI-26E remains the planned whole-phase closeout gate. No runtime, dependency, migration, workflow, deployment or server behavior changes.

## ISI-26E whole-phase closeout

Closeout authority is `automation/specs/ISI-26E-PERFORMANCE-RESILIENCE-CLOSEOUT.md` with machine-readable evidence in `automation/specs/ISI-26E-PERFORMANCE-RESILIENCE-CLOSEOUT-EVIDENCE.json`.

Accepted implementation identity:
- main SHA `e4b5b7f5927bc553fd616800d37beb5d115bb46e`;
- tree `9a30b280ba44798b987167c155f0be6ccc13776e`;
- R1 candidate fingerprint `98653d20a5223d4f6be66f3ee2017f998865b00ecb08a0950c07123d60dc2e24`;
- assistant human review `PASS`;
- independent analysis `PASS`;
- exact staging/commit/normal push/remote equality `PASS`.

Whole-phase audit result: no `REMOVE_BEFORE_NEXT_SLICE` finding remains. The formal 26A performance-contract gate, 26B API/auth/readiness gate, 26C data/statistics/forecast/reporting gate and 26D AI resilience gate are satisfied through the accepted grouped R1 implementation. 26E closes the phase-level evidence/governance audit without additional runtime implementation.

Accepted limitations/deferrals are explicit rather than hidden: latency/throughput remain `UNCALIBRATED` wherever the locked calibration policy does not support a stable threshold; portable resource evidence remains `UNAVAILABLE`; hosted full CI is not dispatched until an explicitly approved ISI-27 release-candidate checkpoint; production capacity and live-server verification remain ISI-28-only. These are not open ISI-26 implementation defects and must not be converted into fabricated production claims.
