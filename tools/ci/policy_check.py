"""Fail-closed repository governance and autonomous-workflow policy checks."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_TASK_SECTIONS = (
    "Status",
    "Baseline",
    "Canonical bootstrap evidence",
    "Dependencies",
    "Objective",
    "Existing architecture",
    "Canonical system inventory impact",
    "Legacy/drift audit",
    "Exact mutable surface",
    "Implementation-tool authority",
    "Locked boundaries",
    "Required behavior",
    "Impact",
    "Security and privacy",
    "Tests",
    "Exact acceptance commands",
    "Evidence",
    "Non-goals",
    "Forbidden changes",
    "Human review and owner gate",
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
    "Read the complete MasterPlan before any task design or implementation.",
    "perform the mandatory legacy/drift audit",
    "Generic `codex` is forbidden for ISI implementation.",
    "exact committed `main` SHA",
    "Canonical System Inventory maintenance",
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
    by_id = {entry["id"]: entry for entry in entries}
    expected_legacy_states = {
        "ISI-15-PRODUCTION-STAGING": "historical",
        "ISI-16-ISI-RS-PRODUCTION-CUTOVER": "superseded",
    }
    for task_id, expected_status in expected_legacy_states.items():
        actual_status = by_id.get(task_id, {}).get("status")
        if actual_status != expected_status:
            fail(f"{task_id} canonical legacy status drift: expected {expected_status}, got {actual_status}")
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
        "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md",
        "automation/STATUS.md",
        "automation/evidence/README.md",
        "docs/ops/ISI-AUTONOMOUS-DEVELOPMENT-LOCK.md",
        "docs/ops/ISI-RELEASE-POLICY.md",
    ):
        if not (ROOT / required).is_file():
            fail(f"required governance artifact is missing: {required}")

    masterplan_text = (ROOT / "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text(encoding="utf-8")
    for required in (
        "Mandatory bootstrap for every new chat, feature or task",
        "Mandatory legacy/drift audit",
        "Canonical Codex execution contract",
        "Canonical Git/GitHub development contract",
        "Canonical platform architecture map",
        "Canonical SYSTEM INVENTORY - complete product map",
        "Accepted ISI-22E implementation checkpoint - 2026-09-13",
    ):
        if required not in masterplan_text:
            fail(f"MasterPlan lost canonical governance section: {required}")

    status_text = (ROOT / "automation/STATUS.md").read_text(encoding="utf-8")
    if status_text.count("## Owner-facing state model") != 1:
        fail("STATUS must contain exactly one Owner-facing state model heading")
    for stale in (
        "Canonical main SHA:",
        "Canonical tree:",
    ):
        if stale in status_text:
            fail(f"STATUS hard-codes a prior implementation checkpoint as live repository identity: {stale}")
    if "Accepted ISI-22E implementation SHA:" not in status_text:
        fail("STATUS lost accepted ISI-22E implementation checkpoint identity")

    # Canonical System Inventory: fail closed on completeness, field shape and cross-project exclusions.
    inventory_heading = "### 0.7 Canonical SYSTEM INVENTORY - complete product map"
    if masterplan_text.count(inventory_heading) != 1:
        fail("MasterPlan must contain exactly one canonical SYSTEM INVENTORY")
    categories = {letter: 0 for letter in "ABCDEFGHIJKLMN"}
    rows = []
    for line in masterplan_text.splitlines():
        if not line.startswith("| INV-"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 18:
            fail(f"SYSTEM INVENTORY row must contain 18 fields: {cells[0] if cells else '<unknown>'}")
        if any(not cell for cell in cells):
            fail(f"SYSTEM INVENTORY row contains an empty field: {cells[0]}")
        if not re.fullmatch(r"INV-[A-N][0-9]{2}", cells[0]):
            fail(f"SYSTEM INVENTORY ID invalid: {cells[0]}")
        categories[cells[0][4]] += 1
        rows.append(cells)
    if len(rows) < 210:
        fail(f"SYSTEM INVENTORY is incomplete: expected at least 210 governed rows, found {len(rows)}")
    ids = [row[0] for row in rows]
    if len(ids) != len(set(ids)):
        fail("SYSTEM INVENTORY contains duplicate IDs")
    missing_categories = [letter for letter, count in categories.items() if count == 0]
    if missing_categories:
        fail(f"SYSTEM INVENTORY missing categories: {','.join(missing_categories)}")
    inventory_by_id = {row[0]: row for row in rows}
    expected_status = {
        "INV-D05": "NOT_PRESENT",
        "INV-E08": "NOT_PRESENT",
        "INV-E09": "NOT_PRESENT",
        "INV-F06": "NOT_PRESENT",
        "INV-H01": "NOT_PRESENT",
        "INV-H02": "NOT_PRESENT",
        "INV-H03": "NOT_PRESENT",
        "INV-H04": "NOT_PRESENT",
        "INV-H05": "CURRENT_AS_BUILT",
        "INV-A17": "NOT_PRESENT",
        "INV-A18": "PLANNED",
        "INV-A19": "PLANNED",
        "INV-A20": "NOT_PRESENT",
        "INV-J13": "TARGET",
        "INV-J15": "TARGET",
        "INV-J16": "DEVELOPMENT_ONLY",
        "INV-J21": "HISTORICAL",
        "INV-J31": "HISTORICAL",
        "INV-L07": "NOT_PRESENT",
        "INV-L08": "NOT_PRESENT",
    }
    for inventory_id, status in expected_status.items():
        actual = inventory_by_id.get(inventory_id, [None, None, None, None])[3]
        if actual != status:
            fail(f"SYSTEM INVENTORY sentinel drift: {inventory_id} expected {status}, got {actual}")
    for phrase in (
        "ISI has no commercial payment/PayPal subsystem",
        "no dedicated Vision service",
        "no dedicated Audio service",
        "no application-owned scheduler",
        "no active external document-conversion service",
        "isi.opus.rs:8445",
    ):
        if phrase not in masterplan_text:
            fail(f"SYSTEM INVENTORY lost explicit canonical boundary: {phrase}")

    release_text = (ROOT / "docs/ops/ISI-RELEASE-POLICY.md").read_text(encoding="utf-8")
    if "direct `main`" not in release_text or "feature branch or pull request is not required" not in release_text:
        fail("release policy contradicts owner-approved direct-main workflow")

    for historical_path in (
        "docs/ops/ISI-PRODUCTION-WORKFLOW-LOCK.md",
        "docs/ops/ISI-SERVER-DEPLOYMENT-RUNBOOK.md",
        "docs/ops/ISI-15-STAGING-RUNBOOK.md",
        "automation/specs/ISI-15-PRODUCTION-STAGING.md",
    ):
        historical_text = (ROOT / historical_path).read_text(encoding="utf-8")
        if "HISTORICAL / SUPERSEDED - DO NOT EXECUTE" not in historical_text:
            fail(f"legacy deployment authority is not explicitly superseded: {historical_path}")

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
