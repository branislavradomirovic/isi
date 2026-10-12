from pathlib import Path
from PIL import Image
from streamlit.testing.v1 import AppTest
from src.streamlit_app import help_manual as h


def test_private_help_has_only_contextual_desktop_screens():
    data=h.manual()
    assert data['presentation']['authenticated_view']=='DESKTOP'
    for entry in [*data['topics'].values(),*data['chapters'].values()]:
        assert entry['screens']
        for name in entry['screens']:
            assert 'mobile' not in name.lower()
            assert data['assets'][name]['view']=='DESKTOP'
            assert Image.open(h.ROOT/'screens'/name).width>=1200
        for names in entry.get('screen_sections',{}).values():
            assert set(names)<=set(entry['screens'])


def test_help_index_links_resolve_and_image_width_is_bounded(monkeypatch):
    app=AppTest.from_string('from src.streamlit_app.help_manual import render_chapter\nrender_chapter("DATA",product="SIMPA")').run(timeout=30)
    assert not app.exception
    assert app.expander[0].label=='Sadržaj ovog uputstva'
    body='\n'.join(x.value for x in app.markdown)
    assert '[data-testid="stImageContainer"] { max-width: 100%; }' in body
    titles=[title for title,_ in h.manual()['chapters']['DATA']['sections']]
    assert all(f'](#{h.section_anchor(t)})' in body for t in titles)
    assert len({h.section_anchor(t) for t in titles})==len(titles)
    assert {x.proto.anchor for x in app.get("subheader")}=={h.section_anchor(t) for t in titles}
    assert all(x.proto.width<=960 for x in app.get('imgs')) if app.get('imgs') else app.get('image')


def test_desktop_word_builder_uses_bookmarks_and_source_hashes():
    source=Path('tools/docs/build_isi30f_desktop_manual.py').read_text()
    assert 'w:hyperlink' in source and 'w:anchor' in source and 'w:bookmarkStart' in source
    assert 'ManualContents' in source and 'Povratak na sadržaj' in source
    assert 'assert width >= 1200' in source and 'hashlib.sha256(raw)' in source


def test_nonstandard_capture_cannot_be_rendered_as_desktop(monkeypatch):
    import pytest
    calls=[]
    monkeypatch.setattr(h.st,'image',lambda *args,**kwargs:calls.append(kwargs))
    with pytest.raises(ValueError,match='help_desktop_asset_required'):
        h._screens({'assets':{'legacy-mobile.jpg':{'view':'MOBILE','width':390}}},['legacy-mobile.jpg'])
    assert not calls
