from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.core.config import Settings
from src.platform.security.models import SecurityRateLimit
from src.platform.security.service import check_login_allowed, clear_login_failures, register_login_failure


def test_login_failure_bucket_blocks_after_threshold_and_clears():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    SecurityRateLimit.__table__.create(engine)
    settings = Settings(
        security_identifier_pepper="test-pepper-abcdefghijklmnopqrstuvwxyz-123456",
        security_login_max_failures=3,
        security_login_window_seconds=900,
        security_login_block_seconds=600,
    )
    now = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)
    with Session(engine) as db:
        assert check_login_allowed(db, email="unknown@example.com", remote_ip="127.0.0.1", now=now, settings=settings).allowed
        register_login_failure(db, email="unknown@example.com", remote_ip="127.0.0.1", now=now, settings=settings)
        register_login_failure(db, email="unknown@example.com", remote_ip="127.0.0.1", now=now, settings=settings)
        blocked = register_login_failure(db, email="unknown@example.com", remote_ip="127.0.0.1", now=now, settings=settings)
        assert not blocked.allowed
        assert not check_login_allowed(db, email="unknown@example.com", remote_ip="127.0.0.1", now=now, settings=settings).allowed
        clear_login_failures(db, email="unknown@example.com", remote_ip="127.0.0.1", settings=settings)
        assert check_login_allowed(db, email="unknown@example.com", remote_ip="127.0.0.1", now=now, settings=settings).allowed
