"""Scoped attribution persistence with live governed input revalidation."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from src.domains.simpa import analytics_service as analytics
from src.domains.simpa.analytics_models import SimpaAttributionArtifact, SimpaStatisticalModelResult, SimpaAnalyticsRun
from src.domains.simpa.statistical_attribution import AttributionError, SCHEMA, explain
from src.domains.simpa.statistical_models import result_fingerprint
from src.platform.data.models import DataAuditEvent
from src.platform.identity.models import Membership


def verified_input(db, *, result_id, organization_id, workspace_id):
    result = db.scalar(
        select(SimpaStatisticalModelResult).where(
            SimpaStatisticalModelResult.id == result_id,
            SimpaStatisticalModelResult.organization_id == organization_id,
            SimpaStatisticalModelResult.workspace_id == workspace_id,
        )
    )
    if result is None:
        raise AttributionError("attribution_result_not_accessible")
    contract_row, indicator, method, contract = analytics._verified_statistical_contract(
        db,
        contract_id=result.statistical_model_contract_id,
    )
    if (
        contract_row.status != "validated"
        or method.status != "validated"
        or indicator.methodology_status != "validated"
        or not indicator.active
        or result.statistical_contract_status != "validated"
        or not result.production_eligible
    ):
        raise AttributionError("attribution_validated_execution_required")
    if (
        result.target_indicator_id,
        result.target_methodology_id,
        result.target_methodology_contract_fingerprint,
        result.statistical_contract_fingerprint,
        result.statistical_contract_version_no,
    ) != (
        indicator.id,
        method.id,
        method.contract_fingerprint,
        contract_row.contract_fingerprint,
        contract_row.version_no,
    ):
        raise AttributionError("attribution_result_binding_changed")
    run = db.scalar(
        select(SimpaAnalyticsRun).where(
            SimpaAnalyticsRun.id == result.analytics_run_id,
            SimpaAnalyticsRun.organization_id == organization_id,
            SimpaAnalyticsRun.workspace_id == workspace_id,
        )
    )
    if run is None:
        raise AttributionError("attribution_run_not_accessible")
    value = analytics.revalidate_analytics_run(db, run=run, organization_id=organization_id, workspace_id=workspace_id)
    records = [
        r
        for r in analytics._records(value, run.monitoring_cycle_id)
        if r.payload["indicator_code"] == indicator.code and r.payload["quality_status"] == "validated"
    ]
    input_hash = hashlib.sha256(
        analytics._canonical_json({"content_fingerprints": [r.content_fingerprint for r in records]}).encode("utf-8")
    ).hexdigest()
    trace = {
        "statistical_contract_id": str(contract_row.id),
        "statistical_contract_version_no": contract_row.version_no,
        "statistical_contract_status": "validated",
        "statistical_contract_fingerprint": contract_row.contract_fingerprint,
        "target_indicator_id": str(indicator.id),
        "target_indicator_code": indicator.code,
        "target_methodology_id": str(method.id),
        "target_methodology_version": method.version_no,
        "target_methodology_contract_fingerprint": method.contract_fingerprint,
        "analytical_artifact_fingerprint": value.artifact_fingerprint,
        "dataset_contract_fingerprint": value.dataset_contract_fingerprint,
        "input_content_fingerprint": input_hash,
    }
    if (
        result.analytical_artifact_fingerprint != value.artifact_fingerprint
        or result.dataset_contract_fingerprint != value.dataset_contract_fingerprint
        or result.input_content_fingerprint != input_hash
        or result.result_detail.get("reproducibility_trace") != trace
        or result.result_fingerprint != result_fingerprint(result.result_detail)
        or result.engine_schema_version != result.result_detail.get("engine_schema_version")
        or result.statsmodels_version != result.result_detail.get("statsmodels_version")
        or result.sample_size != result.result_detail.get("sample_size")
        or result.dropped_missing_count != result.result_detail.get("dropped_missing_count")
    ):
        raise AttributionError("attribution_result_integrity_failed")
    artifact = explain(
        contract,
        result.result_detail,
        [dict(r.payload) for r in records],
        value.field_contract,
        unit=indicator.unit_hint,
    )
    artifact["provenance"] = {
        "organization_id": str(organization_id),
        "workspace_id": str(workspace_id),
        "product": "SIMPA",
        "result_id": str(result.id),
        "result_fingerprint": result.result_fingerprint,
        "analytics_run_id": str(run.id),
        "model_engine_schema_version": result.engine_schema_version,
        "stored_statsmodels_version": result.statsmodels_version,
        **trace,
    }
    return result, artifact


def read(db, *, result_id, organization_id, workspace_id):
    result, expected = verified_input(
        db, result_id=result_id, organization_id=organization_id, workspace_id=workspace_id
    )
    row = db.scalar(
        select(SimpaAttributionArtifact).where(
            SimpaAttributionArtifact.statistical_result_id == result.id,
            SimpaAttributionArtifact.organization_id == organization_id,
            SimpaAttributionArtifact.workspace_id == workspace_id,
            SimpaAttributionArtifact.schema_version == SCHEMA,
        )
    )
    if row is None:
        return {"status": "NOT_CREATED", "schema": SCHEMA}
    expected["creation"] = {
        "id": str(row.id),
        "actor_id": str(row.created_by_membership_id),
        "utc": _utcstamp(row.created_at),
    }
    if (
        row.result_fingerprint != result.result_fingerprint
        or row.artifact != expected
        or row.fingerprint != result_fingerprint(expected)
    ):
        raise AttributionError("attribution_artifact_integrity_failed")
    return {
        "status": "AVAILABLE",
        "id": str(row.id),
        "fingerprint": row.fingerprint,
        "created_at": _utcstamp(row.created_at),
        "artifact": expected,
    }


def create(db, *, result_id, organization_id, workspace_id, actor_id):
    membership = db.get(Membership, actor_id)
    if membership is None or membership.status != "active" or membership.organization_id != organization_id:
        raise AttributionError("attribution_actor_not_accessible")
    current = read(db, result_id=result_id, organization_id=organization_id, workspace_id=workspace_id)
    if current["status"] == "AVAILABLE":
        return current  # verified idempotency; no artifact replacement
    result, artifact = verified_input(
        db, result_id=result_id, organization_id=organization_id, workspace_id=workspace_id
    )
    identity = uuid.uuid4()
    created_at = datetime.now(timezone.utc)
    artifact["creation"] = {"id": str(identity), "actor_id": str(actor_id), "utc": _utcstamp(created_at)}
    fingerprint = result_fingerprint(artifact)
    row = SimpaAttributionArtifact(
        id=identity,
        created_at=created_at,
        organization_id=organization_id,
        workspace_id=workspace_id,
        statistical_result_id=result.id,
        result_fingerprint=result.result_fingerprint,
        schema_version=SCHEMA,
        artifact=artifact,
        fingerprint=fingerprint,
        created_by_membership_id=actor_id,
    )
    db.add(row)
    db.flush()
    db.add(
        DataAuditEvent(
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code="SIMPA",
            actor_membership_id=actor_id,
            event_type="simpa.attribution.created",
            entity_type="simpa_attribution_artifact",
            entity_id=row.id,
            detail=fingerprint,
        )
    )
    return {
        "status": "AVAILABLE",
        "id": str(row.id),
        "fingerprint": fingerprint,
        "created_at": _utcstamp(row.created_at),
        "artifact": artifact,
    }


def _utcstamp(value):
    # SQLite loses the timezone on a datetime written in UTC; PostgreSQL preserves it.
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")
