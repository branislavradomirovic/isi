"""Portable release and negative controls; no additional checkout or private key."""

from __future__ import annotations

import copy
import gzip
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from tools.release import build, provenance, sbom
from tools.release.assemble import REQUIRED, assemble_pack
from tools.release.governance import PHASES, validate_release_state

ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 40


def locks(root):
    (root / "requirements.lock").write_text("Example_Package==1.2.3\n# comment\n")
    (root / "requirements.runtime.lock").write_text("example-package==1.2.3\nother==2.0\n")
    (root / "docker").mkdir()
    (root / "docker/runtime-base.lock.json").write_text("{}\n")


def test_lock_sbom_deterministic_and_explicit_scope(tmp_path):
    locks(tmp_path)
    first = sbom.lock_sbom(tmp_path, SHA)
    assert first == sbom.lock_sbom(tmp_path, SHA)
    sbom.validate_sbom(first)
    assert len(first["components"]) == 2
    assert len(first["components"][0]["properties"]) == 2
    assert "installed image SBOM supplied separately" in first["metadata"]["properties"][0]["value"]
    assert first != sbom.lock_sbom(tmp_path, "b" * 40)


@pytest.mark.parametrize(
    "content", ["", "thing>=1.0", "thing==1\nthing==1", "-r other.txt", 'thing==1; python_version>"3"']
)
def test_invalid_locks_fail_closed(tmp_path, content):
    locks(tmp_path)
    (tmp_path / "requirements.lock").write_text(content)
    with pytest.raises(ValueError):
        sbom.lock_sbom(tmp_path, SHA)


def test_archive_exact_commit_repeat_and_exclusive_output(tmp_path):
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    first, second = tmp_path / "one.tar.gz", tmp_path / "two.tar.gz"
    build.archive_commit(ROOT, first, sha)
    build.archive_commit(ROOT, second, sha)
    assert sbom.sha256_file(first) == sbom.sha256_file(second)
    with tarfile.open(first) as archive:
        names = archive.getnames()
        assert all(name == sha or name.startswith(sha + "/") for name in names)
        assert not any("/.git/" in name or name.endswith("/.env") for name in names)
    with pytest.raises(FileExistsError):
        build.archive_commit(ROOT, first, sha)
    with pytest.raises(ValueError):
        build.archive_commit(ROOT, tmp_path / "bad", "../HEAD")


def test_clean_source_refuses_dirty_tree_and_propagates_branch_guard():
    with (
        patch.object(build, "source_identity", return_value={"head": SHA}),
        patch.object(build.subprocess, "check_output", return_value=b" M file"),
    ):
        with pytest.raises(ValueError, match="clean_committed_main"):
            build.clean_source(ROOT)
    with patch.object(build, "source_identity", side_effect=ValueError("canonical_main_required")):
        with pytest.raises(ValueError, match="canonical_main_required"):
            build.clean_source(ROOT)


def image_inputs():
    identity = dict(source_sha=SHA, image_id="sha256:" + "c" * 64, os="linux", architecture="amd64",
                    runtime_base_lock_sha256="e" * 64)
    report = dict(
        Metadata=dict(ImageID=identity["image_id"], OS=dict(Family="debian", Name="13")),
        Results=[dict(Target="debian", Vulnerabilities=[])],
    )
    bom = dict(bomFormat="CycloneDX", specVersion="1.6", components=[dict(name="python", version="3.11")])
    bom["metadata"] = {
        "component": {"properties": [
            {"name": "aquasecurity:trivy:ImageID", "value": identity["image_id"]},
            {"name": "aquasecurity:trivy:Labels:org.isi.runtime-base.lock.sha256", "value": identity["runtime_base_lock_sha256"]},
        ]},
        "tools": {"components": [{"name": "trivy", "version": "0.75.0"}]},
    }
    return identity, report, bom


