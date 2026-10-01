"""Local synthetic workloads over existing runtime surfaces.

Setup and reference execution are outside measurements. Each concurrent lane owns
an isolated SQLite database/client; this does not measure PostgreSQL contention.
Patches are installed once, outside concurrent execution, and always restored.
"""
from __future__ import annotations

import hashlib
import io
import json
import uuid
import zipfile
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone
from queue import Queue
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import src.platform.models  # noqa: F401
from src.core.database import Base
from tools.performance.contracts import Operation, Workload, fingerprint


_readiness_failure: ContextVar[str | None] = ContextVar("synthetic_readiness_failure", default=None)


def synthetic_readiness():
    from src.platform.observability.readiness import ComponentStatus, collect_readiness
    failing = _readiness_failure.get()
    return collect_readiness([lambda name=name: ComponentStatus(
        name, "unhealthy" if name == failing else "ready",
        "dependency_unavailable" if name == failing else "ok",
    ) for name in ("postgres", "redis", "object_storage")])


@contextmanager
def database() -> Iterator[sessionmaker]:
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    try:
        yield sessionmaker(bind=engine, expire_on_commit=False)
    finally:
        engine.dispose()


def seed_scope(db: Session):
    from src.platform.access.service import bootstrap_reference_catalog, grant_product_access
    from src.platform.access.models import OrganizationEntitlement, Role, RoleAssignment
    from src.platform.identity.models import User, Organization, Membership
    from src.platform.workspaces.models import Workspace

    bootstrap_reference_catalog(db)
    user = User(email="synthetic@example.test", display_name="Synthetic", email_verified_at=datetime.now(timezone.utc))
    org = Organization(slug="synthetic", name="Synthetic")
    other = Organization(slug="other", name="Other synthetic")
    db.add_all([user, org, other])
    db.flush()
    member = Membership(user_id=user.id, organization_id=org.id, status="active")
    db.add(member)
    db.flush()
    db.add(OrganizationEntitlement(organization_id=org.id, product_code="SIMPA", is_active=True))
    db.flush()
    grant_product_access(db, member, "SIMPA")
    role = db.scalar(select(Role).where(Role.code == "analyst"))
    db.add(RoleAssignment(membership_id=member.id, role_id=role.id, product_code="SIMPA"))
    workspace = Workspace(organization_id=org.id, product_code="SIMPA", slug="main", name="Synthetic")
    foreign = Workspace(organization_id=other.id, product_code="SIMPA", slug="other", name="Other")
    db.add_all([workspace, foreign])
    db.flush()
    return user, org, member, workspace, foreign


