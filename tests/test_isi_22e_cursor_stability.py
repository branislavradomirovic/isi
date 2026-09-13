from __future__ import annotations

import base64
from datetime import datetime, timezone
from types import SimpleNamespace

from src.platform.data.ingestion_run_service import (
    create_backfill_ingestion_run,
    create_ingestion_run,
    create_replay_ingestion_run,
)
from src.platform.data.models import DataIngestionRun
from src.platform.data.schemas import IngestionBackfillCreate, IngestionReplayCreate
from src.workers import data_jobs

from test_isi_22e_ingestion_operations import build_case, create_run, run_request


def _worker(case, monkeypatch, run):
    monkeypatch.setattr(data_jobs, "build_storage", lambda: case["storage"])
    monkeypatch.setattr(data_jobs, "get_settings", lambda: SimpleNamespace(data_max_xlsx_uncompressed_bytes=1024 * 1024))
    data_jobs.process_ingestion_job(case["db"], job_id=run.inspection_job_id)


def _next(case, *, key, raw):
    response = create_ingestion_run(case["db"], case["storage"], source_id=case["source"].id,
        request=run_request(case, key=key, cursor=f"{key}:after", observed=datetime.now(timezone.utc)),
        payload_bytes=raw, actor_id=case["membership"].id, backend="inline")
    return case["db"].get(DataIngestionRun, response.run.id)


def test_accepted_incremental_commits_forward_cursor(tmp_path, monkeypatch):
    case = build_case(tmp_path)
    accepted = create_run(case, key="accepted:1", cursor="committed:1", observed=datetime.now(timezone.utc))
    _worker(case, monkeypatch, accepted)
    subsequent = _next(case, key="subsequent:1", raw=b"id\n2\n")
    assert accepted.forward_cursor_committed is True
    assert subsequent.cursor_before == "committed:1"


def test_rejected_incremental_does_not_commit_forward_cursor(tmp_path, monkeypatch):
    case = build_case(tmp_path, freshness_contract={"missing_evidence_action": "REJECT"})
    seed = create_run(case, key="seed:1", cursor="committed:seed", observed=datetime.now(timezone.utc))
    _worker(case, monkeypatch, seed)
    rejected = create_run(case, key="rejected:1", cursor="must-not-commit", raw=b"id\n2\n")
    _worker(case, monkeypatch, rejected)
    subsequent = _next(case, key="subsequent:2", raw=b"id\n3\n")
    assert rejected.forward_cursor_committed is False
    assert subsequent.cursor_before == "committed:seed"


def test_backfill_never_advances_forward_cursor(tmp_path, monkeypatch):
    case = build_case(tmp_path)
    seed = create_run(case, key="seed:backfill", cursor="committed:seed", observed=datetime.now(timezone.utc))
    _worker(case, monkeypatch, seed)
    request = IngestionBackfillCreate(organization_id=case["organization"].id,
        workspace_id=case["workspace"].id, product_code=case["source"].product_code,
        connector_contract_version_id=case["connector"].id, schema_mapping_version_id=case["mapping"].id,
        idempotency_key="backfill:cursor", filename="backfill.csv", content_type="text/csv",
        content_base64=base64.b64encode(b"id\n2\n").decode(), source_observed_at=datetime.now(timezone.utc),
        window_start_cursor="window:start", window_end_cursor="window:end")
    created = create_backfill_ingestion_run(case["db"], case["storage"], source_id=case["source"].id,
        request=request, payload_bytes=b"id\n2\n", actor_id=case["membership"].id, backend="inline")
    backfill = case["db"].get(DataIngestionRun, created.run.id); _worker(case, monkeypatch, backfill)
    subsequent = _next(case, key="subsequent:backfill", raw=b"id\n3\n")
    assert backfill.forward_cursor_committed is False
    assert subsequent.cursor_before == "committed:seed"


def test_replay_never_advances_forward_cursor(tmp_path, monkeypatch):
    case = build_case(tmp_path)
    seed = create_run(case, key="seed:replay", cursor="committed:seed", observed=datetime.now(timezone.utc))
    _worker(case, monkeypatch, seed)
    request = IngestionReplayCreate(organization_id=case["organization"].id,
        workspace_id=case["workspace"].id, product_code=case["source"].product_code,
        idempotency_key="replay:cursor")
    created = create_replay_ingestion_run(case["db"], case["storage"], source_id=case["source"].id,
        run_id=seed.id, request=request, actor_id=case["membership"].id, backend="inline")
    replay = case["db"].get(DataIngestionRun, created.run.id); _worker(case, monkeypatch, replay)
    subsequent = _next(case, key="subsequent:replay", raw=b"id\n2\n")
    assert replay.forward_cursor_committed is False
    assert subsequent.cursor_before == "committed:seed"
