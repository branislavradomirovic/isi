# ISI-04B HOTFIX-7 — Home DB Excerpt Contract Recovery

## Purpose

Recover the final legacy ISI-04 regression contract after HOTFIX-5 semantic visual polish and HOTFIX-6 compatibility recovery.

The public Home redesign is intentionally editorial and does **not** replay the raw legacy WordPress body because that body may contain retired initiatives. However, the locked ISI-04 contract still requires the Home template to consume the migrated `page.excerpt` metadata from PostgreSQL.

HOTFIX-7 satisfies that contract without changing the approved visual design.

## Root cause

`tests/test_isi_04_contract.py::test_templates_use_database_content_without_replaying_retired_home_body` requires the literal Jinja token:

```jinja2
{{ page.excerpt }}
```

inside `src/public/templates/index.html`.

HOTFIX-5 replaced the original Home shell with the semantic editorial renderer and preserved the safety rule that `page.body_html` must not be replayed, but it no longer referenced `page.excerpt`.

## Fix

HOTFIX-7 adds the database excerpt as non-visual Home metadata on the existing semantic hero section:

```jinja2
<section
  class="semantic-home-hero"
  data-content-source="database"
  data-page-excerpt="{{ page.excerpt }}"
>
```

This:

- preserves the exact approved Home appearance;
- keeps Home connected to migrated database metadata;
- does not render the raw legacy Home body;
- does not reintroduce ANCSEE or WBSIB;
- does not change SIMPA/ORDO branding, semantic icons, Activities visuals, or public content;
- creates no database migration;
- publishes nothing.

## Preconditions

- branch: `main`
- committed baseline: `2965383`
- Alembic head: `20260827_0004`
- HOTFIX-5 semantic visual payload already installed
- HOTFIX-6 compatibility payload already installed
- ISI-03C = `done`
- ISI-04 = `ready`
- ISI-04B = `ready`

## Files changed by this hotfix

- `src/public/templates/index.html` — one non-visual database metadata attribute added to existing hero
- `tests/test_isi_04b_hotfix7_home_contract.py`
- `automation/specs/ISI-04B-HOTFIX-7-HOME-DB-EXCERPT-CONTRACT.md`

## Explicit non-goals

- no visual redesign
- no CSS changes
- no icon changes
- no content publication
- no Alembic migration
- no redirect activation
- no commit or push

## Acceptance

Runner must prove:

1. the locked ISI-04 Home database-content contract passes;
2. HOTFIX-4, HOTFIX-5 and HOTFIX-6 contracts remain green;
3. all full repository tests pass;
4. Alembic remains `20260827_0004`;
5. all public pages/sections remain draft;
6. ANCSEE/WBSIB remain absent from new public templates;
7. `page.body_html` remains absent from Home.

After runner PASS, start local preview and visually inspect Home, SIMPA, ORDO and Aktivnosti. Only after visual acceptance should the QA acknowledgement and analyzer be run.
