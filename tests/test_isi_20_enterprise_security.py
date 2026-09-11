from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.api.dependencies import get_db
from src.core.database import Base
from src.platform import models as platform_models  # noqa: F401
from src.platform.auth.models import AuthSession
from src.platform.auth.service import (
    create_invitation,
    create_password_reset_token,
    create_session,
    provision_user,
    utcnow,
    validate_session,
)
from src.platform.identity.models import Organization
from src.platform.security.models import SecurityEvent


PASSWORD = "Synthetic-enterprise-password-2026"


def _factory():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_password_step_up_is_bound_to_authenticated_session_and_emits_safe_events():
    factory = _factory()

    def override_db():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    try:
        with factory() as db:
            user = provision_user(db, email="step-up@example.invalid", display_name="Step Up", password=PASSWORD, email_verified=True)
            current = create_session(db, user)
            other = create_session(db, user)
            db.commit()
        client = TestClient(app)
        headers = {"Authorization": f"Bearer {current.token}"}
        denied = client.post("/api/v1/auth/assurance/password", headers=headers, json={"password": "wrong-value"})
        assert denied.status_code == 401
        assert PASSWORD not in denied.text and "wrong-value" not in denied.text
        allowed = client.post("/api/v1/auth/assurance/password", headers=headers, json={"password": PASSWORD})
        assert allowed.status_code == 200
        assert allowed.json() == {"status": "refreshed", "method": "password"}
        assert PASSWORD not in allowed.text
        with factory() as db:
            assert db.get(AuthSession, current.session_id).password_verified_at is not None
            assert db.get(AuthSession, other.session_id).password_verified_at is None
            events = db.scalars(select(SecurityEvent).where(SecurityEvent.event_type == "auth.assurance.password")).all()
            assert {event.outcome for event in events} == {"failure", "success"}
            assert PASSWORD not in repr([event.event_metadata for event in events])
    finally:
        app.dependency_overrides.clear()


def test_session_fixation_expiry_idle_and_bearer_contract():
    factory = _factory()
    with factory() as db:
        user = provision_user(db, email="sessions@example.invalid", display_name="Sessions", password=PASSWORD, email_verified=True)
        first = create_session(db, user, password_verified=True)
        second = create_session(db, user, password_verified=True)
        assert first.token != second.token
        assert first.token.startswith("isi_sess_") and second.token.startswith("isi_sess_")
        expired = db.get(AuthSession, first.session_id)
        expired.expires_at = utcnow() - timedelta(seconds=1)
        idle = db.get(AuthSession, second.session_id)
        idle.last_seen_at = utcnow() - timedelta(days=2)
        db.flush()
        assert validate_session(db, first.token) is None
        assert validate_session(db, second.token) is None
    client = TestClient(app)
    assert client.post("/api/v1/auth/assurance/password", json={"password": PASSWORD}).status_code == 401
    assert "set-cookie" not in {key.casefold() for key in client.get("/api/v1/health").headers}


def test_account_security_surface_uses_existing_bearer_client_and_defers_provider_mfa():
    api_source = Path("src/streamlit_app/security_api.py").read_text(encoding="utf-8")
    ui_source = Path("src/streamlit_app/security_workspace.py").read_text(encoding="utf-8")
    app_source = Path("src/streamlit_app/app.py").read_text(encoding="utf-8")
    assert 'token=token' in api_source
    assert "/api/v1/auth/sessions" in api_source
    assert "/api/v1/auth/assurance/password" in api_source
    assert "Produkcioni upis i isporuka drugog faktora ostaju odloženi" in ui_source
    assert "remote_ip" not in ui_source and "user_agent" not in ui_source
    assert "account_security" in app_source


def test_logout_and_own_session_revocations_emit_safe_events():
    factory = _factory()

    def override_db():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    try:
        with factory() as db:
            user = provision_user(db, email="revoke-events@example.invalid", display_name="Revoke Events", password=PASSWORD, email_verified=True)
            current = create_session(db, user)
            other = create_session(db, user)
            third = create_session(db, user)
            db.commit()
        client = TestClient(app)
        headers = {"Authorization": f"Bearer {current.token}"}
        assert client.delete(f"/api/v1/auth/sessions/{other.session_id}", headers=headers).status_code == 204
        response = client.post("/api/v1/auth/sessions/revoke-others", headers=headers)
        assert response.status_code == 200 and response.json()["revoked_count"] == 1
        assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
        with factory() as db:
            events = db.scalars(select(SecurityEvent)).all()
            assert {event.event_type for event in events} >= {
                "auth.session.revoke_self",
                "auth.session.revoke_others",
                "auth.logout",
            }
            serialized = repr([event.event_metadata for event in events])
            assert current.token not in serialized and third.token not in serialized
    finally:
        app.dependency_overrides.clear()


def test_password_reset_and_invitation_acceptance_events_do_not_leak_inputs():
    factory = _factory()

    def override_db():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    try:
        with factory() as db:
            user = provision_user(db, email="reset-events@example.invalid", display_name="Reset Events", password=PASSWORD, email_verified=True)
            reset = create_password_reset_token(db, user.email)
            assert reset is not None
            reset_raw = reset[1].token
            org = Organization(slug="invitation-events", name="Invitation Events")
            db.add(org); db.flush()
            invitation = create_invitation(db, organization_id=org.id, email="invited-events@example.invalid")
            invitation_raw = invitation.token
            db.commit()
        replacement = "Replacement-password-2026"
        invited_password = "Invited-password-2026"
        client = TestClient(app)
        reset_response = client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": reset_raw, "new_password": replacement},
        )
        assert reset_response.status_code == 200
        invitation_response = client.post(
            "/api/v1/auth/invitations/accept",
            json={"token": invitation_raw, "display_name": "Invited Events", "password": invited_password},
        )
        assert invitation_response.status_code == 200
        bodies = reset_response.text + invitation_response.text
        assert reset_raw not in bodies and invitation_raw not in bodies
        assert replacement not in bodies and invited_password not in bodies
        with factory() as db:
            events = db.scalars(select(SecurityEvent)).all()
            assert {event.event_type for event in events} >= {
                "auth.password_reset.confirm",
                "auth.invitation.accept",
            }
            metadata = repr([event.event_metadata for event in events])
            for sensitive in (reset_raw, invitation_raw, replacement, invited_password):
                assert sensitive not in metadata
    finally:
        app.dependency_overrides.clear()
