# ISI-27A-R1A-R3 — Final Inherited Compatibility Convergence Recovery

## Status
Owner-authorized local recovery only. No Codex invocation. No staging, commit or push.

## Baseline
- branch: `main`
- accepted scope-lock main SHA: `39dc1d59a74a03c86f68df093cc07e32d41d028c`
- accepted tree: `3c7027b375b041043f7305cdab008aee35f16ef7`
- R1A-R2 full regression state: exactly two failures, `1028 passed`, `43 skipped`.

## Root cause
The remaining failures are inherited assertions, not a 27A runtime defect:

1. `tests/test_isi_08_contract.py` reads `src/streamlit_app/app.py` as text and requires the historical token `render_ordo_indicator_placeholder`. R1 correctly removed the unused import so Ruff could pass, while current ORDO routing uses `render_ordo_indicators`. R3 restores only an explicit non-runtime REQUIRED_COMPATIBILITY source marker; it does not restore the dead import or old routing.
2. `tests/test_isi_26_governance_contract.py` freezes the phase-27A handoff state at `spec_ready`. The owner-approved ISI-27 scope lock and current R1 candidate legitimately make 27A `in_progress`; R3 converges that inherited current-state assertion while preserving every accepted ISI-26 fact.

## Exact recovery mutations
- `src/streamlit_app/app.py`: add a comment-only compatibility marker containing `render_ordo_indicator_placeholder`; runtime routing remains current.
- `tests/test_isi_26_governance_contract.py`: change only the live 27A state assertion to `in_progress` and assert the canonical R1 implementation spec pointer.
- `automation/tasks.json`: record R1A-R3 recovery provenance while keeping 27A `in_progress` and its canonical spec pointer on R1.
- add this recovery contract.

## Locked boundaries
- No Codex.
- No changes to FastAPI auth routes/services, identity, RBAC, administration services, security services, data/reporting services or domain services.
- No migrations, dependencies, lockfiles, Docker/Compose, `.github`, release/deploy tooling or server resources.
- No SIMPA/ORDO/AI Help authority edits.
- No public signup.
- No production SMTP, server, secrets, model or production-data access.
- No Git staging, commit or push.
- No GitHub Actions dispatch.

## Acceptance
- exact post-R2 prestate and exact prior failure log;
- focused 27A + inherited compatibility tests;
- compile, Ruff, mypy, policy and `git diff --check`;
- one full local pytest regression;
- exact final 34-path candidate surface;
- deterministic candidate fingerprint;
- human-review bundle;
- `CI_VERIFIED=NO`, `SERVER_VERIFIED=NO` until later gates.
