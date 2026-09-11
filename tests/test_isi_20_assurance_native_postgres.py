from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import inspect

from src.core.database import build_engine, build_session_factory
from src.platform.auth.models import AuthSession
from src.platform.auth.service import create_session, provision_user, refresh_password_assurance, utcnow


pytestmark = pytest.mark.skipif(
    os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1",
    reason="native PostgreSQL acceptance only",
)


def test_native_postgres_assurance_columns_persist_and_refresh():
    engine = build_engine()
    session_columns = {column["name"] for column in inspect(engine).get_columns("core_auth_sessions")}
    assert {"password_verified_at", "mfa_verified_at"} <= session_columns

    factory = build_session_factory(engine)
    password = "Synthetic-native-assurance-password-2026"
    with factory() as db:
        user = provision_user(
            db,
            email=f"isi20b-{uuid.uuid4().hex}@example.invalid",
            display_name="ISI-20B Native PostgreSQL",
            password=password,
            email_verified=True,
        )
        issued = create_session(db, user, password_verified=True)
        default_issued = create_session(db, user)
        user_id = user.id
        session_id = issued.session_id
        default_session_id = default_issued.session_id
        db.commit()

    checked_at = utcnow()
    with factory() as db:
        model = db.get(AuthSession, session_id)
        assert model is not None
        assert model.password_verified_at is not None
        default_model = db.get(AuthSession, default_session_id)
        assert default_model is not None
        assert default_model.password_verified_at is None
        model.password_verified_at = None
        model.mfa_verified_at = checked_at
        db.commit()

    with factory() as db:
        refreshed = refresh_password_assurance(
            db,
            user_id=user_id,
            session_id=session_id,
            password=password,
            now=checked_at,
        )
        assert refreshed.password_verified_at == checked_at
        db.commit()

    with factory() as db:
        from src.platform.identity.models import User

        persisted = db.get(AuthSession, session_id)
        assert persisted is not None
        assert persisted.password_verified_at == checked_at
        assert persisted.mfa_verified_at == checked_at
        default_persisted = db.get(AuthSession, default_session_id)
        assert default_persisted is not None
        assert default_persisted.password_verified_at is None
        user = db.get(User, user_id)
        assert user is not None
        db.delete(user)
        db.commit()
