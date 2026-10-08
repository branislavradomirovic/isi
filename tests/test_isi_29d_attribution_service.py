import copy
from dataclasses import replace
from uuid import uuid4
import pytest
from sqlalchemy import select
from test_isi_23c_statistical_lifecycle import lifecycle_case as target_fixture, _governed_input, _spec
from src.domains.simpa import analytics_service as analytics, attribution_service as service
from src.domains.simpa.analytics_models import SimpaAnalyticsRun, SimpaAttributionArtifact
from src.domains.simpa.statistical_attribution import AttributionError
from src.domains.simpa.statistical_models import result_fingerprint
from src.platform.data.models import DataAuditEvent

lifecycle_case = target_fixture


@pytest.fixture
def attribution_case(lifecycle_case, monkeypatch):
    db, org, member, indicator, method = lifecycle_case
    contract = analytics.create_statistical_model_contract(
        db, indicator_code=indicator.code, specification=_spec(), actor_id=member.id
    )
    analytics.propose_statistical_model_contract(db, contract_id=contract.id, actor_id=member.id)
    analytics.validate_statistical_model_contract(
        db,
        contract_id=contract.id,
        validation_note="Synthetic approval",
        validation_evidence_reference="evidence://synthetic",
        actor_id=member.id,
    )
    data = _governed_input(indicator.code)
    run = SimpaAnalyticsRun(
        organization_id=org.id,
        workspace_id=uuid4(),
        analytical_artifact_type="ANALYTICAL_SNAPSHOT",
        analytical_snapshot_id=data.artifact_id,
        analytical_artifact_fingerprint=data.artifact_fingerprint,
        dataset_contract_version_id=data.dataset_contract_version_id,
        dataset_contract_fingerprint=data.dataset_contract_fingerprint,
        analytical_quality_state="ACCEPTED_CLEAN",
        status="completed",
        snapshot={},
    )
    db.add(run)
    db.flush()
    monkeypatch.setattr(analytics, "revalidate_analytics_run", lambda *a, **kw: data)
    result = analytics.run_statistical_model(
        db,
        organization_id=org.id,
        workspace_id=run.workspace_id,
        analytics_run_id=run.id,
        statistical_model_contract_id=contract.id,
        controlled_testing_ack=False,
        actor_id=member.id,
    )
    return {
        "db": db,
        "org": org,
        "member": member,
        "method": method,
        "contract": contract,
        "run": run,
        "data": data,
        "result": result,
    }


def args(c):
    return {"result_id": c["result"].id, "organization_id": c["org"].id, "workspace_id": c["run"].workspace_id}


def test_persistence_idempotency_immutable_and_minimal_audit(attribution_case):
    c = attribution_case
    db = c["db"]
    p = args(c)
    assert service.read(db, **p)["status"] == "NOT_CREATED"
    first = service.create(db, **p, actor_id=c["member"].id)
    db.commit()
    second = service.create(db, **p, actor_id=c["member"].id)
    assert first == second == service.read(db, **p)
    assert len(db.scalars(select(SimpaAttributionArtifact)).all()) == 1
    audit = db.scalars(select(DataAuditEvent).where(DataAuditEvent.event_type == "simpa.attribution.created")).one()
    assert audit.detail == first["fingerprint"] and "values" not in audit.detail
    assert "source_locator" not in str(first) and "normalized_record_id" not in str(first)
    row = db.scalars(select(SimpaAttributionArtifact)).one()
    row.fingerprint = "a" * 64
    with pytest.raises(ValueError, match="immutable"):
        db.flush()
    db.rollback()


@pytest.mark.parametrize("kind", ["organization", "workspace", "result", "actor"])
def test_scope_and_actor_fail_closed(attribution_case, kind):
    c = attribution_case
    p = args(c)
    actor = c["member"].id
    if kind == "actor":
        actor = uuid4()
    else:
        p[{"organization": "organization_id", "workspace": "workspace_id", "result": "result_id"}[kind]] = uuid4()
    with pytest.raises(AttributionError):
        service.create(c["db"], **p, actor_id=actor)
    assert not c["db"].scalars(select(SimpaAttributionArtifact)).all()


@pytest.mark.parametrize("kind", ["retired", "method", "result", "input", "artifact", "metrics", "version"])
def test_revalidation_blocks_stale_or_tampered_evidence(attribution_case, monkeypatch, kind):
    c = attribution_case
    db = c["db"]
    service.create(db, **args(c), actor_id=c["member"].id)
    r = c["result"]
    if kind == "retired":
        c["contract"].status = "retired"
    elif kind == "method":
        c["method"].status = "retired"
    elif kind == "result":
        r.result_fingerprint = "a" * 64
    elif kind == "version":
        r.statistical_contract_version_no += 1
    elif kind == "input":
        data = replace(c["data"], records=tuple(replace(x, content_fingerprint="f" * 64) for x in c["data"].records))
        monkeypatch.setattr(analytics, "revalidate_analytics_run", lambda *a, **kw: data)
    elif kind == "artifact":
        row = db.scalars(select(SimpaAttributionArtifact)).one()
        row.artifact = copy.deepcopy(row.artifact)
        row.artifact["baseline"] += 1
    elif kind == "metrics":
        r.result_detail = copy.deepcopy(r.result_detail)
        r.result_detail["metrics"]["rmse"] += 1
        r.result_fingerprint = result_fingerprint(r.result_detail)
    with db.no_autoflush:
        with pytest.raises((AttributionError, analytics.SimpaAnalyticsError)):
            service.read(db, **args(c))


def test_source_invalidation_is_rechecked_on_every_read(attribution_case, monkeypatch):
    c = attribution_case
    service.create(c["db"], **args(c), actor_id=c["member"].id)

    def invalid(*a, **kw):
        raise analytics.SimpaAnalyticsError("source_invalidated")

    monkeypatch.setattr(analytics, "revalidate_analytics_run", invalid)
    with pytest.raises(analytics.SimpaAnalyticsError):
        service.read(c["db"], **args(c))


def test_creation_metadata_and_implementation_are_fingerprinted(attribution_case):
    from datetime import timedelta

    c = attribution_case
    db = c["db"]
    created = service.create(db, **args(c), actor_id=c["member"].id)
    db.commit()
    db.expire_all()
    reread = service.read(db, **args(c))
    assert reread["fingerprint"] == created["fingerprint"]
    assert reread["artifact"]["creation"]["id"] == created["id"]
    assert reread["artifact"]["creation"]["actor_id"] == str(c["member"].id)
    assert len(reread["artifact"]["attribution_implementation_sha256"]) == 64
    assert reread["artifact"]["original_fit_code_sha"] == "NOT_RECORDED_LEGACY_RESULT"
    row = db.scalars(select(SimpaAttributionArtifact)).one()
    row.created_at += timedelta(seconds=1)
    with db.no_autoflush:
        with pytest.raises(AttributionError, match="artifact_integrity"):
            service.read(db, **args(c))
