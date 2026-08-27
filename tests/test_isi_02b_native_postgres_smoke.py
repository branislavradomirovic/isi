import os
import uuid

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from src.core.database import build_engine
from src.platform.auth.service import create_session, provision_user, validate_session
from src.platform.identity.models import User


@pytest.mark.skipif(os.getenv("ISI_RUN_NATIVE_DB_TESTS") != "1", reason="native PostgreSQL smoke is runner-gated")
def test_native_postgres_auth_transaction_smoke():
    engine = build_engine()
    inspector = inspect(engine)
    for table in ("core_auth_sessions", "core_auth_tokens", "core_invitations"):
        assert inspector.has_table(table)

    connection = engine.connect()
    transaction = connection.begin()
    try:
        with Session(bind=connection) as db:
            email = f"isi02b-{uuid.uuid4().hex}@example.invalid"
            user = provision_user(
                db,
                email=email,
                display_name="ISI-02B DB Smoke",
                password="Native-Postgres-password-2026",
                email_verified=True,
            )
            issued = create_session(db, user)
            db.flush()
            assert validate_session(db, issued.token) is not None
            assert db.scalar(select(User).where(User.email == email)) is not None
    finally:
        transaction.rollback()
        connection.close()
