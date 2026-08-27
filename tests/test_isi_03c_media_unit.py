from __future__ import annotations

import hashlib
import json
from pathlib import Path

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.database import Base
from src.public_content.models import PublicMediaAsset
from src.public_migration.media_redirect_validation import download_media_assets


def test_media_download_is_content_addressed_and_deduplicated(tmp_path):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    body = b"same-binary-payload"
    sha = hashlib.sha256(body).hexdigest()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body, headers={"content-type": "application/pdf"}, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)
    storage = tmp_path / "media"
    manifest = tmp_path / "manifest.json"
    with SessionLocal() as db:
        db.add_all(
            [
                PublicMediaAsset(source_url="https://isi.rs/wp-content/a.pdf", legacy_path="/wp-content/a.pdf"),
                PublicMediaAsset(source_url="https://isi.rs/wp-content/b.pdf", legacy_path="/wp-content/b.pdf"),
            ]
        )
        db.commit()
        result = download_media_assets(db, storage_root=storage, manifest_path=manifest, client=client)
        db.commit()
        rows = db.query(PublicMediaAsset).order_by(PublicMediaAsset.source_url).all()

    client.close()
    assert result["assets_total"] == 2
    assert result["unique_blob_count"] == 1
    assert result["duplicate_asset_count"] == 1
    assert rows[0].content_sha256 == rows[1].content_sha256 == sha
    assert rows[0].storage_path == rows[1].storage_path
    assert (storage / rows[0].storage_path).read_bytes() == body
    assert json.loads(manifest.read_text())["source_policy"] == "read_only_get_same_site"
