# ISI-03C — Media + Redirect + Migration Validation

Status: READY

Baseline: committed ISI-03B (`85660cd`, `Add public content model and legacy import`) with Alembic `20260827_0003`.

## Scope

1. Download every `public_media_assets` legacy source from `isi.rs` using GET only.
2. SHA-256 verify and content-address binaries under gitignored `var/media/public/`.
3. Deduplicate identical binary content while retaining source-URL provenance.
4. Rewrite draft `body_html` same-site media links to `/media/...` and page aliases to canonical migrated routes.
5. Block acceptance on any unresolved same-site link.
6. Finalize the legacy route plan: preserve canonical routes, approve only unambiguous aliases as 301 data mappings.
7. Keep every migrated page in `draft`; do not activate redirects or publish/cut over.
8. Produce reproducible media/link/redirect/acceptance artifacts.
9. Keep Alembic head unchanged at `20260827_0003`.
10. No commit and no push.

## Non-goals

- New public visual design.
- SIMPA/ORDO landing page implementation.
- Production object storage/S3 upload.
- Redirect middleware activation.
- DNS/production cutover.
- External website mutation.

## Acceptance

- all inventory media rows are `verified`;
- every local blob exists and matches its DB SHA-256;
- no unresolved same-site links remain in migrated draft content;
- no `pending` redirect records remain;
- approved redirects equal actual legacy aliases, while canonical paths are preserved;
- all public pages remain draft;
- native PostgreSQL readback passes;
- full test suite passes;
- Alembic remains `20260827_0003`;
- `var/media/` is not tracked by Git.
