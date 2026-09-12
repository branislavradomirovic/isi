from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from src.core.config import get_settings


class StorageError(RuntimeError):
    pass


class StorageBackend(Protocol):
    def put_bytes(self, key: str, payload: bytes) -> bool: ...
    def get_bytes(self, key: str) -> bytes: ...
    def exists(self, key: str) -> bool: ...
    def delete_bytes(self, key: str) -> bool: ...


def _safe_key(key: str) -> str:
    relative = Path(str(key))
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise StorageError("unsafe storage key")
    normalized = relative.as_posix().lstrip("/")
    if not normalized:
        raise StorageError("unsafe storage key")
    return normalized


@dataclass(frozen=True)
class LocalFilesystemStorage:
    root: Path

    def _path(self, key: str) -> Path:
        root = self.root.resolve()
        path = (root / _safe_key(key)).resolve(strict=False)
        if path != root and root not in path.parents:
            raise StorageError("unsafe storage key")
        return path

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

    def delete_bytes(self, key: str) -> bool:
        path = self._path(key)
        try:
            path.unlink()
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise StorageError("local storage object delete failed") from exc
        return True


@dataclass(frozen=True)
class S3CompatibleStorage:
    bucket: str
    endpoint_url: str = ""
    access_key_id: str = ""
    secret_access_key: str = ""
    region: str = "us-east-1"

    def _client(self) -> Any:
        if not self.bucket.strip():
            raise StorageError("S3 bucket is not configured")
        try:
            import boto3
            from botocore.config import Config
        except ImportError as exc:
            raise StorageError("boto3 is required for S3-compatible storage") from exc
        kwargs: dict[str, Any] = {
            "service_name": "s3",
            "region_name": self.region or "us-east-1",
            "config": Config(s3={"addressing_style": "path"}, retries={"max_attempts": 3, "mode": "standard"}),
        }
        if self.endpoint_url:
            kwargs["endpoint_url"] = self.endpoint_url
        if self.access_key_id:
            kwargs["aws_access_key_id"] = self.access_key_id
        if self.secret_access_key:
            kwargs["aws_secret_access_key"] = self.secret_access_key
        return boto3.client(**kwargs)

    @staticmethod
    def _missing(exc: Exception) -> bool:
        response = getattr(exc, "response", {}) or {}
        error = response.get("Error", {}) if isinstance(response, dict) else {}
        code = str(error.get("Code", ""))
        status_code = (response.get("ResponseMetadata", {}) or {}).get("HTTPStatusCode") if isinstance(response, dict) else None
        return code in {"404", "NoSuchKey", "NotFound"} or status_code == 404

    def put_bytes(self, key: str, payload: bytes) -> bool:
        normalized = _safe_key(key)
        client = self._client()
        try:
            response = client.get_object(Bucket=self.bucket, Key=normalized)
        except Exception as exc:
            if not self._missing(exc):
                raise StorageError("S3 object read failed") from exc
        else:
            existing = response["Body"].read()
            if existing != payload:
                raise StorageError("content-addressed storage collision")
            return False
        try:
            client.put_object(Bucket=self.bucket, Key=normalized, Body=payload)
        except Exception as exc:
            raise StorageError("S3 object write failed") from exc
        return True

    def get_bytes(self, key: str) -> bytes:
        normalized = _safe_key(key)
        try:
            response = self._client().get_object(Bucket=self.bucket, Key=normalized)
            return response["Body"].read()
        except Exception as exc:
            if self._missing(exc):
                raise StorageError("storage object missing") from exc
            raise StorageError("S3 object read failed") from exc

    def exists(self, key: str) -> bool:
        normalized = _safe_key(key)
        try:
            self._client().head_object(Bucket=self.bucket, Key=normalized)
            return True
        except Exception as exc:
            if self._missing(exc):
                return False
            raise StorageError("S3 object metadata check failed") from exc

    def delete_bytes(self, key: str) -> bool:
        normalized = _safe_key(key)
        client = self._client()
        try:
            client.head_object(Bucket=self.bucket, Key=normalized)
        except Exception as exc:
            if self._missing(exc):
                return False
            raise StorageError("S3 object metadata check failed") from exc
        try:
            client.delete_object(Bucket=self.bucket, Key=normalized)
        except Exception as exc:
            raise StorageError("S3 object delete failed") from exc
        return True


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
            access_key_id=getattr(settings, "data_s3_access_key_id", ""),
            secret_access_key=getattr(settings, "data_s3_secret_access_key", ""),
            region=getattr(settings, "data_s3_region", "us-east-1"),
        )
    raise StorageError(f"unsupported storage backend: {backend}")
