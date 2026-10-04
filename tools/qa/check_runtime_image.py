"""Exercise an exact image's Python ABI, API, Streamlit and auth boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from tools.release.sbom import sha256_file


def run(command: list[str], *, timeout: int = 90) -> str:
    completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=timeout)
    return completed.stdout


def reserve_container(image: str, name: str, command: list[str], inner_port: int) -> tuple[str, str]:
    run(
        [
            "docker",
            "run",
            "-d",
            "--rm",
            "--name",
            name,
            "--network",
            "bridge",
            "-p",
            f"127.0.0.1::{inner_port}",
            "-e",
            "ISI_ENV=development",
            "-e",
            "SECURITY_ALLOWED_HOSTS=localhost,127.0.0.1,testserver",
            image,
            *command,
        ]
    )
    port = run(["docker", "port", name, f"{inner_port}/tcp"]).strip().rsplit(":", 1)[1]
    return name, f"http://127.0.0.1:{port}"


def wait_http(url: str, expected: set[int], *, timeout: float = 45) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                status, body = response.status, response.read(65536)
        except urllib.error.HTTPError as error:
            status, body = error.code, error.read(65536)
        except (OSError, TimeoutError):
            time.sleep(0.25)
            continue
        if status in expected:
            return {"status": status, "body_sha256": hashlib.sha256(body).hexdigest()}
        if status >= 500:
            time.sleep(0.25)
            continue
        raise ValueError(f"unexpected_http_status:{status}")
    raise TimeoutError(f"runtime_http_timeout:{url.rsplit('/', 1)[-1]}")


def inspect_image(image: str) -> dict:
    data = json.loads(run(["docker", "image", "inspect", image]))
    if len(data) != 1:
        raise ValueError("runtime_image_tag_not_unique")
    config = data[0]
    labels = config.get("Config", {}).get("Labels") or {}
    return {
        "os": config.get("Os"),
        "architecture": config.get("Architecture"),
        "engine_image_id": config.get("Id"),
        "labels": labels,
    }


def verify_smoke(image: str, source_sha: str, candidate_sha: str, lock_digest: str) -> dict:
    details = inspect_image(image)
    labels = details["labels"]
    if details["os"] != "linux" or details["architecture"] != "amd64":
        raise ValueError("unsupported_target_platform")
    expected = {
        "org.opencontainers.image.revision": source_sha,
        "org.isi.candidate.sha256": candidate_sha,
        "org.isi.runtime-base.lock.sha256": lock_digest,
        "org.opencontainers.image.source": "https://github.com/branislavradomirovic/isi",
    }
    if any(labels.get(key) != value for key, value in expected.items()):
        raise ValueError("runtime_image_source_or_lock_mismatch")
    script = (
        "import importlib.metadata as m,locale,ssl,sys,time,zoneinfo;"
        "assert sys.version_info[:2] == (3,11);"
        "assert locale.getpreferredencoding(False);"
        "assert zoneinfo.ZoneInfo('UTC');"
        "assert ssl.OPENSSL_VERSION;"
        "assert all(m.version(n) == v for n,v in [('urllib3','2.8.0')]);"
        "assert not any(d.metadata['Name'].lower() in {'pip','setuptools','wheel'} for d in m.distributions());"
        "import fastapi,streamlit,uvicorn,alembic,psycopg,numpy,scipy,statsmodels.api,pyarrow,rq,boto3;"
        "from scipy.special import expit; assert abs(expit(0)-0.5)<1e-12;"
        "print('python=3.11;openssl='+ssl.OPENSSL_VERSION)"
    )
    runtime = run(["docker", "run", "--rm", "--network", "none", image, "python", "-c", script])
    suffix = hashlib.sha256(f"{os.getpid()}:{time.time_ns()}".encode()).hexdigest()[:12]
    names: list[str] = []
    try:
        api_name, api_url = reserve_container(
            image,
            f"isi-r2-api-{suffix}",
            ["python", "-m", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"],
            8000,
        )
        names.append(api_name)
        api_health = wait_http(f"{api_url}/api/v1/health", {200})
        auth_boundary = wait_http(f"{api_url}/api/v1/auth/me", {401})
        ui_name, ui_url = reserve_container(
            image,
            f"isi-r2-ui-{suffix}",
            [
                "python",
                "-m",
                "streamlit",
                "run",
                "src/streamlit_app/app.py",
                "--server.address",
                "0.0.0.0",
                "--server.port",
                "8501",
                "--server.headless",
                "true",
                "--server.baseUrlPath",
                "app",
            ],
            8501,
        )
        names.append(ui_name)
        ui_health = wait_http(f"{ui_url}/app/_stcore/health", {200}, timeout=90)
    finally:
        for name in reversed(names):
            subprocess.run(["docker", "stop", name], check=False, capture_output=True, timeout=30)
    return {
        "result": "PASS",
        "image_id": details["engine_image_id"],
        "source_sha": source_sha,
        "candidate_sha256": candidate_sha,
        "runtime_lock_sha256": lock_digest,
        "platform": f"{details['os']}/{details['architecture']}",
        "runtime": runtime.strip(),
        "api_health": api_health,
        "unauthenticated_account": auth_boundary,
        "streamlit_health": ui_health,
        "production_data_used": False,
        "server_verified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--lock", type=Path, default=Path("docker/runtime-base.lock.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    identity = verify_smoke(args.image, args.source_sha, args.candidate_sha, sha256_file(args.lock))
    args.output.write_text(json.dumps(identity, indent=2, sort_keys=True) + "\n")
    print(json.dumps(identity, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
