from __future__ import annotations

import argparse
import json
import os
import secrets
import stat
import subprocess
from pathlib import Path


def _write_private(path: Path, text: str) -> None:
    path.write_text(text)
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def _openssl_config() -> str:
    return """[req]\ndistinguished_name = dn\nprompt = no\nx509_extensions = v3_req\n[dn]\nCN = localhost\n[v3_req]\nsubjectAltName = @alt_names\nbasicConstraints = critical,CA:FALSE\nkeyUsage = critical,digitalSignature,keyEncipherment\nextendedKeyUsage = serverAuth\n[alt_names]\nDNS.1 = localhost\nIP.1 = 127.0.0.1\n"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare isolated ISI-15 staging runtime material outside Git.")
    parser.add_argument("--runtime-dir", default="/tmp/isi15-staging")
    parser.add_argument("--https-port", type=int, default=8443)
    parser.add_argument("--mailpit-port", type=int, default=8025)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    runtime = Path(args.runtime_dir).resolve()
    env_path = runtime / ".env.staging.runtime"
    credentials_path = runtime / "demo-credentials.json"
    cert_dir = runtime / "certs"
    backup_dir = runtime / "backup"

    if env_path.exists() and not args.force:
        raise SystemExit(f"runtime already exists: {env_path}; pass --force only after stopping the ISI-15 QA project")

    runtime.mkdir(parents=True, exist_ok=True)
    runtime.chmod(0o700)
    cert_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)
    cert_dir.chmod(0o700)
    backup_dir.chmod(0o700)

    pg_password = secrets.token_hex(24)
    s3_access = "isi15" + secrets.token_hex(10)
    s3_secret = secrets.token_hex(32)
    pepper = secrets.token_hex(48)
    demo_password = "ISI15-" + secrets.token_hex(12) + "!Aa7"

    base = f"https://localhost:{args.https_port}"
    env_lines = [
        "ISI_ENV=production",
        "ISI_DEPLOYMENT_PROFILE=staging",
        "ISI_LOG_LEVEL=INFO",
        "POSTGRES_DB=isi15_staging",
        "POSTGRES_USER=isi_app",
        f"POSTGRES_PASSWORD={pg_password}",
        f"DATABASE_URL=postgresql+psycopg://isi_app:{pg_password}@postgres:5432/isi15_staging",
        "REDIS_URL=redis://redis:6379/0",
        f"PUBLIC_BASE_URL={base}",
        f"APP_BASE_URL={base}/app",
        "API_BASE_URL=http://api:8000",
        f"SECURITY_IDENTIFIER_PEPPER={pepper}",
        "SECURITY_ALLOWED_HOSTS=localhost,127.0.0.1,api",
        "SECURITY_TRUST_PROXY_HEADERS=true",
        "PUBLIC_PREVIEW_DRAFTS=false",
        "DATA_STORAGE_BACKEND=s3",
        "DATA_S3_BUCKET=isi15-staging",
        "DATA_S3_ENDPOINT_URL=http://minio:9000",
        f"DATA_S3_ACCESS_KEY_ID={s3_access}",
        f"DATA_S3_SECRET_ACCESS_KEY={s3_secret}",
        "DATA_S3_REGION=us-east-1",
        "DATA_JOB_BACKEND=rq",
        "AI_JOB_BACKEND=rq",
        "AUTH_DELIVERY_MODE=smtp",
        "SMTP_HOST=mailpit",
        "SMTP_PORT=1025",
        "SMTP_FROM_EMAIL=staging@isi.example",
        "SMTP_USERNAME=",
        "SMTP_PASSWORD=",
        "SMTP_USE_TLS=false",
        "SMTP_STARTTLS=false",
        "SMTP_TIMEOUT_SECONDS=10",
        "AI_PROVIDER_DEFAULT=ollama",
        "AI_OLLAMA_BASE_URL=http://host.docker.internal:11434",
        "AI_ALLOW_DEV_STUB=0",
        f"ISI15_HTTPS_PORT={args.https_port}",
        f"ISI15_MAILPIT_UI_PORT={args.mailpit_port}",
        f"ISI15_RUNTIME_DIR={runtime}",
        f"ISI15_ENV_FILE={env_path}",
        "ISI15_APP_IMAGE=isi15-staging-app:local",
        "COMPOSE_PROJECT_NAME=isi15stagingqa",
    ]
    _write_private(env_path, "\n".join(env_lines) + "\n")
    _write_private(
        credentials_path,
        json.dumps(
            {
                "simpa_email": "isi05-simpa@example.com",
                "ordo_email": "isi05-ordo@example.com",
                "dual_email": "isi05-dual@example.com",
                "password": demo_password,
            },
            indent=2,
        )
        + "\n",
    )

    openssl_cfg = runtime / "openssl.cnf"
    openssl_cfg.write_text(_openssl_config())
    key = cert_dir / "isi15.key"
    cert = cert_dir / "isi15.crt"
    for path in (key, cert):
        if path.exists():
            path.unlink()
    try:
        subprocess.run(
            [
                "openssl",
                "req",
                "-x509",
                "-nodes",
                "-newkey",
                "rsa:2048",
                "-keyout",
                str(key),
                "-out",
                str(cert),
                "-days",
                "7",
                "-config",
                str(openssl_cfg),
                "-extensions",
                "v3_req",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise SystemExit("openssl is required to create the local ISI-15 TLS certificate") from exc
    key.chmod(0o600)
    cert.chmod(0o600)

    print(f"ISI-15 runtime prepared: {runtime}")
    print(f"Runtime env: {env_path}")
    print(f"Demo credentials: {credentials_path}")
    print("Secrets were generated outside the repository and were not printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
