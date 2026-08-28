from io import BytesIO

import pytest

from src.platform.data.storage import S3CompatibleStorage, StorageError


class Missing(Exception):
    response = {"Error": {"Code": "NoSuchKey"}, "ResponseMetadata": {"HTTPStatusCode": 404}}


class FakeS3:
    def __init__(self):
        self.objects = {}

    def get_object(self, *, Bucket, Key):
        if Key not in self.objects:
            raise Missing()
        return {"Body": BytesIO(self.objects[Key])}

    def head_object(self, *, Bucket, Key):
        if Key not in self.objects:
            raise Missing()
        return {}

    def put_object(self, *, Bucket, Key, Body):
        self.objects[Key] = bytes(Body)
        return {}


def test_s3_adapter_idempotency_and_collision(monkeypatch):
    fake = FakeS3()
    monkeypatch.setattr(S3CompatibleStorage, "_client", lambda self: fake)
    storage = S3CompatibleStorage(bucket="bucket")
    assert storage.put_bytes("org/SIMPA/ws/hash.bin", b"abc") is True
    assert storage.get_bytes("org/SIMPA/ws/hash.bin") == b"abc"
    assert storage.exists("org/SIMPA/ws/hash.bin") is True
    assert storage.put_bytes("org/SIMPA/ws/hash.bin", b"abc") is False
    with pytest.raises(StorageError, match="collision"):
        storage.put_bytes("org/SIMPA/ws/hash.bin", b"xyz")


def test_s3_adapter_rejects_unsafe_key(monkeypatch):
    fake = FakeS3()
    monkeypatch.setattr(S3CompatibleStorage, "_client", lambda self: fake)
    with pytest.raises(StorageError, match="unsafe"):
        S3CompatibleStorage(bucket="bucket").put_bytes("../secret", b"x")
