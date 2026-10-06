from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    isi_env: str = "development"
    isi_deployment_profile: str = "development"
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
    data_s3_access_key_id: str = ""
    data_s3_secret_access_key: str = ""
    data_s3_region: str = "us-east-1"
    ai_job_backend: str = "inline"
    ai_provider_default: str = "ollama"
    ai_ollama_base_url: str = "http://127.0.0.1:11434"
    ai_ollama_chat_model: str = "qwen2.5:7b-instruct"
    ai_ollama_embedding_model: str = "nomic-embed-text"
    ai_ollama_num_thread: int | None = Field(default=None, ge=1, le=64)
    ai_request_timeout_seconds: int = 120
    ai_default_policy: str = "shared-local-only"
    ai_allow_dev_stub: bool = False
    ai_store_request_text: bool = True
    observability_http_metrics_enabled: bool = False
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

    auth_session_idle_ttl_seconds: int = 3600
    security_login_window_seconds: int = 900
    security_login_max_failures: int = 5
    security_login_block_seconds: int = 900
    security_identifier_pepper: str = ""
    security_allowed_hosts: str = "localhost,127.0.0.1,testserver"
    security_trust_proxy_headers: bool = False
    auth_delivery_mode: str = "null"
    smtp_host: str = ""
    smtp_port: int = 25
    smtp_from_email: str = ""
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = False
    smtp_starttls: bool = False
    smtp_timeout_seconds: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
