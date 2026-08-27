from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    isi_env: str = "development"
    isi_log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://isi_app:change-me@localhost:5432/isi"
    redis_url: str = "redis://localhost:6379/0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    streamlit_port: int = 8501
    public_base_url: str = "http://localhost:8000"
    app_base_url: str = "http://localhost:8501"
    auth_session_ttl_seconds: int = 43200
    auth_email_verification_ttl_seconds: int = 86400
    auth_password_reset_ttl_seconds: int = 1800
    auth_invitation_ttl_seconds: int = 604800


@lru_cache
def get_settings() -> Settings:
    return Settings()
