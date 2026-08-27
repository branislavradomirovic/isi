from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.dependencies import get_db
from src.core.database import Base
from src.platform import models as platform_models  # noqa: F401
from src.platform.auth.delivery import get_auth_delivery
from src.platform.auth.service import create_invitation, provision_user
from src.platform.identity.models import Organization


class CaptureDelivery:
    def __init__(self):
        self.verification_token = None
        self.reset_token = None

    def send_email_verification(self, *, email: str, token: str) -> None:
        self.verification_token = token

    def send_password_reset(self, *, email: str, token: str) -> None:
        self.reset_token = token


def make_client():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    delivery = CaptureDelivery()
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_auth_delivery] = lambda: delivery
    return TestClient(app), SessionLocal, delivery


def teardown_client():
    app.dependency_overrides.clear()


def test_login_me_logout_roundtrip():
    client, SessionLocal, _delivery = make_client()
    try:
        with SessionLocal() as db:
            provision_user(
                db,
                email="api@example.com",
                display_name="API User",
                password="API-secure-password-2026",
                email_verified=True,
            )
            db.commit()

        response = client.post("/api/v1/auth/login", json={"email": "api@example.com", "password": "API-secure-password-2026"})
        assert response.status_code == 200
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        me = client.get("/api/v1/auth/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["email"] == "api@example.com"
        assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
        assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
    finally:
        teardown_client()


def test_password_reset_request_does_not_enumerate_accounts_and_reset_works():
    client, SessionLocal, delivery = make_client()
    try:
        with SessionLocal() as db:
            provision_user(
                db,
                email="reset-api@example.com",
                display_name="Reset API",
                password="Old-API-password-2026",
                email_verified=True,
            )
            db.commit()

        known = client.post("/api/v1/auth/password-reset/request", json={"email": "reset-api@example.com"})
        unknown = client.post("/api/v1/auth/password-reset/request", json={"email": "unknown@example.com"})
        assert known.status_code == unknown.status_code == 202
        assert known.json() == unknown.json() == {"status": "accepted"}
        assert delivery.reset_token

        confirm = client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": delivery.reset_token, "new_password": "New-API-password-2026"},
        )
        assert confirm.status_code == 200
        login = client.post("/api/v1/auth/login", json={"email": "reset-api@example.com", "password": "New-API-password-2026"})
        assert login.status_code == 200
    finally:
        teardown_client()



def test_email_verification_request_is_public_and_non_enumerating():
    client, SessionLocal, delivery = make_client()
    try:
        with SessionLocal() as db:
            provision_user(
                db,
                email="verify-api@example.com",
                display_name="Verify API",
                password="Verify-API-password-2026",
                email_verified=False,
            )
            db.commit()

        known = client.post("/api/v1/auth/email-verification/request", json={"email": "verify-api@example.com"})
        unknown = client.post("/api/v1/auth/email-verification/request", json={"email": "nobody@example.com"})
        assert known.status_code == unknown.status_code == 202
        assert known.json() == unknown.json() == {"status": "accepted"}
        assert delivery.verification_token

        confirm = client.post("/api/v1/auth/email-verification/confirm", json={"token": delivery.verification_token})
        assert confirm.status_code == 200
        login = client.post("/api/v1/auth/login", json={"email": "verify-api@example.com", "password": "Verify-API-password-2026"})
        assert login.status_code == 200
    finally:
        teardown_client()

def test_invitation_acceptance_logs_new_user_in():
    client, SessionLocal, _delivery = make_client()
    try:
        with SessionLocal() as db:
            org = Organization(slug="api-org", name="API Org", status="active")
            db.add(org)
            db.flush()
            issued = create_invitation(db, organization_id=org.id, email="invite-api@example.com")
            db.commit()
            token = issued.token

        response = client.post(
            "/api/v1/auth/invitations/accept",
            json={"token": token, "display_name": "Invite API", "password": "Invite-API-password-2026"},
        )
        assert response.status_code == 200
        access_token = response.json()["access_token"]
        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert me.status_code == 200
        assert me.json()["email_verified"] is True
    finally:
        teardown_client()
