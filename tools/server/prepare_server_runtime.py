from __future__ import annotations

import argparse
import json
import secrets
import stat
import subprocess
from pathlib import Path


def write_private(path: Path, text: str) -> None:
    path.write_text(text)
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def openssl_config() -> str:
    return """[req]\ndistinguished_name = dn\nprompt = no\nx509_extensions = v3_req\n[dn]\nCN = localhost\n[v3_req]\nsubjectAltName = @alt_names\nbasicConstraints = critical,CA:FALSE\nkeyUsage = critical,digitalSignature,keyEncipherment\nextendedKeyUsage = serverAuth\n[alt_names]\nDNS.1 = localhost\nIP.1 = 127.0.0.1\n"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare private pre-cutover ISI runtime on the target server.")
    parser.add_argument("--root", default="/home/ubuntu/ISI")
    parser.add_argument("--force-new", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    runtime = root / "runtime"
    env_path = runtime / ".env.server"
    credentials_path = runtime / "precutover-credentials.json"
    cert_dir = runtime / "certs"

    runtime.mkdir(parents=True, exist_ok=True)
    cert_dir.mkdir(parents=True, exist_ok=True)
    runtime.chmod(0o700)
    cert_dir.chmod(0o700)

    if env_path.exists() and not args.force_new:
        print(f"Reusing existing private server runtime: {env_path}")
        return 0
    if env_path.exists() and args.force_new:
        raise SystemExit("Refusing to rotate an existing server runtime automatically; rotate secrets with a dedicated procedure")

    pg_password = secrets.token_hex(24)
    s3_access = "isi" + secrets.token_hex(10)
    s3_secret = secrets.token_hex(32)
    pepper = secrets.token_hex(48)
    demo_password = "ISI-SERVER-" + secrets.token_hex(12) + "!Aa7"

    env_lines = [
        "ISI_ENV=production",
        "ISI_DEPLOYMENT_PROFILE=staging",
        "ISI_LOG_LEVEL=INFO",
        "POSTGRES_DB=isi_preproduction",
        "POSTGRES_USER=isi_app",
        f"POSTGRES_PASSWORD={pg_password}",
        f"DATABASE_URL=postgresql+psycopg://isi_app:{pg_password}@postgres:5432/isi_preproduction",
        "REDIS_URL=redis://redis:6379/1",
        "PUBLIC_BASE_URL=https://isi.rs",
        "APP_BASE_URL=https://isi.rs/app",
        "API_BASE_URL=http://api:8000",
        f"SECURITY_IDENTIFIER_PEPPER={pepper}",
        "SECURITY_ALLOWED_HOSTS=isi.rs,www.isi.rs,localhost,127.0.0.1,api,streamlit",
        "SECURITY_TRUST_PROXY_HEADERS=true",
        "PUBLIC_PREVIEW_DRAFTS=false",
        "DATA_STORAGE_BACKEND=s3",
        "DATA_S3_BUCKET=isi-preproduction",
        "DATA_S3_ENDPOINT_URL=http://minio:9000",
        f"DATA_S3_ACCESS_KEY_ID={s3_access}",
        f"DATA_S3_SECRET_ACCESS_KEY={s3_secret}",
        "DATA_S3_REGION=us-east-1",
        "DATA_JOB_BACKEND=rq",
        "AI_JOB_BACKEND=rq",
        "AUTH_DELIVERY_MODE=smtp",
        "SMTP_HOST=mailpit",
        "SMTP_PORT=1025",
        "SMTP_FROM_EMAIL=noreply@isi.rs",
        "SMTP_USERNAME=",
        "SMTP_PASSWORD=",
        "SMTP_USE_TLS=false",
        "SMTP_STARTTLS=false",
        "SMTP_TIMEOUT_SECONDS=10",
        "AI_PROVIDER_DEFAULT=ollama",
        "AI_OLLAMA_BASE_URL=http://host.docker.internal:11434",
        "AI_ALLOW_DEV_STUB=0",
        "COMPOSE_PROJECT_NAME=isi",
        "ISI_PRECUTOVER_HTTPS_PORT=8445",
        f"ISI_SERVER_ENV_FILE={env_path}",
        "ISI_POSTGRES_VOLUME=isi_postgres_data",
        "ISI_REDIS_VOLUME=isi_redis_data",
        "ISI_MINIO_VOLUME=isi_minio_data",
        "ISI_MAILPIT_VOLUME=isi_mailpit_data",
        "ISI_INTERNAL_NETWORK=isi_internal",
        "ISI_INGRESS_NETWORK=isi_ingress",
    ]
    write_private(env_path, "\n".join(env_lines) + "\n")
    write_private(
        credentials_path,
        json.dumps(
            {
                "simpa_email": "isi05-simpa@example.com",
                "ordo_email": "isi05-ordo@example.com",
                "dual_email": "isi05-dual@example.com",
                "password": demo_password,
            },
            indent=2,
        ) + "\n",
    )

    openssl_cfg = runtime / "openssl-precutover.cnf"
    openssl_cfg.write_text(openssl_config())
    key = cert_dir / "precutover.key"
    cert = cert_dir / "precutover.crt"
    subprocess.run(
        [
            "openssl", "req", "-x509", "-nodes", "-newkey", "rsa:2048",
            "-keyout", str(key), "-out", str(cert), "-days", "30",
            "-config", str(openssl_cfg), "-extensions", "v3_req",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    key.chmod(0o600)
    cert.chmod(0o600)
    print(f"Created private pre-cutover runtime: {env_path}")
    print("Secrets and QA credentials were generated on the server and were not printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
