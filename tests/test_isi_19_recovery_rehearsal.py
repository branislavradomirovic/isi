from __future__ import annotations

from pathlib import Path


def test_isi19_recovery_rehearsal_is_pinned_idempotent_and_server_free() -> None:
    script = Path("tools/ci/isi19_recovery_rehearsal.sh").read_text(encoding="utf-8")
    assert "postgres:17-alpine" in script
    assert "trap cleanup EXIT" in script
    assert "migration_check.sh live" in script
    assert "SIMPA" in script and "ORDO" in script
    assert "sha256sum" in script
    assert "DEFERRED_SERVER_VERIFICATION" in script
    assert "isi.rs" not in script
    assert "production" not in script.lower()
    assert "ssh " not in script.lower()
    assert "scp " not in script.lower()


def test_native_postgres_gate_invokes_isi19_recovery_rehearsal() -> None:
    script = Path("tools/ci/native_postgres_tests.sh").read_text(encoding="utf-8")
    assert "tools/ci/isi19_recovery_rehearsal.sh" in script
