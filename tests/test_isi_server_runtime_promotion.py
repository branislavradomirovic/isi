from types import SimpleNamespace

import pytest

from src.platform.deployment.runtime import DeploymentConfigurationError, validate_deployment_runtime_settings


def settings(**overrides):
    values = dict(
        isi_deployment_profile="production",
        isi_env="production",
        data_storage_backend="s3",
        data_s3_bucket="isi-production",
        data_s3_endpoint_url="http://minio:9000",
        data_s3_access_key_id="isiaccess12345",
        data_s3_secret_access_key="0123456789abcdef0123456789abcdef",
        data_job_backend="rq",
        ai_job_backend="rq",
        redis_url="redis://redis:6379/0",
        auth_delivery_mode="smtp",
        smtp_host="smtp.example.net",
        smtp_from_email="noreply@isi.rs",
        security_trust_proxy_headers=True,
        public_base_url="https://isi.rs",
        app_base_url="https://isi.rs/app",
        public_preview_drafts=False,
        database_url="postgresql+psycopg://isi_app:secret@postgres:5432/isi",
        ai_allow_dev_stub=False,
        ai_ollama_base_url="http://host.docker.internal:11434",
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def test_production_target_settings_pass():
    validate_deployment_runtime_settings(settings())


@pytest.mark.parametrize(
    "overrides",
    [
        {"smtp_host": "mailpit"},
        {"data_s3_bucket": "isi-preproduction"},
        {"database_url": "postgresql+psycopg://isi_app:secret@postgres:5432/isi_preproduction"},
        {"public_base_url": "https://localhost"},
        {"app_base_url": "https://127.0.0.1/app"},
        {"public_preview_drafts": True},
        {"ai_allow_dev_stub": True},
        {"ai_ollama_base_url": ""},
    ],
)
def test_production_promotion_rejects_preproduction_or_dev_runtime(overrides):
    with pytest.raises(DeploymentConfigurationError):
        validate_deployment_runtime_settings(settings(**overrides))
