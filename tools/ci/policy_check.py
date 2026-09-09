"""Fail-closed repository governance and autonomous-workflow policy checks."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_TASK_SECTIONS = (
    "Status", "Baseline", "Dependencies", "Objective", "Existing architecture",
    "Locked boundaries", "Required behavior", "Impact", "Security and privacy",
    "Tests", "Exact acceptance commands", "Evidence", "Non-goals",
    "Forbidden changes", "Completion definition", "Deferred server verification",
)
FORBIDDEN_WORKFLOW_PATTERNS = {
    "remote shell/copy": re.compile(r"(?im)(?:^|[;&|]\s*|run:\s*)s(?:sh|cp)\b"),
    "server deployment tooling": re.compile(
        r"tools/(?:release/deploy_server_release|server/deploy_release_on_server)\.sh"
    ),
    "DNS/ingress mutation": re.compile(r"(?i)\b(?:cloudflare|route53|change-resource-record-sets|kubectl)\b"),
    "production credential reference": re.compile(r"(?i)secrets\.[A-Z0-9_]*(?:PROD|SMTP|SERVER|SSH|DNS)"),
}


def fail(message: str) -> None:
    raise SystemExit(f"POLICY FAIL: {message}")


def main() -> None:
    tasks = json.loads((ROOT / "automation/tasks.json").read_text())
    entries = tasks["tasks"] if isinstance(tasks, dict) else tasks
    ids = {entry["id"] for entry in entries}
    if len(ids) != len(entries):
        fail("automation/tasks.json contains duplicate task IDs")
    for entry in entries:
        for dependency in entry.get("depends_on", []):
            if dependency not in ids:
                fail(f"{entry['id']} references unknown dependency {dependency}")
        spec = entry.get("spec")
        if spec and not (ROOT / spec).is_file():
            fail(f"{entry['id']} references missing spec {spec}")

    template = (ROOT / "automation/specs/TASK-TEMPLATE.md").read_text()
    missing = [name for name in REQUIRED_TASK_SECTIONS if f"## {name}" not in template]
    if missing:
        fail(f"task template lacks sections: {', '.join(missing)}")
    for required in (
        "AGENTS.md", "automation/STATUS.md", "automation/evidence/README.md",
        "docs/ops/ISI-AUTONOMOUS-DEVELOPMENT-LOCK.md", "docs/ops/ISI-RELEASE-POLICY.md",
    ):
        if not (ROOT / required).is_file():
            fail(f"required governance artifact is missing: {required}")

    workflows = sorted((ROOT / ".github/workflows").glob("*.y*ml"))
    if not workflows:
        fail("no GitHub Actions workflows found")
    for workflow in workflows:
        content = workflow.read_text()
        for label, pattern in FORBIDDEN_WORKFLOW_PATTERNS.items():
            if pattern.search(content):
                fail(f"{workflow.relative_to(ROOT)} contains forbidden {label}")
    print(f"POLICY PASS: {len(entries)} tasks and {len(workflows)} workflow(s) validated")


if __name__ == "__main__":
    main()
