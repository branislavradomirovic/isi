from pathlib import Path


def test_locked_workflow_forbids_local_docker_runtime_and_manual_owner_qa():
    text = Path("docs/ops/ISI-PRODUCTION-WORKFLOW-LOCK.md").read_text()
    assert "Do not run the ISI Docker runtime on the developer workstation" in text
    assert "reuse the existing server Ollama runtime" in text
    assert "owner does not perform manual browser QA" in text
    assert "No script in this workflow may commit, push, reset, clean" in text


def test_old_local_staging_launcher_fails_closed():
    text = Path("tools/staging/run_isi15_staging_qa.sh").read_text()
    assert "Local ISI Docker staging execution is disabled" in text
    assert "docker compose" not in text
    assert "exit 64" in text


def test_server_preflight_is_read_only_and_does_not_read_env_files():
    text = Path("tools/server/isi_server_preflight.sh").read_text()
    forbidden = (
        "docker compose up",
        "docker compose down",
        "docker rm",
        "docker volume rm",
        "docker network rm",
        "docker system prune",
        "git reset",
        "git clean",
        "git commit",
        "git push",
        "ufw allow",
        "ufw delete",
        "systemctl restart",
        "systemctl stop",
        "source .env",
        "cat .env",
    )
    assert not any(token in text for token in forbidden)
    assert "docker compose ls" in text
    assert "ss -ltnp" in text
    assert "127.0.0.1:11434/api/tags" in text
    assert "no_env_files_read=true" in text
