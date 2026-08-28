# ISI-09 HOTFIX-1 — Offline JSON Migration Recovery

## Purpose
Recover the partially installed ISI-09 workspace after Alembic offline SQL rendering failed while seeding the `simpa.monitoring.synthesis` prompt version.

## Root cause
`op.bulk_insert()` was asked to literalize a Python `dict` into a SQLAlchemy `JSON` column while Alembic was running with `--sql` / `literal_binds=True`. PostgreSQL JSON has no generic SQLAlchemy literal renderer for a Python dict in this path, so offline compilation failed before the database migration was applied.

## Recovery strategy
Keep the prompt row `bulk_insert` unchanged, but replace the prompt-version JSON `bulk_insert` with an explicit parameterized `INSERT` that:

- serializes the schema with `json.dumps(..., sort_keys=True)`;
- binds it as `Text`;
- uses `CAST(:output_schema AS JSON)` in SQL;
- remains valid for both Alembic offline SQL rendering and normal online PostgreSQL execution.

## Safety invariants
- Expected Git branch: `main`.
- Expected committed HEAD: `a6b5702`.
- Expected partial task state: `ISI-09-SIMPA-ANALYTICS-AI = ready`.
- Expected database state before recovery: `20260828_0007`.
- Expected database state after recovery: `20260828_0008`.
- No reset, restore, clean, commit, or push.
- No reinstallation of the full ISI-09 payload.
- No changes to SIMPA analytics runtime behavior, AI policy, Ollama model selection, or UI.

## Acceptance
1. Recovery patch applies idempotently to the installed ISI-09 migration.
2. Focused regression test passes.
3. `alembic upgrade 20260828_0008 --sql` renders successfully and contains the SIMPA prompt JSON cast.
4. Native PostgreSQL upgrades from `0007` to `0008`.
5. Focused ISI-09 suite passes.
6. Native PostgreSQL acceptance passes.
7. Full regression suite passes.
8. Docker Compose config and `git diff --check` pass.
9. ISI-09 remains `ready` pending browser/AI QA.
