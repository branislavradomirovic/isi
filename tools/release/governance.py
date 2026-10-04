"""Serial release gates may advance only with recorded acceptance evidence."""

from __future__ import annotations

import re

PHASES = (
    "ISI-27A-SHARED-HELP-RELEASE-UX-COMPLETENESS",
    "ISI-27B-RC-EVIDENCE-GOVERNANCE-PACK",
    "ISI-27C-REPRODUCIBLE-RELEASE-SUPPLY-CHAIN-ASSURANCE",
    "ISI-27D-EXACT-MAIN-RC-ACCEPTANCE-CLOSEOUT",
)
PARENT = "ISI-27-INDUSTRIAL-RELEASE-CANDIDATE"
SERVER = "ISI-28-CURRENT-SERVER-CONTROLLED-UPGRADE"
LABELS = {
    PHASES[0]: "ISI-27A - Shared Help & Release UX Completeness",
    PHASES[1]: "ISI-27B - RC Evidence & Governance Pack",
    PHASES[2]: "ISI-27C - Reproducible Release & Supply-Chain Assurance",
    PHASES[3]: "ISI-27D - Exact-Main RC Acceptance & Phase Closeout",
    SERVER: "ISI-28 - Current Server Controlled Upgrade",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_release_state(tasks: dict) -> str:
    current = None
    for key in PHASES:
        task = tasks[key]
        if current is None and task["status"] == "done":
            for field, size in (
                ("accepted_main_sha", 40),
                ("accepted_main_tree", 40),
                ("accepted_candidate_fingerprint", 64),
            ):
                require(
                    re.fullmatch("[0-9a-f]{" + str(size) + "}", task.get(field, "")),
                    f"Missing acceptance identity: {key}/{field}",
                )
        elif current is None:
            require(task["status"] in {"spec_ready", "in_progress"}, f"Current gate not locked: {key}")
            current = key
        else:
            require(task["status"] == "planned", f"Gate advanced before its predecessor: {key}")
    if current:
        require(tasks[PARENT]["status"] == "in_progress", "Invalid release state")
        require(tasks[PARENT]["active_checkpoint"] == current, "Invalid release state")
        require(tasks[SERVER]["status"] == "deferred", "Server enabled before RC acceptance")
        return current
    acceptance = tasks[PHASES[-1]].get("ci_acceptance", {})
    require(acceptance.get("workflow") == "ISI required acceptance", "Invalid release state")
    require(
        acceptance.get("status") == "completed" and acceptance.get("conclusion") == "success", "Invalid release state"
    )
    require(acceptance.get("head_sha") == tasks[PHASES[-1]]["accepted_main_sha"], "Invalid release state")
    require(isinstance(acceptance.get("run_id"), int) and acceptance["run_id"] > 0, "Invalid release state")
    require(acceptance.get("owner_checkpoint_approved") is True, "Invalid release state")
    require(
        acceptance.get("usage_precheck_record") and acceptance.get("usage_postcheck_record"), "Invalid release state"
    )
    require(
        tasks[PARENT]["status"] == "done" and tasks[PARENT].get("active_checkpoint") == SERVER, "Invalid release state"
    )
    require(tasks[SERVER]["status"] in {"planned", "spec_ready", "in_progress", "done"}, "Invalid release state")
    return SERVER


def live_pointer(tasks: dict) -> str:
    current = validate_release_state(tasks)
    if current == SERVER:
        return "ISI-27 is CI_VERIFIED and ISI-28 is current"
    return f"ISI-27A is accepted on main and {current.split('-')[1]} is current"


def last_accepted(tasks: dict) -> str:
    validate_release_state(tasks)
    return next(key for key in reversed(PHASES) if tasks[key]["status"] == "done")
