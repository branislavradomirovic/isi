# ISI-05 — Authenticated App Shell

## Status
Implementation task. The task remains `ready` until explicit manual browser QA is recorded.

## Baseline
- Required Git HEAD: `35b1361` — `Complete ISI public website production readiness`
- Required clean working tree before install.
- Required Python: 3.11.x; validated development baseline is 3.11.15.
- Required Alembic head before and after: `20260827_0004`.
- Required predecessor: `ISI-04C-PUBLIC-WEBSITE-POLISH-PRODUCTION-READINESS = done`.

## Architectural contract
ISI remains one platform with one authentication/identity system, one tenant model, one API/backend and shared infrastructure. SIMPA and ORDO are separate flagship domain applications on that shared core.

Role and product entitlement remain separate:
- role = what a member may do;
- product access = which product the member may enter.

The authenticated access path remains:
`User -> Membership -> Organization -> Role/permissions -> Product entitlement -> Workspace`.

## Scope
This task upgrades the existing ISI-02B/02C authentication/context foundation into the real authenticated application shell.

### API
Adds `GET /api/v1/app-shell`:
- requires a valid bearer session;
- validates organization/product/workspace through the existing server-side app-context resolver;
- never trusts a client-selected tenant, product or workspace without revalidation;
- returns the resolved organization, product, workspace, roles, permissions and shell navigation capabilities;
- rejects cross-tenant, cross-product and inaccessible workspace selections with HTTP 403.

### Streamlit authenticated application
Replaces the proof-of-concept authenticated screen with a structured shared shell:
- branded ISI login;
- official transparent ISI logo;
- visible SIMPA and ORDO product marks;
- direct entry for one-organization/one-product users;
- product switcher only when more than one product is actually accessible;
- organization switcher only when more than one organization is accessible;
- workspace switcher only when multiple workspaces are accessible;
- server validation of every resolved shell selection;
- explicit no-access, no-workspace, unauthorized and API-unavailable states;
- logout and local session cleanup;
- shared navigation generated from server-resolved permission codes;
- overview shell for SIMPA and ORDO without implementing domain functionality early.

### Permission-driven navigation
The shell may expose:
- Pregled — product access / workspace shell;
- Podaci — `data.read`;
- Indikatori — `indicator.read`;
- Analitika — `analysis.read`;
- Scenariji — `scenario.read`;
- Izveštaji — `report.read`;
- Administracija — organization/member/workspace management or audit permissions.

These are shell entry points only. Domain workflows remain scheduled for ISI-06 through ISI-13.

### Local QA helper
Adds an explicit development-only provisioning tool. It is never run by the task runner. It can create:
- SIMPA-only demo access;
- ORDO-only demo access;
- dual SIMPA+ORDO demo access.

The helper requires an explicit password and rejects production/staging environments. It supports cleanup of its own demo records.

## Non-goals
- No new database migration.
- No new SIMPA domain model.
- No new ORDO domain model.
- No data ingestion.
- No AI/RAG.
- No report engine.
- No production publication/cutover.
- No automatic Git commit or push.
- No Docker PostgreSQL for local development.

## Security requirements
- Access checks stay server-side.
- Cross-tenant workspace selection must be rejected.
- Product access is not inferred from role names.
- Session expiry/invalid token returns the login state.
- Product/organization switching is limited to the authenticated context.
- No raw password is stored in Streamlit session state.
- The demo provisioner is opt-in and development-only.

## Manual browser QA
Use `docs/qa/ISI-05-BROWSER-QA-MATRIX.md`.

After the runner is green:
1. provision one or more local QA accounts explicitly;
2. run FastAPI locally;
3. run Streamlit locally;
4. verify login, direct routing, dual-product switcher, no-access state and logout;
5. record QA only after acceptance;
6. run the final read-only analyzer;
7. manually commit.

## Next
`ISI-06-SHARED-DATA-PLATFORM`
