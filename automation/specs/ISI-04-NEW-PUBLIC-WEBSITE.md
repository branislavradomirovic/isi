# ISI-04 — New Public Website

## Purpose
Replace the foundation public placeholder with the first real FastAPI/Jinja ISI public website while preserving the migration safety contract established by ISI-03.

## Baseline
- Git baseline: `2965383` (`Complete legacy media and redirect migration validation`)
- Alembic head remains `20260827_0003`
- Native local PostgreSQL remains the local development database
- Existing migrated legacy content remains `draft`
- Redirect activation remains deferred

## Architecture contract
- ISI is the institutional parent brand.
- SIMPA and ORDO are independent flagship platforms under ISI.
- No COSMOS public hierarchy.
- Public website remains FastAPI + Jinja2 + HTML/CSS + minimal vanilla JS.
- Authenticated application remains Streamlit.
- Public page content is read from PostgreSQL, not copied into route functions/templates.
- Two new flagship platform pages are seeded into `public_pages` / `public_page_translations` as `draft` content.
- Production must never expose draft content, even if the preview flag is accidentally enabled.

## Rendering contract
- `/` Serbian homepage
- `/en/` English homepage
- `/simpa/`, `/en/simpa/`
- `/ordo/`, `/en/ordo/`
- single-segment migrated institutional routes render through the shared page renderer
- migrated media is served from `/media/...`
- canonical and alternate-language metadata are emitted
- mobile navigation and keyboard focus states are present
- `prefers-reduced-motion` is respected

## Visual direction
Institutional/editorial, warm ivory, ink/charcoal and restrained ISI green. SIMPA uses petrol/teal emphasis. ORDO uses muted gold/stone emphasis. Avoid generic SaaS dashboards, neon/cyberpunk styling and card overload.

## Publication safety
ISI-04 does not publish legacy content. Local visual QA uses `PUBLIC_PREVIEW_DRAFTS=true`. In production, draft preview is hard-disabled in code.

## Manual QA
Before commit, inspect at least:
- `/`
- `/simpa/`
- `/ordo/`
- `/tim/`
- `/nasledje/`
- `/en/`
- one migrated document/media link
- mobile width

Record approval with the supplied manual-QA recorder before running the final analyzer.
