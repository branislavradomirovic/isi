# ISI-02C — Authenticated App Context

## Objective
Connect the completed authentication lifecycle to organization, product entitlement, role/permission and workspace resolution, then expose that context to the Streamlit authenticated shell through FastAPI.

## Locked architecture
- Authentication and authorization remain separate concerns.
- `Role` answers what a user may do; product access answers whether the user may enter SIMPA/ORDO.
- Tenant scope is `Organization`.
- SIMPA-only users route directly to SIMPA; ORDO-only users route directly to ORDO.
- Users with multiple organizations or both products receive a selector/product switcher.
- Workspace selection is validated server-side and may never cross tenant/product boundaries.
- Streamlit does not query PostgreSQL directly. It consumes FastAPI.
- Opaque access tokens stay in Streamlit server-side session state; they are never placed in URLs.
- No domain business functionality is invented in this task.
- No schema migration is required; Alembic must remain at `20260827_0002`.
- The existing ISI-02A reference catalog is idempotently activated in native PostgreSQL: SIMPA/ORDO products, system roles, permissions and role-permission mappings.

## Deliverables
- `src/platform/app_context/` resolver and API schemas.
- `/api/v1/app-context` authenticated endpoint.
- `/api/v1/app-context/select` server-side selection validator.
- Functional Streamlit login + authenticated shell + organization/product/workspace selectors.
- SIMPA/ORDO product switch behavior without merging domain models.
- SQLite service/API tests and native PostgreSQL transaction smoke.
- Native reference catalog bootstrap/verification (idempotent data initialization, not a schema migration).
- Automation task registration and analyzer contract.

## Routing contract
1. No accessible product: `no_access`.
2. One organization + one product + one workspace: direct `workspace` route.
3. One organization + one product + zero/multiple workspaces: direct `product` route.
4. Multiple organizations or multiple products: `selector`.

## Security contract
- Suspended memberships and suspended organizations are excluded.
- Product access requires active membership product access + active/current organization entitlement.
- Role/permission lists are product-scoped (`*` + selected product).
- Cross-organization and cross-product workspace selection is rejected.
- Platform admin remains an explicit global bypass consistent with ISI-02A.
- The client never decides authorization; it only selects from server-resolved options.

## Non-goals
- Persistent "last selected workspace" preference.
- Browser cookie/session hardening beyond the existing opaque session model.
- SIMPA or ORDO domain modules.
- Public website work.
- New database schema.
- Commit or push.