@contextmanager
def api_lane(kind: str) -> Iterator[Callable[[], object]]:
    from src.api.app import app
    from src.api.dependencies import get_db
    from src.platform.auth.service import create_session
    from src.platform.observability.readiness import collect_readiness

    # Fresh application dependency map; preserve real routes, middleware and handlers.
    local = FastAPI(middleware=list(app.user_middleware), exception_handlers=dict(app.exception_handlers))
    from src.api.app import health
    from src.api.app_context_routes import router as context_router
    from src.api.app_shell_routes import router as shell_router
    local.add_api_route("/api/v1/health", health)
    local.include_router(context_router)
    local.include_router(shell_router)
    from src.api.diagnostics_routes import router as diagnostics_router
    local.include_router(diagnostics_router)
    with database() as factory, ExitStack() as stack:
        with factory() as db:
            user, org, _, workspace, foreign = seed_scope(db)
            token = create_session(db, user).token
            db.commit()
            org_id, workspace_id, foreign_id = str(org.id), str(workspace.id), str(foreign.id)

        def get_local_db():
            with factory() as db:
                yield db

        local.dependency_overrides[get_db] = get_local_db
        client = stack.enter_context(TestClient(local, raise_server_exceptions=False))
        headers = {"Authorization": f"Bearer {token}"}
        params = {"organization_id": org_id, "product_code": "SIMPA", "workspace_id": workspace_id}

        def operation():
            if kind == "api.health.read.v1":
                response = client.get("/api/v1/health")
                assert response.status_code == 200
                assert response.json() == {"status": "ok", "service": "isi-api", "phase": "foundation"}
                return response.json()
            if kind == "api.readiness.synthetic.v1":
                # Each component fails independently; no dependency connection is attempted.
                outcomes = []
                for failing in (None, "postgres", "redis", "object_storage"):
                    marker = _readiness_failure.set(failing)
                    try:
                        response = client.get("/api/v1/diagnostics/readiness")
                    finally:
                        _readiness_failure.reset(marker)
                    snapshot = response.json()
                    assert response.status_code == (200 if failing is None else 503)
                    assert snapshot == {"status": "ready" if failing is None else "not_ready", "components": [
                        {"component": name, "state": "unhealthy" if name == failing else "ready",
                         "reason_code": "dependency_unavailable" if name == failing else "ok"}
                        for name in ("postgres", "redis", "object_storage")
                    ]}
                    outcomes.append(snapshot)
                def broken():
                    raise RuntimeError("synthetic failure detail must not escape")
                failed = collect_readiness([broken])
                assert failed == {"status": "not_ready", "components": [
                    {"component": "diagnostic", "state": "unhealthy", "reason_code": "check_failed"}]}
                return outcomes + [failed]
            path = "/api/v1/app-context" if kind.endswith("context.v1") else "/api/v1/app-shell"
            response = client.get(path, headers=headers, params=params)
            assert response.status_code == 200
            body = response.json()
            if kind.endswith("context.v1"):
                assert [o["id"] for o in body["organizations"]] == [org_id]
                assert [p["code"] for p in body["organizations"][0]["products"]] == ["SIMPA"]
                assert [w["id"] for w in body["organizations"][0]["products"][0]["workspaces"]] == [workspace_id]
                assert body["initial_route"]["workspace_id"] == workspace_id
            else:
                assert body["product"]["code"] == "SIMPA" and body["workspace"]["id"] == workspace_id
                assert foreign_id not in json.dumps(body)
            assert client.get(path, params=params).status_code == 401
            assert client.get(path, headers={"Authorization": "Bearer invalid-synthetic"}, params=params).status_code == 401
            for changes in ({"workspace_id": foreign_id}, {"product_code": "ORDO", "workspace_id": None}):
                bad = params | changes
                if kind.endswith("context.v1"):
                    denied = client.post("/api/v1/app-context/select", headers=headers, json=bad)
                else:
                    denied = client.get("/api/v1/app-shell", headers=headers, params={k: v for k, v in bad.items() if v})
                assert denied.status_code == 403
            # Do not hash raw session/user/tenant response content into canonical evidence.
            return {"authorized": 1, "unauthenticated": 2, "scope_denied": 2, "product": "SIMPA"}
        yield operation


def payloads(rows: int) -> tuple[tuple[str, bytes], ...]:
    if rows not in (8, 512):
        raise ValueError("fixture_size_not_registered")
    csv = ("x,y\n" + "".join(f"{i},{i * 2}\n" for i in range(rows))).encode()
    data = json.dumps([{"x": i, "y": i * 2} for i in range(rows)]).encode()
    output = io.BytesIO()
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        entries = {
            "xl/workbook.xml": f'<workbook xmlns="{ns}"><sheets><sheet name="Synthetic" sheetId="1"/></sheets></workbook>',
            "xl/worksheets/sheet1.xml": f'<worksheet xmlns="{ns}"><sheetData>' +
            ''.join(f'<row r="{i+1}"><c r="A{i+1}"/><c r="B{i+1}"/></row>' for i in range(rows + 1)) +
            '</sheetData></worksheet>',
        }
        for name, body in entries.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, body)
    return (("csv", csv), ("json", data), ("xlsx", output.getvalue()))


def ingestion_operation() -> object:
    from src.platform.data.ingestion import IngestionError, inspect_payload, extract_structured_records
    results = []
    for rows in (8, 512):
        for extension, payload in payloads(rows):
            profile = inspect_payload(payload, filename=f"synthetic.{extension}", max_uncompressed_bytes=67108864)
            assert (profile.row_count, profile.column_count) == (rows, 2)
            assert profile.sheet_count == (1 if extension == "xlsx" else None)
            if extension != "xlsx":
                records = extract_structured_records(payload, filename=f"synthetic.{extension}",
                                                     schema_kind="TABULAR", max_uncompressed_bytes=67108864)
                assert len(records) == rows
            results.append((extension, rows, profile.schema_fingerprint))
    # Exercise both member and aggregate uncompressed guards, preserving runtime limits.
    for aggregate in (False, True):
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
            for index in range(2 if aggregate else 1):
                archive.writestr(f"part{index}", b"x" * (60 if aggregate else 101))
        try:
            inspect_payload(out.getvalue(), filename="synthetic.xlsx", max_uncompressed_bytes=100)
        except IngestionError as exc:
            code = "xlsx_uncompressed_limit_exceeded" if aggregate else "xlsx_member_too_large"
            assert str(exc) == code
            results.append(code)
        else:
            raise AssertionError("guard_not_enforced")
    return results


