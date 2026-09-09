import json
from pathlib import Path


def test_task_registry_and_docs_contract():
    tasks = json.loads(Path("automation/tasks.json").read_text())["tasks"]
    by_id = {item["id"]: item for item in tasks}
    assert by_id["ISI-14-SECURITY-HARDENING"]["status"] == "done"
    assert by_id["ISI-15-PRODUCTION-STAGING"]["status"] in {"ready", "done"}
    assert by_id["ISI-15-PRODUCTION-STAGING"]["depends_on"] == ["ISI-14-SECURITY-HARDENING"]
    assert by_id["ISI-16-ISI-RS-PRODUCTION-CUTOVER"]["status"] == "on_hold"
    assert Path("automation/specs/ISI-15-PRODUCTION-STAGING.md").is_file()
    assert Path("docs/architecture/ADR-0023-production-staging.md").is_file()
    assert Path("docs/qa/ISI-15-STAGING-QA-MATRIX.md").is_file()
