from types import SimpleNamespace

import pytest

from src.platform.deployment.runtime import DeploymentConfigurationError, validate_deployment_runtime_settings


def valid_settings(**overrides):
    values = dict(
        isi_deployment_profile="staging",
        isi_env="production",
        data_storage_backend="s3",
        data_s3_bucket="isi15-staging",
        data_s3_endpoint_url="http://minio:9000",
        data_s3_access_key_id="isi15access123",
        data_s3_secret_access_key="0123456789abcdef0123456789abcdef",
        data_job_backend="rq",
        ai_job_backend="rq",
        redis_url="redis://redis:6379/0",
        auth_delivery_mode="smtp",
        smtp_host="mailpit",
        smtp_from_email="staging@isi.example",
        security_trust_proxy_headers=True,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def test_development_profile_is_backward_compatible():
    validate_deployment_runtime_settings(SimpleNamespace(isi_deployment_profile="development"))


def test_staging_profile_accepts_production_shaped_settings():
    validate_deployment_runtime_settings(valid_settings())


@pytest.mark.parametrize(
    "field,value",
    [
        ("isi_env", "development"),
        ("data_storage_backend", "local"),
        ("data_job_backend", "inline"),
        ("ai_job_backend", "inline"),
        ("auth_delivery_mode", "null"),
        ("security_trust_proxy_headers", False),
    ],
)
def test_staging_profile_fails_closed(field, value):
    with pytest.raises(DeploymentConfigurationError):
        validate_deployment_runtime_settings(valid_settings(**{field: value}))
