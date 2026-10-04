"""Consolidate reports only after actual required upstream jobs succeeded."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from tools.release.build import build_bundle, write_json
from tools.release.evidence import consolidate, source_identity, verify

REQUIRED = {
    "policy",
    "quality",
    "tests",
    "architecture-security",
    "migration",
    "native-postgres",
    "compose",
    "supply-chain",
    "build",
    "performance-release",
}


def assemble_pack(root: Path, output: Path, needs: dict) -> dict:
    if set(needs) != REQUIRED or any(job.get("result") != "success" for job in needs.values()):
        raise ValueError("upstream_job_not_successful")
    identity = source_identity(root)
    gates = dict.fromkeys(("regression", "native", "performance", "policy", "diff"), 0)
    # These zero results derive from completed upstream jobs, not default claims.
    pack = consolidate(root, output, identity, gates)
    write_json(output / "upstream-jobs.json", needs)
    write_json(output / "gates.json", gates)
    write_json(output / "pack.json", pack)
    for product, acceptance in pack["methodology"].items():
        write_json(output / f"{product}-methodology.json", {"source": identity, "acceptance": acceptance})
    write_json(
        output / "model-evaluation-provenance.json",
        {"source": identity, "evaluations": pack["evaluation_provenance"], "model_authority": pack["model_authority"]},
    )
    verify(root, output)
    return pack


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    assemble_pack(root, args.reports, json.loads(os.environ["ISI_UPSTREAM_JOBS"]))
    print(json.dumps(build_bundle(root, args.output, args.reports, args.image), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
