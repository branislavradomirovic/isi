# ISI-03A — Legacy isi.rs Content Inventory

## Goal
Create a reproducible, read-only inventory of the current `isi.rs` website before any public redesign or content import.

## Baseline
- ISI-00/01 foundation committed.
- ISI-02A identity/access/workspaces committed.
- ISI-02B authentication lifecycle committed.
- ISI-02C authenticated app context committed.
- Native PostgreSQL schema remains at `20260827_0002`; ISI-03A does not change the database.

## Deliverables
- `src/public_migration/legacy_inventory.py`
- `tools/legacy_isi_inventory.py`
- `docs/migration/ISI-03-legacy-content-plan.md`
- generated `data/migration/legacy_isi/inventory.json`
- generated `data/migration/legacy_isi/pages.csv`
- generated `data/migration/legacy_isi/assets.csv`
- generated `data/migration/legacy_isi/redirect_map.csv`
- generated `data/migration/legacy_isi/summary.json`
- tests for parser/artifact/read-only contracts

## Crawler safety
The crawler performs same-origin HTTP GET requests only. It does not authenticate, submit forms, post data, call WordPress admin endpoints, mutate the source website, download binary assets, or change the local database.

## Required legacy seeds
- `/`
- `/tim/`
- `/aktivnosti/`
- `/dokumenti/`
- `/biblioteka`
- `/inkluzivni-razvoj/`
- `/nasledje/`
- `/en/homepage-english/`

## Acceptance
1. Required files exist.
2. Focused tests pass.
3. Live read-only inventory runs against `https://isi.rs/`.
4. Homepage and known current navigation routes are represented in the inventory.
5. Inventory contains at least one Serbian page and one English page.
6. Redirect candidates are generated with `review_status=pending`; no redirect is automatically approved.
7. Alembic remains at `20260827_0002`.
8. Full test suite passes.
9. No commit or push is performed by the runner/analyzer.
