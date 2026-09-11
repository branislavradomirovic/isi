from __future__ import annotations

import ast
import uuid
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.api.dependencies import get_db
from src.core.database import Base
from src.platform import models as platform_models  # noqa: F401
from src.platform.auth.models import AuthSession
from src.platform.auth.service import (
    OTHER_SESSIONS_REVOCATION_REASON,
    SELF_REVOCATION_REASON,
    create_session,
    derive_device_label,
    list_user_sessions,
    provision_user,
    revoke_other_user_sessions,
    revoke_user_session,
    utcnow,
    validate_session,
)
from src.platform.identity.models import User


TEST_PASSWORD = "Synthetic-session-management-password-2026"
SAFE_INVENTORY_FIELDS = {
    "session_id",
    "created_at",
    "last_seen_at",
    "expires_at",
    "is_current",
    "is_revoked",
    "revoked_at",
    "revocation_reason",
    "device_label",
}


@pytest.fixture()
def session_factory():
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _user(db: Session, label: str):
    return provision_user(
        db,
        email=f"{label}-{uuid.uuid4().hex}@example.invalid",
        display_name=f"{label.title()} User",
        password=TEST_PASSWORD,
        email_verified=True,
    )


def test_device_label_is_bounded_and_create_session_keeps_raw_client_data_private(session_factory):
    labels = {
        derive_device_label(None),
        derive_device_label("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"),
        derive_device_label("Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X)"),
        derive_device_label("Mozilla/5.0 (Windows NT 10.0; Win64; x64)"),
        derive_device_label("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0)"),
        derive_device_label("Mozilla/5.0 (X11; Linux x86_64)"),
        derive_device_label("curl/8.7.1"),
        derive_device_label("SyntheticSecretBrowser/12345 203.0.113.55"),
    }
    assert labels <= {
        "Unknown device",
        "Mobile device",
        "Tablet device",
        "Windows computer",
        "Mac computer",
        "Linux computer",
        "Automated client",
    }
    assert all(len(label) <= 80 for label in labels)
    assert all("SyntheticSecretBrowser" not in label and "203.0.113.55" not in label for label in labels)

    with session_factory() as db:
        user = _user(db, "device")
        issued = create_session(
            db,
            user,
            remote_ip="203.0.113.55",
            user_agent="SyntheticSecretBrowser/12345 203.0.113.55",
        )
        stored = db.get(AuthSession, issued.session_id)
        assert stored is not None
        assert stored.device_label == "Unknown device"
        assert stored.remote_ip is None
        assert stored.user_agent is None
        assert stored.remote_ip_hash is not None
        assert stored.user_agent_hash is not None


def test_session_inventory_is_private_safe_current_and_bounded(session_factory):
    with session_factory() as db:
        owner = _user(db, "inventory-owner")
        other = _user(db, "inventory-other")
        start = utcnow() - timedelta(days=1)
        issued = []
        for index in range(105):
            current = create_session(db, owner, user_agent="Mozilla/5.0 (X11; Linux x86_64)")
            model = db.get(AuthSession, current.session_id)
            model.created_at = start + timedelta(minutes=index)
            issued.append(current)
        other_session = create_session(db, other, user_agent="Mozilla/5.0 (Windows NT 10.0)")
        db.flush()

        # The authenticated current session remains visible even when it is older
        # than the otherwise newest 100 records.
        current_session_id = issued[0].session_id
        inventory = list_user_sessions(
            db,
            user_id=owner.id,
            current_session_id=current_session_id,
        )

        assert len(inventory) == 100
        created_timestamps = [item.created_at.replace(tzinfo=None).timestamp() for item in inventory]
        assert created_timestamps == sorted(created_timestamps, reverse=True)
        assert sum(item.is_current for item in inventory) == 1
        assert next(item for item in inventory if item.is_current).session_id == current_session_id
        assert all(item.session_id != other_session.session_id for item in inventory)
        assert all(set(vars(item)) == SAFE_INVENTORY_FIELDS for item in inventory)
        serialized = repr(inventory)
        owner_models = [db.get(AuthSession, item.session_id) for item in inventory]
        assert all(model.token_hash not in serialized for model in owner_models)
        assert all(model.remote_ip_hash not in serialized for model in owner_models if model.remote_ip_hash)
        assert all(model.user_agent_hash not in serialized for model in owner_models if model.user_agent_hash)


