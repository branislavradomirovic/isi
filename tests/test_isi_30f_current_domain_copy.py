from pathlib import Path
import ast

from streamlit.testing.v1 import AppTest


def test_current_simpa_overview_renders_honest_empty_scope(monkeypatch):
    from src.streamlit_app import simpa_workspace as ui

    monkeypatch.setattr(ui.simpa_api, 'foundation', lambda *_: {
        'profile': None, 'actor_count': 0, 'cycle_count': 0, 'mapping_count': 0,
        'validated_observation_count': 0, 'conceptual_indicator_count': 15,
    })
    monkeypatch.setattr(ui.simpa_api, 'actors', lambda *_: [])
    monkeypatch.setattr(ui.simpa_api, 'cycles', lambda *_: [])
    app = AppTest.from_string('''
from src.streamlit_app.simpa_workspace import render_simpa_overview
render_simpa_overview(token="synthetic", shell={"organization":{"id":"synthetic-org"},"workspace":{"id":"synthetic-workspace"},"product":{"code":"SIMPA","permission_codes":["workspace.read"]}})
''').run()
    assert not app.exception
    captions = '\n'.join(x.value for x in app.caption)
    assert 'menije Analitika i AI' in captions and 'dodeljenim dozvolama' in captions
    assert 'ISI-08' not in captions and 'Foundation status' not in '\n'.join(x.value for x in app.markdown)
    assert all(x.value == '0' for x in app.metric)
    assert 'izmišljenu JLS' in app.info[0].value
    assert not app.text_input and not app.get("form")


def test_active_indicator_copy_keeps_source_and_methodology_limits():
    for product in ('simpa', 'ordo'):
        source = Path(f'src/streamlit_app/{product}_workspace.py').read_text()
        module = ast.parse(source)
        function = next(x for x in module.body if isinstance(x, ast.FunctionDef) and x.name == f'render_{product}_indicators')
        active = ast.get_source_segment(source, function)
        assert 'katalog' in active and 'porekl' in active and 'koncept' in active
        assert 'Analitika' in active or 'Analitiku' in active
        assert all(x not in active for x in ('ISI-08', 'ISI-09', 'ISI-10', 'provenance-ready'))
        assert 'permission_codes' not in active  # existing read-only registry, no new write authority


def test_simpa_scope_denies_cross_product_before_data_read(monkeypatch):
    from src.streamlit_app import simpa_workspace as ui

    def forbidden(*_, **__):
        raise AssertionError('cross-product read')

    monkeypatch.setattr(ui.simpa_api, 'foundation', forbidden)
    app = AppTest.from_string('''
from src.streamlit_app.simpa_workspace import render_simpa_overview
render_simpa_overview(token="synthetic", shell={"organization":{"id":"synthetic-org"},"workspace":{"id":"synthetic-workspace"},"product":{"code":"ORDO"}})
''').run()
    assert not app.exception
    assert not app.metric
    assert 'nije izabran' in app.info[0].value
