from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_alembic_env_registers_platform_models() -> None:
    text = (ROOT / "migrations" / "env.py").read_text()
    assert "src.platform" in text
    assert "platform_models" in text


def test_identity_access_migration_exists_and_has_expected_tables() -> None:
    migration = ROOT / "migrations" / "versions" / "20260827_0001_identity_access_workspaces.py"
    text = migration.read_text()
    for table in (
        "core_users",
        "core_organizations",
        "core_memberships",
        "core_products",
        "core_organization_entitlements",
        "core_membership_product_access",
        "core_roles",
        "core_permissions",
        "core_role_permissions",
        "core_role_assignments",
        "core_workspaces",
    ):
        assert table in text
