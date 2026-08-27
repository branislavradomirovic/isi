# ISI-03B HOTFIX-1 — Canonical legacy alias deduplication

## Problem
The live ISI inventory contains legacy URL aliases that differ only by URL form, e.g. `/biblioteka` and `/biblioteka/`. Both records are valid legacy sources and both must be preserved for migration/redirect provenance, but they map to the same logical page, locale and renderable translation.

The original ISI-03B importer iterated source records one-by-one and attempted to create two `PublicPageTranslation` rows for the same `(page_id, locale)`, violating `uq_public_page_translation_locale`.

## Required behavior
- Group successful legacy page rows by `(page_key, locale)` before creating translations.
- Preserve every source URL as a `PublicLegacySource`.
- Preserve every redirect candidate separately.
- Create exactly one `PublicPageTranslation` per logical page + locale.
- Prefer the legacy path that exactly matches `canonical_url` as the translation route.
- If multiple aliases map to the same logical page + locale but their captured content hashes differ, abort rather than silently selecting one.
- Keep all imported pages `draft` and redirects `pending`.
- Keep Alembic head at `20260827_0003`; no new migration is required.
- Import must remain idempotent.

## Acceptance
- Regression test covers `/biblioteka` + `/biblioteka/`.
- Native PostgreSQL readback calculates expected translation count from unique `(page_key, locale)` values, not raw source count.
- All 14 successful legacy source pages remain represented by `PublicLegacySource` records.
- Analyzer verifies report fields `logical_pages`, `logical_page_translations`, and `legacy_alias_pages`.
- No source-site mutation, commit, or push.
