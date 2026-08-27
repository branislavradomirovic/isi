# ISI-03C — Media, Redirect and Migration Validation

## Purpose

Finalize the technical migration staging created by ISI-03A/03B without publishing the new website.

## Media policy

- Legacy binary assets are fetched from `isi.rs` with read-only HTTP GET requests.
- Local development binaries live under `var/media/public/` and are intentionally gitignored.
- Every blob is addressed by SHA-256 under `legacy/<prefix>/<sha256>.<ext>`.
- Duplicate content shares one local blob while every legacy source URL keeps its own database provenance row.
- `public_media_assets` is updated only after download/hash verification.

## Content-link policy

- Same-site legacy media links are rewritten to `/media/...` paths.
- Same-site legacy page aliases are rewritten to the canonical migrated route for the same locale.
- External links are preserved.
- Any unmapped same-site page or media link blocks ISI-03C acceptance and is reported for recovery.

## Redirect policy

- A legacy path that is already the canonical migrated route is preserved and requires no redirect (`disabled` in the redirect table).
- An unambiguous alias is approved as a 301 mapping (`approved`).
- ISI-03C does **not** activate redirect middleware and does not perform cutover.

## Publication policy

All imported public content remains `draft`. ISI-03C is migration staging/validation only.

## Acceptance artifacts

- `data/migration/legacy_isi/media_manifest.json`
- `data/migration/legacy_isi/link_normalization_report.json`
- `data/migration/legacy_isi/final_redirect_map.csv`
- `data/migration/legacy_isi/migration_acceptance_report.json`

Local binary media under `var/media/public/` is not committed to Git.
