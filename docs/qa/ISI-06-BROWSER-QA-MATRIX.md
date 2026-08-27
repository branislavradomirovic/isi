# ISI-06 Browser QA Matrix

Task remains `ready` until this matrix is manually accepted.

## Profiles
- SIMPA-only demo user
- ORDO-only demo user
- dual-product demo user

## Checks
- `Podaci` is a real module, not an ISI-06 placeholder.
- Scope banner shows the selected organization, product and workspace.
- SIMPA source list never appears in ORDO after switching product.
- Upload is visible only when `data.upload` exists.
- CSV upload creates a source/version and finishes ingestion.
- JSON upload creates a source/version and finishes ingestion.
- XLSX upload reports structural metadata without claiming semantic interpretation.
- PDF/DOCX upload is registered without fabricated extraction results.
- Duplicate bytes reuse tenant-scoped storage safely.
- Invalid/oversize/unsupported uploads return a controlled error, never a traceback.
- Source catalog shows actual DB state only.
- Logout and product/workspace switch remain functional.
