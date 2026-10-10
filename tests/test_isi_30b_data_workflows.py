from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from streamlit.testing.v1 import AppTest

from src.streamlit_app import data_api
from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired

SCOPE = dict(organization_id='org', product_code='SIMPA', workspace_id='space')
SOURCE = dict(id='source', name='Sintetički izvor')
RUN = dict(id='run', run_no=1, status='FAILED', inspection_job_id='job')


def script():
    from src.streamlit_app.data_source_workspace import render_source_inspection
    import streamlit as st
    render_source_inspection(token='synthetic', shell=st.session_state['shell'], sources=st.session_state['sources'])


def app(monkeypatch, permissions=('data.read', 'data.upload'), runs=None):
    for name, value in [('get_source_detail', dict(versions=[])), ('list_ingestion_runs', runs if runs is not None else [RUN]),
                        ('get_ingestion_run', RUN), ('retry_ingestion_run', dict(status='QUEUED'))]:
        monkeypatch.setattr(data_api, name, Mock(return_value=value))
    at = AppTest.from_function(script)
    at.session_state['shell'] = dict(organization=dict(id='org'), product=dict(code='SIMPA', permission_codes=permissions),
                                    workspace=dict(id='space'))
    at.session_state['sources'] = [SOURCE]
    at.run()
    assert not at.exception
    return at


@pytest.mark.parametrize('product', ['SIMPA', 'ORDO'])
@pytest.mark.parametrize('name, suffix, extra', [
    ('get_source_detail', '', {}), ('list_ingestion_runs', '/ingestion-runs', {}),
    ('get_ingestion_run', '/ingestion-runs/run', dict(run_id='run')),
    ('get_run_evaluation', '/ingestion-runs/run/evaluation', dict(run_id='run')),
    ('get_run_governed_output', '/ingestion-runs/run/governed-output', dict(run_id='run')),
    ('retry_ingestion_run', '/ingestion-runs/run/retry', dict(run_id='run')),
])
def test_wrappers_scope(monkeypatch, name, suffix, extra, product):
    request = Mock(return_value=SimpleNamespace(status_code=200, json=lambda: {}))
    monkeypatch.setattr(data_api, 'request', request)
    scope = {**SCOPE, 'product_code': product}
    getattr(data_api, name)('synthetic', source_id='source', **scope, **extra)
    method = 'POST' if name == 'retry_ingestion_run' else 'GET'
    request.assert_called_once_with(method, '/api/v1/data/sources/source' + suffix, token='synthetic',
                                    **({'json': scope} if method == 'POST' else {'params': scope}))


def test_version_payload(monkeypatch):
    request = Mock(return_value=SimpleNamespace(status_code=201, json=lambda: {}))
    monkeypatch.setattr(data_api, 'request', request)
    data_api.create_source_version('synthetic', source_id='s', **SCOPE, filename='sample.csv', content_type='text/csv', payload=b'a,b')
    assert request.call_args.kwargs['json'] == {**SCOPE, 'filename': 'sample.csv', 'content_type': 'text/csv', 'content_base64': 'YSxi'}


@pytest.mark.parametrize('status, error', [(401, AuthenticationRequired), (403, AccessDenied), (503, ApiUnavailable)])
def test_error_contract(monkeypatch, status, error):
    monkeypatch.setattr(data_api, 'request', Mock(return_value=SimpleNamespace(status_code=status)))
    with pytest.raises(error):
        data_api.get_source_detail('synthetic', source_id='s', **SCOPE)


def test_retry_requires_confirmation(monkeypatch):
    at = app(monkeypatch)
    at.button[-1].click().run()
    assert 'Potvrdite' in at.error[0].value
    data_api.retry_ingestion_run.assert_not_called()


def test_retry_rechecks_fresh_state(monkeypatch):
    at = app(monkeypatch)
    data_api.get_ingestion_run.side_effect = [RUN, {**RUN, 'status': 'QUEUED'}]
    at.checkbox[-1].check()
    at.button[-1].click().run()
    data_api.retry_ingestion_run.assert_not_called()
    assert 'Status se promenio' in at.warning[0].value


def test_confirmed_retry_scoped(monkeypatch):
    at = app(monkeypatch)
    at.checkbox[-1].check()
    at.button[-1].click().run()
    data_api.retry_ingestion_run.assert_called_once_with('synthetic', **SCOPE, source_id='source', run_id='run')
    assert not at.exception


def test_readonly_hides_mutations(monkeypatch):
    at = app(monkeypatch, permissions=('data.read',))
    assert not at.checkbox and not at.file_uploader
    assert all('Ponovi' not in button.label for button in at.button)


def test_no_permission_no_reads(monkeypatch):
    at = app(monkeypatch, permissions=())
    data_api.get_source_detail.assert_not_called()
    assert not at.button


def test_no_runs_no_retry(monkeypatch):
    at = app(monkeypatch, runs=[])
    assert all('Ponovi' not in button.label for button in at.button)
    assert any('Nema kontrolisanih' in caption.value for caption in at.caption)


def test_ambiguous_dispatch_requires_refresh(monkeypatch):
    at = app(monkeypatch)
    data_api.retry_ingestion_run.side_effect = ApiUnavailable('Servis nije dostupan')
    at.checkbox[-1].check()
    at.button[-1].click().run()
    assert any('možda već registrovan' in item.value for item in at.warning)


def test_source_specific_keys(monkeypatch):
    at = app(monkeypatch)
    at.checkbox[-1].check().run()
    at.session_state['sources'] = [dict(id='second', name='Drugi sintetički izvor')]
    at.run()
    assert not at.checkbox[-1].value
