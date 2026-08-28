from pathlib import Path


def test_sidebar_uses_buttons_not_radio_controls():
    source = Path("src/streamlit_app/app.py").read_text()
    assert "st.sidebar.radio(" not in source
    assert "isi_product_button_" in source
    assert "isi_nav_button_" in source
    assert 'type="primary" if code == current else "secondary"' in source


def test_ai_workspace_uses_real_local_ollama_diagnostic():
    source = Path("src/streamlit_app/ai_workspace.py").read_text()
    assert "Lokalni Ollama foundation test" in source
    assert 'item.get("provider_type") == "ollama"' in source
    assert '"isi-ollama-chat-default"' in source
    assert "_render_dev_diagnostic(" not in source


def test_launcher_opens_one_tab_and_runs_headless_streamlit():
    source = Path("tools/qa/run_isi07_local_qa.sh").read_text()
    assert "--server.headless true" in source
    assert source.count('open "http://localhost:$APP_PORT"') == 1
    assert "AI_PROVIDER_DEFAULT=ollama" in source
    assert "qwen2.5:7b-instruct" in source
    assert "tools/smoke_local_ollama_chat.py" in source


def test_real_ollama_smoke_requires_gateway_and_selected_model():
    source = Path("tools/smoke_local_ollama_chat.py").read_text()
    assert '"isi-ollama-chat-default"' in source
    assert 'job.get("provider_name") != "ollama"' in source
    assert 'job.get("model_name") != args.model' in source
    assert 'structured.get("status") != "ok"' in source


def test_no_database_migration_is_added_by_hotfix():
    assert not Path("migrations/versions/20260828_0007_isi07_hotfix1.py").exists()
