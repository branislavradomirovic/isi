# ISI-04B HOTFIX-3 — User Asset Safety Gate

## Purpose
Recover the ISI-04B public-experience refinement runner after the pre-install safety gate rejected the pre-existing user-owned `assets/ISILogo` path.

## Root cause
HOTFIX-2 intentionally validates every pre-existing changed path before copying its payload. The allowlist omitted the already-present user asset path `assets/ISILogo`, so the runner exited before installing any HOTFIX-2 files.

## Contract
- Preserve `assets/ISILogo` and anything below `assets/ISILogo/` unchanged.
- Treat this path only as an allowed pre-existing user asset; the hotfix must not overwrite, remove, stage, or relocate it.
- Install the full HOTFIX-2 public-experience payload after the safety gate passes.
- Keep Alembic at `20260827_0004`.
- Keep all public pages/sections draft-only.
- Keep ANCSEE/WBSIB out of the new landing rendering.
- Keep SIMPA/ORDO public SVG marks and the redesigned Documents, Library and Inclusive Development views.
- No commit or push.
