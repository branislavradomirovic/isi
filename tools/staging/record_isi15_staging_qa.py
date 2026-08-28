from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

TASK15 = "ISI-15-PRODUCTION-STAGING"
TASK16 = "ISI-16-ISI-RS-PRODUCTION-CUTOVER"
ACK = "ISI-15 STAGING QA PASS"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--runtime-dir", default="/tmp/isi15-staging")
    parser.add_argument("--ack", required=True)
    args = parser.parse_args()
    if args.ack != ACK:
        raise SystemExit(f"ERROR: set MANUAL_ACK='{ACK}' only after staging/security/browser QA is complete")

    repo = Path(args.repo).resolve()
    technical_path = Path(args.runtime_dir).resolve() / "technical-pass.json"
    if not technical_path.is_file():
        raise SystemExit(f"ERROR: technical staging PASS evidence missing: {technical_path}")
    technical_bytes = technical_path.read_bytes()
    technical = json.loads(technical_bytes)
    if technical.get("status") != "PASS" or technical.get("task") != TASK15:
        raise SystemExit("ERROR: technical staging evidence is not an ISI-15 PASS")
    if technical.get("alembic_revision") != "20260828_0013":
        raise SystemExit("ERROR: technical staging evidence has an unexpected Alembic revision")
    if technical.get("production_cutover_performed") is not False or technical.get("secrets_recorded") is not False:
        raise SystemExit("ERROR: technical staging evidence violates the safety contract")

    evidence = repo / "automation/evidence/ISI-15-staging-qa.json"
    if evidence.exists():
        raise SystemExit(f"ERROR: evidence already exists: {evidence}")

    tasks_path = repo / "automation/tasks.json"
    data = json.loads(tasks_path.read_text())
    tasks = data["tasks"]
    by_id = {item["id"]: item for item in tasks}
    if by_id[TASK15]["status"] != "ready" or by_id[TASK16]["status"] != "planned":
        raise SystemExit("ERROR: expected ISI-15 ready / ISI-16 planned before QA closeout")

    evidence_payload = {
        "task": TASK15,
        "status": "PASS",
        "manual_ack": ACK,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "technical_evidence_sha256": hashlib.sha256(technical_bytes).hexdigest(),
        "alembic_revision": technical["alembic_revision"],
        "technical_checks": technical.get("checks", []),
        "scope": [
            "production-shaped isolated Compose staging",
            "HTTPS/reverse-proxy/browser QA",
            "SIMPA/ORDO/dual access",
            "S3-compatible storage",
            "SMTP sink",
            "RQ workers",
            "backup/restore rehearsal",
        ],
        "production_cutover_performed": False,
        "secrets_recorded": False,
    }

    # All validation is complete before either repository file is changed.
    by_id[TASK15]["status"] = "done"
    by_id[TASK16]["status"] = "ready"
    tasks_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps(evidence_payload, indent=2) + "\n")

    print("ISI-15 task done")
    print("ISI-16 task ready")
    print("Staging/browser QA evidence PASS recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
