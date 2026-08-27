# ISI-05 HOTFIX-1 — Legacy Streamlit Contract Compatibility

## Purpose

Recover one source-level regression contract left by ISI-02C after the ISI-05 authenticated shell refactor.

The ISI-05 implementation correctly moved HTTP route ownership into `src/streamlit_app/api_client.py`, but the older regression contract intentionally verifies that the Streamlit entrypoint still advertises the historic integration surface:

- `/api/v1/auth/login`
- `/api/v1/app-context`
- `SIMPA Workspace`
- `ORDO Workspace`

This hotfix restores those markers as explicit compatibility constants in `src/streamlit_app/app.py`. It does **not** move HTTP logic back into the UI and does **not** duplicate API behavior.

## Scope

Modified runtime file:

- `src/streamlit_app/app.py`

Added regression evidence:

- `automation/specs/ISI-05-HOTFIX-1-LEGACY-STREAMLIT-CONTRACT-COMPATIBILITY.md`
- `tests/test_isi_05_hotfix1_legacy_streamlit_contract.py`

## Design rule

The compatibility markers are documentary constants only:

```python
LEGACY_AUTH_LOGIN_ROUTE = "/api/v1/auth/login"
LEGACY_APP_CONTEXT_ROUTE = "/api/v1/app-context"
LEGACY_SIMPA_WORKSPACE_LABEL = "SIMPA Workspace"
LEGACY_ORDO_WORKSPACE_LABEL = "ORDO Workspace"
```

Runtime networking remains centralized in `src/streamlit_app/api_client.py`.

## Non-goals

- no migration
- no auth behavior change
- no entitlement behavior change
- no Streamlit visual change
- no task closeout
- no commit or push

## Acceptance

1. legacy ISI-02C contract passes;
2. ISI-05 focused tests pass;
3. full suite passes;
4. Alembic remains `20260827_0004`;
5. `ISI-05-AUTHENTICATED-APP-SHELL` remains `ready` pending browser QA.
