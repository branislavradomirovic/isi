from pathlib import Path


def test_security_migration_contract():
    text = Path("migrations/versions/20260828_0013_security_hardening.py").read_text()
    assert 'revision = "20260828_0013"' in text
    assert 'down_revision = "20260828_0012"' in text
    for token in ("core_security_rate_limits", "core_security_events", "remote_ip_hash", "user_agent_hash", "revoked_reason"):
        assert token in text
