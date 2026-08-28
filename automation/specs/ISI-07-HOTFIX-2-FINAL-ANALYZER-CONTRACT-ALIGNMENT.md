# ISI-07 HOTFIX-2 — Final Analyzer Contract Alignment

## Purpose

Align the ISI-07 static audit/final-analyzer contract with the accepted ISI-07 HOTFIX-1 UI.

HOTFIX-1 intentionally replaced the development-stub UI diagnostic with a real local Ollama foundation diagnostic. The final analyzer still required the old literal `Development-only` in `src/streamlit_app/ai_workspace.py`, so the final analyzer failed even though the accepted implementation and HOTFIX-1 regression suite were correct.

## Scope

- Update `tools/audit_shared_ai_foundation.py` to assert the accepted local Ollama diagnostic contract.
- Add a regression test that prevents the stale `Development-only` UI marker from being reintroduced as a final-analyzer requirement.
- No runtime behavior changes.
- No database changes.
- No migration.
- No task-state changes.
- No commit or push.

## Required baseline

- branch: `main`
- HEAD: `d3c27d7`
- working tree: clean
- ISI-07 task: `done`
- ISI-07 visual/AI QA evidence: `PASS`
- Alembic: `20260828_0006`

## Accepted audit contract

The Streamlit AI workspace must contain:

- `Shared AI Foundation`
- `Lokalni Ollama foundation test`
- `_render_local_ollama_diagnostic`
- an Ollama provider-type selection

The old `_render_dev_diagnostic` UI path must remain absent.

## Non-goals

This hotfix does not change AI models, policy, provider routing, RAG isolation, database schema, launcher behavior, or the accepted browser experience.
