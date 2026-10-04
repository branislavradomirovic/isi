"""Deterministic 27C runner; isolated synthetic acceptance only."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from tools.release.evidence import consolidate, source_identity, verify
from tools.qa.analyze_isi27c import check_surface

ROOT = Path(__file__).resolve().parents[2]


def execute_gate(command: list[str], *, root: Path, output: Path, filename: str, env: dict[str, str]) -> int:
    # Machine-readable stdout must never be interleaved with library warnings.
    with (output / filename).open("w") as log, (output / f"{filename}.stderr").open("w") as errors:
        return subprocess.run(command, cwd=root, env=env, stdout=log, stderr=errors, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    args = parser.parse_args()
    check_surface()
    output = args.output.resolve()
    authority = ROOT / "automation/evidence/ISI-27C"
    if not output.is_relative_to(authority) or output == authority:
        raise SystemExit("Output must be a new child of automation/evidence/ISI-27C")
    identity = source_identity(ROOT)
    output.mkdir(parents=True, exist_ok=False)
    (output / "source-start.json").write_text(json.dumps(identity, sort_keys=True) + "\n")
    image_dir = args.image.resolve()
    if not image_dir.is_relative_to(authority) or image_dir == authority:
        raise SystemExit("Image evidence must be a child of the 27C evidence directory")
    for filename in (
        "image-identity.json",
        "image.tar.gz",
        "image-scan.json",
        "image-sbom.cdx.json",
        "runtime-check.json",
    ):
        if not (image_dir / filename).is_file():
            raise SystemExit(f"FAIL: missing image evidence: {filename}; no gates executed")
    env = dict(os.environ)
    # Native acceptance owns disposable PostgreSQL; never inherit a live URL.
    env.pop("DATABASE_URL", None)
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env["PATH"]
    commands = {
        "regression": [sys.executable, "-m", "pytest", "-q", f"--junitxml={output / 'pytest.xml'}"],
        "native": ["bash", "tools/ci/native_postgres_tests.sh"],
        "performance": [sys.executable, "-m", "tools.performance.run_isi26"],
        "policy": [sys.executable, "-m", "tools.ci.policy_check"],
        "diff": ["git", "diff", "--check"],
        "quality": [
            "bash",
            "-c",
            "python -m pip check && python -m ruff check tools/release tools/qa/run_isi27c.py tools/qa/analyze_isi27c.py tools/qa/check_runtime_image.py tests/test_isi_27c_release_supply_chain.py tests/test_isi_27c_runtime_image_contract.py && python -m ruff check --select E9 src tests && python -m mypy",
        ],
        "compose": ["bash", "tools/ci/compose_config.sh"],
    }
    gates = {}
    for name, command in commands.items():
        print(f"27C gate: {name}", flush=True)
        filename = "performance.jsonl" if name == "performance" else f"{name}.log"
        code = execute_gate(command, root=ROOT, output=output, filename=filename, env=env)
        gates[name] = code
        (output / "gates.json").write_text(json.dumps(gates, sort_keys=True) + "\n")
        if code:
            raise SystemExit(f"FAIL: {name}; see {output / filename} and its .stderr companion")
        if name == "native":
            shutil.copyfile(
                ROOT / "test-results/native-postgres/pytest-native-postgres.xml", output / "native-postgres.xml"
            )
            shutil.copyfile(
                ROOT / "test-results/native-postgres/isi19-recovery/rehearsal-summary.json", output / "recovery.json"
            )
    from tools.release.build import validate_image_archive, validate_image_inputs
    from tools.release.sbom import sha256_file

    image_identity = json.loads((image_dir / "image-identity.json").read_text())
    if image_identity.get("candidate_sha256") != identity["candidate_sha256"]:
        raise SystemExit("Image was not built from this candidate")
    if sha256_file(image_dir / "image.tar.gz") != image_identity["archive_sha256"]:
        raise SystemExit("Image archive changed")
    validate_image_inputs(
        image_identity,
        json.loads((image_dir / "image-scan.json").read_text()),
        json.loads((image_dir / "image-sbom.cdx.json").read_text()),
        sha=identity["head"],
    )
    validate_image_archive(image_dir / "image.tar.gz", image_identity)
    runtime = json.loads((image_dir / "runtime-check.json").read_text())
    if (
        runtime.get("result") != "PASS"
        or runtime.get("source_sha") != identity["head"]
        or runtime.get("candidate_sha256") != identity["candidate_sha256"]
        or runtime.get("runtime_lock_sha256") != image_identity.get("runtime_base_lock_sha256")
        or runtime.get("image_id") != image_identity.get("engine_image_id")
    ):
        raise SystemExit("Runtime acceptance does not match this exact image/source")
    gates["image"] = 0
    gates["runtime"] = 0
    (output / "all-gates.json").write_text(json.dumps(gates, sort_keys=True) + "\n")
    image_record = {
        "directory": str(image_dir.relative_to(ROOT)),
        "files": {
            name: sha256_file(image_dir / name)
            for name in (
                "image.tar.gz",
                "image-identity.json",
                "image-scan.json",
                "image-sbom.cdx.json",
                "runtime-check.json",
            )
        },
    }
    (output / "image-acceptance.json").write_text(json.dumps(image_record, sort_keys=True) + "\n")
    gates = {name: gates[name] for name in ("regression", "native", "performance", "policy", "diff")}
    (output / "gates.json").write_text(json.dumps(gates, sort_keys=True) + "\n")
    pack = consolidate(ROOT, output, identity, gates)
    (output / "pack.json").write_text(json.dumps(pack, indent=2, sort_keys=True) + "\n")
    for product, acceptance in pack["methodology"].items():
        (output / f"{product}-methodology.json").write_text(
            json.dumps({"source": identity, "acceptance": acceptance}, sort_keys=True) + "\n"
        )
    (output / "model-evaluation-provenance.json").write_text(
        json.dumps(
            {
                "source": identity,
                "evaluations": pack["evaluation_provenance"],
                "model_authority": pack["model_authority"],
            },
            sort_keys=True,
        )
        + "\n"
    )
    print(json.dumps(verify(ROOT, output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
