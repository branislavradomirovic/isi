# ISI-02A — Identity, Organization, Access and Workspace Data Model

## Status
Implementation package for the first sub-task of ISI-02.

## Purpose
Establish the shared multi-tenant platform data model and authorization contract that both SIMPA and ORDO will use.

This task intentionally does **not** implement login, password hashing, sessions, email verification, password reset, invitations, public auth forms, or Streamlit workspace switching. Those belong to ISI-02B/ISI-02C.

## Locked architectural decisions

1. ISI is one institutional and technological platform.
2. SIMPA and ORDO are separate domain applications sharing one platform core.
3. Organization is the tenant boundary.
4. A user may belong to multiple organizations through memberships.
5. Product entitlement belongs to the organization.
6. Product access belongs to the membership and may only exist when the organization is entitled to that product.
7. Roles do not imply product access.
8. Role assignments may be organization-wide (`*`) or product-scoped (`SIMPA` / `ORDO`).
9. Workspaces belong to one organization and one product.
10. SIMPA and ORDO domain tables are not introduced in this task.
11. No business data is stored in generic JSON blobs.
12. Authorization is deny-by-default.

## Core entities

### User
Shared identity record.

Required fields:
- UUID id
- normalized unique email
- password_hash placeholder for the future auth milestone
- display_name
- is_active
- is_platform_admin
- created_at / updated_at

No password hashing behavior is introduced in ISI-02A.

### Organization
Tenant/institution record.

Required fields:
- UUID id
- unique slug
- name
- status
- created_at / updated_at

### Membership
Connects a user to an organization.

Required fields:
- UUID id
- user_id
- organization_id
- status
- created_at / updated_at

A `(user_id, organization_id)` pair must be unique.

### Product
Reference catalog.

Initial product codes:
- `SIMPA`
- `ORDO`

### OrganizationEntitlement
Defines which products an organization is licensed/authorized to use.

### MembershipProductAccess
Defines which organization products a specific membership may access.

Membership product access is invalid unless an active organization entitlement exists for the same product. This invariant is enforced by the service layer in this milestone and covered by tests.

### Role
System role catalog.

Initial roles:
- organization_admin
- domain_manager
- analyst
- data_manager
- reviewer
- viewer

### Permission
Permission catalog.

Permission codes are capability-based rather than page-based.

### RolePermission
Many-to-many role/permission map.

### RoleAssignment
Assigns a role to a membership.

Scope rules:
- `product_code="*"` means organization-wide
- `product_code="SIMPA"` means SIMPA-only role assignment
- `product_code="ORDO"` means ORDO-only role assignment

A role assignment does not grant product access by itself.

### Workspace
Shared platform workspace envelope.

Required fields:
- UUID id
- organization_id
- product_code
- slug
- name
- status
- created_by_membership_id
- created_at / updated_at

Domain data remains in `src/domains/simpa` or `src/domains/ordo` and future domain tables.

## Table naming
Shared platform tables use the `core_` prefix:

- core_users
- core_organizations
- core_memberships
- core_products
- core_organization_entitlements
- core_membership_product_access
- core_roles
- core_permissions
- core_role_permissions
- core_role_assignments
- core_workspaces

## Authorization contract

`can_access_product(session, user_id, organization_id, product_code)` returns true only when:
- user is active;
- membership is active;
- organization entitlement is active;
- membership product access is active.

Platform administrators may bypass tenant product-access checks for administrative purposes.

`has_permission(...)` is deny-by-default and evaluates:
- active user;
- active membership;
- product access when a product is requested;
- role assignments scoped to `*` or the requested product;
- role-to-permission mappings.

## Reference catalog
Provide deterministic bootstrap data for:
- products;
- roles;
- permissions;
- role-permission mappings.

The bootstrap routine must be idempotent.

## Required access tests

1. SIMPA-only organization/member:
   - SIMPA access true
   - ORDO access false
2. ORDO-only organization/member:
   - ORDO access true
   - SIMPA access false
3. Dual-product organization/member:
   - both true
4. Organization A user cannot access Organization B without a membership there.
5. Membership product access without organization entitlement is rejected by the grant service.
6. Viewer cannot run analysis.
7. Analyst can run analysis but cannot manage members.
8. Organization admin with `*` scope can manage members.
9. Product-scoped role does not leak permissions to the other product.
10. Disabled user or suspended membership is denied.

## Migration requirements
Create one Alembic revision introducing the shared platform tables.

The migration must be importable and renderable with:

```bash
alembic upgrade head --sql
```

No live PostgreSQL connection is required by this task package.

## Out of scope
- password hashing
- login/logout
- JWT/session cookies
- email verification
- password reset
- invitation emails
- Streamlit workspace selector
- public login page redesign
- SIMPA domain models
- ORDO domain models
- AI models or RAG
- billing

## Acceptance gate
The task passes only when:
- repository starts clean on `main`;
- required model files exist;
- Alembic metadata registers platform models;
- migration renders offline;
- reference catalog bootstrap is idempotent;
- access matrix tests pass;
- full pytest suite passes;
- compileall passes;
- git diff whitespace check passes;
- only allowed ISI-02A paths changed;
- no commit/push is performed by runner/analyzer.
