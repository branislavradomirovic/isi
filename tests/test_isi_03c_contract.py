import json
from pathlib import Path


def test_task_and_required_artifact_contract():
    tasks = json.loads(Path("automation/tasks.json").read_text())["tasks"]
    task = next(item for item in tasks if item["id"] == "ISI-03C-MEDIA-REDIRECT-VALIDATION")
    assert task["status"] == "done"
    assert task["next"] == "ISI-04-NEW-PUBLIC-WEBSITE"
    assert Path(task["spec"]).is_file()
    assert Path("src/public_migration/media_redirect_validation.py").is_file()
    assert Path("tools/migrate_legacy_isi_media.py").is_file()
    assert Path("tools/validate_legacy_isi_migration.py").is_file()
