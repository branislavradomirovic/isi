"""Local deterministic 29D runner with isolated native migration lane."""

from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.qa.analyze_isi29d import FILES, manifest  # noqa: E402


def main() -> int:
    p = ROOT / "automation/evidence/ISI-29D"
    candidate = manifest()
    env = dict(os.environ)
    env["PATH"] = str(ROOT / ".venv/bin") + os.pathsep + env.get("PATH", "")
    assert env.get("ISI_29D_NATIVE_DATABASE_URL"), "isolated synthetic native DB URL required"
    focused = [x for x in FILES if x.startswith("tests/") and "native" not in x]
    commands = [
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            *[x for x in FILES if x.endswith(".py")],
        ],
        [sys.executable, "-m", "tools.ci.policy_check"],
        [sys.executable, "-m", "mypy", "tools/ci"],
        [sys.executable, "-m", "pytest", "-q", *focused, "--junitxml=" + str(p / "focused.xml")],
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_isi_29d_native_postgres.py",
            "--junitxml=" + str(p / "native.xml"),
        ],
        [sys.executable, "-m", "pytest", "-q", "--junitxml=" + str(p / "regression.xml")],
        [sys.executable, "-m", "pip", "check"],
        ["git", "diff", "--check"],
    ]
    gates = []
    for i, command in enumerate(commands):
        log = p / f"gate-{i}.log"
        with log.open("wb") as h:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=h, stderr=subprocess.STDOUT)
        gates.append(
            {
                "command": command,
                "returncode": result.returncode,
                "log": log.name,
                "sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
            }
        )
        print(f"gate {i}: {result.returncode}", flush=True)
        if result.returncode:
            print(log.read_text()[-7000:])
            return result.returncode
    assert manifest() == candidate
    xml = {x: hashlib.sha256((p / x).read_bytes()).hexdigest() for x in ["focused.xml", "native.xml", "regression.xml"]}
    (p / "acceptance.json").write_text(
        json.dumps({"status": "PASS", "candidate": candidate, "gates": gates, "xml_sha256": xml}, indent=2) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
