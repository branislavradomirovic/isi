from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from src.core.config import get_settings


class StorageError(RuntimeError):
    pass


class StorageBackend(Protocol):
    def put_bytes(self, key: str, payload: bytes) -> bool: ...
    def get_bytes(self, key: str) -> bytes: ...
    def exists(self, key: str) -> bool: ...


@dataclass(frozen=True)
class LocalFilesystemStorage:
    root: Path

    def _path(self, key: str) -> Path:
        relative = Path(key)
        if relative.is_absolute() or ".." in relative.parts:
            raise StorageError("unsafe storage key")
        return self.root / relative

    def put_bytes(self, key: str, payload: bytes) -> bool:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_bytes() != payload:
                raise StorageError("content-addressed storage collision")
            return False
        tmp = path.with_name(path.name + f".tmp-{os.getpid()}")
        tmp.write_bytes(payload)
        os.replace(tmp, path)
        return True

    def get_bytes(self, key: str) -> bytes:
        path = self._path(key)
        if not path.exists():
            raise StorageError("storage object missing")
        return path.read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()


@dataclass(frozen=True)
class S3CompatibleStorage:
    bucket: str
    endpoint_url: str

    def _unavailable(self) -> None:
        raise StorageError("S3-compatible runtime adapter is not enabled until deployment hardening")

    def put_bytes(self, key: str, payload: bytes) -> bool:
        self._unavailable()
        return False

    def get_bytes(self, key: str) -> bytes:
        self._unavailable()
        return b""

    def exists(self, key: str) -> bool:
        self._unavailable()
        return False


def scoped_storage_key(*, organization_id: str, product_code: str, workspace_id: str, sha256: str, extension: str) -> str:
    ext = extension.lower().lstrip(".") or "bin"
    return f"{organization_id}/{product_code}/{workspace_id}/{sha256[:2]}/{sha256}.{ext}"


def digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def build_storage() -> StorageBackend:
    settings = get_settings()
    backend = getattr(settings, "data_storage_backend", "local")
    if backend == "local":
        return LocalFilesystemStorage(Path(getattr(settings, "data_storage_root", ".isi-data")))
    if backend == "s3":
        return S3CompatibleStorage(
            bucket=getattr(settings, "data_s3_bucket", ""),
            endpoint_url=getattr(settings, "data_s3_endpoint_url", ""),
        )
    raise StorageError(f"unsupported storage backend: {backend}")
