# ISI-10 HOTFIX-1 — Native PostgreSQL Config Contract Recovery

## Problem
The ISI-10 runtime migration completed successfully and Alembic reached `20260828_0009`, but native PostgreSQL acceptance failed during test collection because `tests/test_isi_10_native_postgres.py` imported a non-existent module-level `settings` object from `src.core.config`.

The established repository database-test contract uses `src.core.database.build_engine()` / `build_session_factory()` instead of importing a global settings singleton.

## Scope
- replace only the ISI-10 native PostgreSQL test's configuration access;
- use `src.core.database.build_engine()`;
- preserve all ORDO table/catalog assertions;
- add a regression test preventing `from src.core.config import settings` from returning;
- rerun native PostgreSQL acceptance, focused ISI-10 tests and the full regression suite.

## Non-goals
- no runtime ORDO logic changes;
- no schema or migration changes;
- no task closeout;
- no commit or push;
- no downgrade/re-upgrade of the database.

## Required precondition
- `ISI-10-ORDO-DOMAIN-FOUNDATION = ready`
- Alembic is already `20260828_0009`
- partial ISI-10 implementation is present.

## Expected result
Native PostgreSQL acceptance uses the same database construction contract as prior ISI phases and the full test suite passes without changing Alembic state.
