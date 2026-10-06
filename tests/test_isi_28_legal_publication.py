import hashlib
import json

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.core.database import Base
from src.public_content.models import PublicPage, PublicPageTranslation
from tools.publish_isi_legal_notices import SOURCE, publish


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine, tables=[PublicPage.__table__, PublicPageTranslation.__table__])
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_publication_digest_locales_placeholders_and_idempotency(db):
    raw = SOURCE.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert publish(db, raw, digest) == {"pages_created": 2, "pages_unchanged": 0}
    db.commit()
    assert publish(db, raw, digest) == {"pages_created": 0, "pages_unchanged": 2}
    pages = list(db.scalars(select(PublicPage)))
    assert all(p.status == "published" and not p.is_navigation and p.published_at for p in pages)
    translations = list(db.scalars(select(PublicPageTranslation)))
    assert len(translations) == 4
    for row in translations:
        assert row.source_content_sha256 == digest
        assert ("PODATAK U PRIPREMI" if row.locale == "sr-Latn" else "INFORMATION PENDING") in row.body_text
        assert "institutzasocijalnuinkluziju@gmail.com" in row.body_text


def test_wrong_digest_is_rejected_before_writes(db):
    with pytest.raises(ValueError, match="digest mismatch"):
        publish(db, SOURCE.read_bytes(), "0" * 64)
    assert db.scalar(select(PublicPage)) is None


def test_collision_on_second_page_does_not_create_first_page(db):
    page = PublicPage(page_key="other", page_type="standard", status="published")
    db.add(page)
    db.flush()
    db.add(PublicPageTranslation(page_id=page.id, locale="sr-Latn", route_path="/privatnost/"))
    db.commit()
    raw = SOURCE.read_bytes()
    with pytest.raises(ValueError, match="different content"):
        publish(db, raw, hashlib.sha256(raw).hexdigest())
    assert db.scalar(select(PublicPage).where(PublicPage.page_key == "legal.terms")) is None


def test_changed_existing_content_is_preserved(db):
    raw = SOURCE.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    publish(db, raw, digest)
    db.commit()
    row = db.scalar(select(PublicPageTranslation))
    row.body_html = "<p>Owner content</p>"
    db.commit()
    with pytest.raises(ValueError, match="refusing overwrite"):
        publish(db, raw, digest)
    assert row.body_html == "<p>Owner content</p>"


def test_missing_locale_fails_before_writes(db):
    payload = json.loads(SOURCE.read_bytes())
    del payload["pages"][1]["translations"]["en"]
    raw = json.dumps(payload).encode()
    with pytest.raises(ValueError, match="both locales"):
        publish(db, raw, hashlib.sha256(raw).hexdigest())
    assert db.scalar(select(PublicPage)) is None
