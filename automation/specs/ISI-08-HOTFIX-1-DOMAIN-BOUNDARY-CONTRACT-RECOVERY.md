# ISI-08 HOTFIX-1 — Domain Boundary Contract Recovery

## Trigger

The ISI-08 main runner successfully installed the SIMPA domain foundation, migrated native PostgreSQL from `20260828_0006` to `20260828_0007`, passed focused ISI-08 tests and native PostgreSQL acceptance, but the full regression suite failed on the pre-existing architecture contract:

`tests/test_architecture_contract.py::test_no_product_logic_is_smuggled_into_domain_boundaries`

The contract requires both `src/domains/simpa/__init__.py` and `src/domains/ordo/__init__.py` to remain empty package-boundary markers.

## Root cause

ISI-08 exported SIMPA catalog constants from `src/domains/simpa/__init__.py`. No runtime code relies on that convenience export. Product/domain code already imports concrete modules directly.

## Fix

- Restore `src/domains/simpa/__init__.py` to an empty file.
- Preserve all SIMPA domain logic in concrete modules such as `catalog.py`, `models.py`, `service.py` and `schemas.py`.
- Add a regression test that locks the empty SIMPA/ORDO package-boundary contract and verifies the catalog remains directly importable.

## Non-goals

- No database migration.
- No rollback of `20260828_0007`.
- No changes to SIMPA models, catalog contents, API, Streamlit UI, shared data or shared AI foundations.
- No task closeout.
- No commit or push.

## Expected baseline

- branch `main`
- HEAD `db99eb7`
- `ISI-08-SIMPA-DOMAIN-FOUNDATION` status `ready`
- Alembic `20260828_0007`
- partial/uncommitted ISI-08 implementation already installed

## Acceptance

- architecture boundary regression passes;
- focused ISI-08 suite passes;
- native PostgreSQL acceptance passes;
- full suite passes;
- Alembic remains `20260828_0007`;
- `git diff --check` passes.
