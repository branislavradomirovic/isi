"""Run with python -m tools.performance.run_isi26; JSON evidence goes to stdout."""
from __future__ import annotations

import json
import subprocess

from tools.performance.evidence import render, summarize, validate_record
from tools.performance.harness import run
from tools.performance.scenarios import prepared
from tools.performance.workloads import catalogue


def main() -> int:
    sha = subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    accepted = True
    for workload in catalogue():
        with prepared(workload) as operation:
            result = run(workload, operation, repository_sha=sha)
        record = render(result)
        validate_record(json.loads(record))
        print(record)
        accepted &= summarize(result)["accepted"]
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
