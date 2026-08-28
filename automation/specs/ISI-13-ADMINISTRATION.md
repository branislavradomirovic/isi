# ISI-13 — Administration

## Status
Implementation task. The task remains `ready` until explicit local browser QA is accepted and recorded.

## Baseline
- Required Git HEAD: `cd958b8` — `Complete shared reporting`.
- Required clean working tree.
- Required Python: `3.11.15`.
- Required native PostgreSQL/Alembic before: `20260828_0011`.
- Required predecessor: `ISI-12-REPORTING = done`.
- Local development continues to use native PostgreSQL; Docker Compose remains deployment topology only.

## Architectural contract
ISI-13 turns the existing identity/access foundation into a real organization administration workspace without collapsing roles into product access.

The authorization chain remains:

`User -> Membership -> Organization -> role/permission -> product entitlement -> membership product access -> workspace`

Roles answer **what a member may do**. Product access answers **which flagship product the member may enter**. Organization entitlement remains a platform/commercial boundary and is read-only to organization administrators in this phase.

## Scope

### Organization administration
The administration workspace exposes the active organization and active product context. Organization name may be changed only by an actor with organization-wide `organization.manage`; organization slug/status and platform-admin flags are not editable here.

### Members
Administrators can:
- view organization members;
- suspend/reactivate memberships only with organization-wide `members.manage`, because membership status affects every product;
- grant/revoke membership product access only when the organization has a current active entitlement for that product;
- assign/remove product-scoped roles;
- assign/remove organization-wide roles only when the actor has organization-wide management authority.

For each product, the final active `organization_admin` (whether product-scoped or organization-wide) may not be suspended, stripped of the relevant role, or stripped of that product access. This prevents accidental tenant lockout.

### Invitations
Existing `core_invitations` remain the invitation identity primitive. ISI-13 adds explicit pre-acceptance grants:
- `core_invitation_product_grants`;
- `core_invitation_role_grants`.

A development invitation may carry one active product grant and one non-administrator role. When the existing authentication acceptance flow creates/reactivates the membership, the grants are applied server-side. `organization_admin` is deliberately not grantable by invitation in this first administration phase; it must be assigned explicitly to an existing member by an organization-wide administrator.

SMTP/provider invitation delivery is not fabricated. Development may expose the opaque invitation token for QA. Production invitation creation is blocked with `invitation_delivery_not_configured` until a real delivery adapter exists.

### Workspaces
Authorized administrators can create, archive and reactivate workspaces for the active product. Workspaces are never hard-deleted by this phase. Creation requires a current organization entitlement for the product.

### Audit
Migration `20260828_0012` introduces immutable `core_admin_audit_events`. Every successful administrative mutation records:
- organization;
- optional product scope;
- actor user/membership;
- action;
- target type/id;
- before state;
- after state;
- timestamp.

Audit rows are append-only from the administration service. There is no API delete/update endpoint for audit events.

### API
Adds `/api/v1/administration/*` for:
- scoped snapshot;
- invitation create/revoke;
- membership status;
- membership product access;
- role assignment/removal;
- workspace create/archive/reactivate;
- organization display-name update;
- audit read.

Server-side permission checks are mandatory. UI visibility is not authorization.

### Streamlit
The existing `Administracija` shell navigation becomes a real workspace with product-aware sections:
- Pregled;
- Članovi;
- Pozivi;
- Workspace-i;
- Organizacija;
- Audit.

Sections and mutation controls are shown only when the current shell permissions allow them.

## Safety invariants
- Role and product entitlement/access remain separate concepts.
- Organization administrators cannot activate/deactivate organization entitlements in ISI-13.
- Product access cannot exist as active access without a current organization entitlement.
- `organization_admin` invitation escalation is forbidden.
- Organization-wide membership suspension and role mutation require organization-wide management permission. Role-removal scope is resolved from the stored assignment server-side, never trusted from a client query parameter.
- The final active organization administrator cannot be removed or locked out.
- Organization admin cannot set `is_platform_admin`.
- No cross-organization membership/workspace/invitation mutation.
- No cross-product workspace mutation.
- No destructive workspace delete.
- No production invitation token disclosure and no pretend email delivery.
- Every successful mutation emits an immutable admin audit event.

## Non-goals
- No platform superadmin console.
- No billing/subscription management or entitlement mutation UI.
- No SMTP/provider implementation.
- No SSO/SAML/OIDC.
- No security hardening/cutover work; that is ISI-14+.
- No public administration portal.
- No automatic Git commit or push.

## Acceptance
The main runner must pass:
- exact baseline gate;
- static administration audit;
- Alembic offline migration render;
- native PostgreSQL migration to `20260828_0012`;
- focused ISI-13 contracts;
- native PostgreSQL acceptance;
- full regression suite;
- Docker Compose config;
- `git diff --check`.

Then local QA must prove the real administration workspace, permission-aware sections, read-only entitlement boundary, invitation safety, audit visibility and SIMPA/ORDO isolation before visual QA evidence is recorded.

## Next
`ISI-14-SECURITY-HARDENING`