def simpa_operation() -> object:
    from src.domains.simpa.statistical_models import run_statistical_model
    contract = {
        "schema_version": "SIMPA-STATISTICAL-MODEL-CONTRACT-v1", "analysis_key": "association",
        "target_indicator_code": "target", "target_methodology_id": str(uuid.UUID(int=1)),
        "target_methodology_version": 1, "target_methodology_contract_fingerprint": "a" * 64,
        "target_field": "value_numeric", "target_semantic": "continuous", "model_family": "ols",
        "feature_fields": ["x"], "confidence_level": .95, "covariance_type": "nonrobust",
        "missing_data_rule": "complete_case", "feature_scaling": "none", "include_intercept": True,
        "aggregate_only": True, "non_causal": True, "purpose": "Synthetic aggregate association.",
        "limitations": "Non-causal synthetic system-level data.", "positive_outcome_definition": None,
    }
    results = []
    for count in (16, 256):
        records = [{"x": i, "value_numeric": 2 + 3 * i + (i % 3) * .1} for i in range(count)]
        result = run_statistical_model(contract, records, [{"field_key": "x", "logical_type": "NUMBER", "required": False}])
        assert result["sample_size"] == count and result["non_causal"] is True
        assert abs(result["coefficients"][1]["estimate"] - 3) < .01
        results.append(result)
    return results


def ordo_operation() -> object:
    from src.domains.ordo.forecasting import ForecastNotEstimated, forecast_family, run_rolling_origin
    from src.domains.ordo.forecast_metrics import aggregate_point_metrics
    results = []
    for count in (16, 128):
        values = list(range(count))
        for family in ("naive", "seasonal_naive"):
            forecast = forecast_family(values, 3, family, seasonality_period=4)
            assert forecast == ([count - 1] * 3 if family == "naive" else list(range(count - 4, count - 1)))
            backtest = run_rolling_origin(values, family=family, initial_train_periods=8,
                                         step_size=2, horizon=3, minimum_origins=2, seasonality_period=4)
            for row in backtest:
                assert max(row["training"]) < min(row["actual"])
                if family == "naive":
                    metrics = aggregate_point_metrics(row["actual"], row["forecast"])
                    assert metrics["MAE"] == 2 and metrics["bias"] == -2
            results.append({"forecast": forecast, "backtest": backtest})
    for family, period, code in (("ets", None, "EXECUTABLE_FAMILY_NOT_DEFINED_24C"),
                                 ("seasonal_naive", None, "SEASONAL_PERIOD_REQUIRED")):
        try:
            forecast_family([1, 2, 3], 2, family, seasonality_period=period)
        except ForecastNotEstimated as exc:
            assert str(exc) == code
            results.append({"status": "NOT_ESTIMATED", "reason": code})
        else:
            raise AssertionError("automatic_family_fallback")
    return results


