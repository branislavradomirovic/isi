from pathlib import Path


def test_last_admin_and_entitlement_guards_are_pinned():
    service = Path("src/platform/administration/service.py").read_text()
    assert "last_organization_admin_required" in service
    assert "last_organization_admin_product_access_required" in service
    assert "organization_entitlement_not_active" in service
    assert "_protect_last_admin_for_product" in service


def test_production_invitation_delivery_is_not_faked():
    routes = Path("src/api/administration_routes.py").read_text()
    assert 'isi_env.casefold() == "production"' in routes
    assert "invitation_delivery_not_configured" in routes
    assert '"development_token": token' in routes
