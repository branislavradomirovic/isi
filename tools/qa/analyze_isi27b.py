"""Read-only independent exact-surface and evidence analysis."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from tools.release.evidence import verify

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "c177f9d705efd6f68d95ef7d13847b03a8e19229"
ALLOWED = {
    ".gitignore", "tests/test_isi_21_native_postgres.py",
    "tools/ci/native_postgres_tests.sh", "tools/ci/isi19_recovery_rehearsal.sh",
    "automation/specs/ISI-27B-R1-RC-EVIDENCE-GOVERNANCE-PACK.md",
    "tools/release/evidence.py", "tools/qa/run_isi27b.py",
    "tools/qa/analyze_isi27b.py", "tests/test_isi_27b_release_evidence.py",
    "docs/release/ISI-RC-GOVERNANCE-PACK.md",
    "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md",
    "TECHNICAL_DOCUMENTATION.md", "automation/STATUS.md", "automation/tasks.json",
}


def check_surface() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if head != BASELINE:
        raise SystemExit("FAIL: locked baseline changed")
    status = subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT, text=True)
    for line in status.splitlines():
        if line[:2] not in {" M", "??"} or line[3:] not in ALLOWED:
            raise SystemExit(f"FAIL: scope/index violation: {line}")
        if line.startswith("??") and any(row.endswith((b" ", b"\t")) for row in (ROOT / line[3:]).read_bytes().splitlines()):
            raise SystemExit(f"FAIL: whitespace: {line[3:]}")
    if subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=False).returncode:
        raise SystemExit("FAIL: changed-line whitespace")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    check_surface()
    print(json.dumps(verify(ROOT, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
