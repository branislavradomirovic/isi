from pathlib import Path


def test_scope_checks_are_server_side():
    routes = Path("src/api/administration_routes.py").read_text()
    assert "resolve_selection" in routes
    assert "has_permission" in routes
    assert "has_org_wide_permission" in routes
    assert "organization_wide_permission_required" in routes
    assert "members.manage" in routes
    assert "workspace.manage" in routes
    assert 'scope: str = Query("product")' not in routes
    assert "allow_org_wide = has_org_wide_permission" in routes
    assert 'assignment.product_code == "*" and not allow_org_wide' in Path("src/platform/administration/service.py").read_text()
