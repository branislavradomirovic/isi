# ISI-04B HOTFIX-5 — Semantic Visual Polish

## Status
Implementation recovery / visual refinement. No production publication. No commit or push.

## Baseline
- Repository: `/Users/branislavradomirovic/Applications/Python/ISI`
- Branch: `main`
- Committed baseline: `2965383`
- Expected Alembic head: `20260827_0004`
- ISI-03C: `done`
- ISI-04: `ready`
- ISI-04B: `ready`
- HOTFIX-4 already applied in the working tree.

## Problem statement
Browser QA after HOTFIX-4 found five concrete issues:

1. The official ISI logo from `assets/ISILogo` renders with an opaque white rectangle.
2. Domain/list icons are chosen from broad visual categories and are therefore repeated/generic rather than semantically tied to the text.
3. SIMPA and ORDO marks are not sufficiently visible in the public hierarchy.
4. The home page visual hierarchy is too complex in several areas; the evidence/action diagram and resource previews must be simplified.
5. `Aktivnosti` still falls back to legacy/blank image areas instead of a professional image-led editorial presentation.

## Locked design direction
- Warm ivory institutional background.
- Dark green ISI identity with restrained sage and muted gold accents.
- Editorial serif headings + clean sans-serif UI text.
- ISI is the parent institution.
- SIMPA and ORDO are distinct flagship platforms and retain separate marks.
- No COSMOS public hierarchy.
- ANCSEE and WBSIB remain outside the new landing/public flagship scope.

## Scope

### A. Official ISI logo — transparent web derivative
The official source remains under `assets/ISILogo` and MUST NOT be modified.

HOTFIX-5 creates:

`src/public/static/img/brand/isi-logo-transparent.svg`

The installer removes only obvious full-canvas white SVG rectangles when present and the CSS uses `mix-blend-mode: multiply` as a safe visual fallback for opaque white canvas shapes. The source SHA-256 remains recorded in `data/public/isi_brand_manifest.json`.

### B. Semantic icon vocabulary
Add a dedicated icon policy in:

`src/public/semantic_icons.py`

Every seeded `PublicPageSectionItem` receives an icon from its actual concept (section key, item key, domain code and label), not merely from `visual_kind`.

Examples:
- Centri za socijalni rad → social-work icon
- Jedinice lokalne samouprave → municipality icon
- Obrazovanje → education icon
- Zdravstvo → health icon
- Zapošljavanje → employment icon
- Civilno društvo → community/civil-society icon
- Siromaštvo → poverty icon
- Dostupnost usluga → service-access icon
- Teritorijalna koncentracija rizika → territory icon
- Kulturno nasleđe → heritage icon
- Prirodni resursi → nature icon
- Lokalna privreda → economy icon
- Scenario / prediction / decision items → corresponding model/prediction/decision icons

The shared `icons.svg` sprite is expanded to cover all 90 seeded public section items and common document/activity concepts.

### C. SIMPA / ORDO visibility
- SIMPA and ORDO marks are visible in the main navigation.
- Marks are visible in home flagship cards.
- Marks are prominent in platform hero lockups and diagrams.
- SIMPA mark uses a connected data/network language.
- ORDO mark uses modular decision-architecture geometry.

### D. Home simplification
The home page keeps the approved design but reduces visual noise:
- one clean ISI evidence/action system diagram;
- four non-numeric proof/architecture chips (no invented metrics);
- two flagship cards;
- four institutional principles;
- three compact resource previews (Dokumenti, Biblioteka, Inkluzivni razvoj).

No fabricated impact counts are introduced.

### E. Activities redesign
A dedicated `activities.html` renderer is introduced.

The route extracts activity links and nearby migrated images from the existing migrated HTML. When an activity has no usable migrated image, the page uses a local semantic editorial SVG illustration instead of an empty/broken placeholder.

Local fallback visuals:
- conference
- workshop
- public dialogue
- training
- publication/result

The new page includes:
- hero visual;
- type filters with semantic icons;
- search;
- featured activity;
- secondary cards;
- optional publication/result cards when corresponding migrated entries exist.

No invented activity URL is created.

### F. Documents / Library / Inclusive Development
- Documents: document-type icons reflect Strategija / Izveštaj / Smernice / Analiza / Propis rather than one generic file icon.
- Documents: source grouping recognises more specific institution families such as SIPRU, RZS, UNDP and local governments when supported by migrated titles/URLs.
- Library: collection-specific icon/cover fallback replaces repeated generic book blocks.
- Inclusive development: rights, community participation, service quality, local capacity, outcomes, partnership and ISI tools use separate semantic icons.

## Non-goals
- No new Alembic migration.
- No AI/RAG implementation.
- No publication of draft content.
- No redirect activation.
- No production cutover.
- No fabricated institutional logos or unverified impact statistics.
- No modification of `assets/ISILogo`.

## Files added/changed
- `src/public/semantic_icons.py`
- `src/public/catalog_service.py`
- `src/public/routes.py`
- `src/public/templates/base.html`
- `src/public/templates/index.html`
- `src/public/templates/platform.html`
- `src/public/templates/activities.html`
- `src/public/templates/documents.html`
- `src/public/templates/library.html`
- `src/public/templates/inclusive_development.html`
- `src/public/templates/partials/header.html`
- `src/public/templates/partials/domain_sections.html`
- `src/public/static/css/semantic-polish.css`
- `src/public/static/img/icons.svg`
- `src/public/static/img/simpa-mark.svg`
- `src/public/static/img/ordo-mark.svg`
- `src/public/static/img/activities/*.svg`
- `data/public/isi_brand_manifest.json` (installer metadata only)
- architecture/design references/tests/spec.

## Acceptance gates
Runner must prove:
- branch/main + baseline contract;
- current partial ISI-04/04B working-tree scope only;
- native PostgreSQL reachable;
- Alembic remains `20260827_0004`;
- official ISI source asset exists and remains unchanged;
- transparent derivative exists;
- all seeded domain items resolve to an existing semantic icon;
- SIMPA/ORDO marks are present in header/home/platform;
- activity page always has image/illustration fallback;
- retired public initiatives are absent from the new design templates;
- public pages/sections remain draft;
- focused and full pytest pass;
- Docker Compose config and `git diff --check` pass.

Final analyzer additionally requires explicit browser visual-QA acknowledgement.
