from __future__ import annotations

from tools.release.governance import LABELS, validate_release_state

import ast
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.streamlit_app import api_client
from src.streamlit_app.shared_help_workspace import HELP_REQUIRED_FIELDS, SHARED_HELP_TOPICS

IDS = ("INV-A01", "INV-A02", "INV-A03", "INV-A04", "INV-A05", "INV-A06", "INV-A08",
       "INV-A14", "INV-A15", "INV-A16", "INV-A17", "INV-A21")
MASTER = Path("docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md")


def _top_rows():
    # Only the canonical top-level table; later material-action tables are not coverage authority.
    head = Path("docs/help/ISI-HELP-COVERAGE-MATRIX.md").read_text().split("\n## ", 1)[0]
    return {cells[0]: cells for line in head.splitlines() if line.startswith("| INV-A")
            for cells in [[cell.strip() for cell in line.strip("|").split("|")]]}


def test_exact_topics_and_guide_satisfy_all_ten_substantive_fields():
    assert [t["id"] for t in SHARED_HELP_TOPICS] == [f"ISI-H{i:02}" for i in range(1, 13)]
    assert tuple(t["inventory_id"] for t in SHARED_HELP_TOPICS) == IDS
    assert set(HELP_REQUIRED_FIELDS) == {"what", "when", "roles_permissions", "steps", "fields_statuses",
                                        "example", "non_goals", "errors_recovery", "limitations", "provenance_review"}
    guide = Path("docs/help/ISI-SHARED-USER-GUIDE.md").read_text()
    for topic in SHARED_HELP_TOPICS:
        assert topic["coverage"] == "VERIFIED"
        assert topic["id"] in guide
        for field in HELP_REQUIRED_FIELDS:
            assert isinstance(topic[field], str) and len(topic[field].strip()) >= 40
            assert topic[field] in guide


def test_top_matrix_inventory_and_protected_predecessors():
    rows = _top_rows()
    assert len(rows) == 21
    for inventory in IDS:
        assert rows[inventory][2] == "VERIFIED"
        assert "tests/test_isi_27a_shared_help_contract.py" in rows[inventory][4]
        assert "ISI-SHARED-USER-GUIDE.md" in rows[inventory][4]
        inventory_row = next(line for line in MASTER.read_text().splitlines() if line.startswith(f"| {inventory} |"))
        assert "shared_help_workspace.py" in inventory_row
        assert "test_isi_27a_shared_help_contract.py" in inventory_row
        assert "| NOT_PRESENT |" in inventory_row if inventory == "INV-A17" else "| CURRENT_AS_BUILT |" in inventory_row
    for inventory in ("INV-A09", "INV-A10", "INV-A11", "INV-A12", "INV-A13", "INV-A18", "INV-A19"):
        assert rows[inventory][2] == "VERIFIED"
        assert "ISI-27A" not in rows[inventory][4]  # Predecessor evidence remains independent.
    assert rows["INV-A07"][2] == "MISSING"
    assert rows["INV-A20"][2:4] == ["MISSING", "OUT_OF_SCOPE"]
    for inventory in ("INV-A07", "INV-A20"):
        line = next(line for line in MASTER.read_text().splitlines() if line.startswith(f"| {inventory} |"))
        assert [c.strip() for c in line.strip("|").split("|")][13] == "NO"
    assert "invitation-only" in rows["INV-A17"][4] and "NOT_PRESENT" in rows["INV-A17"][4]


