from pathlib import Path

import pytest

from tools.server.isi28_operations import (
    BEGIN, END, OperationsError, merged_crontab, validate_lock,
)


def valid_lock():
    return {'schema': 1, 'target': 'isi-only', 'source_sha': 'a' * 40,
            'image': 'sha256:' + 'b' * 64, 'runtime_env_sha256': 'c' * 64,
            'database': 'isi_production', 'bucket': 'isi-production',
            'operational_mode': 'preproduction-testing', 'backups_disabled': True}


def test_explicit_release_lock():
    validate_lock(valid_lock())


@pytest.mark.parametrize('key,value', [
    ('schema', 2), ('target', 'all'), ('source_sha', 'main'), ('image', 'isi-app:latest'),
    ('runtime_env_sha256', ''), ('database', 'isi_preproduction'), ('bucket', 'other'),
    ('backups_disabled', False), ('backups_disabled', 1), ('operational_mode', 'production'),
])
def test_lock_fails_closed(key, value):
    lock = valid_lock()
    lock[key] = value
    with pytest.raises(OperationsError):
        validate_lock(lock)


def test_cron_preserves_other_jobs_and_replaces_only_own_block():
    before = 'MAILTO=owner\n0 * * * * existing-job\n' + BEGIN + '\nold-isi\n' + END + '\n# other\n'
    result = merged_crontab(before, '*/5 * * * * isi-monitor\n15 3 * * * isi-backup')
    assert result.startswith('MAILTO=owner\n0 * * * * existing-job\n# other\n')
    assert 'old-isi' not in result
    assert result.count(BEGIN) == result.count(END) == 1
    assert merged_crontab(result, '*/5 * * * * isi-monitor\n15 3 * * * isi-backup') == result


@pytest.mark.parametrize('text', [BEGIN, END, END + '\n' + BEGIN,
                                 BEGIN + '\n' + BEGIN + '\n' + END])
def test_cron_refuses_ambiguous_markers(text):
    with pytest.raises(OperationsError):
        merged_crontab(text, 'new')


def test_cron_refuses_injected_markers():
    with pytest.raises(OperationsError):
        merged_crontab('', 'job\n' + END)


def test_operational_scope_has_no_backup_or_shared_mutation():
    text = Path('tools/server/isi28_operations.py').read_text()
    assert 'central-ingress' not in text and 'krcuga' not in text and 'app-api' not in text
    assert "'stop'" not in text and "'start'" not in text
    assert 'pg_dump' not in text and 'rmtree' not in text and 'unlink(' not in text
    assert 'DEFERRED_BY_OWNER_PREPRODUCTION' in text
    assert "'offsite_verified'] = False" in text


def test_same_responsive_navigation_breakpoint_and_intact_product_links():
    css = Path('src/public/static/css/public-readiness.css').read_text()
    js = Path('src/public/static/js/public-readiness.js').read_text()
    assert '@media (max-width: 1380px)' in css
    assert 'max-width: 1380px' in js and 'min-width: 1381px' in js
    assert '.semantic-primary-nav > a { flex-shrink: 0; }' in css
    assert '.semantic-primary-nav { flex-shrink: 0; gap: 12px; }' in css
    assert 'max-height: calc(100dvh - 110px); overflow-y: auto;' in css


def test_host_only_bootstrap_refuses_local_execution(tmp_path, monkeypatch):
    from tools.server import isi28_operations as ops
    monkeypatch.chdir(tmp_path)
    with pytest.raises(OperationsError, match='canonical_server_only'):
        ops._bootstrap(tmp_path / 'lock.json')



def test_monitor_is_read_only_and_backup_exception_is_not_false_production(tmp_path, monkeypatch):
    from tools.server import isi28_operations as ops
    import json
    from types import SimpleNamespace
    monkeypatch.setattr(ops, 'ROOT', tmp_path)
    state = {'readiness': 'ready', 'api': True, 'ui': True,
             'queues': {n: {'queued': 0, 'started': 0, 'failed': 0} for n in ['isi-data', 'isi-ai']},
             'worker_queues_alive': ['isi-data', 'isi-ai']}
    monkeypatch.setattr(ops, '_job', lambda *a, **k: json.dumps(state).encode())
    monkeypatch.setattr(ops.shutil, 'disk_usage', lambda _: SimpleNamespace(free=50, total=100))
    class TLS:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def getpeercert(self): return {'notAfter': 'Oct  6 00:00:00 2030 GMT'}
    monkeypatch.setattr(ops.socket, 'create_connection', lambda *a, **k: TLS())
    monkeypatch.setattr(ops.ssl, 'create_default_context', lambda: SimpleNamespace(
        wrap_socket=lambda *a, **k: TLS()))
    report = ops.monitor(valid_lock())
    assert report['status'] == 'PASS'
    assert report['backups_status'] == 'DEFERRED_BY_OWNER_PREPRODUCTION'
    assert report['operational_mode'] == 'preproduction-testing'
    assert report['alerts_delivery_verified'] is report['offsite_verified'] is False
    assert list(tmp_path.iterdir()) == []


def test_pending_email_ui_disables_recovery_and_preserves_login(monkeypatch):
    from types import SimpleNamespace
    from streamlit.testing.v1 import AppTest
    from src.streamlit_app import api_client
    monkeypatch.setattr('src.core.config.get_settings', lambda: SimpleNamespace(auth_delivery_mode='pending'))
    def forbidden(*args, **kwargs):
        pytest.fail('pending email must not invoke API send')
    monkeypatch.setattr(api_client, 'request_password_reset', forbidden)
    monkeypatch.setattr(api_client, 'request_email_verification', forbidden)
    app = AppTest.from_file(Path('src/streamlit_app/app.py').resolve(), default_timeout=20).run()
    assert not app.exception
    assert any('Email dostava još nije aktivirana' in item.value for item in app.info)
    sends = [x for x in app.button if x.label == 'Pošalji zahtev']
    assert len(sends) == 2 and all(x.disabled for x in sends)
    assert next(x for x in app.button if x.label == 'Prijavi se').disabled is False
    app.text_input(key='isi_recovery_email_reset').set_value('synthetic@example.invalid')
    from streamlit.testing.v1.errors import AppTestError
    with pytest.raises(AppTestError, match='Cannot update a disabled'):
        sends[0].click()
    app.run()
    assert not app.exception
