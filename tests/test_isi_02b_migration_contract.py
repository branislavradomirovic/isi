from pathlib import Path


def test_auth_migration_contract():
    text = Path("migrations/versions/20260827_0002_authentication_lifecycle.py").read_text()
    assert 'revision: str = "20260827_0002"' in text
    assert 'down_revision: str | None = "20260827_0001"' in text
    for table in ("core_auth_sessions", "core_auth_tokens", "core_invitations"):
        assert table in text
    for column in ("email_verified_at", "last_login_at", "password_changed_at"):
        assert column in text
    assert "lower(email)" in text
