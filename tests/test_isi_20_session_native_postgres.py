from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import inspect

from src.core.database import build_engine, build_session_factory
from src.platform.auth.models import AuthSession
from src.platform.auth.service import (
    create_session,
    list_user_sessions,
    provision_user,
    revoke_other_user_sessions,
)
from src.platform.identity.models import User


pytestmark = pytest.mark.skipif(
    os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1",
    reason="native PostgreSQL acceptance only",
)


def test_native_postgres_session_inventory_and_revocation():
    engine = build_engine()
    session_columns = {column["name"] for column in inspect(engine).get_columns("core_auth_sessions")}
    assert "device_label" in session_columns

    factory = build_session_factory(engine)
    with factory() as db:
        owner = provision_user(
            db,
            email=f"isi20c-owner-{uuid.uuid4().hex}@example.invalid",
            display_name="ISI-20C Native Owner",
            password="Synthetic-native-session-password-2026",
            email_verified=True,
        )
        other = provision_user(
            db,
            email=f"isi20c-other-{uuid.uuid4().hex}@example.invalid",
            display_name="ISI-20C Native Other",
            password="Synthetic-native-session-password-2026",
            email_verified=True,
        )
        current = create_session(db, owner, user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0)")
        owner_other = create_session(db, owner, user_agent="Mozilla/5.0 (X11; Linux x86_64)")
        foreign = create_session(db, other, user_agent="Mozilla/5.0 (Windows NT 10.0)")
        owner_id = owner.id
        other_id = other.id
        current_id = current.session_id
        owner_other_id = owner_other.session_id
        foreign_id = foreign.session_id
        db.commit()

    with factory() as db:
        inventory = list_user_sessions(db, user_id=owner_id, current_session_id=current_id)
        assert {item.session_id for item in inventory} == {current_id, owner_other_id}
        assert next(item for item in inventory if item.is_current).device_label == "Mac computer"
        assert revoke_other_user_sessions(db, user_id=owner_id, current_session_id=current_id) == 1
        db.commit()

    with factory() as db:
        assert db.get(AuthSession, current_id).revoked_at is None
        assert db.get(AuthSession, owner_other_id).revoked_at is not None
        assert db.get(AuthSession, foreign_id).revoked_at is None
        assert revoke_other_user_sessions(db, user_id=owner_id, current_session_id=current_id) == 0
        owner = db.get(User, owner_id)
        other = db.get(User, other_id)
        assert owner is not None
        assert other is not None
        db.delete(owner)
        db.delete(other)
        db.commit()
