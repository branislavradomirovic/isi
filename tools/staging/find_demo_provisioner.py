from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

MARKER = "ISI-05 local demo profile(s) ready"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    candidates: list[Path] = []
    this_file = Path(__file__).resolve()
    for path in (repo / "tools").rglob("*.py"):
        if path.resolve() == this_file:
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        if MARKER in text:
            candidates.append(path)
    if len(candidates) != 1:
        print(f"ERROR: expected exactly one ISI-05 demo provisioner, found {len(candidates)}", file=sys.stderr)
        return 1
    helper = candidates[0]
    source = helper.read_text()
    if "--password" not in source:
        print(f"ERROR: demo provisioner does not expose the locked --password contract: {helper}", file=sys.stderr)
        return 1

    env = os.environ.copy()
    env["ISI_ENV"] = "development"
    env["ISI_DEPLOYMENT_PROFILE"] = "development"
    env["AUTH_DELIVERY_MODE"] = "null"
    env["SECURITY_TRUST_PROXY_HEADERS"] = "false"
    env["PUBLIC_BASE_URL"] = "http://localhost"
    env["APP_BASE_URL"] = "http://localhost/app"
    print(f"Using existing development-only demo provisioner: {helper.relative_to(repo)}")
    completed = subprocess.run([sys.executable, str(helper), "--all", "--password", args.password], cwd=repo, env=env)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
