"""Deterministic 27B runner; isolated synthetic acceptance only."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from tools.release.evidence import consolidate, source_identity, verify
from tools.qa.analyze_isi27b import check_surface

ROOT = Path(__file__).resolve().parents[2]


def execute_gate(command: list[str], *, root: Path, output: Path, filename: str, env: dict[str, str]) -> int:
    # Machine-readable stdout must never be interleaved with library warnings.
    with (output / filename).open("w") as log, (output / f"{filename}.stderr").open("w") as errors:
        return subprocess.run(command, cwd=root, env=env, stdout=log, stderr=errors, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    check_surface()
    output = args.output.resolve()
    authority = ROOT / "automation/evidence/ISI-27B"
    if not output.is_relative_to(authority) or output == authority:
        raise SystemExit("Output must be a new child of automation/evidence/ISI-27B")
    identity = source_identity(ROOT)
    output.mkdir(parents=True, exist_ok=False)
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
    }
    gates = {}
    for name, command in commands.items():
        print(f"27B gate: {name}", flush=True)
        filename = "performance.jsonl" if name == "performance" else f"{name}.log"
        code = execute_gate(command, root=ROOT, output=output, filename=filename, env=env)
        gates[name] = code
        (output / "gates.json").write_text(json.dumps(gates, sort_keys=True) + "\n")
        if code:
            raise SystemExit(f"FAIL: {name}; see {output / filename} and its .stderr companion")
        if name == "native":
            shutil.copyfile(ROOT / "test-results/native-postgres/pytest-native-postgres.xml", output / "native-postgres.xml")
            shutil.copyfile(ROOT / "test-results/native-postgres/isi19-recovery/rehearsal-summary.json", output / "recovery.json")
    pack = consolidate(ROOT, output, identity, gates)
    (output / "pack.json").write_text(json.dumps(pack, indent=2, sort_keys=True) + "\n")
    for product, acceptance in pack["methodology"].items():
        (output / f"{product}-methodology.json").write_text(json.dumps({"source": identity, "acceptance": acceptance}, sort_keys=True) + "\n")
    (output / "model-evaluation-provenance.json").write_text(json.dumps({"source": identity, "evaluations": pack["evaluation_provenance"], "model_authority": pack["model_authority"]}, sort_keys=True) + "\n")
    print(json.dumps(verify(ROOT, output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
