"""Fail-closed, non-production recovery primitives for ISI.

The module intentionally contains no scheduler and no production target discovery.
Callers must provide explicit artifacts, storage keys and a non-production target label.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Callable, Protocol, Sequence

from src.platform.data.storage import StorageBackend

MANIFEST_SCHEMA_VERSION = 1
TOOL_VERSION = "isi-recovery/1"
_ALLOWED_NONPRODUCTION_TARGETS = {
    "ci",
    "test",
    "testing",
    "dev",
    "development",
    "staging",
    "synthetic",
}


class RecoveryError(RuntimeError):
    """Raised when recovery cannot continue safely or verifiably."""


class Cipher(Protocol):
    algorithm: str

    def encrypt(self, payload: bytes) -> bytes: ...

    def decrypt(self, payload: bytes) -> bytes: ...


@dataclass(frozen=True)
class NoEncryption:
    """Explicit identity cipher used by synthetic CI fixtures."""

    algorithm: str = "none"

    def encrypt(self, payload: bytes) -> bytes:
        return payload

    def decrypt(self, payload: bytes) -> bytes:
        return payload


@dataclass(frozen=True)
class ArtifactRecord:
    logical_name: str
    kind: str
    relative_path: str
    size_bytes: int
    sha256: str
    content_size_bytes: int
    content_sha256: str
    encryption: str = "none"
    source_key: str | None = None

    def to_dict(self) -> dict[str, object]:
        value: dict[str, object] = {
            "logical_name": self.logical_name,
            "kind": self.kind,
            "relative_path": self.relative_path,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "content_size_bytes": self.content_size_bytes,
            "content_sha256": self.content_sha256,
            "encryption": self.encryption,
        }
        if self.source_key is not None:
            value["source_key"] = self.source_key
        return value

    @classmethod
    def from_dict(cls, value: object) -> ArtifactRecord:
        if not isinstance(value, dict):
            raise RecoveryError("manifest artifact must be an object")
        try:
            record = cls(
                logical_name=str(value["logical_name"]),
                kind=str(value["kind"]),
                relative_path=str(value["relative_path"]),
                size_bytes=int(value["size_bytes"]),
                sha256=str(value["sha256"]),
                content_size_bytes=int(value["content_size_bytes"]),
                content_sha256=str(value["content_sha256"]),
                encryption=str(value.get("encryption", "none")),
                source_key=str(value["source_key"]) if value.get("source_key") is not None else None,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise RecoveryError("manifest artifact is malformed") from exc
        _validate_artifact_record(record)
        return record


@dataclass(frozen=True)
class RecoveryManifest:
    backup_id: str
    created_at: str
    source_descriptor: str
    artifacts: tuple[ArtifactRecord, ...]
    database_schema_revision: str = "not-applicable"
    verification_state: str = "UNVERIFIED"
    schema_version: int = MANIFEST_SCHEMA_VERSION
    tool_version: str = TOOL_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "tool_version": self.tool_version,
            "backup_id": self.backup_id,
            "created_at": self.created_at,
            "source_descriptor": self.source_descriptor,
            "database_schema_revision": self.database_schema_revision,
            "verification_state": self.verification_state,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
        }

    def to_json(self) -> str:
        """Return canonical JSON suitable for checksums and evidence."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"

    @classmethod
    def from_json(cls, payload: str) -> RecoveryManifest:
        try:
            value = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise RecoveryError("recovery manifest is not valid JSON") from exc
        if not isinstance(value, dict):
            raise RecoveryError("recovery manifest must be an object")
        try:
            schema_version = int(value["schema_version"])
            artifacts_value = value["artifacts"]
            if not isinstance(artifacts_value, list):
                raise RecoveryError("manifest artifacts must be a list")
            manifest = cls(
                schema_version=schema_version,
                tool_version=str(value["tool_version"]),
                backup_id=str(value["backup_id"]),
                created_at=str(value["created_at"]),
                source_descriptor=str(value["source_descriptor"]),
                database_schema_revision=str(value["database_schema_revision"]),
                verification_state=str(value["verification_state"]),
                artifacts=tuple(ArtifactRecord.from_dict(item) for item in artifacts_value),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise RecoveryError("recovery manifest is malformed") from exc
        validate_manifest(manifest)
        return manifest


@dataclass(frozen=True)
class BackupSet:
    backup_id: str
    created_at: datetime
    path: Path


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_nonproduction_target(target_label: str) -> str:
    normalized = target_label.strip().lower()
    if normalized not in _ALLOWED_NONPRODUCTION_TARGETS:
        raise RecoveryError("recovery target is not an explicitly allowed non-production target")
    return normalized


def _safe_relative_path(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise RecoveryError("unsafe recovery artifact path")
    return path.as_posix()


def _safe_descriptor(value: str) -> str:
    descriptor = value.strip()
    lowered = descriptor.lower()
    if not descriptor or "://" in descriptor or "password=" in lowered or "token=" in lowered or "@" in descriptor:
        raise RecoveryError("source descriptor must be a non-secret logical label")
    return descriptor


def _validate_digest(value: str) -> None:
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value.lower()):
        raise RecoveryError("manifest contains an invalid SHA-256 digest")


def _validate_artifact_record(record: ArtifactRecord) -> None:
    if not record.logical_name.strip() or not record.kind.strip():
        raise RecoveryError("manifest artifact names must be non-empty")
    _safe_relative_path(record.relative_path)
    if record.size_bytes < 0 or record.content_size_bytes < 0:
        raise RecoveryError("manifest artifact sizes must be non-negative")
    _validate_digest(record.sha256)
    _validate_digest(record.content_sha256)
    if not record.encryption.strip():
        raise RecoveryError("manifest artifact encryption state is required")


def validate_manifest(manifest: RecoveryManifest) -> None:
    if manifest.schema_version != MANIFEST_SCHEMA_VERSION:
        raise RecoveryError("unsupported recovery manifest schema version")
    if manifest.tool_version != TOOL_VERSION:
        raise RecoveryError("unsupported recovery tool version")
    if not manifest.backup_id.strip():
        raise RecoveryError("backup identifier is required")
    _safe_descriptor(manifest.source_descriptor)
    try:
        created = datetime.fromisoformat(manifest.created_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RecoveryError("manifest creation timestamp is invalid") from exc
    if created.tzinfo is None:
        raise RecoveryError("manifest creation timestamp must include a timezone")
    paths: set[str] = set()
    object_keys: set[str] = set()
    for artifact in manifest.artifacts:
        _validate_artifact_record(artifact)
        if artifact.relative_path in paths:
            raise RecoveryError("manifest contains duplicate artifact paths")
        paths.add(artifact.relative_path)
        if artifact.source_key is not None:
            if artifact.source_key in object_keys:
                raise RecoveryError("manifest contains duplicate source keys")
            object_keys.add(artifact.source_key)


def make_manifest(
    *,
    backup_id: str,
    created_at: str,
    source_descriptor: str,
    artifacts: Sequence[ArtifactRecord],
    database_schema_revision: str = "not-applicable",
    verification_state: str = "UNVERIFIED",
) -> RecoveryManifest:
    manifest = RecoveryManifest(
        backup_id=backup_id,
        created_at=created_at,
        source_descriptor=_safe_descriptor(source_descriptor),
        artifacts=tuple(artifacts),
        database_schema_revision=database_schema_revision,
        verification_state=verification_state,
    )
    validate_manifest(manifest)
    return manifest


def write_manifest(manifest: RecoveryManifest, path: Path) -> None:
    validate_manifest(manifest)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manifest.to_json(), encoding="utf-8")


def load_manifest(path: Path) -> RecoveryManifest:
    return RecoveryManifest.from_json(path.read_text(encoding="utf-8"))


def write_artifact(
    *,
    backup_root: Path,
    relative_path: str,
    payload: bytes,
    logical_name: str,
    kind: str,
    source_key: str | None = None,
    cipher: Cipher | None = None,
) -> ArtifactRecord:
    active_cipher: Cipher = cipher or NoEncryption()
    safe_path = _safe_relative_path(relative_path)
    stored = active_cipher.encrypt(payload)
    path = backup_root / safe_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(stored)
    record = ArtifactRecord(
        logical_name=logical_name,
        kind=kind,
        relative_path=safe_path,
        size_bytes=len(stored),
        sha256=sha256_bytes(stored),
        content_size_bytes=len(payload),
        content_sha256=sha256_bytes(payload),
        encryption=active_cipher.algorithm,
        source_key=source_key,
    )
    _validate_artifact_record(record)
    return record


def record_existing_artifact(
    *,
    backup_root: Path,
    relative_path: str,
    logical_name: str,
    kind: str,
    source_key: str | None = None,
) -> ArtifactRecord:
    safe_path = _safe_relative_path(relative_path)
    path = backup_root / safe_path
    if not path.is_file():
        raise RecoveryError("recovery artifact is missing")
    payload = path.read_bytes()
    return ArtifactRecord(
        logical_name=logical_name,
        kind=kind,
        relative_path=safe_path,
        size_bytes=len(payload),
        sha256=sha256_bytes(payload),
        content_size_bytes=len(payload),
        content_sha256=sha256_bytes(payload),
        encryption="none",
        source_key=source_key,
    )


def read_verified_artifact(
    *,
    backup_root: Path,
    artifact: ArtifactRecord,
    cipher: Cipher | None = None,
) -> bytes:
    active_cipher: Cipher = cipher or NoEncryption()
    if active_cipher.algorithm != artifact.encryption:
        raise RecoveryError("artifact encryption handler does not match manifest")
    path = backup_root / _safe_relative_path(artifact.relative_path)
    if not path.is_file():
        raise RecoveryError("recovery artifact is missing")
    stored = path.read_bytes()
    if len(stored) != artifact.size_bytes or sha256_bytes(stored) != artifact.sha256:
        raise RecoveryError("recovery artifact integrity verification failed")
    try:
        payload = active_cipher.decrypt(stored)
    except Exception as exc:
        raise RecoveryError("recovery artifact decryption failed") from exc
    if len(payload) != artifact.content_size_bytes or sha256_bytes(payload) != artifact.content_sha256:
        raise RecoveryError("recovery artifact content verification failed")
    return payload


def verify_manifest_artifacts(
    manifest: RecoveryManifest,
    *,
    backup_root: Path,
    cipher: Cipher | None = None,
) -> None:
    validate_manifest(manifest)
    for artifact in manifest.artifacts:
        read_verified_artifact(backup_root=backup_root, artifact=artifact, cipher=cipher)


def backup_storage_objects(
    storage: StorageBackend,
    *,
    keys: Sequence[str],
    backup_root: Path,
    backup_id: str,
    created_at: str,
    source_descriptor: str,
    cipher: Cipher | None = None,
) -> RecoveryManifest:
    if len(set(keys)) != len(keys):
        raise RecoveryError("object backup keys must be unique")
    artifacts: list[ArtifactRecord] = []
    for index, key in enumerate(sorted(keys)):
        if not key.strip():
            raise RecoveryError("object backup key must be non-empty")
        payload = storage.get_bytes(key)
        key_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        artifacts.append(
            write_artifact(
                backup_root=backup_root,
                relative_path=f"objects/{index:06d}-{key_hash}.bin",
                payload=payload,
                logical_name=f"object-{index:06d}",
                kind="object",
                source_key=key,
                cipher=cipher,
            )
        )
    return make_manifest(
        backup_id=backup_id,
        created_at=created_at,
        source_descriptor=source_descriptor,
        artifacts=artifacts,
    )


def restore_storage_objects(
    manifest: RecoveryManifest,
    *,
    backup_root: Path,
    target_storage: StorageBackend,
    target_label: str,
    cipher: Cipher | None = None,
) -> tuple[str, ...]:
    validate_nonproduction_target(target_label)
    restored: list[str] = []
    for artifact in manifest.artifacts:
        if artifact.kind != "object":
            continue
        if artifact.source_key is None:
            raise RecoveryError("object artifact is missing its source key")
        payload = read_verified_artifact(backup_root=backup_root, artifact=artifact, cipher=cipher)
        target_storage.put_bytes(artifact.source_key, payload)
        if target_storage.get_bytes(artifact.source_key) != payload:
            raise RecoveryError("restored object verification failed")
        restored.append(artifact.source_key)
    return tuple(restored)


def postgres_dump_command(database_url: str, output_path: Path) -> tuple[str, ...]:
    if not database_url.strip():
        raise RecoveryError("PostgreSQL source is required")
    return (
        "pg_dump",
        "--format=custom",
        "--no-owner",
        "--no-privileges",
        "--file",
        str(output_path),
        database_url,
    )


def postgres_restore_command(database_url: str, input_path: Path) -> tuple[str, ...]:
    if not database_url.strip():
        raise RecoveryError("PostgreSQL target is required")
    return (
        "pg_restore",
        "--no-owner",
        "--no-privileges",
        "--exit-on-error",
        "--dbname",
        database_url,
        str(input_path),
    )


def _run_postgres_command(
    command: tuple[str, ...],
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]],
    failure_message: str,
) -> None:
    try:
        result = runner(command, check=False, capture_output=True, text=True)
    except OSError as exc:
        raise RecoveryError(failure_message) from exc
    if result.returncode != 0:
        # Deliberately do not include command/stdout/stderr because they can contain a credential-bearing DSN.
        raise RecoveryError(failure_message)


