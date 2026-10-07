# ISI-29A — Graphical XAI for persisted SIMPA/ORDO results

## Status
IMPLEMENTED / REVIEW_VERIFIED — unstaged runtime candidate exists; NOT CI_VERIFIED. Owner authorized execution of 29A–29F on 2026-10-07. Local runner, independent analyzer and synthetic visual/keyboard review PASS: 23 focused tests, 1203 regression passes, 43 existing native-lane skips, zero failures/errors. Final current fingerprint is in automation/evidence/ISI-29A/human-review.json; owner exact commit approval remains required. Parent plan: `docs/roadmap/ISI-29-XAI-GIS-ENTITY-FINDINGS-PLAN.md`.

## Baseline
Exact main `374dda3db89f6fb87dde7f5b761642440da17bef`, tree `13051743a26f78a50f3a664518c643ff540bd9f9`; direct remote equality confirmed. Required acceptance #96 / 37515814577 completed/success, all 12 jobs success. One canonical worktree, empty index/stash at bootstrap. This planning candidate is an explicit governance companion prestate: runner must hash its complete allowlist before runtime edits and reject any unrelated dirty file. A later committed baseline requires renewed SHA/CI reconciliation; no blind baseline substitution.

## Canonical bootstrap evidence
Complete MasterPlan-first read, AGENTS, tasks/STATUS, ADR-0025, 24A/24B spatial contracts, 28 R3 and ops release/development rules reviewed. Actual statistical_xai, analytics_xai, Streamlit consumers, statistical model engine, ORDO forecast/spatial engine, ingestion/entity governance and existing contract tests inspected. DONE/PARTIAL/MISSING/DRIFT and classified findings are in parent plan section 1/6. No incompatible unclassified legacy is allowed to pass runner preflight.

## Dependencies
Existing accepted statistical/forecast result contracts and 23D/24D Help. No new source data/model/policy/dependency is required for 29A. Empty live workspace cannot prove chart acceptance; synthetic fixtures demonstrate software behavior and clearly labeled controlled data is required later for domain/live acceptance.

## Objective
Render faithful graphical explanations beside existing evidence tables for actual persisted results, with accessible tabular parity and truthful unsupported states. This is the first bounded part of the broader XAI/GIS request.

## Existing architecture
Domain builders remain authorities: `build_statistical_xai` and `build_forecast_xai`. Streamlit is presentation; backend scoping/auth and result immutability remain intact. Existing result JSON provides coefficients and confidence bounds, forecast points/intervals and backtest records. No refitting inside UI.

## Legacy/drift audit
Parent plan section 6 applies. Two obsolete active codex-isi rules and mutable latest checkpoint status are reconciled in governance companion. Historical unsupported states/accepted phases and identity-only spatial contracts are compatibility/history, not fake current capability. ORDO overview permission bug is reserved for named 29C contract, outside this slice.

## Exact mutable surface
Only these 15 runtime/task paths, plus the eight explicit governance companion paths below, may change in the eventual 29A candidate:

1. `src/streamlit_app/xai_charts.py` (new fixed-template safe renderer/read model)
2. `src/streamlit_app/simpa_analytics_workspace.py`
3. `src/streamlit_app/ordo_analytics_workspace.py`
4. `src/streamlit_app/simpa_help_workspace.py`
5. `src/streamlit_app/ordo_help_workspace.py`
6. `docs/help/SIMPA-USER-GUIDE.md`
7. `docs/help/ORDO-USER-GUIDE.md`
8. `docs/help/ISI-HELP-COVERAGE-MATRIX.md`
9. `tests/test_isi_29a_xai_charts.py` (new)
10. `tests/test_isi_29a_xai_ui_contract.py` (new)
11. `tests/test_isi_29a_xai_help_contract.py` (new)
12. `tools/qa/run_isi29a.py` (new deterministic runner)
13. `tools/qa/analyze_isi29a.py` (new read-only analyzer)
14. `automation/specs/ISI-29A-GRAPHICAL-XAI.md`
15. `docs/roadmap/ISI-29-XAI-GIS-ENTITY-FINDINGS-PLAN.md`

