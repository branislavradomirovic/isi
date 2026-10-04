"""Owner SSH signatures over artifact-bound in-toto statements; no private keys."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from tools.release.sbom import sha256_file

TRUST = Path(__file__).with_name("allowed_signers")
PRINCIPAL = "branislavradomirovic"
NAMESPACE = "isi-release"


def safe_file(directory: Path, name: str) -> Path:
    if not isinstance(name, str) or Path(name).name != name or name in {"", ".", ".."}:
        raise ValueError("unsafe_artifact_path")
    path = directory / name
    if path.is_symlink() or not path.is_file():
        raise ValueError("missing_or_symlink_artifact")
    return path


def create_provenance(directory: Path) -> dict:
    manifest = json.loads(safe_file(directory, "manifest.json").read_text())
    statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": "manifest.json", "digest": {"sha256": sha256_file(directory / "manifest.json")}}],
        "predicateType": "https://github.com/branislavradomirovic/isi/provenance/v1",
        "predicate": {
            "source_sha": manifest["source_sha"],
            "source_tree": manifest["source_tree"],
            "candidate_sha256": manifest["candidate_sha256"],
            "image_id": manifest["image"]["image_id"],
            "runtime_base_lock_sha256": manifest["image"].get("runtime_base_lock_sha256"),
            "assurance": "owner-reviewed ISI evidence; no SLSA certification claim",
        },
    }
    (directory / "provenance.json").write_text(json.dumps(statement, indent=2, sort_keys=True) + "\n")
    return statement


def write_checksums(directory: Path) -> None:
    paths = sorted(path for path in directory.iterdir() if path.name != "SHA256SUMS")
    for path in paths:
        safe_file(directory, path.name)
    (directory / "SHA256SUMS").write_text("".join(f"{sha256_file(path)}  {path.name}\n" for path in paths))


def verify_bundle(directory: Path, *, signed: bool = True) -> dict:
    manifest = json.loads(safe_file(directory, "manifest.json").read_text())
    if manifest.get("schema") != "ISI-RC-BUNDLE-v1" or not manifest.get("files"):
        raise ValueError("invalid_bundle_manifest")
    for field, length in (("source_sha", 40), ("source_tree", 40), ("candidate_sha256", 64)):
        if not re.fullmatch(r"[0-9a-f]{" + str(length) + "}", manifest.get(field, "")):
            raise ValueError("invalid_source_identity")
    for name, digest in manifest["files"].items():
        if sha256_file(safe_file(directory, name)) != digest:
            raise ValueError("artifact_digest_mismatch")
    expected = set(manifest["files"]) | {"manifest.json", "source-manifest.json", "provenance.json"}
    if signed:
        expected.add("provenance.json.sig")
    records = {}
    for line in safe_file(directory, "SHA256SUMS").read_text().splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match or match[2] in records:
            raise ValueError("invalid_checksums")
        records[match[2]] = match[1]
        if sha256_file(safe_file(directory, match[2])) != match[1]:
            raise ValueError("checksum_mismatch")
    if set(records) != expected or {p.name for p in directory.iterdir()} != expected | {"SHA256SUMS"}:
        raise ValueError("unexpected_or_missing_artifact")
    provenance_path = safe_file(directory, "provenance.json")
    statement = json.loads(provenance_path.read_text())
    subject = [{"name": "manifest.json", "digest": {"sha256": sha256_file(directory / "manifest.json")}}]
    predicate = statement.get("predicate", {})
    if statement.get("_type") != "https://in-toto.io/Statement/v1" or statement.get("subject") != subject:
        raise ValueError("provenance_subject_mismatch")
    if statement.get("predicateType") != "https://github.com/branislavradomirovic/isi/provenance/v1":
        raise ValueError("provenance_type_mismatch")
    if (
        any(predicate.get(key) != manifest[key] for key in ("source_sha", "source_tree", "candidate_sha256"))
        or predicate.get("image_id") != manifest["image"]["image_id"]
    ):
        raise ValueError("provenance_source_mismatch")
    if predicate.get("runtime_base_lock_sha256") != manifest["image"].get("runtime_base_lock_sha256"):
        raise ValueError("provenance_runtime_lock_mismatch")
    if signed:
        verify_signature(provenance_path, safe_file(directory, "provenance.json.sig"))
        validate_materials(directory)
    return {
        "source_sha": manifest["source_sha"],
        "manifest_sha256": sha256_file(directory / "manifest.json"),
        "signed": signed,
    }


def verify_signature(message: Path, signature: Path) -> None:
    with message.open("rb") as stream:
        result = subprocess.run(
            ["ssh-keygen", "-Y", "verify", "-f", str(TRUST), "-I", PRINCIPAL, "-n", NAMESPACE, "-s", str(signature)],
            stdin=stream,
            capture_output=True,
            check=False,
        )
    if result.returncode:
        raise ValueError("untrusted_or_invalid_signature")


def sign_bundle(directory: Path, public_key: Path) -> dict:
    verify_bundle(directory, signed=False)
    validate_materials(directory)
    message = directory / "provenance.json"
    subprocess.run(["ssh-keygen", "-Y", "sign", "-f", str(public_key), "-n", NAMESPACE, str(message)], check=True)
    verify_signature(message, directory / "provenance.json.sig")
    write_checksums(directory)
    return verify_bundle(directory)


def validate_materials(directory: Path) -> None:
    """Sign only a real source/image/acceptance bundle, never a source-only archive."""
    from tools.release.assemble import REQUIRED
    from tools.release.build import validate_image_archive, validate_image_inputs
    from tools.release.evidence import REPORTS, junit
    from tools.release.sbom import validate_sbom

    def read(name: str) -> dict:
        return json.loads(safe_file(directory, name).read_text())

    manifest = read("manifest.json")
    pack = read("rc-pack.json")
    if pack.get("schema") != "ISI-27B-RC-PACK-v1":
        raise ValueError("invalid_rc_pack")
    source = pack.get("source", {})
    if any(
        source.get(key) != manifest[field]
        for key, field in (("head", "source_sha"), ("tree", "source_tree"), ("candidate_sha256", "candidate_sha256"))
    ):
        raise ValueError("pack_source_mismatch")
    jobs = read("upstream-jobs.json")
    if set(jobs) != REQUIRED or any(job.get("result") != "success" for job in jobs.values()):
        raise ValueError("upstream_acceptance_not_successful")
    gates = read("gates.json")
    if (
        gates != pack.get("gates")
        or set(gates) != {"regression", "native", "performance", "policy", "diff"}
        or any(value != 0 for value in gates.values())
    ):
        raise ValueError("acceptance_gate_mismatch")
    for key, name in REPORTS.items():
        if pack.get("reports", {}).get(key) != {"path": name, "sha256": sha256_file(safe_file(directory, name))}:
            raise ValueError("acceptance_report_mismatch")
    if junit(directory / "pytest.xml") != pack.get("regression") or junit(
        directory / "native-postgres.xml", native=True
    ) != pack.get("native_postgres"):
        raise ValueError("acceptance_test_mismatch")
    recovery = read("recovery.json")
    if any(recovery.get(key) != "success" for key in ("status", "postgresql17_restore", "object_storage_restore")):
        raise ValueError("recovery_not_successful")
    validate_sbom(read("lock-sbom.cdx.json"))
    image = read("image-identity.json")
    if image != manifest["image"] or image.get("candidate_sha256") != manifest["candidate_sha256"]:
        raise ValueError("image_candidate_mismatch")
    validate_image_inputs(image, read("image-scan.json"), read("image-sbom.cdx.json"), sha=manifest["source_sha"])
    archive = safe_file(directory, "image.tar.gz")
    if sha256_file(archive) != image.get("archive_sha256"):
        raise ValueError("image_archive_mismatch")
    validate_image_archive(archive, image)
    runtime = read("runtime-check.json")
    if (
        runtime.get("result") != "PASS"
        or runtime.get("source_sha") != manifest["source_sha"]
        or runtime.get("candidate_sha256") != manifest["candidate_sha256"]
        or runtime.get("runtime_lock_sha256") != image.get("runtime_base_lock_sha256")
        or runtime.get("image_id") != image.get("engine_image_id")
    ):
        raise ValueError("runtime_compatibility_mismatch")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--sign-public-key", type=Path)
    args = parser.parse_args()
    result = (
        sign_bundle(args.directory, args.sign_public_key) if args.sign_public_key else verify_bundle(args.directory)
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