def test_governance_keeps_candidate_and_later_gate_boundaries():
    tasks = {t["id"]: t for t in json.loads(Path("automation/tasks.json").read_text())["tasks"]}
    key = "ISI-27A-SHARED-HELP-RELEASE-UX-COMPLETENESS"
    assert tasks[key]["status"] == "done"
    assert tasks[key]["accepted_main_sha"] == "74acd5d9a890733347554633f44a6d5319717ba3"
    assert tasks[key]["accepted_main_tree"] == "a69b8582a77555611b64a5527548e67a5b0c45cb"
    assert tasks[key]["accepted_candidate_fingerprint"] == "01ed26dd8e1193606f17c097f88ba0fd68b4f3ce2127de0845468998d3dc8d64"
    assert tasks[key]["spec"] == "automation/specs/ISI-27A-R1-SHARED-HELP-RELEASE-UX-COMPLETENESS.md"
    current = validate_release_state(tasks)
    for path in (MASTER, Path("automation/STATUS.md"), Path("TECHNICAL_DOCUMENTATION.md")):
        text = path.read_text()
        assert "ISI-SHARED-USER-GUIDE.md" in text
        for marker in ("STAGE_COMMIT_PUSH=NO", "GITHUB_ACTIONS_DISPATCH=NO", "SERVER_MUTATION=NO", "CI_VERIFIED=NO", "SERVER_VERIFIED=NO"):
            assert marker in text
    tech = Path("TECHNICAL_DOCUMENTATION.md").read_text()
    status = Path("automation/STATUS.md").read_text()
    master = MASTER.read_text()
    assert "74acd5d9a890733347554633f44a6d5319717ba3" in tech
    assert f"{LABELS[current]}` is the current checkpoint" in master
    assert f"Current checkpoint: `{LABELS[current]}`" in status


def test_shared_navigation_routes_without_private_calls(monkeypatch):
    # Execute actual shell functions without executing app startup/network code.
    path = Path("src/streamlit_app/app.py")
    tree = ast.parse(path.read_text())
    names = {"_navigation", "_render_shell"}
    extracted = ast.Module(body=[node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names], type_ignores=[])
    definitions = ast.unparse(extracted)
    script = '''import streamlit as st
from typing import Any
from src.streamlit_app.shared_help_workspace import render_shared_help
NAV_KEY = "isi_shell_navigation"
''' + definitions + '''
shell = {"product": {"code": "SIMPA"}, "navigation": []}
code = _navigation(shell)
_render_shell(shell, code)
'''
    monkeypatch.setattr(api_client, "app_context", lambda *args: pytest.fail("Help must not fetch context"))
    app = AppTest.from_string(script).run()
    assert not app.exception
    assert app.title[0].value == "ISI Help · Pomoć"
    assert len(app.selectbox[0].options) == 12
    assert any(b.label == "SIMPA Help" for b in app.button)
    assert not any(b.label == "ORDO Help" for b in app.button)


@pytest.mark.parametrize("module,fn,topic", [
    ("data_workspace", "render_data_workspace", "ISI-H07"),
    ("reporting_workspace", "render_reporting", "ISI-H08"),
    ("administration_workspace", "render_administration", "ISI-H09"),
    ("security_workspace", "render_account_security", "ISI-H10"),
])
def test_contextual_entry_precedes_private_data_calls(module, fn, topic):
    tree = ast.parse(Path(f"src/streamlit_app/{module}.py").read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == fn)
    first = function.body[0]
    assert isinstance(first, ast.Expr) and isinstance(first.value, ast.Call)
    assert first.value.func.id == "render_topic_summary"
    assert ast.literal_eval(first.value.args[0]) == topic
    app = AppTest.from_string(f'from src.streamlit_app.shared_help_workspace import render_topic_summary\nrender_topic_summary("{topic}")').run()
    assert not app.exception
    assert topic in app.expander[0].label
    assert len(app.markdown) >= 11


def test_all_shared_topics_render_and_do_not_read_customer_state():
    app = AppTest.from_string('from src.streamlit_app.shared_help_workspace import render_shared_help\nrender_shared_help()').run()
    for topic in SHARED_HELP_TOPICS:
        app.selectbox[0].select(topic["id"]).run()
        assert not app.exception
        assert any(topic["what"] == item.value for item in app.markdown)
    tree = ast.parse(Path("src/streamlit_app/shared_help_workspace.py").read_text())
    assert not any(isinstance(n, ast.Attribute) and n.attr in {"session_state", "query_params"} for n in ast.walk(tree))
    assert not any(isinstance(n, ast.ImportFrom) and n.module and ("api" in n.module or "platform" in n.module) for n in ast.walk(tree))
