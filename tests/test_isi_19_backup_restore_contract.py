from __future__ import annotations

import subprocess
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.platform.data.storage import LocalFilesystemStorage, S3CompatibleStorage
from src.platform.recovery.service import (
    ArtifactRecord,
    BackupSet,
    RecoveryError,
    RecoveryManifest,
    backup_storage_objects,
    delete_backup_sets,
    load_manifest,
    plan_retention,
    postgres_dump_command,
    postgres_restore_command,
    read_verified_artifact,
    restore_storage_objects,
    run_postgres_restore,
    validate_nonproduction_target,
    verify_manifest_artifacts,
    write_artifact,
    write_manifest,
)

FIXED_TIME = "2026-09-10T12:00:00Z"


def test_manifest_is_canonical_versioned_and_detects_corruption(tmp_path: Path) -> None:
    artifact = write_artifact(
        backup_root=tmp_path,
        relative_path="database/isi.dump",
        payload=b"synthetic-database-payload",
        logical_name="postgresql-main",
        kind="postgresql-custom-dump",
    )
    manifest = RecoveryManifest(
        backup_id="synthetic-001",
        created_at=FIXED_TIME,
        source_descriptor="synthetic-ci",
        artifacts=(artifact,),
        database_schema_revision="synthetic-head",
    )

    first = manifest.to_json()
    second = manifest.to_json()
    assert first == second
    assert '"schema_version":1' in first
    assert '"verification_state":"UNVERIFIED"' in first

    manifest_path = tmp_path / "manifest.json"
    write_manifest(manifest, manifest_path)
    loaded = load_manifest(manifest_path)
    assert loaded == manifest
    verify_manifest_artifacts(loaded, backup_root=tmp_path)

    (tmp_path / artifact.relative_path).write_bytes(b"tampered")
    with pytest.raises(RecoveryError, match="integrity verification failed"):
        read_verified_artifact(backup_root=tmp_path, artifact=artifact)


def test_local_object_recovery_preserves_simpa_ordo_keys_and_bytes(tmp_path: Path) -> None:
    source = LocalFilesystemStorage(tmp_path / "source")
    target = LocalFilesystemStorage(tmp_path / "target")
    keys = (
        "org-a/SIMPA/workspace-a/aa/simpa-fixture.bin",
        "org-a/ORDO/workspace-b/bb/ordo-fixture.bin",
    )
    expected = {
        keys[0]: b"synthetic-simpa-object",
        keys[1]: b"synthetic-ordo-object",
    }
    for key, payload in expected.items():
        source.put_bytes(key, payload)

    backup_root = tmp_path / "backup"
    manifest = backup_storage_objects(
        source,
        keys=keys,
        backup_root=backup_root,
        backup_id="objects-001",
        created_at=FIXED_TIME,
        source_descriptor="synthetic-local-storage",
    )
    restored = restore_storage_objects(
        manifest,
        backup_root=backup_root,
        target_storage=target,
        target_label="ci",
    )

    assert set(restored) == set(keys)
    for key, payload in expected.items():
        assert target.get_bytes(key) == payload
    assert all(item.source_key in keys for item in manifest.artifacts)


class _FakeBody:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return self.payload


class _MissingObject(Exception):
    def __init__(self) -> None:
        self.response = {"Error": {"Code": "NoSuchKey"}, "ResponseMetadata": {"HTTPStatusCode": 404}}


class _FakeS3Client:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, _FakeBody]:
        try:
            payload = self.objects[(Bucket, Key)]
        except KeyError as exc:
            raise _MissingObject() from exc
        return {"Body": _FakeBody(payload)}

    def put_object(self, *, Bucket: str, Key: str, Body: bytes) -> None:
        self.objects[(Bucket, Key)] = bytes(Body)

    def head_object(self, *, Bucket: str, Key: str) -> None:
        if (Bucket, Key) not in self.objects:
            raise _MissingObject()


