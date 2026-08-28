from pathlib import Path


def test_administration_module_and_domain_boundaries():
    assert Path("src/platform/administration/__init__.py").read_text().strip() == ""
    service = Path("src/platform/administration/service.py").read_text()
    assert "AdministrationError" in service
    assert "organization_entitlement_not_active" in service
    assert "is_platform_admin =" not in service
    assert "entitlement.is_active =" not in service
    assert "session.delete(workspace)" not in service


def test_task_spec_locks_role_vs_product_access_boundary():
    text = Path("automation/specs/ISI-13-ADMINISTRATION.md").read_text()
    assert "Roles answer **what a member may do**" in text
    assert "Product access answers **which flagship product" in text
    assert "Organization entitlement remains a platform/commercial boundary" in text