def run_postgres_dump(
    database_url: str,
    output_path: Path,
    *,
    target_label: str,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> None:
    validate_nonproduction_target(target_label)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _run_postgres_command(
        postgres_dump_command(database_url, output_path),
        runner=runner,
        failure_message="PostgreSQL backup command failed",
    )
    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RecoveryError("PostgreSQL backup artifact was not created")


def run_postgres_restore(
    database_url: str,
    input_path: Path,
    *,
    target_label: str,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> None:
    validate_nonproduction_target(target_label)
    if not input_path.is_file():
        raise RecoveryError("PostgreSQL restore artifact is missing")
    _run_postgres_command(
        postgres_restore_command(database_url, input_path),
        runner=runner,
        failure_message="PostgreSQL restore command failed",
    )


def plan_retention(
    backups: Sequence[BackupSet],
    *,
    keep_last: int,
    max_age_days: int,
    now: datetime | None = None,
) -> tuple[BackupSet, ...]:
    if keep_last < 0 or max_age_days < 0:
        raise RecoveryError("retention values must be non-negative")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise RecoveryError("retention clock must be timezone-aware")
    ordered = sorted(backups, key=lambda item: (item.created_at, item.backup_id), reverse=True)
    protected_ids = {item.backup_id for item in ordered[:keep_last]}
    cutoff = current - timedelta(days=max_age_days)
    return tuple(item for item in ordered if item.backup_id not in protected_ids and item.created_at < cutoff)


def delete_backup_sets(
    backups: Sequence[BackupSet],
    *,
    backup_root: Path,
    target_label: str,
    allow_delete: bool = False,
) -> tuple[str, ...]:
    validate_nonproduction_target(target_label)
    if not allow_delete:
        raise RecoveryError("retention deletion requires explicit non-production opt-in")
    root = backup_root.resolve()
    deleted: list[str] = []
    for item in backups:
        path = item.path.resolve()
        if path == root or not path.is_relative_to(root):
            raise RecoveryError("retention candidate is outside the backup root")
        if path.is_dir():
            for child in sorted(path.rglob("*"), reverse=True):
                if child.is_file() or child.is_symlink():
                    child.unlink()
                elif child.is_dir():
                    child.rmdir()
            path.rmdir()
        elif path.exists():
            path.unlink()
        deleted.append(item.backup_id)
    return tuple(deleted)
