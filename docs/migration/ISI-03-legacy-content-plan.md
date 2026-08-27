# ISI-03 Legacy isi.rs Content Migration Plan

## Objective
Move the current public institutional content from `https://isi.rs/` into the new ISI Platform without losing source URLs, Serbian/English language context, documents, media references, or redirectability.

## Stage split
- **ISI-03A — Inventory:** read-only crawl, page/asset inventory, source hashes, language classification, redirect candidates.
- **ISI-03B — Content model + import:** introduce database-backed public content entities and import approved legacy content.
- **ISI-03C — Redirect/media validation:** media copy/hash/deduplication, redirect decisions, broken-link checks, migration report.

## Current known legacy navigation baseline
The legacy site currently exposes institutional sections for Tim, Aktivnosti, Dokumenti, Biblioteka, Inkluzivni razvoj and Nasleđe, plus Serbian/English language navigation. The homepage also carries the ISI identity statement and links to ANCSEE and WBSIB.

## Rules
1. Source site is read-only during migration.
2. Do not delete or rewrite the live WordPress site during ISI-03.
3. Every imported item must retain its legacy source URL and source hash.
4. Redirects remain `pending` until reviewed in ISI-03B/03C.
5. Public content must eventually be database/content-managed; templates must not become the source of truth.
6. The new public hierarchy will include SIMPA and ORDO as flagship ISI platforms, but legacy inventory must not invent content that is absent from the source.
7. Serbian and English content are preserved as distinct locale records.
8. Binary media is inventoried in 03A; downloading/deduplication is deferred to 03C.
