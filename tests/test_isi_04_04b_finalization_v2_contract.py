import json
from pathlib import Path

TASK_IDS = (
    "ISI-04-NEW-PUBLIC-WEBSITE",
    "ISI-04B-DOMAIN-KNOWLEDGE-CONTENT-ENRICHMENT",
)


def test_exact_isi_04_and_04b_tasks_are_done():
    data = json.loads(Path("automation/tasks.json").read_text())
    by_id = {task["id"]: task for task in data["tasks"]}
    for task_id in TASK_IDS:
        assert by_id[task_id]["status"] == "done"


def test_visual_qa_acceptance_record_exists():
    record = Path("docs/design/ISI-04-04B-VISUAL-QA-ACCEPTANCE.md")
    assert record.exists()
    text = record.read_text()
    assert "Status: PASS" in text
    assert "HOTFIX-8" in text
