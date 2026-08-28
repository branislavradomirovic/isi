import pytest

from src.core.config import Settings
from src.platform.security.service import SecurityConfigurationError, validate_production_security_settings


def _settings(**overrides):
    values = dict(
        isi_env="production",
        public_base_url="https://isi.rs",
        app_base_url="https://isi.rs/app",
        security_identifier_pepper="x" * 48,
        security_allowed_hosts="isi.rs,www.isi.rs",
        auth_delivery_mode="smtp",
    )
    values.update(overrides)
    return Settings(**values)


def test_production_security_settings_accept_safe_baseline():
    validate_production_security_settings(_settings())


@pytest.mark.parametrize("overrides", [
    {"security_identifier_pepper": ""},
    {"security_allowed_hosts": "*"},
    {"public_base_url": "http://isi.rs"},
    {"app_base_url": "http://isi.rs/app"},
    {"auth_delivery_mode": "null"},
])
def test_production_security_settings_fail_closed(overrides):
    with pytest.raises(SecurityConfigurationError):
        validate_production_security_settings(_settings(**overrides))
