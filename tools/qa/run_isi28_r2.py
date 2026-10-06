"""Deterministic local gate; no staging, CI dispatch or server actions."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    evidence = root / "automation/evidence/ISI-28/r2"
    evidence.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    commands = [
        [sys.executable, "-m", "ruff", "check", "src/platform/deployment/runtime.py",
         "src/platform/auth/delivery.py", "src/api/auth_routes.py",
         "tools/publish_isi_legal_notices.py", "tools/qa/run_isi28_r2.py",
         "tools/qa/analyze_isi28_r2.py", "tests/test_isi_28_pending_email.py",
         "tests/test_isi_28_legal_publication.py"],
        [sys.executable, "-m", "mypy", "tools/ci"],
        [sys.executable, "-m", "tools.ci.policy_check"],
        ["git", "diff", "--check"],
        [sys.executable, "-m", "pytest", "--junitxml=" + str(evidence / "regression-final.xml")],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=root, env=env)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
