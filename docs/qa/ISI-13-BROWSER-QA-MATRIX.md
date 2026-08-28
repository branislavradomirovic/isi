# ISI-13 Browser QA Matrix

Use the dual demo account for the positive path and the SIMPA-only account for product-isolation negative control.

- Administration opens as a real workspace, not a placeholder.
- Active organization and product are clear.
- Organization entitlement is visible but read-only.
- Members show membership status, active product access and scoped roles.
- Product access and roles are visually distinct concepts.
- Organization-admin role cannot be selected in invitation flow.
- Development invitation token is clearly marked non-production; no claim of email delivery exists.
- Workspace list can create/archive/reactivate without hard delete.
- Organization rename is available only with organization-wide management authority.
- Audit tab shows append-only administrative mutation events when `audit.read` is present.
- SIMPA-only account cannot open ORDO administration context.
- Switching SIMPA <-> ORDO does not mix workspace or member product scope.
- No traceback, raw exception or duplicate browser tab.
