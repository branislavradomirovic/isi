from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.api import auth_routes
from src.platform.auth import delivery
from src.platform.deployment.runtime import DeploymentConfigurationError, validate_deployment_runtime_settings


def settings(**overrides):
    values = dict(
        isi_deployment_profile="production", isi_env="production",
        data_storage_backend="s3", data_s3_bucket="isi-production",
        data_s3_endpoint_url="http://minio:9000", data_s3_access_key_id="test-access-key",
        data_s3_secret_access_key="test-secret-value-long-enough", data_job_backend="rq",
        ai_job_backend="rq", redis_url="redis://redis:6379/0", auth_delivery_mode="pending",
        smtp_host="", smtp_from_email="", smtp_username="", smtp_password="",
        security_trust_proxy_headers=True, public_base_url="https://isi.example",
        app_base_url="https://isi.example/app/", database_url="postgresql://db/isi_production",
        ai_ollama_base_url="http://host.docker.internal:11434", public_preview_drafts=False,
        ai_allow_dev_stub=False,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def test_explicit_production_pending_accepts_empty_email_configuration():
    validate_deployment_runtime_settings(settings())


@pytest.mark.parametrize("field", ["smtp_host", "smtp_from_email", "smtp_username", "smtp_password"])
def test_pending_rejects_residual_smtp_configuration(field):
    with pytest.raises(DeploymentConfigurationError):
        validate_deployment_runtime_settings(settings(**{field: "not-empty"}))


@pytest.mark.parametrize("mode", ["null", "none", "development", "unexpected"])
def test_production_does_not_accept_silent_delivery_modes(mode):
    with pytest.raises(DeploymentConfigurationError):
        validate_deployment_runtime_settings(settings(auth_delivery_mode=mode))


def test_staging_pending_is_not_an_implicit_exception():
    with pytest.raises(DeploymentConfigurationError):
        validate_deployment_runtime_settings(settings(isi_deployment_profile="staging"))


def test_pending_never_constructs_smtp_or_null_delivery(monkeypatch):
    monkeypatch.setattr(delivery, "get_settings", settings)
    assert not delivery.auth_delivery_configured()
    with pytest.raises(delivery.AuthDeliveryError, match="temporarily unavailable"):
        delivery.get_auth_delivery()


def test_request_dependency_returns_account_independent_unavailable_before_tokens(monkeypatch):
    monkeypatch.setattr(auth_routes, "get_settings", settings)
    monkeypatch.setattr(auth_routes, "get_auth_delivery", lambda: pytest.fail("delivery must not be constructed"))
    with pytest.raises(HTTPException) as exc:
        auth_routes._require_email_available()
    assert exc.value.status_code == 503
    assert "temporarily unavailable" in exc.value.detail


@pytest.mark.parametrize("path", ["/email-verification/request", "/password-reset/request"])
@pytest.mark.parametrize("email", ["known@example.com", "unknown@example.com"])
def test_pending_http_requests_never_open_db_or_issue_tokens(monkeypatch, path, email):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from src.api.dependencies import get_db

    monkeypatch.setattr(auth_routes, "get_settings", settings)
    application = FastAPI()
    application.include_router(auth_routes.router)
    application.dependency_overrides[get_db] = lambda: pytest.fail("pending request must not open database")
    with TestClient(application) as client:
        response = client.post("/api/v1/auth" + path, json={"email": email})
    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication email delivery is temporarily unavailable"}