def test_s3_compatible_backend_recovery_contract(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = _FakeS3Client()
    monkeypatch.setattr(S3CompatibleStorage, "_client", lambda self: client)
    source = S3CompatibleStorage(bucket="synthetic-source")
    target = S3CompatibleStorage(bucket="synthetic-target")
    key = "org-a/SIMPA/workspace-a/cc/s3-fixture.bin"
    source.put_bytes(key, b"synthetic-s3-compatible-payload")

    manifest = backup_storage_objects(
        source,
        keys=(key,),
        backup_root=tmp_path / "backup",
        backup_id="s3-contract-001",
        created_at=FIXED_TIME,
        source_descriptor="synthetic-s3-compatible",
    )
    restore_storage_objects(
        manifest,
        backup_root=tmp_path / "backup",
        target_storage=target,
        target_label="testing",
    )
    assert target.get_bytes(key) == b"synthetic-s3-compatible-payload"


def test_retention_is_dry_run_by_default_and_delete_is_explicit(tmp_path: Path) -> None:
    now = datetime(2026, 9, 10, tzinfo=timezone.utc)
    backups: list[BackupSet] = []
    for index, age_days in enumerate((1, 3, 40, 80)):
        path = tmp_path / f"backup-{index}"
        path.mkdir()
        (path / "manifest.json").write_text("synthetic", encoding="utf-8")
        backups.append(
            BackupSet(
                backup_id=f"backup-{index}",
                created_at=now - timedelta(days=age_days),
                path=path,
            )
        )

    eligible = plan_retention(backups, keep_last=2, max_age_days=30, now=now)
    assert [item.backup_id for item in eligible] == ["backup-2", "backup-3"]
    assert all(item.path.exists() for item in backups)

    with pytest.raises(RecoveryError, match="explicit non-production opt-in"):
        delete_backup_sets(eligible, backup_root=tmp_path, target_label="ci")
    assert all(item.path.exists() for item in backups)

    deleted = delete_backup_sets(
        eligible,
        backup_root=tmp_path,
        target_label="ci",
        allow_delete=True,
    )
    assert deleted == ("backup-2", "backup-3")
    assert backups[0].path.exists() and backups[1].path.exists()


def test_production_target_is_rejected_and_command_errors_do_not_leak_dsn(tmp_path: Path) -> None:
    with pytest.raises(RecoveryError, match="not an explicitly allowed"):
        validate_nonproduction_target("production")

    secret_dsn = "postgresql://ci_user:super-secret@127.0.0.1:5432/isi_target"
    dump_command = postgres_dump_command(secret_dsn, tmp_path / "db.dump")
    restore_command = postgres_restore_command(secret_dsn, tmp_path / "db.dump")
    assert dump_command[0] == "pg_dump"
    assert restore_command[0] == "pg_restore"
    assert "--exit-on-error" in restore_command

    (tmp_path / "db.dump").write_bytes(b"synthetic-dump")

    def failed_runner(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=["pg_restore"], returncode=1, stdout="", stderr=secret_dsn)

    with pytest.raises(RecoveryError) as exc_info:
        run_postgres_restore(
            secret_dsn,
            tmp_path / "db.dump",
            target_label="ci",
            runner=failed_runner,
        )
    assert "super-secret" not in str(exc_info.value)
    assert secret_dsn not in str(exc_info.value)


def test_manifest_rejects_path_traversal_duplicate_keys_and_encryption_mismatch(tmp_path: Path) -> None:
    good = write_artifact(
        backup_root=tmp_path,
        relative_path="objects/000001.bin",
        payload=b"fixture",
        logical_name="object-1",
        kind="object",
        source_key="org-a/SIMPA/ws/file.bin",
    )
    bad_path = replace(good, relative_path="../escape.bin")
    manifest = RecoveryManifest(
        backup_id="bad",
        created_at=FIXED_TIME,
        source_descriptor="synthetic-ci",
        artifacts=(bad_path,),
    )
    with pytest.raises(RecoveryError, match="unsafe recovery artifact path"):
        RecoveryManifest.from_json(manifest.to_json())

    duplicate = RecoveryManifest(
        backup_id="duplicate",
        created_at=FIXED_TIME,
        source_descriptor="synthetic-ci",
        artifacts=(good, replace(good, logical_name="object-2", relative_path="objects/000002.bin")),
    )
    with pytest.raises(RecoveryError, match="duplicate source keys"):
        RecoveryManifest.from_json(duplicate.to_json())

    encrypted_record = replace(good, encryption="external-kms-hook")
    with pytest.raises(RecoveryError, match="handler does not match"):
        read_verified_artifact(backup_root=tmp_path, artifact=encrypted_record)


def test_artifact_schema_requires_sha256_and_sizes() -> None:
    with pytest.raises(RecoveryError):
        ArtifactRecord.from_dict(
            {
                "logical_name": "bad",
                "kind": "object",
                "relative_path": "objects/bad.bin",
                "size_bytes": 1,
                "sha256": "not-a-digest",
                "content_size_bytes": 1,
                "content_sha256": "not-a-digest",
                "encryption": "none",
            }
        )
