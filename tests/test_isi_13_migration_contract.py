from pathlib import Path


def test_migration_contract():
    text = Path("migrations/versions/20260828_0012_administration.py").read_text()
    assert 'revision = "20260828_0012"' in text
    assert 'down_revision = "20260828_0011"' in text
    for table in ("core_invitation_product_grants", "core_invitation_role_grants", "core_admin_audit_events"):
        assert table in text
    assert "ck_core_invitation_role_grant_scope" in text
    assert "ck_core_admin_audit_product_scope" in text
