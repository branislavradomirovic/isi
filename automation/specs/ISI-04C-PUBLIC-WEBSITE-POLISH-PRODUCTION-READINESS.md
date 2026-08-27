# ISI-04C — Public Website Polish & Production Readiness

## Baseline

- Expected Git baseline: `8135cfe` — `Complete ISI public website and domain knowledge foundation`
- `ISI-04-NEW-PUBLIC-WEBSITE`: `done`
- `ISI-04B-DOMAIN-KNOWLEDGE-CONTENT-ENRICHMENT`: `done`
- Alembic: `20260827_0004 (head)`
- Local development remains native PostgreSQL. This task does not start Docker PostgreSQL.
- Public content remains draft. This task does **not** publish or cut over `isi.rs`.

## Goal

Take the approved ISI public design from visual acceptance to a technically production-ready public web layer, without changing the approved information architecture or the SIMPA/ORDO brand hierarchy.

## Scope

1. Responsive behavior for desktop, tablet and mobile, including compact navigation.
2. Accessibility baseline: semantic landmarks, keyboard navigation, visible focus, `aria-current`, search labels, meaningful activity-image alt text, target sizes and reduced-motion support.
3. SEO metadata: canonical, SR/EN hreflang, x-default, Open Graph, Twitter/X card metadata and robots directives.
4. Brand/browser metadata based on the installed official ISI logo: favicon route and web manifest.
5. `robots.txt` with safe non-production behavior and production sitemap reference.
6. `sitemap.xml` generated only from **published** public content; draft preview content must not leak into the sitemap.
7. Branded public 404 page while preserving JSON/API 404 behavior for `/api/*`.
8. Public navigation state, mobile menu escape/close behavior and external-link safety.
9. Lightweight performance polish: lazy image loading where appropriate, decoding hints, no heavy framework/dependency addition.
10. Public-route audit and final browser QA matrix.

## Non-goals

- No publication of draft content.
- No production DNS/TLS cutover.
- No new database migration.
- No Streamlit authenticated app changes; those start in ISI-05.
- No new authentication/authorization model.
- No replacement of the approved visual design.
- No automatic commit or push.

## Acceptance criteria

- Exact baseline gate passes.
- New task `ISI-04C-PUBLIC-WEBSITE-POLISH-PRODUCTION-READINESS` exists and remains `ready` until explicit browser QA acceptance.
- `/robots.txt`, `/sitemap.xml`, `/site.webmanifest`, and `/favicon.ico` return valid responses.
- Draft preview uses `noindex,nofollow`; robots disallows crawling outside production.
- Sitemap contains no draft-only pages.
- Canonical, Open Graph, Twitter/X and hreflang metadata render on public pages.
- `aria-current="page"` is present on active navigation items.
- Mobile navigation is keyboard closable with Escape and uses the existing toggle state contract.
- Activity content images have meaningful alt text; decorative illustrations remain `alt=""`.
- Search controls expose explicit accessible labels.
- `prefers-reduced-motion` is honored.
- Public 404 is branded; API 404 remains JSON.
- Full test suite, Docker Compose config and `git diff --check` pass.
- Manual browser QA is required before final analyzer/commit.

## Browser QA matrix

See `docs/qa/ISI-04C-BROWSER-QA-MATRIX.md` after installation.

## Next phase

After ISI-04C is accepted, analyzed and manually committed, continue immediately with `ISI-05-AUTHENTICATED-APP-SHELL`.
