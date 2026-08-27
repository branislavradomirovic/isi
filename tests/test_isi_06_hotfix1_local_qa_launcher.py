from pathlib import Path


def test_isi06_launcher_resolves_script_dir_before_repo_cd():
    text = Path("tools/qa/run_isi06_local_qa.sh").read_text()
    script_dir_pos = text.index('SCRIPT_DIR=')
    repo_cd_pos = text.index('cd "$REPO"')
    assert script_dir_pos < repo_cd_pos
    assert 'cp "$(cd "$(dirname "$0")"' not in text
    assert '$SCRIPT_DIR/stop_isi06_local_qa.sh' in text
    assert '$SCRIPT_DIR/status_isi06_local_qa.sh' in text


def test_isi06_launcher_failure_cleanup_is_pid_scoped():
    text = Path("tools/qa/run_isi06_local_qa.sh").read_text()
    assert 'stopping only processes started by this launcher' in text
    assert 'kill "$pid"' in text
    assert 'pkill' not in text
    assert 'killall' not in text
