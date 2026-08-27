# ADR-0006 — Database-backed Public Content and Legacy Migration

Status: Accepted

## Decision
The new ISI public website is database/content-driven. Institutional content is not hardcoded into Jinja templates and is not copied directly from legacy WordPress markup at render time.

The public content domain is separated into:

- logical public pages and localized page translations;
- explicit structured entities for people, activities, publications, documents, programs and partners;
- media asset records;
- legacy source provenance;
- redirect candidates.

Legacy content is imported as `draft` and redirect candidates remain `pending` until manual and automated migration validation is complete.

## Source provenance
Every migrated legacy page stores the source URL, legacy path, locale, inventory content hash, snapshot content hash, HTML response hash, extraction method and capture time. A source hash mismatch between the committed ISI-03A inventory and ISI-03B snapshot capture blocks import.

## Rendering boundary
Sanitized body HTML may later be rendered by the FastAPI/Jinja public website. Raw WordPress page chrome, scripts, forms, navigation and footer markup are not trusted as new-site content.

## Media
ISI-03B registers media references only. Binary download, deduplication, hashing, local/S3 storage mapping and reference rewriting belong to ISI-03C.
