# ISI-09 HOTFIX-2 — Methodology Guard Contract Recovery

## Context
ISI-09 HOTFIX-1 correctly replaced `op.bulk_insert(versions, ...)` with an offline-safe explicit `INSERT ... CAST(:output_schema AS JSON)` because Alembic `--sql` cannot literalize Python dictionaries into PostgreSQL JSON columns.

The existing ISI-09 methodology guard test still asserted the obsolete implementation detail `op.bulk_insert(versions`, so it failed even though the migration semantics were preserved and the database upgrade to `20260828_0008` succeeded.

## Scope
- Keep the already-correct offline-safe migration unchanged.
- Replace the formatting/implementation-specific methodology guard assertion with semantic assertions.
- Preserve the real safety invariant: ISI-09 must not seed any validated SIMPA indicator methodology.
- Verify the SIMPA synthesis prompt and its version are still seeded.
- Verify the prompt-version JSON schema remains offline-safe.
- Run focused and full regression suites.

## Non-goals
- No migration change.
- No schema downgrade/upgrade.
- No AI runtime change.
- No Ollama/provider change.
- No UI change.
- No task closeout, commit or push.

## Expected state
- committed HEAD: `a6b5702`
- ISI-09 task: `ready`
- Alembic: `20260828_0008`
- HOTFIX-1 offline-safe migration already present.