@pytest.mark.parametrize(
    "mutation", [
        "sha",
        "id",
        "platform",
        "scan-id",
        "empty-results",
        "empty-sbom",
        "high",
        "critical",
        "ignored-high",
        "sbom-id",
        "scanner-version",
    ]
)
def test_image_scan_negative_controls(mutation):
    identity, report, bom = image_inputs()
    if mutation == "sha":
        identity["source_sha"] = "b" * 40
    if mutation == "id":
        identity["image_id"] = "not-a-digest"
    if mutation == "platform":
        identity["os"] = "windows"
    if mutation == "scan-id":
        report["Metadata"]["ImageID"] = "different"
    if mutation == "empty-results":
        report["Results"] = []
    if mutation == "empty-sbom":
        bom["components"] = []
    if mutation in {"high", "critical", "ignored-high"}:
        key = "IgnoredVulnerabilities" if mutation == "ignored-high" else "Vulnerabilities"
        report["Results"][0][key] = [{"Severity": "CRITICAL" if mutation == "critical" else "HIGH"}]
    if mutation == "sbom-id":
        bom["metadata"]["component"]["properties"][0]["value"] = "different"
    if mutation == "scanner-version":
        bom["metadata"]["tools"]["components"][0]["version"] = "unapproved"
    with pytest.raises(ValueError):
        build.validate_image_inputs(identity, report, bom, sha=SHA)


def test_scan_valid_inputs():
    build.validate_image_inputs(*image_inputs(), sha=SHA)


def image_archive(path, revision=SHA):
    config = dict(
        os="linux",
        architecture="amd64",
        config=dict(
            Labels={"org.opencontainers.image.source": sbom.REPOSITORY, "org.opencontainers.image.revision": revision}
        ),
    )
    raw = json.dumps(config).encode()
    digest = hashlib.sha256(raw).hexdigest()
    entries = {"manifest.json": json.dumps([{"Config": digest + ".json"}]).encode(), digest + ".json": raw}
    with gzip.open(path, "wb") as compressed, tarfile.open(fileobj=compressed, mode="w") as archive:
        for name, content in entries.items():
            member = tarfile.TarInfo(name)
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
    return dict(source_sha=SHA, image_id="sha256:" + digest, os="linux", architecture="amd64")


def test_archive_binds_real_config_and_oci_source(tmp_path):
    path = tmp_path / "image.tar.gz"
    identity = image_archive(path)
    build.validate_image_archive(path, identity)
    identity["image_id"] = "sha256:" + "e" * 64
    with pytest.raises(ValueError, match="config_digest"):
        build.validate_image_archive(path, identity)
    identity = image_archive(path, revision="b" * 40)
    with pytest.raises(ValueError, match="oci_source"):
        build.validate_image_archive(path, identity)


def unsigned_bundle(root):
    (root / "payload.tar.gz").write_bytes(b"fixed public payload")
    (root / "source-manifest.json").write_text("{}\n")
    manifest = dict(
        schema="ISI-RC-BUNDLE-v1",
        source_sha=SHA,
        source_tree="b" * 40,
        candidate_sha256="d" * 64,
        image={"image_id": "sha256:" + "c" * 64},
        files={name: sbom.sha256_file(root / name) for name in ["payload.tar.gz", "source-manifest.json"]},
    )
    build.write_json(root / "manifest.json", manifest)
    provenance.create_provenance(root)
    provenance.write_checksums(root)
    return manifest


def test_unsigned_bundle_is_not_signed_acceptance(tmp_path):
    unsigned_bundle(tmp_path)
    assert provenance.verify_bundle(tmp_path, signed=False)["signed"] is False
    with pytest.raises(ValueError):
        provenance.verify_bundle(tmp_path)


