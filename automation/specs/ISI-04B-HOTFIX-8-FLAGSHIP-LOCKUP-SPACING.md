# ISI-04B HOTFIX-8 — Flagship Lockup Spacing

## Purpose

A very small visual correction to the approved public Home page after browser QA.

Observed issue on the SIMPA flagship card:

- `SIMPA` wraps into two lines (`SIMP` / `A`),
- the large platform lettering does not have enough breathing room inside the left lockup,
- the ORDO card is otherwise visually correct and the rest of HOTFIX-5/6/7 must remain unchanged.

## Scope

This hotfix changes **only** the flagship lockup CSS in:

`src/public/static/css/semantic-polish.css`

It does not change templates, routes, content, database state, migrations, semantic icon mapping, Activities visuals, the official ISI asset, SIMPA/ORDO SVG marks, or publication state.

## Required behavior

For the Home flagship SIMPA/ORDO cards:

1. Platform title must remain on a single line on normal desktop widths.
2. SIMPA and ORDO title sizes remain visually balanced.
3. The mark/title lockup receives slightly more internal breathing room.
4. The platform mark is reduced slightly so the title has enough horizontal space.
5. Text must not be forced against the card or internal divider.
6. Existing responsive one-column behavior remains unchanged.

## CSS contract

HOTFIX-8 appends one idempotent override block identified by:

`ISI-04B-HOTFIX-8-FLAGSHIP-LOCKUP-SPACING`

The override uses:

- `white-space: nowrap`
- `word-break: keep-all`
- `overflow-wrap: normal`
- a slightly smaller balanced desktop title size
- slightly smaller 90px platform marks
- 19px lockup gap
- right-side breathing room on the lockup

On narrow mobile widths the title remains single-line but receives a smaller responsive size and mark.

## Safety

- No Alembic migration.
- No database mutation.
- No content publication.
- No commit or push.
- Official `assets/ISILogo` is not touched.
- Retired initiatives remain absent.
- HOTFIX-5 semantic icons and Activities visuals remain intact.

## Acceptance

- focused HOTFIX-8 CSS contract passes;
- complete pytest suite passes;
- Alembic head is unchanged;
- `git diff --check` passes;
- final browser QA confirms `SIMPA` is one line with comfortable spacing.
