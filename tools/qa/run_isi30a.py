"""Deterministic local gates; no hosted checkpoint or server mutation."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.qa.analyze_isi30a import FILES, manifest  # noqa: E402


def main():
    folder = ROOT / "automation/evidence/ISI-30A"
    folder.mkdir(parents=True, exist_ok=True)
    candidate = manifest()
    env = dict(os.environ)
    env["PATH"] = str(ROOT / ".venv/bin") + os.pathsep + env.get("PATH", "")
    commands = [
        [sys.executable, "-m", "ruff", "check", *[name for name in FILES if name.endswith(".py")]],
        [sys.executable, "-m", "tools.ci.policy_check"],
        [sys.executable, "-m", "mypy", "tools/ci"],
        [sys.executable, "-m", "pytest", "tests/test_isi_30a_workflow_shell.py", "--junitxml=" + str(folder / "focused.xml")],
        [sys.executable, "-m", "pytest", "--junitxml=" + str(folder / "regression.xml")],
        [sys.executable, "-m", "pip", "check"],
        ["git", "diff", "--check"],
    ]
    gates = []
    for i, command in enumerate(commands):
        log = folder / f"gate-{i}.log"
        with log.open("wb") as handle:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=handle, stderr=subprocess.STDOUT)
        gates.append({"command": command, "returncode": result.returncode,
                      "log": log.name, "sha256": hashlib.sha256(log.read_bytes()).hexdigest()})
        print(f"gate {i}: {result.returncode}", flush=True)
        if result.returncode:
            print(log.read_text()[-6000:])
            return result.returncode
    assert candidate == manifest(), "Candidate changed while gates were running"
    (folder / "acceptance.json").write_text(json.dumps({
        "status": "LOCAL_GATES_PASS", "candidate": candidate, "gates": gates,
        "xml_sha256": {name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
                       for name in ("focused.xml", "regression.xml")},
        "browser": "REQUIRED_SEPARATELY", "ci_verified": False, "server_verified": False,
    }, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