@contextmanager
def report_lane() -> Iterator[Callable[[], object]]:
    from src.platform.reporting.models import Report, ReportVersion
    from src.platform.reporting.render import render_json, render_markdown, render_html
    with database() as factory:
        with factory() as db:
            _, org, _, workspace, _ = seed_scope(db)
            report = Report(organization_id=org.id, workspace_id=workspace.id, product_code="SIMPA",
                            report_type="monitoring_summary", title="Synthetic <script>not executable</script>")
            db.add(report)
            db.flush()
            ids = []
            for version, count in enumerate((2, 32), 1):
                content = {"sections": [{"key": f"s{i}", "title": "Synthetic", "text": "<script>unsafe</script>",
                                         "rows": [{"period": j, "value": j * 2} for j in range(32)]} for i in range(count)]}
                row = ReportVersion(report_id=report.id, version_no=version, status="draft", content=content,
                                    source_manifest=[], content_sha256=fingerprint(content), source_manifest_sha256=fingerprint([]))
                db.add(row)
                db.flush()
                ids.append(row.id)
            db.commit()

        def operation():
            checksums = []
            with factory() as db:
                for identity in ids:
                    row = db.get(ReportVersion, identity)
                    assert fingerprint(row.content) == row.content_sha256
                    metadata = {"title": report.title, "product_code": "SIMPA", "report_type": report.report_type,
                                "version_no": row.version_no, "status": row.status, "content_sha256": row.content_sha256}
                    for renderer in (render_json, render_markdown, render_html):
                        text = renderer(metadata=metadata, content=row.content, source_manifest=row.source_manifest)
                        if renderer is render_json:
                            assert json.loads(text)["content"] == row.content
                        if renderer is render_html:
                            assert "<script>" not in text and "&lt;script&gt;" in text
                        checksums.append(hashlib.sha256(text.encode()).hexdigest())
            return checksums
        yield operation


@contextmanager
def data_lane() -> Iterator[Callable[[], object]]:
    from src.platform.data.models import DataSource, DataSourceVersion, IngestionJob
    from src.workers.data_jobs import process_ingestion_job
    with database() as factory:
        with factory() as db:
            _, org, _, workspace, _ = seed_scope(db)
            source = DataSource(organization_id=org.id, workspace_id=workspace.id, product_code="SIMPA",
                                name="Synthetic", source_kind="dataset")
            db.add(source)
            db.commit()
            scope = {"organization_id": org.id, "workspace_id": workspace.id, "product_code": "SIMPA"}
        sequence = 0

        def operation():
            nonlocal sequence
            summary = ingestion_operation()
            with factory() as db:
                for rows in (8, 512):
                    for extension, payload in payloads(rows):
                        sequence += 1
                        version = DataSourceVersion(**scope, source_id=source.id, version_no=sequence,
                            original_filename=f"synthetic.{extension}", extension=extension, size_bytes=len(payload),
                            sha256=hashlib.sha256(payload).hexdigest(), storage_key=f"{rows}.{extension}")
                        db.add(version)
                        db.flush()
                        job = IngestionJob(**scope, version_id=version.id)
                        db.add(job)
                        db.flush()
                        process_ingestion_job(db, job_id=job.id)
                        assert job.status == "succeeded" and job.attempts == 1
                        assert (version.row_count, version.column_count) == (rows, 2)
                        process_ingestion_job(db, job_id=job.id)
                        assert job.attempts == 1  # terminal replay is a no-op
                db.commit()
            return summary
        yield operation


class SyntheticTimeout:
    def complete(self, request):
        from src.platform.ai.providers import ProviderError
        assert request.timeout_seconds == 5
        raise ProviderError("timeout")


def synthetic_provider(model):
    from src.platform.ai.providers import DevelopmentStubProvider
    if model.model_key == "synthetic-timeout":
        return SyntheticTimeout()
    if model.provider_type != "stub" or not model.local_provider:
        raise AssertionError("non_local_provider_forbidden")
    return DevelopmentStubProvider()


def circuit_operation() -> object:
    from src.platform.ai.service import circuit_allows_direct, record_circuit_failure, record_circuit_success
    state = SimpleNamespace(circuit_state="closed", consecutive_failures=0, failure_threshold=2,
                            cooldown_seconds=60, opened_at=None, last_failure_at=None, last_success_at=None, version=1)
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert circuit_allows_direct(state, now=now)
    record_circuit_failure(state, now=now)
    assert state.circuit_state == "closed"
    record_circuit_failure(state, now=now + timedelta(seconds=1))
    assert state.circuit_state == "open"
    assert not circuit_allows_direct(state, now=now + timedelta(seconds=60))
    assert circuit_allows_direct(state, now=now + timedelta(seconds=61))
    assert state.circuit_state == "half_open"
    record_circuit_success(state, now=now + timedelta(seconds=62))
    assert state.circuit_state == "closed" and state.consecutive_failures == 0
    return ("closed", "open", "half_open", "closed")


