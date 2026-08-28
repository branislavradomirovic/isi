# ISI-07 Browser / AI QA Matrix

## Preconditions
- FastAPI: `http://localhost:8004`
- Streamlit: `http://localhost:8504`
- QA launcher reports API smoke PASS and UI READY

## SIMPA-only
1. Login as `isi05-simpa@example.com`.
2. AI navigation is visible only when `ai.run` is granted.
3. Active scope shows SIMPA and the selected workspace.
4. Foundation diagnostic job is clearly marked development-only.
5. A `sensitive` SIMPA diagnostic shows effective policy `local_only`.
6. ORDO jobs are not visible.

## ORDO-only
1. Login as `isi05-ordo@example.com`.
2. AI workspace scope is ORDO.
3. SIMPA jobs are not visible.
4. Generic foundation diagnostics do not claim ORDO domain analysis.

## Dual account
1. Login as `isi05-dual@example.com`.
2. Run/view a SIMPA diagnostic.
3. Switch to ORDO.
4. SIMPA private jobs disappear from the ORDO-scoped list.
5. Run/view an ORDO diagnostic.
6. Switch back to SIMPA and confirm ORDO private job is not listed.

## Registry / provenance
- model key, provider, model name, prompt key/version and policy are visible;
- job status, attempts, latency and review status are shown;
- no raw request/output appears in audit/provenance summaries beyond the job detail intended for the active tenant scope;
- no fabricated production metrics are shown.

## Failure behavior
- wrong password remains controlled;
- unavailable Ollama is reported as capability state, not a traceback;
- dev stub is labelled and only available while the QA launcher explicitly enables it;
- no cross-tenant/product resource can be fetched by changing browser-side IDs.
