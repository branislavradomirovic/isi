"""Fail-closed repository governance and autonomous-workflow policy checks."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_TASK_SECTIONS = (
    "Status",
    "Baseline",
    "Dependencies",
    "Objective",
    "Existing architecture",
    "Locked boundaries",
    "Required behavior",
    "Impact",
    "Security and privacy",
    "Tests",
    "Exact acceptance commands",
    "Evidence",
    "Non-goals",
    "Forbidden changes",
    "Completion definition",
    "Deferred server verification",
)
AGENTS_REQUIRED_SNIPPETS = (
    "The platform contains two domain products only: SIMPA and ORDO.",
    "Do not introduce COSMOS as an application, domain, menu, product, tenant, database namespace, or user-visible layer.",
    "The existing ISI server is a deployment target, not a development environment.",
    "Do not SSH to the server",
    "Do not request, store, print, commit, or expose production secrets.",
    "Server-side verification remains deferred until an explicitly approved deployment task.",
    "Never delete, weaken, skip, xfail, or bypass a failing test merely to make acceptance green.",
    "Never fabricate domain formulas, indicator validation, thresholds, risk scores, forecasts, causal effects, recommendations, or institutional conclusions.",
    "Preserve tenant isolation and SIMPA/ORDO isolation",
    "Sensitive SIMPA data must follow the existing local-only AI policy",
)
AUTOMATION_SCAN_ROOTS = (ROOT / ".github/workflows", ROOT / "tools/ci")
AUTOMATION_SCAN_SUFFIXES = {".yml", ".yaml", ".sh", ".py"}
FORBIDDEN_AUTOMATION_PATTERNS = {
    "remote shell": re.compile(r"(?im)(?:^|[\s;&|])ssh(?:\s|$)"),
    "remote copy": re.compile(r"(?im)(?:^|[\s;&|])scp(?:\s|$)"),
    "remote rsync": re.compile(r"(?im)\brsync\b[^\n]*\w+@[\w.-]+:"),
    "server deployment tooling": re.compile(
        r"tools/(?:release/deploy_server_release|server/deploy_release_on_server)\.sh"
    ),
    "direct current-site contact": re.compile(r"(?i)https?://(?:www\.)?isi\.rs(?:/|\b)"),
    "DNS/ingress/infrastructure mutation": re.compile(
        r"(?i)\b(?:cloudflare|route53|change-resource-record-sets|kubectl|ansible-playbook)\b|terraform\s+apply"
    ),
    "production credential reference": re.compile(r"(?i)secrets\.[A-Z0-9_]*(?:PROD|SMTP|SERVER|SSH|DNS)"),
}


def fail(message: str) -> None:
    raise SystemExit(f"POLICY FAIL: {message}")


def validate_agents_text(text: str) -> list[str]:
    """Return missing binding invariants from AGENTS.md."""
    return [snippet for snippet in AGENTS_REQUIRED_SNIPPETS if snippet not in text]


def validate_automation_text(path: Path, text: str) -> list[str]:
    """Return fail-closed policy violations for one executable automation file."""
    return [f"{path}: forbidden {label}" for label, pattern in FORBIDDEN_AUTOMATION_PATTERNS.items() if pattern.search(text)]


def iter_automation_files() -> list[Path]:
    files: list[Path] = []
    for scan_root in AUTOMATION_SCAN_ROOTS:
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in AUTOMATION_SCAN_SUFFIXES:
                continue
            if path.resolve() == Path(__file__).resolve():
                continue
            files.append(path)
    return sorted(files)


def main() -> None:
    tasks = json.loads((ROOT / "automation/tasks.json").read_text(encoding="utf-8"))
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

    template = (ROOT / "automation/specs/TASK-TEMPLATE.md").read_text(encoding="utf-8")
    missing = [name for name in REQUIRED_TASK_SECTIONS if f"## {name}" not in template]
    if missing:
        fail(f"task template lacks sections: {', '.join(missing)}")

    for required in (
        "AGENTS.md",
        "automation/STATUS.md",
        "automation/evidence/README.md",
        "docs/ops/ISI-AUTONOMOUS-DEVELOPMENT-LOCK.md",
        "docs/ops/ISI-RELEASE-POLICY.md",
    ):
        if not (ROOT / required).is_file():
            fail(f"required governance artifact is missing: {required}")

    agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    missing_agents = validate_agents_text(agents_text)
    if missing_agents:
        fail(f"AGENTS.md lost binding invariant(s): {', '.join(missing_agents)}")

    workflows = sorted((ROOT / ".github/workflows").glob("*.y*ml"))
    if not workflows:
        fail("no GitHub Actions workflows found")

    violations: list[str] = []
    automation_files = iter_automation_files()
    for path in automation_files:
        violations.extend(validate_automation_text(path.relative_to(ROOT), path.read_text(encoding="utf-8")))
    if violations:
        fail("; ".join(violations))

    print(
        f"POLICY PASS: {len(entries)} tasks, {len(workflows)} workflow(s), "
        f"{len(automation_files)} automation file(s), AGENTS invariants validated"
    )


if __name__ == "__main__":
    main()
