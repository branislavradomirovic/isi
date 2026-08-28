from pathlib import Path


def test_shared_ai_audit_matches_accepted_ollama_workspace_contract():
    audit = Path("tools/audit_shared_ai_foundation.py").read_text()
    # Assert the semantic contract, not Python formatting of require(...).
    assert "src/streamlit_app/ai_workspace.py" in audit
    assert "Shared AI Foundation" in audit
    assert "Lokalni Ollama foundation test" in audit
    assert "_render_local_ollama_diagnostic" in audit
    assert 'item.get("provider_type") == "ollama"' in audit
    assert "Development-only" not in audit


def test_ai_workspace_retains_hotfix1_ollama_contract():
    source = Path("src/streamlit_app/ai_workspace.py").read_text()
    assert "Shared AI Foundation" in source
    assert "Lokalni Ollama foundation test" in source
    assert "_render_local_ollama_diagnostic" in source
    assert 'item.get("provider_type") == "ollama"' in source
    assert "_render_dev_diagnostic(" not in source
