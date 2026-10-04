"""Read-only independent exact-surface and evidence analysis."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from tools.release.evidence import verify

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "16a928b20907d570df2cf05101a969e1f0cda736"
ALLOWED = {
    "docker/runtime-base.lock.json",
    "tools/qa/check_runtime_image.py",
    "tests/test_isi_27c_runtime_image_contract.py",
    "automation/specs/ISI-27C-R2-MINIMAL-RUNTIME-BASE-PROPOSAL.md",
    "requirements.lock",
    "requirements.runtime.lock",
    "automation/STATUS.md",
    "automation/specs/ISI-PUBLIC-PORTAL-AUDIT-REMEDIATION-R1.md",
    "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md",
    "tools/qa/run_isi27c.py",
    "tests/test_isi_17_harness_contract.py",
    "automation/specs/ISI-27B-R1-RC-EVIDENCE-GOVERNANCE-PACK.md",
    ".gitignore",
    "tools/release/build.py",
    "tools/qa/analyze_isi27c.py",
    "docs/release/ISI-RELEASE-SUPPLY-CHAIN.md",
    "tests/test_isi_26_governance_contract.py",
    "docs/ops/ISI-DEVELOPMENT-WORKSTATION-REQUIREMENTS.md",
    "tests/test_isi_27a_shared_help_contract.py",
    "tests/test_isi_27_scope_contract.py",
    "tools/release/sbom.py",
    "docker/Dockerfile",
    "tests/fixtures/isi27_signature_message.json",
    "tools/release/assemble.py",
    "tools/release/build_server_release.sh",
    "TECHNICAL_DOCUMENTATION.md",
    "tools/release/provenance.py",
    ".dockerignore",
    "tests/fixtures/isi27_signature_message.json.sig",
    "tests/test_isi_27c_release_supply_chain.py",
    ".github/workflows/ci.yml",
    "tools/release/governance.py",
    "automation/specs/ISI-27C-R1-REPRODUCIBLE-RELEASE-SUPPLY-CHAIN.md",
    "automation/tasks.json",
    "tools/release/allowed_signers",
    "automation/specs/ISI-27B-ACCEPTANCE-EVIDENCE.json",
}


def check_surface() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if head != BASELINE:
        raise SystemExit("FAIL: locked baseline changed")
    status = subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT, text=True)
    for line in status.splitlines():
        if line[:2] not in {" M", "??"} or line[3:] not in ALLOWED:
            raise SystemExit(f"FAIL: scope/index violation: {line}")
        if line.startswith("??") and any(
            row.endswith((b" ", b"\t")) for row in (ROOT / line[3:]).read_bytes().splitlines()
        ):
            raise SystemExit(f"FAIL: whitespace: {line[3:]}")
    if subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=False).returncode:
        raise SystemExit("FAIL: changed-line whitespace")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    check_surface()
    result = verify(ROOT, args.output)
    pack = json.loads((args.output / "pack.json").read_text())
    if json.loads((args.output / "source-start.json").read_text()) != pack["source"]:
        raise SystemExit("FAIL: acceptance start identity mismatch")
    gates = json.loads((args.output / "all-gates.json").read_text())
    if set(gates) != {
        "regression",
        "native",
        "performance",
        "policy",
        "diff",
        "quality",
        "compose",
        "image",
        "runtime",
    } or any(gates.values()):
        raise SystemExit("FAIL: incomplete 27C gates")
    image = json.loads((args.output / "image-acceptance.json").read_text())
    from tools.release.build import validate_image_inputs, validate_image_archive
    from tools.release.sbom import sha256_file

    image_dir = ROOT / image["directory"]
    identity = json.loads((image_dir / "image-identity.json").read_text())
    if identity.get("candidate_sha256") != result["candidate_sha256"]:
        raise SystemExit("FAIL: candidate image source changed")
    for name, digest in image["files"].items():
        if sha256_file(image_dir / name) != digest:
            raise SystemExit("FAIL: candidate image artifact changed")
    validate_image_inputs(
        identity,
        json.loads((image_dir / "image-scan.json").read_text()),
        json.loads((image_dir / "image-sbom.cdx.json").read_text()),
        sha=BASELINE,
    )
    validate_image_archive(image_dir / "image.tar.gz", identity)
    runtime = json.loads((image_dir / "runtime-check.json").read_text())
    if (
        runtime.get("result") != "PASS"
        or runtime.get("source_sha") != BASELINE
        or runtime.get("candidate_sha256") != result["candidate_sha256"]
        or runtime.get("runtime_lock_sha256") != identity.get("runtime_base_lock_sha256")
        or runtime.get("image_id") != identity.get("engine_image_id")
    ):
        raise SystemExit("FAIL: image runtime acceptance mismatch")
    print(
        json.dumps(
            {
                **result,
                "image": "PASS",
                "runtime": "PASS",
                "all_gates": "PASS",
                "SERVER_VERIFIED": False,
                "CI_VERIFIED": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
