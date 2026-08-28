# ADR-0021 — Organization administration without collapsing authorization layers

## Decision
Administration is a shared platform capability. Organization administrators manage memberships, member product access, roles and workspaces through server-side permissions and append-only audit events.

Organization entitlement remains read-only in ISI-13. Roles and product access remain distinct. Platform-superadmin and billing/subscription administration are deferred.

## Invitation decision
Pending invitations may carry explicit product and product-scoped role grants. Acceptance applies those grants through the existing authentication lifecycle. Organization-admin role cannot be granted by invitation in ISI-13.

## Lockout protection
For each product, the last active organization administrator (product-scoped or organization-wide) cannot be suspended, stripped of the relevant role, or stripped of that product access path.

## Audit
All successful mutations append `core_admin_audit_events`; no administration endpoint mutates or deletes audit rows.
