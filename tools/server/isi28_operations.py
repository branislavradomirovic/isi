"""ISI-only operations. Host execution requires an explicit protected release lock."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import ssl
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/home/ubuntu/ISI')
SERVICES = ('api', 'streamlit', 'data-worker', 'ai-worker')
BEGIN = '# BEGIN ISI-28 MANAGED OPERATIONS'
END = '# END ISI-28 MANAGED OPERATIONS'


class OperationsError(RuntimeError):
    """Safe, data-free failure code."""


def validate_lock(value: dict) -> None:
    if value.get('schema') != 1 or value.get('target') != 'isi-only':
        raise OperationsError('release_lock_invalid')
    if not re.fullmatch(r'[0-9a-f]{40}', str(value.get('source_sha', ''))):
        raise OperationsError('release_sha_invalid')
    for key in ('image', 'runtime_env_sha256'):
        pattern = r'sha256:[0-9a-f]{64}' if key == 'image' else r'[0-9a-f]{64}'
        if not re.fullmatch(pattern, str(value.get(key, ''))):
            raise OperationsError('release_digest_invalid')
    if value.get('database') != 'isi_production' or value.get('bucket') != 'isi-production':
        raise OperationsError('production_target_invalid')
    if value.get('operational_mode') != 'preproduction-testing' or value.get('backups_disabled') is not True:
        raise OperationsError('owner_testing_boundary_invalid')


def merged_crontab(existing: str, block: str) -> str:
    """Replace exactly our bounded block; refuse malformed/nested markers."""
    lines = existing.splitlines()
    starts = [i for i, line in enumerate(lines) if line == BEGIN]
    ends = [i for i, line in enumerate(lines) if line == END]
    if len(starts) > 1 or len(ends) > 1 or bool(starts) != bool(ends):
        raise OperationsError('cron_markers_invalid')
    if starts:
        if starts[0] >= ends[0]:
            raise OperationsError('cron_markers_invalid')
        lines = lines[:starts[0]] + lines[ends[0] + 1:]
    if BEGIN in block or END in block or not block.strip():
        raise OperationsError('cron_block_invalid')
    return '\n'.join([*lines, BEGIN, block.rstrip('\n'), END]) + '\n'


def _run(args: list[str], *, payload: bytes | None = None, timeout: int = 90) -> bytes:
    try:
        result = subprocess.run(args, input=payload, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        raise OperationsError('operation_unavailable_or_timeout') from None
    if result.returncode:
        raise OperationsError('operation_failed')
    return result.stdout


def _private_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.chmod(0o600)
    os.replace(temporary, path)


def _bootstrap(lock_path: Path) -> dict:
    if Path.cwd().resolve() != ROOT or lock_path != ROOT / 'runtime/deployed-release.json':
        raise OperationsError('canonical_server_only')
    if lock_path.is_symlink() or lock_path.stat().st_mode & 0o077:
        raise OperationsError('release_lock_permissions')
    lock = json.loads(lock_path.read_text())
    validate_lock(lock)
    env = ROOT / 'runtime/.env.server'
    if env.is_symlink() or env.stat().st_mode & 0o077:
        raise OperationsError('runtime_permissions')
    if hashlib.sha256(env.read_bytes()).hexdigest() != lock['runtime_env_sha256']:
        raise OperationsError('runtime_configuration_drift')
    image = json.loads(_run(['docker', 'image', 'inspect', lock['image']]))[0]
    if image['Config']['Labels'].get('org.opencontainers.image.revision') != lock['source_sha']:
        raise OperationsError('runtime_image_drift')
    for service in SERVICES:
        row = json.loads(_run(['docker', 'inspect', f'isi-{service}-1']))[0]
        actual = json.loads(_run(['docker', 'image', 'inspect', row['Image']]))[0]
        if actual['Id'] != image['Id'] or not row['State']['Running']:
            raise OperationsError('runtime_service_drift')
    return lock


def _job(lock: dict, code: str, *, timeout: int = 90) -> bytes:
    return _run(['docker', 'run', '--rm', '--pull=never', '--network', 'isi_internal',
                 '--env-file', str(ROOT / 'runtime/.env.server'), '--memory', '512m',
                 '--cpus', '1', '--entrypoint', 'python', lock['image'], '-c', code], timeout=timeout)


def monitor(lock: dict) -> dict:
    """Read-only checks; no restart or outbound alerts."""
    code = '''import json,datetime,httpx
from src.core.config import get_settings
from src.platform.observability.readiness import readiness_snapshot
from redis import Redis
from rq import Queue,Worker
from rq.registry import FailedJobRegistry,StartedJobRegistry
s=get_settings();r=Redis.from_url(s.redis_url,socket_timeout=3,socket_connect_timeout=3)
ready=readiness_snapshot();c=httpx.Client(timeout=5)
api=c.get('http://api:8000/api/v1/health').status_code==200
ui=c.get('http://streamlit:8501/app/_stcore/health').status_code==200
queues={n:{'queued':Queue(n,connection=r).count,'started':StartedJobRegistry(n,connection=r).count,'failed':FailedJobRegistry(n,connection=r).count} for n in ['isi-data','isi-ai']}
now=datetime.datetime.now(datetime.timezone.utc)
live=[]
for w in Worker.all(connection=r):
 h=w.last_heartbeat
 if h and h.tzinfo is None:h=h.replace(tzinfo=datetime.timezone.utc)
 if h and (now-h).total_seconds()<120:live.extend(w.queue_names())
print(json.dumps({'readiness':ready['status'],'api':api,'ui':ui,'queues':queues,'worker_queues_alive':sorted(set(live))}))
'''
    state = json.loads(_job(lock, code))
    disk = shutil.disk_usage(ROOT)
    state['disk_free_percent'] = round(disk.free / disk.total * 100, 2)
    context = ssl.create_default_context()
    with socket.create_connection(('127.0.0.1', 8445), timeout=8) as connection:
        with context.wrap_socket(connection, server_hostname='isi.opus.rs') as tls:
            certificate = tls.getpeercert()
    expiry = ssl.cert_time_to_seconds(certificate['notAfter'])
    state['certificate_days_remaining'] = round(
        (expiry - datetime.now(timezone.utc).timestamp()) / 86400, 2)
    state['backups_status'] = 'DEFERRED_BY_OWNER_PREPRODUCTION'
    state['operational_mode'] = 'preproduction-testing'
    state['alerts_delivery_verified'] = False
    state['offsite_verified'] = False
    state['status'] = 'PASS' if (state['readiness'] == 'ready' and state['api'] and state['ui']
        and {'isi-data', 'isi-ai'}.issubset(state['worker_queues_alive'])
        and all(v['failed'] == 0 and v['queued'] < 100 for v in state['queues'].values())
        and state['disk_free_percent'] >= 15 and state['certificate_days_remaining'] >= 14
) else 'ATTENTION'
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('monitor',))
    parser.add_argument('--lock', type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        lock = _bootstrap(args.lock)
        report = monitor(lock)
    except Exception as exc:
        report = {'status': 'FAIL', 'reason': str(exc) if isinstance(exc, OperationsError) else 'operation_failed'}
    output = ROOT / 'runtime' / ('isi28-' + args.action + '-latest.json')
    # No writes outside the canonical host even when bootstrap fails locally.
    if Path.cwd().resolve() == ROOT and output.parent.is_dir():
        _private_json(output, report)
    print(json.dumps(report, sort_keys=True))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