@contextmanager
def ai_lane(kind: str) -> Iterator[Callable[[], object]]:
    from src.platform.ai.governance import register_model, register_fallback, authorized_runtime_fallbacks
    from src.platform.ai.models import AIModel, AIJobAttempt
    from src.platform.ai.policy import resolve_effective_policy, provider_allowed
    from src.platform.ai.service import bootstrap_ai_registry, create_ai_job, execute_ai_job
    with database() as factory:
        with factory() as db:
            _, org, member, workspace, _ = seed_scope(db)
            bootstrap_ai_registry(db, include_dev_stub=True)
            source = AIModel(model_key="synthetic-timeout", provider_type="stub", provider_name="development-stub",
                             model_name="synthetic-timeout", purpose="chat", product_scope="SIMPA", local_provider=True,
                             timeout_seconds=5)
            db.add(source)
            db.flush()
            target = db.scalar(select(AIModel).where(AIModel.model_key == "isi-dev-stub-chat"))
            registrations = []
            for index, model in enumerate((source, target)):
                registrations.append(register_model(db, organization_id=org.id, workspace_id=workspace.id,
                    product_code="SIMPA", capability_key="simpa.synthetic", product_scope="SIMPA", model_family="llm",
                    model_key=f"synthetic-{index}", version="1", lifecycle_state="candidate", runtime_model_id=model.id,
                    actor_id=member.id, provenance={"source": "synthetic"}))
            edge = register_fallback(db, source_registration_id=registrations[0].id, target_registration_id=registrations[1].id,
                priority=1, trigger_codes=["timeout", "circuit_open"], semantically_equivalent=True, requires_human_review=True,
                provenance="synthetic", actor_id=member.id, organization_id=org.id, workspace_id=workspace.id, product_code="SIMPA")
            db.commit()
            source_id, target_id, edge_id = registrations[0].id, registrations[1].id, edge.id
            scope = {"organization_id": org.id, "workspace_id": workspace.id, "product_code": "SIMPA", "actor_id": member.id}

        def operation():
            transitions = circuit_operation()
            with factory() as db:
                sensitive = resolve_effective_policy(product_code="SIMPA", sensitivity="sensitive", provider_policy="any",
                    allow_external=True, require_human_review=False, max_attempts=2)
                assert sensitive.forced_local_only and not provider_allowed(policy=sensitive, local_provider=False)
                allowed = authorized_runtime_fallbacks(db, source_registration_id=source_id, product_code="SIMPA",
                                                       policy=sensitive, error_code="timeout")
                assert len(allowed) == 1 and allowed[0][0].id == edge_id and allowed[0][1].id == target_id
                assert authorized_runtime_fallbacks(db, source_registration_id=source_id, product_code="ORDO",
                                                    policy=sensitive, error_code="timeout") == []
                assert authorized_runtime_fallbacks(db, source_registration_id=source_id, product_code="SIMPA",
                                                    policy=sensitive, error_code="invalid_provider_response") == []
                is_circuit = kind == "ai.circuit.synthetic.v1"
                job = create_ai_job(db, **scope, input_text="Synthetic diagnostic", prompt_key="foundation.diagnostic",
                    model_key="synthetic-timeout" if is_circuit else "isi-dev-stub-chat",
                    policy_key="shared-local-only", sensitivity="internal",
                    model_registration_id=source_id if is_circuit else None)
                result = execute_ai_job(db, job_id=job.id)
                attempts = list(db.scalars(select(AIJobAttempt).where(AIJobAttempt.job_id == job.id).order_by(AIJobAttempt.attempt_no)))
                if is_circuit:
                    assert result.status == "review_required" and result.human_review_status == "pending"
                    assert len(attempts) == 2 and attempts[0].error_code == "timeout"
                    assert attempts[1].is_fallback and attempts[1].requires_human_review and attempts[1].fallback_edge_id == edge_id
                else:
                    assert result.status == "succeeded" and len(attempts) == 1
                # Unbound failing job must never scan registrations or silently use this valid edge.
                legacy = create_ai_job(db, **scope, input_text="Synthetic diagnostic", prompt_key="foundation.diagnostic",
                    model_key="synthetic-timeout", policy_key="shared-local-only", sensitivity="internal")
                failed = execute_ai_job(db, job_id=legacy.id)
                assert failed.status == "failed" and failed.error_code == "timeout" and failed.attempts == 1
                db.commit()
            return {"transitions": transitions, "attempts": len(attempts), "review_required": is_circuit,
                    "timeout": 1, "sensitive_local_only": True, "legacy_no_fallback": True}
        yield operation


