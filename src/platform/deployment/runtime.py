from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit


class DeploymentConfigurationError(RuntimeError):
    pass


def _text(settings: Any, name: str, default: str = "") -> str:
    return str(getattr(settings, name, default) or "").strip()


def _bool(settings: Any, name: str, default: bool = False) -> bool:
    value = getattr(settings, name, default)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _require_non_placeholder(errors: list[str], label: str, value: str, *, minimum: int = 1) -> None:
    lowered = value.casefold()
    placeholders = {"change-me", "changeme", "password", "secret", "example", "placeholder"}
    if len(value) < minimum or lowered in placeholders or "change_me" in lowered:
        errors.append(f"{label} must be explicitly configured")


def validate_deployment_runtime_settings(settings: Any) -> None:
    profile = _text(settings, "isi_deployment_profile", "development").casefold()
    if profile not in {"staging", "production"}:
        return

    errors: list[str] = []
    if _text(settings, "isi_env").casefold() != "production":
        errors.append("ISI_ENV must be production for staging/production deployment profiles")

    if _text(settings, "data_storage_backend").casefold() != "s3":
        errors.append("DATA_STORAGE_BACKEND must be s3")
    _require_non_placeholder(errors, "DATA_S3_BUCKET", _text(settings, "data_s3_bucket"), minimum=3)
    endpoint = _text(settings, "data_s3_endpoint_url")
    if not endpoint or urlsplit(endpoint).scheme not in {"http", "https"}:
        errors.append("DATA_S3_ENDPOINT_URL must be an explicit http(s) URL")
    _require_non_placeholder(errors, "DATA_S3_ACCESS_KEY_ID", _text(settings, "data_s3_access_key_id"), minimum=8)
    _require_non_placeholder(errors, "DATA_S3_SECRET_ACCESS_KEY", _text(settings, "data_s3_secret_access_key"), minimum=16)

    if _text(settings, "data_job_backend").casefold() != "rq":
        errors.append("DATA_JOB_BACKEND must be rq")
    if _text(settings, "ai_job_backend").casefold() != "rq":
        errors.append("AI_JOB_BACKEND must be rq")
    redis_url = _text(settings, "redis_url")
    if not redis_url.startswith(("redis://", "rediss://")):
        errors.append("REDIS_URL must be explicitly configured")

    delivery_mode = _text(settings, "auth_delivery_mode").casefold()
    if delivery_mode == "pending" and profile == "production":
        if any(_text(settings, key) for key in ("smtp_host", "smtp_from_email", "smtp_username", "smtp_password")):
            errors.append("pending auth delivery requires empty SMTP host, sender and credentials")
    else:
        if delivery_mode != "smtp":
            errors.append("AUTH_DELIVERY_MODE must be smtp, or explicit pending in production")
        _require_non_placeholder(errors, "SMTP_HOST", _text(settings, "smtp_host"), minimum=2)
        sender = _text(settings, "smtp_from_email")
        if "@" not in sender:
            errors.append("SMTP_FROM_EMAIL must be explicitly configured")

    if not _bool(settings, "security_trust_proxy_headers"):
        errors.append("SECURITY_TRUST_PROXY_HEADERS must be true behind the staging reverse proxy")

    if profile == "production":
        public_url = urlsplit(_text(settings, "public_base_url"))
        app_url = urlsplit(_text(settings, "app_base_url"))
        for label, parsed in (("PUBLIC_BASE_URL", public_url), ("APP_BASE_URL", app_url)):
            if parsed.scheme != "https" or not parsed.hostname or parsed.hostname in {"localhost", "127.0.0.1"}:
                errors.append(f"{label} must be a non-local HTTPS URL in production")

        smtp_host = _text(settings, "smtp_host").casefold()
        if delivery_mode == "smtp" and smtp_host in {"mailpit", "localhost", "127.0.0.1"}:
            errors.append("production deployment must not use Mailpit/local SMTP")

        bucket = _text(settings, "data_s3_bucket").casefold()
        if "staging" in bucket or "preproduction" in bucket:
            errors.append("production DATA_S3_BUCKET must not use staging/preproduction storage")

        database_url = _text(settings, "database_url").casefold()
        if "preproduction" in database_url or "staging" in database_url:
            errors.append("production DATABASE_URL must not use staging/preproduction database")

        if _bool(settings, "public_preview_drafts"):
            errors.append("PUBLIC_PREVIEW_DRAFTS must be false in production")
        if _bool(settings, "ai_allow_dev_stub"):
            errors.append("AI_ALLOW_DEV_STUB must be false in production")
        ai_url = urlsplit(_text(settings, "ai_ollama_base_url"))
        if ai_url.scheme not in {"http", "https"} or not ai_url.hostname:
            errors.append("AI_OLLAMA_BASE_URL must be explicitly configured in production")

    if errors:
        raise DeploymentConfigurationError("; ".join(errors))