def test_revoke_one_own_session_and_cross_user_fails_closed(session_factory):
    with session_factory() as db:
        owner = _user(db, "revoke-owner")
        other = _user(db, "revoke-other")
        own = create_session(db, owner)
        current = create_session(db, owner)
        foreign = create_session(db, other)

        assert revoke_user_session(db, user_id=owner.id, session_id=own.session_id) is True
        assert revoke_user_session(db, user_id=owner.id, session_id=own.session_id) is True
        assert db.get(AuthSession, own.session_id).revoked_reason == SELF_REVOCATION_REASON
        assert validate_session(db, current.token) is not None

        assert revoke_user_session(db, user_id=owner.id, session_id=foreign.session_id) is False
        assert db.get(AuthSession, foreign.session_id).revoked_at is None

        assert revoke_user_session(db, user_id=owner.id, session_id=current.session_id) is True
        assert validate_session(db, current.token) is None


def test_revoke_other_sessions_preserves_current_and_is_idempotent(session_factory):
    with session_factory() as db:
        owner = _user(db, "others-owner")
        other = _user(db, "others-other")
        current = create_session(db, owner)
        first = create_session(db, owner)
        second = create_session(db, owner)
        already_revoked = create_session(db, owner)
        foreign = create_session(db, other)
        revoke_user_session(db, user_id=owner.id, session_id=already_revoked.session_id)

        assert revoke_other_user_sessions(
            db,
            user_id=owner.id,
            current_session_id=current.session_id,
        ) == 2
        assert db.get(AuthSession, current.session_id).revoked_at is None
        assert db.get(AuthSession, first.session_id).revoked_reason == OTHER_SESSIONS_REVOCATION_REASON
        assert db.get(AuthSession, second.session_id).revoked_reason == OTHER_SESSIONS_REVOCATION_REASON
        assert db.get(AuthSession, already_revoked.session_id).revoked_reason == SELF_REVOCATION_REASON
        assert db.get(AuthSession, foreign.session_id).revoked_at is None
        assert revoke_other_user_sessions(
            db,
            user_id=owner.id,
            current_session_id=current.session_id,
        ) == 0
        assert validate_session(db, current.token) is not None


def test_session_routes_use_authenticated_context(session_factory):
    def override_db():
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    try:
        with session_factory() as db:
            owner = _user(db, "route-owner")
            other = _user(db, "route-other")
            current = create_session(db, owner, user_agent="Mozilla/5.0 (Windows NT 10.0)")
            owner_other = create_session(db, owner)
            foreign = create_session(db, other)
            db.commit()
            current_token = current.token
            current_id = current.session_id
            owner_id = owner.id
            owner_other_id = owner_other.session_id
            foreign_id = foreign.session_id

        client = TestClient(app)
        headers = {"Authorization": f"Bearer {current_token}"}
        response = client.get("/api/v1/auth/sessions", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert all(set(item) == SAFE_INVENTORY_FIELDS for item in response.json())
        assert next(item for item in response.json() if item["is_current"])["session_id"] == str(current_id)

        cross_user = client.delete(f"/api/v1/auth/sessions/{foreign_id}", headers=headers)
        assert cross_user.status_code == 404
        revoked = client.delete(f"/api/v1/auth/sessions/{owner_other_id}", headers=headers)
        assert revoked.status_code == 204

        with session_factory() as db:
            replacement = create_session(db, db.get(User, owner_id))
            db.commit()
            replacement_token = replacement.token
            replacement_id = replacement.session_id

        replacement_headers = {"Authorization": f"Bearer {replacement_token}"}
        revoke_others = client.post("/api/v1/auth/sessions/revoke-others", headers=replacement_headers)
        assert revoke_others.status_code == 200
        assert revoke_others.json() == {"revoked_count": 1}
        assert client.get("/api/v1/auth/sessions", headers=replacement_headers).status_code == 200
        with session_factory() as db:
            assert db.get(AuthSession, replacement_id).revoked_at is None
            assert db.get(AuthSession, foreign_id).revoked_at is None
    finally:
        app.dependency_overrides.clear()


def test_session_inventory_migration_is_exact_0016_to_0015():
    migration_path = Path("migrations/versions/20260911_0016_session_inventory.py")
    module = ast.parse(migration_path.read_text(encoding="utf-8"), filename=str(migration_path))
    assignments = {
        node.targets[0].id: node.value.value
        for node in module.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Constant)
    }
    assert assignments["revision"] == "20260911_0016"
    assert assignments["down_revision"] == "20260911_0015"
    source = migration_path.read_text(encoding="utf-8")
    assert source.count("op.add_column(") == 1
    assert source.count("op.drop_column(") == 1
    assert '"device_label"' in source
