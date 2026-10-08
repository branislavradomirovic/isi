# ISI-29E — versioned entity/claim extraction and human review

Status: LOCKED local implementation contract, 2026-10-08.
Baseline: main 95fec43590e9b1d3eb44d55867666581118ec650; origin/direct GitHub equality, clean single worktree/index/stash. Required acceptance37746165918 completed/success, all12 jobs; recorded signed preproduction deployment. No new server action in29E.

## Bootstrap and legacy audit
DONE:29A-D accepted code/CI/scoped server evidence. PARTIAL:governed knowledge metadata and document registration. MISSING:anchored extraction/review, entity disambiguation, separate extraction fixtures. DRIFT:mutable29D candidate/#96 current ledgers — REMOVE_BEFORE_NEXT_SLICE, synchronize in this candidate. Historical checkpoints/selected-only AI jobs — LEGITIMATE_HISTORY/REQUIRED_COMPATIBILITY. Identity-only ORDO, historical analytics, staging safety assets — REQUIRED_COMPATIBILITY. Broader inventory historical future25/24D notes — REMOVE_IN_NAMED_PHASE(ISI-29F). No duplicate extraction pipeline or alternate worktree; no new dependency/provider/CI exemption.

## Architecture and required behavior
Shared transport/persistence/strict anchoring; separate domain-owned prompts and gazetteers. TXT document sources must be active, succeeded, AVAILABLE, GOVERNED/FROZEN, aggregate nonpersonal, classified with purpose/owner and local-analysis AI permission. Digital normalized tables consume only existing validated/frozen governed snapshot plus LOCAL_ANALYSIS eligibility; never raw CSV parsing or quarantine bypass. UTF8 exact document spans or immutable normalized cell locators; source/version/hash and language preserved. Bounded200KB bytes/12000 characters/200 cells/20000 serialized request characters/100 mentions/100 claims; accepted retrieval100 claims/2MB; oversized inputs rejected, never silently truncate. No URL fetch, PDF/DOCX parser, OCR/VLM, geocoder, model installation or promotion.

Explicit create requires data.read+ai.run, registered local chat model and separate fixed versioned SIMPA/ORDO prompt; local-only reviewed policy, existing AI queue/worker and attempts. Pin request/source/model/prompt/policy/code identity. Worker rechecks authorization/source before provider call and after return; strict nested schema and exact quotes/spans, duplicate IDs, entity types, numeric/unit/period transcription, citations checked. Unsupported/malformed/ungrounded results fail closed without displaying provider bodies. Claims are quoted atomics with observation/model_output/assumption/AI_inference kinds, supporting and contradicting citations; no derived numerical authority or confidence. Each field uses exact source anchor or explicit missing. Geographic mention suggestions use exact names in separately scoped gazetteers; even unique match remains unverified until human attestation; ambiguous/unmatched remain unresolved, no coordinates inferred.

Immutable extraction envelope and append-only review decisions bind hashes/creator/time/job+attempt. EXTRACTED_UNVERIFIED -> REVIEWED_ACCEPTED or REJECTED; reviewer data.validate, explicit attestation and fingerprint/unique final decision; corrections new request/version, no overwrite. Review selected claim territory separately from entity location/document scope using existing scoped validated polygon geometry+date and preserved provenance. No geometry identity assigned by LLM; unresolved allowed. Human entity identity selections pin scoped kind/id/key/name and revalidate current registry; source cell fields may share a record only with exact individual supporting citations. Source invalidation/purge/reclassification/retirement and geometry retirement/date/binding drift block current read/review/retrieval. Rejected/unverified excluded from accepted territory/period retrieval. Cancelled pending bindings block provider execution; retry is explicit new idempotency key, duplicated create returns same binding and no redispatch. Dispatch failures exposed sanitised; no raw text in audit/evidence.

Existing Data UI:explicit load, source/snapshot+model+language authoring, job/retry/cancel and review queue; raw quotes plain text; details provenance/alternatives/claims/review/filters; permission-gated controls with backend authority. Ten-item Help guide/matrix and actual desktop/mobile synthetic browser proof required. No exports/report integration until29F.

Canonical system inventory impact: INV-A08/A22,B29,C45,D04,M22; document new persistence/worker guard/prompt/gazetteer/UI ownership in same candidate. SIMPA/ORDO only.

## Exact mutable surface
- `TECHNICAL_DOCUMENTATION.md`
- `automation/STATUS.md`
- `automation/tasks.json`
- `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
- `docs/roadmap/ISI-29-XAI-GIS-ENTITY-FINDINGS-PLAN.md`
- `docs/help/ISI-HELP-COVERAGE-MATRIX.md`
- `docs/help/ISI-EXTRACTION-GUIDE.md`
- `automation/specs/ISI-29E-ENTITY-CLAIM-EXTRACTION.md`
- `src/platform/extraction/__init__.py`
- `src/platform/extraction/contracts.py`
- `src/platform/extraction/models.py`
- `src/platform/extraction/service.py`
- `src/domains/simpa/extraction_adapter.py`
- `src/domains/ordo/extraction_adapter.py`
- `src/platform/models.py`
- `src/api/extraction_routes.py`
- `src/api/app.py`
- `src/workers/ai_jobs.py`
- `src/streamlit_app/extraction_api.py`
- `src/streamlit_app/extraction_workspace.py`
- `src/streamlit_app/data_workspace.py`
- `migrations/versions/20261008_0037_extraction.py`
- `tests/test_isi_29e_contracts.py`
- `tests/test_isi_29e_service.py`
- `tests/test_isi_29e_ui_api.py`
- `tests/test_isi_29e_native_postgres.py`
- `tests/evals/SIMPA-EXTRACTION-v1.json`
- `tests/evals/ORDO-EXTRACTION-v1.json`
- `tools/qa/run_isi29e.py`
- `tools/qa/analyze_isi29e.py`

## Acceptance
.venv/bin/python tools/qa/run_isi29e.py: strict changed-file Ruff, policy, mypytools/ci, focused contracts/service/API/UI/eval tests zero skips, isolated loopback PG17 migration0036->0037->0036->0037 constraints, full regression (existing native lane skips declared), pipcheck/diffcheck. Separate synthetic annotated fixtures for SIMPA/ORDO Latin/Cyrillic/EN, ambiguity/injection/citation/numeric tamper and isolation; software correctness only, institutional extraction quality UNCALIBRATED until real adjudicated corpus and frozen owner thresholds. Independent read-only analyzer binds exact files/logs/XML/browser; assistant exact review then standing approved verified commit/push. No hosted checkpoint or deployment in this development slice;29F owns whole-plan acceptance.

29E final governance review: general AI jobs retain metadata only for extraction; successful raw input/output/structured copies are cleared in the worker transaction. Quotations remain solely in source-revalidated extraction artifacts, preventing general AI/report reads from bypassing source withdrawal (REMOVE_BEFORE_NEXT_SLICE, resolved in this candidate; legacy non-extraction jobs REQUIRED_COMPATIBILITY). Code fingerprint pins service/contracts/models and the selected product extraction/spatial adapter. Empty pending request text and runtime-policy/model parameter drift fail before provider execution. Signed/decimal/date fragments cannot silently become partial numeric value/period tokens; spelling stays verbatim without numerical interpretation or domain formula. Exact final gates required after these bounded corrections.