def queue_contract(kind: str) -> dict:
    """Transport-contract preflight, not real Redis capacity measurement."""
    from src.platform.ai import queue as ai_queue
    from src.platform.data import queue as data_queue
    module = ai_queue if kind == "ai" else data_queue
    dispatch = module.dispatch_ai_job if kind == "ai" else module.dispatch_job
    error = module.AIQueueError if kind == "ai" else module.DataQueueError
    settings = SimpleNamespace(ai_job_backend="rq", data_job_backend="rq", redis_url="redis://synthetic.invalid")
    factory = MagicMock()
    row = SimpleNamespace(rq_job_id="")
    factory.return_value.__enter__.return_value.get.return_value = row
    identity = uuid.UUID(int=1)
    with patch.object(module, "get_settings", return_value=settings), patch.object(module, "Redis") as redis, \
         patch.object(module, "Queue") as queue, patch.object(module, "build_session_factory", return_value=factory):
        queue.return_value.enqueue.return_value.id = "synthetic-rq"
        dispatch(identity)
        queue.assert_called_once_with("isi-ai" if kind == "ai" else "isi-data", connection=redis.from_url.return_value)
        target = "src.workers.ai_jobs.run_ai_job" if kind == "ai" else "src.workers.data_jobs.run_ingestion_job"
        queue.return_value.enqueue.assert_called_once_with(target, str(identity), job_timeout=900)
        assert row.rq_job_id == "synthetic-rq"
        factory.return_value.__enter__.return_value.commit.assert_called_once()
        queue.return_value.enqueue.side_effect = RuntimeError("synthetic private detail")
        try:
            dispatch(identity)
        except error as exc:
            assert "private" not in str(exc)
        else:
            raise AssertionError("queue_failure_not_propagated")
    return {"accepted_dispatch": 1, "bounded_failure": 1, "job_timeout": 900}


@contextmanager
def prepared(workload: Workload) -> Iterator[Callable[[], Operation]]:
    """Pre-create independent lanes and references, restore every patch on exit."""
    if not __debug__:
        raise RuntimeError("assertion_enabled_acceptance_required")
    with ExitStack() as stack:
        preflight = queue_contract(workload.category) if workload.category in {"ai", "data"} else None
        if workload.workload_id == "api.readiness.synthetic.v1":
            stack.enter_context(patch("src.api.diagnostics_routes.readiness_snapshot", side_effect=synthetic_readiness))
        if workload.category == "ai":
            settings = SimpleNamespace(isi_env="development", ai_allow_dev_stub=True, ai_store_request_text=False,
                                       ai_request_timeout_seconds=5)
            stack.enter_context(patch("src.platform.ai.service.get_settings", return_value=settings))
            stack.enter_context(patch("src.platform.ai.service.provider_for_model", side_effect=synthetic_provider))
        if workload.category == "data":
            contents = {f"{rows}.{extension}": payload for rows in (8, 512) for extension, payload in payloads(rows)}
            storage = SimpleNamespace(get_bytes=lambda key: contents[key])
            stack.enter_context(patch("src.workers.data_jobs.build_storage", return_value=storage))
            stack.enter_context(patch("src.workers.data_jobs.get_settings",
                                      return_value=SimpleNamespace(data_max_xlsx_uncompressed_bytes=67108864)))
        lanes: Queue = Queue()
        for _ in range(min(workload.concurrency, workload.samples)):
            if workload.category == "api":
                operation = stack.enter_context(api_lane(workload.workload_id))
            elif workload.category == "data":
                operation = stack.enter_context(data_lane())
            elif workload.category == "simpa":
                operation = simpa_operation
            elif workload.category == "ordo":
                operation = ordo_operation
            elif workload.category == "report":
                operation = stack.enter_context(report_lane())
            else:
                operation = stack.enter_context(ai_lane(workload.workload_id))
            expected = fingerprint({"result": operation(), "preflight": preflight})
            lanes.put((operation, expected))

        def measured() -> Operation:
            operation, expected = lanes.get()
            try:
                actual = fingerprint({"result": operation(), "preflight": preflight})
                if actual != expected:
                    return Operation(success=False, correct=False, reason="correctness_mismatch")
                return Operation(result_sha256=actual)
            finally:
                lanes.put((operation, expected))
        yield measured
