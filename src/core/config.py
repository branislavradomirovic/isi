from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    isi_env: str = "development"
    isi_log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://isi_app:change-me@localhost:5432/isi"
    redis_url: str = "redis://localhost:6379/0"
    data_storage_backend: str = "local"
    data_storage_root: str = ".isi-data"
    data_job_backend: str = "inline"
    data_max_upload_bytes: int = 16777216
    data_max_xlsx_uncompressed_bytes: int = 67108864
    data_s3_bucket: str = ""
    data_s3_endpoint_url: str = ""
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    streamlit_port: int = 8501
    public_base_url: str = "http://localhost:8000"
    app_base_url: str = "http://localhost:8501"
    public_preview_drafts: bool = False
    auth_session_ttl_seconds: int = 43200
    auth_email_verification_ttl_seconds: int = 86400
    auth_password_reset_ttl_seconds: int = 1800
    auth_invitation_ttl_seconds: int = 604800


@lru_cache
def get_settings() -> Settings:
    return Settings()
