"""The pinned minimal image must preserve actual ISI runtime contracts."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.qa import check_runtime_image
from tools.release.sbom import sha256_file

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "docker/runtime-base.lock.json").read_text())


def test_runtime_base_supplier_and_package_inputs_are_immutable():
    assert LOCK["index_digest"].startswith("sha256:") and len(LOCK["index_digest"]) == 71
    assert LOCK["image"] == "cgr.dev/chainguard/wolfi-base"
    assert LOCK["repository"] == "https://apk.cgr.dev/chainguard"
    assert LOCK["architectures"] == ["amd64"]
    assert LOCK["packages"] == {"python-3.11": "3.11.17-r1", "py3.11-pip": "26.2.1-r2"}
    assert LOCK["runtime_packages"] == {
        "ca-certificates-bundle": "20260909-r2",
        "tzdata": "2026e-r0",
    }
    assert LOCK["python"] == "3.11"
    assert "Trivy CycloneDX SBOM" in LOCK["runtime_scope"]


def test_dockerfile_uses_pinned_multistage_wolfi_and_removes_build_tools():
    dockerfile = (ROOT / "docker/Dockerfile").read_text()
    assert f"sha256:{LOCK['index_digest'].split(':', 1)[1]}" in dockerfile
    for package, version in {**LOCK["packages"], **LOCK["runtime_packages"]}.items():
        assert f"{package}={version}" in dockerfile
    assert "FROM python-base AS builder" in dockerfile
    assert "FROM python-base AS runtime" in dockerfile
    assert "pip uninstall -y pip setuptools wheel" in dockerfile
    assert "COPY --from=builder /opt/isi-venv /opt/isi-venv" in dockerfile
    assert "FROM python:3.11-slim" not in dockerfile
    assert "cgr.dev/chainguard/wolfi-base:latest" not in dockerfile


def test_runtime_probe_binds_oci_revision_candidate_and_lock(tmp_path):
    source = "a" * 40
    candidate = "b" * 64
    lock_hash = sha256_file(ROOT / "docker/runtime-base.lock.json")
    inspect = {
        "Os": "linux",
        "Architecture": "amd64",
        "Id": "sha256:" + "c" * 64,
        "Config": {
            "Labels": {
                "org.opencontainers.image.revision": source,
                "org.isi.candidate.sha256": candidate,
                "org.isi.runtime-base.lock.sha256": lock_hash,
                "org.opencontainers.image.source": "https://github.com/branislavradomirovic/isi",
            }
        },
    }

    def fake_run(command, **kwargs):
        if command[:3] == ["docker", "image", "inspect"]:
            return json.dumps([inspect])
        if command[:2] == ["docker", "run"] and "--name" in command:
            return "container-id"
        if command[:2] == ["docker", "port"]:
            return "127.0.0.1:49152"
        if command[:2] == ["docker", "run"]:
            return "python=3.11;openssl=test"
        raise AssertionError(command)

    def fake_wait(url, expected, **kwargs):
        status = 401 if url.endswith("/api/v1/auth/me") else 200
        assert status in expected
        return {"status": status, "body_sha256": "d" * 64}

    with (
        patch.object(check_runtime_image, "run", side_effect=fake_run),
        patch.object(check_runtime_image, "wait_http", side_effect=fake_wait),
        patch.object(check_runtime_image.subprocess, "run"),
    ):
        result = check_runtime_image.verify_smoke("isi:test", source, candidate, lock_hash)
    assert result["result"] == "PASS"
    assert result["unauthenticated_account"]["status"] == 401
    assert result["api_health"]["status"] == 200
    assert result["streamlit_health"]["status"] == 200
    assert result["production_data_used"] is False


@pytest.mark.parametrize(
    "key,value",
    [
        ("org.opencontainers.image.revision", "f" * 40),
        ("org.isi.candidate.sha256", "f" * 64),
        ("org.isi.runtime-base.lock.sha256", "f" * 64),
        ("org.opencontainers.image.source", "https://example.invalid"),
    ],
)
def test_runtime_probe_rejects_source_or_lock_mismatch(key, value):
    inspect = {
        "Os": "linux",
        "Architecture": "amd64",
        "Config": {
            "Labels": {
                "org.opencontainers.image.revision": "a" * 40,
                "org.isi.candidate.sha256": "b" * 64,
                "org.isi.runtime-base.lock.sha256": sha256_file(ROOT / "docker/runtime-base.lock.json"),
                "org.opencontainers.image.source": "https://github.com/branislavradomirovic/isi",
            }
        },
    }
    inspect["Config"]["Labels"][key] = value
    with patch.object(check_runtime_image, "run", return_value=json.dumps([inspect])):
        with pytest.raises(ValueError, match="runtime_image_source_or_lock_mismatch"):
            check_runtime_image.verify_smoke(
                "isi:test", "a" * 40, "b" * 64, sha256_file(ROOT / "docker/runtime-base.lock.json")
            )


def test_runtime_contract_remains_in_approved_system_map():
    master = (ROOT / "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    technical = (ROOT / "TECHNICAL_DOCUMENTATION.md").read_text()
    assert "INV-J32" in master and "docker/runtime-base.lock.json" in master
    assert "ISI-27C R2" in technical