Governance companion set (eight total, including repeated spec/plan): MasterPlan, TECHNICAL_DOCUMENTATION.md, automation/STATUS.md, automation/tasks.json, docs/ops/ISI-AUTONOMOUS-DEVELOPMENT-LOCK.md, automation/specs/TASK-TEMPLATE.md, this spec and parent plan. Evidence under ignored `automation/evidence/ISI-29A/`; no secrets/raw institutional payloads. All other paths frozen. Implement runner and independent analyzer before invoking a CLI implementation handoff or runtime editing; verify planning prestate fingerprints and exact allowed surface.

## Canonical system inventory impact
INV-A22/M22 target rows become PARTIAL only after verified 29A runtime candidate; INV-A10/A11/A18/A19/A21 coverage is extended for new graphical actions. No GIS/entity/SHAP target row becomes as-built from 29A. Preserve accepted predecessors and named deferred inventory cleanup.

## Implementation-tool authority
If CLI handoff is used, standard `codex` authenticated with the canonical owner Outlook account; locked MD + runner + independent analyzer, per superseding 2026-09-19 owner decision. Analyzer never invokes Codex or mutates repository/control state. No stage, commit, push, deploy or production secrets.

## Locked boundaries
SIMPA aggregate non-causal results; ORDO forecast vs scenario and NOT_ESTIMATED; unchanged model families/output units; existing Organization/Membership/Role/Product/Workspace checks. Numerical authority remains persisted deterministic domain result. Renderer must not infer missing fields or manufacture confidence/diagnostic labels.

## Required behavior
1. SIMPA coefficient point + stored CI plot, exact term labels and family/link-scale caption. Zero coefficient remains valid. No CI: explicit unavailable state, not zero-width interval. Non-finite/malformed bounds: safe unavailable warning; no silently corrected evidence.
2. ORDO forecast points and stored lower/upper bounds, exact horizon/order and interval-method caption. Historical actual-vs-forecast view uses persisted backtest records; overlapping origins remain distinct selectable origins. Never join separate folds into invented continuous history. No history from raw source read.
3. NOT_ESTIMATED shows reason and existing Help; no artificial zero line/points. Unsupported SHAP/feature-importance remains explicit and references pending 29D.
4. Table/JSON evidence remains reachable beside chart; model/result/provenance identity and methodological notices visible. Deterministic renderer output is derived only from accepted schema fields; unknown legacy version gives explicit unavailable fallback.
5. Prefer dependency-free fixed-template SVG generated from validated numeric plot data; escape all labels and enforce bounded row/text/payload limits. No scripts, events, foreignObject, user-controlled CSS/URLs or arbitrary raw SVG injection. Document selected finite limits in implementation before test fixtures; truncation is explicit with full permitted table retained.
6. Responsive chart sizing, keyboard-readable controls, title/description, plain text/table alternative and clearly labeled SR/EN terminology per existing UI convention. Same outcome for authorized reader/admin; chart cannot fetch broader data.
7. Do not draw residual/calibration charts when required raw points are absent. Display actual stored diagnostics without invented thresholds.
8. Update full 0.5A Help checklist for chart viewing, CI/scale interpretation, fold selection, unavailable and error recovery. Existing VERIFIED matrix means old accepted actions only; new chart actions begin MISSING/PARTIAL and promote only with evidence.

## Impact
- Database/migrations: NONE; no fitted result or old row mutation.
- API: NONE; consume existing authorized result responses.
- UI: two existing analytics surfaces and contextual Help; no new product/menu.
- Workers: NONE.
- Configuration: NONE; no dependency or external chart service.

## Security and privacy
Safe text/SVG escaping and bounded data; no source fetch or external URL. Do not cache across scope or write sensitive chart labels to audit evidence/screenshots. No live tenant data required locally. UI visibility never replaces backend permission checks.

