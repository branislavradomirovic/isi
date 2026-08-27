# ISI-05 HOTFIX-2 — Demo Auth and Branding Alignment

## Purpose

Repair the two issues found during the first authenticated app-shell browser QA:

1. local QA identities could not log in;
2. the official ISI logo was visually left-biased and retained an opaque white artboard on the warm-ivory Streamlit login surface.

The hotfix preserves the ISI-05 architecture and does not change migrations, product/role separation, tenant isolation, or production auth semantics.

## Root cause

The initial demo provisioner created addresses such as `isi05-simpa@isi.local`. The FastAPI login contract uses Pydantic `EmailStr`, and the email validator rejects `.local` as a special-use/reserved suffix before authentication runs. The browser therefore received a validation failure rather than a credential check.

The demo identities are changed to RFC-safe reserved example addresses:

- `isi05-simpa@example.com`
- `isi05-ordo@example.com`
- `isi05-dual@example.com`

`example.com` is intentionally reserved for documentation/testing and is valid for `EmailStr` validation.

The second defect was visual. The official ISI brand asset contains an opaque white artboard in the browser rendering path. ISI-05 now renders the official derived asset in a centered brand wrapper and uses compositing (`mix-blend-mode: multiply`) so white becomes visually transparent against the ISI ivory surface. The source asset remains unchanged.

## Demo entitlement correction

The demo Organization represents one institution entitled to both flagship products. Therefore organization-level entitlements are always active for both SIMPA and ORDO. User-profile differences are expressed only through `MembershipProductAccess` and product-scoped role assignments:

- SIMPA profile: SIMPA only
- ORDO profile: ORDO only
- dual profile: SIMPA + ORDO

This mirrors the locked architecture: **role != product entitlement/access**.

## Added QA smoke gate

`tools/smoke_local_app_shell_login.py` performs a real HTTP smoke test after FastAPI starts and before Streamlit opens. For each demo profile it verifies:

- `/api/v1/auth/login` returns 200;
- `/api/v1/auth/me` returns the expected identity;
- `/api/v1/app-context` exposes exactly the expected products;
- `/api/v1/app-shell` accepts each allowed product/workspace context;
- logout succeeds;
- a deliberately wrong password returns 401.

The local QA launcher refuses to report READY if this chain fails.

## Brand acceptance

Login screen and sidebar must show:

- official ISI logo;
- centered alignment;
- no visible white rectangle/artboard;
- no modification of `assets/ISILogo`;
- responsive sizing on narrow layouts.

## Non-goals

- no new migration;
- no production publication;
- no new SIMPA/ORDO business logic;
- no auth redesign;
- no automatic commit/push.
