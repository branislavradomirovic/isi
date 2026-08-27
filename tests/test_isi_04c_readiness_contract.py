from pathlib import Path
import json


def test_isi_04c_task_registered_and_ready():
    data = json.loads(Path("automation/tasks.json").read_text())
    by_id = {task["id"]: task for task in data["tasks"]}
    task = by_id["ISI-04C-PUBLIC-WEBSITE-POLISH-PRODUCTION-READINESS"]
    assert task["status"] in {"ready", "done"}
    assert task["next"] == "ISI-05-AUTHENTICATED-APP-SHELL"


def test_readiness_assets_are_wired_into_base_template():
    base = Path("src/public/templates/base.html").read_text()
    assert 'partials/seo_meta.html' in base
    assert '/static/css/public-readiness.css' in base
    assert '/static/js/public-readiness.js' in base
    assert 'id="main-content" tabindex="-1"' in base


def test_reduced_motion_and_focus_contracts_exist():
    css = Path("src/public/static/css/public-readiness.css").read_text()
    assert "prefers-reduced-motion: reduce" in css
    assert ":focus-visible" in css
    assert "min-height: 44px" in css
    assert "@media (max-width: 980px)" in css
    assert "@media (max-width: 680px)" in css
