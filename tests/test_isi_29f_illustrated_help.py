import pytest
from streamlit.testing.v1 import AppTest
from src.streamlit_app import help_manual as h
from src.streamlit_app.shared_help_workspace import SHARED_HELP_TOPICS, PUBLIC_HELP_TOPIC_IDS
from src.streamlit_app.simpa_help_workspace import SIMPA_HELP_TOPICS
from src.streamlit_app.ordo_help_workspace import ORDO_HELP_TOPICS


def test_all_topics_fields_screens_have_exact_reviewed_local_identity():
    data = h.manual()
    assert set(data['topics']) == {x['id'] for x in (*SHARED_HELP_TOPICS, *SIMPA_HELP_TOPICS, *ORDO_HELP_TOPICS)}
    assert h.PUBLIC == frozenset(PUBLIC_HELP_TOPIC_IDS)
    for name, metadata in data['assets'].items():
        assert h.image_bytes(name, metadata).startswith(b'\xff\xd8')
        assert metadata['kind'] in {'SYNTHETIC', 'SERVER_BASELINE'}
        assert metadata['caption'] and metadata['captured']
    assert set(x.name for x in (h.ROOT/'screens').iterdir()) == set(data['assets'])
    for value in data['topics'].values():
        assert value['availability'] and value['screens']
        assert all(x in data['assets'] for x in value['screens'])
    for value in data['chapters'].values():
        assert len(value['sections']) == 10 and value['screens']


@pytest.mark.parametrize('name', ['../login.jpg', '/private/tmp/login.jpg', 'https://example.test/image.jpg'])
def test_help_rejects_nonlocal_asset_path(name):
    with pytest.raises(ValueError, match='help_asset_invalid'):
        h.image_bytes(name, {'sha256':'0'*64})


def test_help_asset_tamper_is_blocked():
    name = next(iter(h.manual()['assets']))
    with pytest.raises(ValueError, match='help_asset_changed'):
        h.image_bytes(name, {'sha256':'0'*64})


@pytest.mark.parametrize('product', ['SIMPA', 'ORDO'])
def test_every_domain_topic_and_new_manual_chapter_renders_in_correct_context(product):
    code=f'from src.streamlit_app.{product.lower()}_help_workspace import render_{product.lower()}_help\nrender_{product.lower()}_help(shell={{"product":{{"code":"{product}"}}}})'
    app=AppTest.from_string(code).run(timeout=30)
    assert not app.exception
    topics=SIMPA_HELP_TOPICS if product=='SIMPA' else ORDO_HELP_TOPICS
    for key in [x['id'] for x in topics]+list(h.chapters(product)):
        app.selectbox[0].select(key).run(timeout=30)
        assert not app.exception
        assert len(app.markdown)>=10
        assert app.get('image')  # actual local image protobuf rendered
    assert ('SHAP' in h.chapters(product)) == (product=='SIMPA')


def test_public_manual_refuses_private_topic_before_loading_images(monkeypatch):
    def forbidden():
        pytest.fail('private Help read attempted in public mode')
    monkeypatch.setattr(h,'manual',forbidden)
    app=AppTest.from_string('from src.streamlit_app.help_manual import render_topic\nrender_topic({"id":"ISI-H09"},public=True)').run()
    assert not app.exception and app.info
    assert not app.get('imgs')
