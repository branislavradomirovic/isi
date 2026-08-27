# ISI-04 HOTFIX-1 — Seed Module Import Recovery

## Trigger

ISI-04 stopped during focused test collection with:

`ModuleNotFoundError: No module named 'tools'`

The test imported application seed logic from the repository-level `tools/` directory. The project packaging contract installs `src*`, not `tools*`, so the test relied on an incidental working-directory import path.

## Fix

Move reusable SIMPA/ORDO public-page seed logic into the installable application package:

`src/public/platform_seed.py`

Keep `tools/seed_public_platform_pages.py` as a thin CLI wrapper only. Tests import the service from `src.public.platform_seed`.

## Safety

- no Alembic migration
- no schema mutation
- no publication
- no redirect activation
- SIMPA/ORDO remain draft-only
- resumes the already-applied ISI-04 working tree
- no commit / push

## Acceptance

- focused ISI-04 suite passes
- seed is idempotent
- native PostgreSQL has SIMPA/ORDO drafts
- Alembic remains `20260827_0003`
- full suite passes
- visual QA remains mandatory before final analyzer/commit
