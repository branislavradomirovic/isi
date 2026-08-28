from pathlib import Path


def require(path: str, *tokens: str) -> None:
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"missing required artifact: {path}")
    text = p.read_text()
    for token in tokens:
        if token not in text:
            raise SystemExit(f"{path}: missing administration contract token: {token}")


require("src/platform/administration/models.py", "core_admin_audit_events", "core_invitation_product_grants", "core_invitation_role_grants")
require("src/platform/administration/service.py", "last_organization_admin_required", "organization_entitlement_not_active", "organization_admin_invitation_forbidden", "apply_invitation_grants")
require("src/api/administration_routes.py", "/api/v1/administration", "invitation_delivery_not_configured", "organization_wide_permission_required")
require("src/streamlit_app/administration_workspace.py", "Administracija", "Entitlement je read-only", "Članovi", "Workspace-i", "Audit")
require("src/platform/auth/service.py", "apply_invitation_grants")
require("migrations/versions/20260828_0012_administration.py", 'revision = "20260828_0012"', 'down_revision = "20260828_0011"')

service = Path("src/platform/administration/service.py").read_text()
if "entitlement.is_active =" in service:
    raise SystemExit("organization entitlement mutation is forbidden in ISI-13")
if "is_platform_admin =" in service:
    raise SystemExit("organization administration must not mutate platform-admin flag")
if "session.delete(workspace)" in service:
    raise SystemExit("workspace hard delete is forbidden in ISI-13")
if Path("src/platform/administration/__init__.py").read_text().strip():
    raise SystemExit("platform administration package __init__ must stay empty")
print("ISI-13 administration static audit PASS")
