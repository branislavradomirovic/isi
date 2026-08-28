from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ai_routes_enforce_scope_and_permission():
    text = (ROOT / "src/api/ai_routes.py").read_text()
    assert 'router = APIRouter(prefix="/api/v1/ai"' in text
    assert '"ai.run"' in text
    assert "resolve_selection" in text
    assert "has_permission" in text
    for path in ('"/capabilities"', '"/models"', '"/prompts"', '"/jobs"', '"/embeddings"'):
        assert path in text


def test_shell_and_streamlit_have_real_ai_entry():
    shell = (ROOT / "src/platform/app_shell/service.py").read_text()
    schemas = (ROOT / "src/platform/app_shell/schemas.py").read_text()
    app = (ROOT / "src/streamlit_app/app.py").read_text()
    assert 'NavigationRule("ai", "AI", "AI", "ai.run", "ISI-07")' in shell
    assert '    "ai",' in schemas
    assert "render_ai_workspace" in app
    assert 'nav_code == "ai"' in app
