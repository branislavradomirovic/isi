from pathlib import Path


def test_isi_05_files_and_shared_shell_contract():
    required = [
        "src/platform/app_shell/service.py",
        "src/platform/app_shell/schemas.py",
        "src/api/app_shell_routes.py",
        "src/streamlit_app/api_client.py",
        "src/streamlit_app/selection.py",
        "src/streamlit_app/assets/app-shell.css",
        "docs/qa/ISI-05-BROWSER-QA-MATRIX.md",
    ]
    for item in required:
        assert Path(item).exists(), item

    app_source = Path("src/api/app.py").read_text()
    assert "app_shell_router" in app_source
    assert "app.include_router(app_shell_router)" in app_source

    streamlit_source = Path("src/streamlit_app/app.py").read_text()
    assert "isi-logo-transparent.svg" in streamlit_source
    assert "simpa-mark.svg" in streamlit_source
    assert "ordo-mark.svg" in streamlit_source
    assert "product entitlement" in streamlit_source
    assert "_logout" in streamlit_source


def test_isi_05_does_not_add_domain_models_or_migration():
    assert not Path("migrations/versions/20260827_0005_authenticated_app_shell.py").exists()
    service = Path("src/platform/app_shell/service.py").read_text()
    assert "src.domains.simpa" not in service
    assert "src.domains.ordo" not in service


def test_isi_05_task_is_ready_or_done_and_points_to_isi_06():
    import json
    data = json.loads(Path("automation/tasks.json").read_text())
    by_id = {task["id"]: task for task in data["tasks"]}
    task = by_id["ISI-05-AUTHENTICATED-APP-SHELL"]
    assert task["status"] in {"ready", "done"}
    assert task["next"] == "ISI-06-SHARED-DATA-PLATFORM"
