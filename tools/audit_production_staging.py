from __future__ import annotations

import json
from pathlib import Path


class AuditError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def text(path: str) -> str:
    file = Path(path)
    require(file.is_file(), f"missing {path}")
    return file.read_text()


def main() -> int:
    tasks = json.loads(text("automation/tasks.json"))["tasks"]
    by_id = {item["id"]: item for item in tasks}
    require(by_id["ISI-14-SECURITY-HARDENING"]["status"] == "done", "ISI-14 must remain done")
    require(by_id["ISI-15-PRODUCTION-STAGING"]["status"] in {"ready", "done"}, "ISI-15 task missing")
    require(by_id["ISI-16-ISI-RS-PRODUCTION-CUTOVER"]["status"] in {"planned", "ready"}, "ISI-16 task missing")

    compose = text("docker-compose.staging.yml")
    for marker in (
        "postgres:", "redis:", "minio:", "mailpit:", "migrate:", "api:", "streamlit:",
        "data-worker:", "ai-worker:", "nginx:", "127.0.0.1:${ISI15_HTTPS_PORT", "isi-data", "isi-ai",
    ):
        if marker in {"isi-data", "isi-ai"}:
            continue
        require(marker in compose, f"staging Compose marker missing: {marker}")
    require('"5432:' not in compose and "- 5432:" not in compose, "PostgreSQL must not publish a host port")
    require('"6379:' not in compose and "- 6379:" not in compose, "Redis must not publish a host port")
    require("minio/minio:RELEASE.2025-09-07T16-13-09Z" in compose, "pinned local MinIO harness image missing")
    require("axllent/mailpit:v1.31.0" in compose, "pinned Mailpit harness image missing")
    require("service_completed_successfully" in compose, "migration/init dependency contract missing")

    nginx = text("docker/nginx/isi15-staging.conf")
    for marker in ("listen 443 ssl", "location /app/", "proxy_set_header Upgrade", "X-Robots-Tag", "Disallow: /"):
        require(marker in nginx, f"nginx staging marker missing: {marker}")

    config = text("src/core/config.py")
    for marker in ("isi_deployment_profile", "data_s3_access_key_id", "data_s3_secret_access_key", "smtp_host", "smtp_from_email"):
        require(marker in config, f"config field missing: {marker}")

    storage = text("src/platform/data/storage.py")
    require("import boto3" in storage, "real S3-compatible adapter missing")
    require("content-addressed storage collision" in storage, "storage collision contract missing")

    delivery = text("src/platform/auth/delivery.py")
    for marker in ("SMTPAuthDelivery", "send_email_verification", "send_password_reset", "send_invitation", "auth_delivery_configured"):
        require(marker in delivery, f"SMTP delivery marker missing: {marker}")

    app = text("src/api/app.py")
    require("validate_deployment_runtime_settings" in app, "deployment runtime startup gate missing")
    require("deployment_router" in app, "deployment readiness router missing")

    pyproject = text("pyproject.toml")
    require("boto3>=1.40,<2" in pyproject, "boto3 dependency missing")

    for path in (
        "tools/staging/prepare_runtime.py",
        "tools/staging/run_isi15_staging_qa.sh",
        "tools/staging/backup_restore_rehearsal.sh",
        "tools/staging/smoke_https.py",
        "tools/staging/probe_legacy_migration_artifacts.py",
        "docs/qa/ISI-15-STAGING-QA-MATRIX.md",
    ):
        require(Path(path).is_file(), f"missing staging operational artifact: {path}")

    env = text(".env.staging.example")
    require("GENERATE_AT_RUNTIME" in env, "staging env template must not contain real secrets")
    banned = ["ISI05-Demo-QA-2026!", "BEGIN PRIVATE KEY"]
    for value in banned:
        require(value not in env, f"secret-like value present in staging template: {value}")

    print("ISI-15 production staging static audit PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AuditError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
