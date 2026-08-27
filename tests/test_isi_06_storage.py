from pathlib import Path

from src.platform.data.storage import LocalFilesystemStorage, digest_bytes, scoped_storage_key


def test_local_storage_is_content_addressed_and_idempotent(tmp_path: Path):
    storage = LocalFilesystemStorage(tmp_path)
    payload = b"same payload"
    digest = digest_bytes(payload)
    key = scoped_storage_key(
        organization_id="org-a",
        product_code="SIMPA",
        workspace_id="ws-1",
        sha256=digest,
        extension="csv",
    )
    assert storage.put_bytes(key, payload) is True
    assert storage.put_bytes(key, payload) is False
    assert storage.get_bytes(key) == payload
    assert key.startswith("org-a/SIMPA/ws-1/")
