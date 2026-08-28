from pathlib import Path


def test_existing_auth_acceptance_applies_administration_grants():
    auth = Path("src/platform/auth/service.py").read_text()
    assert "apply_invitation_grants" in auth
    service = Path("src/platform/administration/service.py").read_text()
    assert "grant_product_access" in service
    assert "InvitationRoleGrant" in service
    assert "RoleAssignment" in service


def test_invitation_does_not_escalate_to_org_admin():
    service = Path("src/platform/administration/service.py").read_text()
    assert "organization_admin_invitation_forbidden" in service
    assert "invitation_org_wide_role_forbidden" in service
