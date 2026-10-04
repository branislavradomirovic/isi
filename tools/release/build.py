"""Portable clean-main source archive and exact-image release bundle."""

from __future__ import annotations

import argparse
import gzip
import json
import re
import shutil
import subprocess
import tarfile
import hashlib
from pathlib import Path

from tools.release.evidence import source_identity
from tools.release.sbom import lock_sbom, sha256_file, validate_sbom

ROOT = Path(__file__).resolve().parents[2]


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def clean_source(root: Path) -> dict:
    identity = source_identity(root)
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=root).strip():
        raise ValueError("release_requires_clean_committed_main")
    return identity


def archive_commit(root: Path, output: Path, sha: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("invalid_source_sha")
    with output.open("xb") as destination:
        process = subprocess.Popen(
            ["git", "archive", "--format=tar", f"--prefix={sha}/", sha], cwd=root, stdout=subprocess.PIPE
        )
        try:
            with gzip.GzipFile(filename="", mode="wb", mtime=0, fileobj=destination) as compressed:
                shutil.copyfileobj(process.stdout, compressed)
        finally:
            if process.stdout is not None:
                process.stdout.close()
        if process.wait():
            raise ValueError("git_archive_failed")


def build_source(root: Path, output: Path) -> dict:
    identity = clean_source(root)
    output.mkdir(parents=True, exist_ok=False)
    name = f"ISI-server-{identity['head'][:12]}.tar.gz"
    archive_commit(root, output / name, identity["head"])
    sbom = lock_sbom(root, identity["head"])
    validate_sbom(sbom)
    write_json(output / "lock-sbom.cdx.json", sbom)
    manifest = {
        "schema": "ISI-SOURCE-ARTIFACT-v1",
        "source_sha": identity["head"],
        "source_tree": identity["tree"],
        "candidate_sha256": identity["candidate_sha256"],
        "archive": name,
        "files": {name: sha256_file(output / name), "lock-sbom.cdx.json": sha256_file(output / "lock-sbom.cdx.json")},
        "release_qualified": False,
    }
    write_json(output / "source-manifest.json", manifest)
    return manifest


def validate_image_inputs(identity: dict, report: dict, sbom: dict, *, sha: str) -> None:
    validate_sbom(sbom)
    if identity.get("source_sha") != sha or not re.fullmatch(r"sha256:[0-9a-f]{64}", identity.get("image_id", "")):
        raise ValueError("image_source_identity_mismatch")
    if identity.get("os") != "linux" or identity.get("architecture") not in {"amd64", "arm64"}:
        raise ValueError("unsupported_image_platform")
    properties = sbom.get("metadata", {}).get("component", {}).get("properties", [])
    image_ids = [item.get("value") for item in properties if item.get("name") == "aquasecurity:trivy:ImageID"]
    if image_ids != [identity["image_id"]]:
        raise ValueError("sbom_image_identity_mismatch")
    base_lock = [
        item.get("value")
        for item in properties
        if item.get("name") == "aquasecurity:trivy:Labels:org.isi.runtime-base.lock.sha256"
    ]
    if base_lock != [identity.get("runtime_base_lock_sha256")]:
        raise ValueError("sbom_runtime_base_lock_mismatch")
    scanners = sbom.get("metadata", {}).get("tools", {}).get("components", [])
    if not any(tool.get("name") == "trivy" and tool.get("version") == "0.75.0" for tool in scanners):
        raise ValueError("sbom_scanner_version_mismatch")
    if report.get("Metadata", {}).get("ImageID") != identity["image_id"]:
        raise ValueError("scan_image_identity_mismatch")
    if not report.get("Results") or not report.get("Metadata", {}).get("OS"):
        raise ValueError("incomplete_image_scan")
    for result in report["Results"]:
        for vulnerability in (result.get("Vulnerabilities") or []) + (result.get("IgnoredVulnerabilities") or []):
            if vulnerability.get("Severity") in {"HIGH", "CRITICAL"}:
                raise ValueError("blocking_image_vulnerability")


def image_archive_identity(path: Path) -> dict:
    # Read bounded Docker save metadata; never extract paths from an untrusted tar.
    with tarfile.open(path, "r:gz") as archive:

        def read(name: str) -> bytes:
            member = archive.getmember(name)
            if not member.isfile() or member.size > 1024 * 1024:
                raise ValueError("invalid_image_metadata")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("missing_image_metadata")
            return stream.read()

        metadata = json.loads(read("manifest.json"))
        if len(metadata) != 1:
            raise ValueError("single_release_image_required")
        config_bytes = read(metadata[0]["Config"])
        config = json.loads(config_bytes)
        labels = config.get("config", {}).get("Labels", {})
        if labels.get("org.opencontainers.image.source") != "https://github.com/branislavradomirovic/isi":
            raise ValueError("image_oci_source_mismatch")
        return {
            "image_id": "sha256:" + hashlib.sha256(config_bytes).hexdigest(),
            "os": config.get("os"),
            "architecture": config.get("architecture"),
            "source_sha": labels.get("org.opencontainers.image.revision"),
            "candidate_sha256": labels.get("org.isi.candidate.sha256"),
            "runtime_base_lock_sha256": labels.get("org.isi.runtime-base.lock.sha256"),
        }


def validate_image_archive(path: Path, identity: dict) -> None:
    actual = image_archive_identity(path)
    if actual["image_id"] != identity["image_id"]:
        raise ValueError("image_config_digest_mismatch")
    if actual["os"] != identity["os"] or actual["architecture"] != identity["architecture"]:
        raise ValueError("image_archive_platform_mismatch")
    if identity.get("candidate_sha256") is not None and actual["candidate_sha256"] != identity["candidate_sha256"]:
        raise ValueError("image_candidate_digest_mismatch")
    if actual["source_sha"] != identity["source_sha"]:
        raise ValueError("image_oci_source_mismatch")
    if actual["runtime_base_lock_sha256"] != identity.get("runtime_base_lock_sha256"):
        raise ValueError("image_runtime_lock_mismatch")


def build_bundle(root: Path, output: Path, pack_dir: Path, image_dir: Path) -> dict:
    from tools.release.evidence import REPORTS, verify
    from tools.release.provenance import create_provenance, write_checksums

    source = clean_source(root)
    verify(root, pack_dir)
    pack = json.loads((pack_dir / "pack.json").read_text())
    if pack["source"] != source:
        raise ValueError("rc_pack_source_mismatch")
    image_identity = json.loads((image_dir / "image-identity.json").read_text())
    image_report = json.loads((image_dir / "image-scan.json").read_text())
    image_sbom = json.loads((image_dir / "image-sbom.cdx.json").read_text())
    if image_identity.get("candidate_sha256") != source["candidate_sha256"]:
        raise ValueError("image_candidate_source_mismatch")
    validate_image_inputs(image_identity, image_report, image_sbom, sha=source["head"])
    if sha256_file(image_dir / "image.tar.gz") != image_identity.get("archive_sha256"):
        raise ValueError("image_archive_digest_mismatch")
    validate_image_archive(image_dir / "image.tar.gz", image_identity)
    source_manifest = build_source(root, output)
    files = dict(source_manifest["files"])
    files["source-manifest.json"] = sha256_file(output / "source-manifest.json")
    for filename in (
        "image-identity.json",
        "image-scan.json",
        "image-sbom.cdx.json",
        "image.tar.gz",
        "runtime-check.json",
    ):
        shutil.copyfile(image_dir / filename, output / filename)
        files[filename] = sha256_file(output / filename)
    shutil.copyfile(pack_dir / "pack.json", output / "rc-pack.json")
    files["rc-pack.json"] = sha256_file(output / "rc-pack.json")
    for filename in (
        *REPORTS.values(),
        "gates.json",
        "SIMPA-methodology.json",
        "ORDO-methodology.json",
        "model-evaluation-provenance.json",
        "upstream-jobs.json",
    ):
        shutil.copyfile(pack_dir / filename, output / filename)
        files[filename] = sha256_file(output / filename)
    manifest = {
        "schema": "ISI-RC-BUNDLE-v1",
        "source_sha": source["head"],
        "source_tree": source["tree"],
        "candidate_sha256": source["candidate_sha256"],
        "archive": source_manifest["archive"],
        "image": image_identity,
        "files": files,
        "provenance": "provenance.json",
        "signature": "provenance.json.sig",
        "checksums": "SHA256SUMS",
        "signing_namespace": "isi-release",
    }
    write_json(output / "manifest.json", manifest)
    create_provenance(output)
    write_checksums(output)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pack", type=Path)
    parser.add_argument("--image", type=Path)
    args = parser.parse_args()
    if bool(args.pack) != bool(args.image):
        raise SystemExit("Both RC pack and exact image evidence are required for a release bundle")
    result = build_bundle(ROOT, args.output, args.pack, args.image) if args.pack else build_source(ROOT, args.output)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
