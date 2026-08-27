# ISI-03B — Public Content Model + Legacy Content Import

## Goal
Create the database-backed public content layer for the new ISI website and import the legacy `isi.rs` page inventory into a safe draft/staging state with source provenance.

## Baseline
- ISI-00/01 foundation committed.
- ISI-02A identity/access/workspaces committed.
- ISI-02B authentication lifecycle committed.
- ISI-02C authenticated app context committed.
- ISI-03A live legacy inventory committed.
- Native PostgreSQL schema starts at `20260827_0002`.

## Important migration rule
ISI-03A deliberately stored inventory metadata and content hashes, not renderable page bodies. ISI-03B therefore performs a second read-only GET pass over exactly the committed ISI-03A page URLs, captures normalized content snapshots, verifies that the source content has not drifted from the committed inventory hash, and only then imports content into the new `isi` database.

If any committed source page changed between ISI-03A and ISI-03B, the runner stops and requires a fresh ISI-03A inventory. It never silently imports mismatched source content.

## New public content schema
Core migration/staging tables:
- `public_pages`
- `public_page_translations`
- `public_legacy_sources`
- `public_media_assets`
- `public_redirects`

Structured public content tables prepared for the new site:
- `public_people` / `public_person_translations`
- `public_activities` / `public_activity_translations`
- `public_publications` / `public_publication_translations`
- `public_documents` / `public_document_translations`
- `public_programs` / `public_program_translations`
- `public_partners` / `public_partner_translations`

The specialized entity tables are schema foundation only in ISI-03B. Legacy pages are not heuristically split into people, activities, publications, documents, programs or partners. That mapping remains explicit and reviewable.

## Content state
All imported legacy pages are `draft`. No imported page is automatically published.

All redirect candidates remain `pending`. No 301 redirect is automatically approved or activated.

Media references are registered as `pending`; binary media download, hashing and storage verification are deferred to ISI-03C.

## Locales
- `sr-Latn`
- `en`

The Serbian homepage `/` and the known English homepage `/en/homepage-english/` are paired as translations of the same logical `home` page. Other pages are paired only when their normalized legacy route unambiguously matches; the importer never invents translation relationships.

## Source snapshot safety
- same-origin GET requests only;
- no authentication;
- no form submission;
- no POST/PUT/PATCH/DELETE;
- no WordPress admin calls;
- sanitized stored HTML;
- script/style/form/navigation chrome excluded from imported content;
- source URL, inventory hash, snapshot hash and capture time preserved.

## Migration
New Alembic revision:
- `20260827_0003_public_content_model.py`

Expected head after runner:
- `20260827_0003`

## Import invariants
1. Every successful HTML page in the committed ISI-03A inventory has exactly one current snapshot.
2. No source hash drift is accepted.
3. Every successful source page has one `public_legacy_sources` provenance record.
4. Every imported translation is `draft` through its parent page.
5. No redirect is approved automatically.
6. Every inventory asset is represented in `public_media_assets` with `migration_status=pending`.
7. Import is idempotent; rerunning does not duplicate content.
8. Existing authenticated/platform tables are untouched except for the new public-content migration.
9. Full tests pass.
10. Runner/analyzer never commit or push.

## Non-goals
- no new public visual design;
- no replacement of the live `isi.rs` site;
- no media binary migration yet;
- no redirect activation yet;
- no CMS/admin UI yet;
- no SIMPA/ORDO domain implementation;
- no publishing of imported content.