@pytest.mark.parametrize(
    "mutation", ["payload", "source-manifest", "extra", "checksums", "path", "symlink", "provenance"]
)
def test_bundle_tampering_rejected(tmp_path, mutation):
    manifest = unsigned_bundle(tmp_path)
    if mutation == "payload":
        (tmp_path / "payload.tar.gz").write_bytes(b"changed")
    if mutation == "source-manifest":
        (tmp_path / "source-manifest.json").write_text("changed")
    if mutation == "extra":
        (tmp_path / "unexpected").write_text("extra")
    if mutation == "checksums":
        (tmp_path / "SHA256SUMS").write_text("invalid\n")
    if mutation == "path":
        manifest["files"]["../outside"] = "e" * 64
        build.write_json(tmp_path / "manifest.json", manifest)
    if mutation == "symlink":
        (tmp_path / "payload.tar.gz").unlink()
        (tmp_path / "payload.tar.gz").symlink_to(ROOT / "README.md")
    if mutation == "provenance":
        statement = json.loads((tmp_path / "provenance.json").read_text())
        statement["predicate"]["source_sha"] = "e" * 40
        build.write_json(tmp_path / "provenance.json", statement)
        provenance.write_checksums(tmp_path)
    with pytest.raises(ValueError):
        provenance.verify_bundle(tmp_path, signed=False)


def test_real_public_signature_fixture_and_tampering(tmp_path):
    message = ROOT / "tests/fixtures/isi27_signature_message.json"
    signature = message.with_suffix(".json.sig")
    provenance.verify_signature(message, signature)
    changed = tmp_path / "changed.json"
    changed.write_text(message.read_text() + "tampered")
    with pytest.raises(ValueError, match="invalid_signature"):
        provenance.verify_signature(changed, signature)
    assert "PRIVATE KEY" not in signature.read_text()


@pytest.mark.parametrize("result", ["failure", "skipped", "cancelled", None])
def test_assembly_refuses_non_success_upstream(tmp_path, result):
    needs = {key: {"result": "success"} for key in REQUIRED}
    needs["build"]["result"] = result
    with pytest.raises(ValueError, match="upstream"):
        assemble_pack(ROOT, tmp_path, needs)


def test_serial_guard_survives_optimized_python():
    tasks = {task["id"]: task for task in json.loads((ROOT / "automation/tasks.json").read_text())["tasks"]}
    assert validate_release_state(tasks) in PHASES or tasks[PHASES[-1]]["status"] == "done"
    forged = copy.deepcopy(tasks)
    forged[PHASES[0]].pop("accepted_main_sha", None)
    with pytest.raises(AssertionError):
        validate_release_state(forged)
    command = "import json; from tools.release.governance import validate_release_state; validate_release_state(json.loads(input()))"
    result = subprocess.run(
        [str(ROOT / ".venv/bin/python"), "-O", "-c", command],
        input=json.dumps(forged),
        text=True,
        capture_output=True,
        cwd=ROOT,
    )
    assert result.returncode != 0 and "AssertionError" in result.stderr


def test_manual_workflow_keeps_all_blocking_gates_and_pinned_scanner():
    document = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    trigger = document.get("on", document.get(True))
    assert set(trigger) == {"workflow_dispatch"}
    jobs = document["jobs"]
    assert set(jobs["acceptance"]["needs"]) == REQUIRED | {"release-bundle"}
    assert set(jobs["release-bundle"]["needs"]) == REQUIRED
    scanners = [step for step in jobs["build"]["steps"] if "aquasecurity/trivy-action@" in step.get("uses", "")]
    assert len(scanners) == 2
    assert all(
        step["uses"].endswith("ed142fd0673e97e23eac54620cfb913e5ce36c25") and step["with"]["version"] == "v0.75.0"
        for step in scanners
    )
    assert scanners[0]["with"]["exit-code"] == "1" and scanners[0]["with"]["ignore-unfixed"] is False
    assert scanners[0]["with"]["severity"] == "HIGH,CRITICAL"
    assert all(not step.get("continue-on-error") for step in jobs["build"]["steps"])


def test_signing_refuses_structural_fixture_without_real_release_materials(tmp_path):
    unsigned_bundle(tmp_path)
    with pytest.raises(ValueError, match="missing_or_symlink_artifact"):
        provenance.sign_bundle(tmp_path, Path("unused-public-key"))
