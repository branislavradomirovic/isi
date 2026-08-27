# ISI-04 HOTFIX-2 — Regression Contract Alignment

## Purpose

Recover ISI-04 after the seed-module import fix exposed two stale regression contracts in the full test suite.

This hotfix does **not** change public-site implementation, database schema, publication state, redirect activation, or migrated content.

## Observed failures

1. `tests/test_health.py::test_public_home_is_jinja_and_names_both_domains`
   expected `/` to render with the default application configuration. ISI-04 intentionally keeps all public pages in `draft`, while `PUBLIC_PREVIEW_DRAFTS` defaults to false. The correct production-safe default is therefore HTTP 404 until a later explicit publication/cutover phase.

2. `tests/test_isi_03c_contract.py::test_task_and_required_artifact_contract`
   expected `ISI-03C-MEDIA-REDIRECT-VALIDATION` to remain `ready`. ISI-04 correctly advanced the predecessor task to `done` and set ISI-04 to `ready`.

## Fix

- Replace the stale public-home regression with an isolated SQLite test asserting that draft content is hidden when draft preview is disabled.
- Keep the existing ISI-04 route test as the positive rendering contract: with local preview enabled, `/`, `/simpa/`, `/ordo/`, and `/en/` render successfully.
- Update the ISI-03C lifecycle contract from `ready` to `done`.

## Safety

- No Alembic migration.
- Alembic must remain `20260827_0003`.
- No public page may be published or archived.
- No redirect is activated.
- No source website mutation.
- No commit or push.
- Manual visual QA remains mandatory before the final analyzer.
