# ADR-0012 — Public Website Production Readiness

## Decision

The public `isi.rs` layer remains FastAPI + Jinja2 + HTML/CSS/SVG + minimal vanilla JavaScript. Production-readiness work is added as a thin public layer rather than by replacing the approved templates or introducing a frontend framework.

SEO and crawl behavior are environment aware: draft/local preview is `noindex,nofollow`, non-production `robots.txt` disallows crawling, and `sitemap.xml` is generated only from content that is actually `published` in the public content model.

The official ISI logo already installed under `src/public/static/img/brand/` remains the source for browser identity. SIMPA and ORDO remain subordinate flagship identities under ISI.

Public 404 rendering is branded, while API errors preserve JSON semantics. Accessibility uses progressive enhancement: semantic HTML and keyboard navigation work without requiring client-side rendering.

## Consequences

- No schema migration is required.
- No draft content is published by this phase.
- Production cutover remains ISI-16.
- Authenticated application work starts separately in ISI-05.