## Tests
Focused coverage: expected finite plot coordinates/data, exact CI/zero/missing preservation, malformed bounds/unknown schema; hostile labels/oversized arrays; every existing SIMPA family scale; ORDO folds/intervals/non-estimated; chart/table parity; permission consumer unchanged; Help/matrix new action lifecycle. Existing 23D/24D and all regression suites remain intact. Responsive desktop 1440/1280 and mobile 390/768, keyboard and no horizontal clipping checked on a local preview with synthetic authorized results.

## Exact acceptance commands
After runner/analyzer exist:

```
.venv/bin/python tools/qa/run_isi29a.py
.venv/bin/python tools/qa/analyze_isi29a.py
.venv/bin/python -m pytest -q tests/test_isi_29a_xai_charts.py tests/test_isi_29a_xai_ui_contract.py tests/test_isi_29a_xai_help_contract.py
.venv/bin/python -m pytest -q
.venv/bin/python -m tools.ci.policy_check
git diff --check
```

Runner must fail closed if canonical interpreter/dependencies are absent; use existing workstation requirements, no package installation fallback. Runner records full existing quality/architecture gates as applicable and full regression, no test weakening. Independent analyzer binds source/diff/report hashes and rejects missing/failed gates or schema/API/dependency/server changes. Repeated analyzer reads must not change candidate/evidence identities.

## Evidence
Sanitized baseline/prestate/candidate manifests, commands/results and focused/full/quality reports, renderer/schema reference comparisons, responsive/keyboard capture inventory, independent-analysis report and human review under `automation/evidence/ISI-29A/`. No passwords/cookies/tokens or institutional payloads in captures. Any unavailable lane remains explicit and blocks its corresponding claim.

## Non-goals
GIS geometry/maps/joins, SHAP generation, numerical fitting, extraction/NER/OCR, new model families, forecast refit, policy thresholds, backend permission fix, SMTP/backups/server changes. Parent plan owns subsequent packages.

## Forbidden changes
No domain computation/semantic changes, migration, dependency upgrades, workflow triggers, weakened tests, alternate worktrees/branches, staging/commit/push or server action.

## Human review and owner gate
Assistant reviews exact candidate after deterministic runner/independent analysis. Existing feature instruction authorizes local implementation. Exact staging/commit/push still requires owner approval of that concrete candidate; hosted checkpoint separately approved with usage pre/post.

## Completion definition
IMPLEMENTED only after required local gates and reviewed exact unstaged candidate. REVIEW_VERIFIED requires no unresolved technical blocker. CI_VERIFIED only after approved commit/push and all required exact-main jobs completed/success. No whole ISI-29 or full-production claim from this first slice.

## Deferred server verification
DEFERRED_SERVER_VERIFICATION. This task makes no server contact or mutation; later deployment remains ISI-28-controlled.


## Candidate read-model and preview record — 2026-10-07

Dependency-free fixed-template SVG; max 24 coefficients, 60 plot points, 40 selectable origins, 128 label characters, 128000 SVG bytes; responsive width capped at 800px. Missing bounds are explicit; empirical forecast interval is not forced to contain point. Unknown schemas, malformed/nonfinite inputs and unrenderable numeric range fail closed. No sources, model refit, dependencies, APIs or migrations changed. Existing tables/JSON remain. In-app Help extends existing SIMPA-H11/ORDO-H10 ten-field topics; new matrix actions remain PARTIAL until package closeout. Synthetic preview at 1440/1280/768/390 and keyboard origin selection passed. Final gate and candidate identity: ignored `automation/evidence/ISI-29A/acceptance.json` and analyzer output. No hosted/server acceptance.


29A local verification record: IMPLEMENTED / REVIEW_VERIFIED candidate; 23 focused and 1203 regression passes, 43 existing native-lane skips, zero failures/errors. Four responsive widths and keyboard backtest selection verified on synthetic local preview. Exact report/fingerprint: `automation/evidence/ISI-29A/human-review.json`. No CI_VERIFIED or server deployment of 29A. 29B–F remain unimplemented; 29B read-only preparation recorded separately.
