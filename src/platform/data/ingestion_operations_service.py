from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.platform.data.models import (
    DataAuditEvent,
    DataConnectorContractVersion,
    DataGovernedIngestionOutput,
    DataIngestionDeadLetter,
    DataIngestionEvaluation,
    DataIngestionOperationalPolicyVersion,
    DataIngestionRun,
    DataNormalizedRecord,
    DataQualityResult,
    DataRecordGovernancePolicyVersion,
    DataSource,
    DataSourceSchemaMappingVersion,
)
from src.platform.data.schemas import (
    GovernedIngestionOutputResponse,
    IngestionDeadLetterResponse,
    IngestionDeadLetterResolveRequest,
    IngestionEvaluationResponse,
    IngestionOperationalPolicyVersionCreate,
    IngestionOperationalPolicyVersionResponse,
)
from src.platform.data.service import DataPlatformError, get_scoped_source


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _json(text_value: str) -> object:
    return json.loads(text_value)


def _locked_source(session: Session, *, source_id: uuid.UUID, organization_id: uuid.UUID,
                   workspace_id: uuid.UUID, product_code: str) -> DataSource:
    source = get_scoped_source(session, source_id=source_id, organization_id=organization_id,
                               workspace_id=workspace_id, product_code=product_code)
    locked = session.scalar(select(DataSource).where(DataSource.id == source.id).with_for_update())
    if locked is None or locked.status != "active":
        raise DataPlatformError("source_not_accessible")
    return locked


def _binding(session: Session, source: DataSource, connector_id: uuid.UUID, mapping_id: uuid.UUID,
             record_policy_id: uuid.UUID):
    connector = session.get(DataConnectorContractVersion, connector_id)
    mapping = session.get(DataSourceSchemaMappingVersion, mapping_id)
    record_policy = session.get(DataRecordGovernancePolicyVersion, record_policy_id)
    scope = (source.id, source.organization_id, source.workspace_id, source.product_code)
    if connector is None or (connector.source_id, connector.organization_id, connector.workspace_id, connector.product_code) != scope:
        raise DataPlatformError("connector_contract_version_not_accessible")
    if mapping is None or (mapping.source_id, mapping.organization_id, mapping.workspace_id, mapping.product_code) != scope:
        raise DataPlatformError("schema_mapping_version_not_accessible")
    if record_policy is None or (record_policy.source_id, record_policy.organization_id, record_policy.workspace_id, record_policy.product_code) != scope:
        raise DataPlatformError("record_policy_version_not_accessible")
    if (mapping.connector_contract_version_id != connector.id
            or record_policy.connector_contract_version_id != connector.id
            or record_policy.schema_mapping_version_id != mapping.id):
        raise DataPlatformError("operational_policy_binding_mismatch")
    return connector, mapping, record_policy


def _policy_response(row: DataIngestionOperationalPolicyVersion) -> IngestionOperationalPolicyVersionResponse:
    return IngestionOperationalPolicyVersionResponse(
        id=row.id, source_id=row.source_id,
        connector_contract_version_id=row.connector_contract_version_id,
        schema_mapping_version_id=row.schema_mapping_version_id,
        record_governance_policy_version_id=row.record_governance_policy_version_id,
        organization_id=row.organization_id, workspace_id=row.workspace_id,
        product_code=row.product_code, version_no=row.version_no,
        contract_format_version=row.contract_format_version,
        freshness_contract=_json(row.freshness_contract_json),
        quality_contract=_json(row.quality_contract_json),
        backfill_contract=_json(row.backfill_contract_json),
        dead_letter_contract=_json(row.dead_letter_contract_json),
        fingerprint=row.fingerprint, lifecycle_state=row.lifecycle_state,
        created_by_membership_id=row.created_by_membership_id,
        activated_by_membership_id=row.activated_by_membership_id,
        retired_by_membership_id=row.retired_by_membership_id,
        created_at=row.created_at, activated_at=row.activated_at, retired_at=row.retired_at,
    )


def _audit(session: Session, row, *, actor_id: uuid.UUID | None, event_type: str, detail: str) -> None:
    session.add(DataAuditEvent(
        organization_id=row.organization_id, workspace_id=row.workspace_id,
        product_code=row.product_code, actor_membership_id=actor_id,
        event_type=event_type, entity_type=row.__tablename__.removeprefix("core_data_"),
        entity_id=row.id, detail=detail,
    ))


def create_ingestion_operational_policy_version(
    session: Session, *, source_id: uuid.UUID,
    payload: IngestionOperationalPolicyVersionCreate, actor_id: uuid.UUID | None,
) -> IngestionOperationalPolicyVersionResponse:
    source = _locked_source(session, source_id=source_id, organization_id=payload.organization_id,
                            workspace_id=payload.workspace_id, product_code=payload.product_code)
    connector, mapping, record_policy = _binding(
        session, source, payload.connector_contract_version_id,
        payload.schema_mapping_version_id, payload.record_governance_policy_version_id,
    )
    semantic = {
        "contract_format_version": 1, "source_id": str(source.id),
        "organization_id": str(source.organization_id), "workspace_id": str(source.workspace_id),
        "product_code": source.product_code,
        "connector_contract_version_id": str(connector.id),
        "schema_mapping_version_id": str(mapping.id),
        "record_governance_policy_version_id": str(record_policy.id),
        "freshness_contract": payload.freshness_contract.model_dump(mode="json"),
        "quality_contract": payload.quality_contract.model_dump(mode="json"),
        "backfill_contract": payload.backfill_contract.model_dump(mode="json"),
        "dead_letter_contract": payload.dead_letter_contract.model_dump(mode="json"),
    }
    fingerprint = _fingerprint(semantic)
    if session.scalar(select(DataIngestionOperationalPolicyVersion.id).where(
        DataIngestionOperationalPolicyVersion.source_id == source.id,
        DataIngestionOperationalPolicyVersion.fingerprint == fingerprint,
    )) is not None:
        raise DataPlatformError("operational_policy_unchanged")
    version_no = (session.scalar(select(func.max(DataIngestionOperationalPolicyVersion.version_no)).where(
        DataIngestionOperationalPolicyVersion.source_id == source.id)) or 0) + 1
    row = DataIngestionOperationalPolicyVersion(
        source_id=source.id, connector_contract_version_id=connector.id,
        schema_mapping_version_id=mapping.id, record_governance_policy_version_id=record_policy.id,
        organization_id=source.organization_id, workspace_id=source.workspace_id,
        product_code=source.product_code, version_no=version_no, contract_format_version=1,
        freshness_contract_json=_canonical(semantic["freshness_contract"]),
        quality_contract_json=_canonical(semantic["quality_contract"]),
        backfill_contract_json=_canonical(semantic["backfill_contract"]),
        dead_letter_contract_json=_canonical(semantic["dead_letter_contract"]),
        fingerprint=fingerprint, lifecycle_state="DRAFT", created_by_membership_id=actor_id,
    )
    session.add(row); session.flush()
    _audit(session, row, actor_id=actor_id, event_type="data.ingestion_operational_policy_version.created",
           detail=f"version_no={version_no}; fingerprint={fingerprint}")
    return _policy_response(row)


def list_ingestion_operational_policy_versions(session: Session, *, source_id: uuid.UUID,
        organization_id: uuid.UUID, workspace_id: uuid.UUID, product_code: str):
    source = get_scoped_source(session, source_id=source_id, organization_id=organization_id,
                               workspace_id=workspace_id, product_code=product_code)
    rows = session.scalars(select(DataIngestionOperationalPolicyVersion).where(
        DataIngestionOperationalPolicyVersion.source_id == source.id,
        DataIngestionOperationalPolicyVersion.organization_id == source.organization_id,
        DataIngestionOperationalPolicyVersion.workspace_id == source.workspace_id,
        DataIngestionOperationalPolicyVersion.product_code == source.product_code,
    ).order_by(DataIngestionOperationalPolicyVersion.version_no.desc())).all()
    return [_policy_response(row) for row in rows]


def activate_ingestion_operational_policy_version(session: Session, *, source_id: uuid.UUID,
        policy_version_id: uuid.UUID | None = None, policy_id: uuid.UUID | None = None,
        organization_id: uuid.UUID, workspace_id: uuid.UUID, product_code: str,
        actor_id: uuid.UUID | None) -> IngestionOperationalPolicyVersionResponse:
    source = _locked_source(session, source_id=source_id, organization_id=organization_id,
                            workspace_id=workspace_id, product_code=product_code)
    requested_id = policy_version_id or policy_id
    row = session.scalar(select(DataIngestionOperationalPolicyVersion).where(
        DataIngestionOperationalPolicyVersion.id == requested_id,
        DataIngestionOperationalPolicyVersion.source_id == source.id,
        DataIngestionOperationalPolicyVersion.organization_id == source.organization_id,
        DataIngestionOperationalPolicyVersion.workspace_id == source.workspace_id,
        DataIngestionOperationalPolicyVersion.product_code == source.product_code,
    ).with_for_update())
    if row is None: raise DataPlatformError("operational_policy_version_not_accessible")
    if row.lifecycle_state == "ACTIVE": return _policy_response(row)
    if row.lifecycle_state != "DRAFT": raise DataPlatformError("operational_policy_state_conflict")
    connector, mapping, record_policy = _binding(session, source, row.connector_contract_version_id,
                                                  row.schema_mapping_version_id,
                                                  row.record_governance_policy_version_id)
    if connector.lifecycle_state != "ACTIVE": raise DataPlatformError("operational_policy_connector_not_active")
    if mapping.lifecycle_state != "ACTIVE": raise DataPlatformError("operational_policy_mapping_not_active")
    if record_policy.lifecycle_state != "ACTIVE": raise DataPlatformError("operational_policy_record_policy_not_active")
    now = _utcnow()
    active = session.scalars(select(DataIngestionOperationalPolicyVersion).where(
        DataIngestionOperationalPolicyVersion.source_id == source.id,
        DataIngestionOperationalPolicyVersion.lifecycle_state == "ACTIVE",
    ).with_for_update()).all()
    for prior in active:
        prior.lifecycle_state = "RETIRED"; prior.retired_at = now; prior.retired_by_membership_id = actor_id
        _audit(session, prior, actor_id=actor_id, event_type="data.ingestion_operational_policy_version.retired",
               detail=f"replacement_id={row.id}")
    session.flush()
    row.lifecycle_state = "ACTIVE"; row.activated_at = now; row.activated_by_membership_id = actor_id
    _audit(session, row, actor_id=actor_id, event_type="data.ingestion_operational_policy_version.activated",
           detail="DRAFT_TO_ACTIVE")
    session.flush(); return _policy_response(row)


def get_active_ingestion_operational_policy_for_binding(session: Session, *, source_id: uuid.UUID,
        organization_id: uuid.UUID, workspace_id: uuid.UUID, product_code: str,
        connector_contract_version_id: uuid.UUID, schema_mapping_version_id: uuid.UUID,
        record_governance_policy_version_id: uuid.UUID | None):
    row = session.scalar(select(DataIngestionOperationalPolicyVersion).where(
        DataIngestionOperationalPolicyVersion.source_id == source_id,
        DataIngestionOperationalPolicyVersion.lifecycle_state == "ACTIVE"))
    if row is None: return None
    expected = (organization_id, workspace_id, product_code, connector_contract_version_id,
                schema_mapping_version_id, record_governance_policy_version_id)
    actual = (row.organization_id, row.workspace_id, row.product_code,
              row.connector_contract_version_id, row.schema_mapping_version_id,
              row.record_governance_policy_version_id)
    if actual != expected: raise DataPlatformError("operational_policy_binding_mismatch")
    return row


def validate_pinned_ingestion_operational_policy(session: Session, *, run: DataIngestionRun):
    if run.operational_policy_version_id is None: return None
    row = session.get(DataIngestionOperationalPolicyVersion, run.operational_policy_version_id)
    if row is None or (row.source_id, row.organization_id, row.workspace_id, row.product_code,
        row.connector_contract_version_id, row.schema_mapping_version_id,
        row.record_governance_policy_version_id) != (
        run.source_id, run.organization_id, run.workspace_id, run.product_code,
        run.connector_contract_version_id, run.schema_mapping_version_id,
        run.record_governance_policy_version_id):
        raise DataPlatformError("operational_policy_integrity_failed")
    return row


def _metrics(session: Session, run: DataIngestionRun) -> dict[str, object]:
    rows = session.scalars(select(DataNormalizedRecord).where(DataNormalizedRecord.ingestion_run_id == run.id)).all()
    counts = {name: sum(row.disposition == value for row in rows) for name, value in (
        ("current_record_count", "ACCEPTED"), ("duplicate_record_count", "DUPLICATE"),
        ("quarantined_record_count", "QUARANTINED"), ("superseded_record_count", "SUPERSEDED"))}
    total = len(rows)
    # The ratio denominator is every materialized row for this run; an empty run has ratio 0.
    return {"materialized_record_count": total, **counts,
            "quarantine_ratio": counts["quarantined_record_count"] / total if total else 0.0}


def _evaluation_response(row: DataIngestionEvaluation) -> IngestionEvaluationResponse:
    return IngestionEvaluationResponse(id=row.id, source_id=row.source_id,
        ingestion_run_id=row.ingestion_run_id, operational_policy_version_id=row.operational_policy_version_id,
        organization_id=row.organization_id, workspace_id=row.workspace_id, product_code=row.product_code,
        freshness_status=row.freshness_status, quality_status=row.quality_status, decision=row.decision,
        freshness_details=_json(row.freshness_details_json), quality_details=_json(row.quality_details_json),
        record_metrics=_json(row.record_metrics_json), evidence_fingerprint=row.evidence_fingerprint,
        evaluated_at=row.evaluated_at)


def create_or_get_ingestion_evaluation(session: Session, *, run: DataIngestionRun) -> IngestionEvaluationResponse:
    existing = session.scalar(select(DataIngestionEvaluation).where(DataIngestionEvaluation.ingestion_run_id == run.id))
    if existing is not None: return _evaluation_response(existing)
    policy = validate_pinned_ingestion_operational_policy(session, run=run)
    if policy is None: raise DataPlatformError("operational_policy_required")
    freshness_contract = _json(policy.freshness_contract_json)
    quality_contract = _json(policy.quality_contract_json)
    reference = _aware(run.queued_at)
    if run.source_observed_at is None:
        freshness_status = "UNKNOWN"
        freshness_reject = freshness_contract["missing_evidence_action"] == "REJECT"
        freshness_warning = not freshness_reject
        freshness_details = {"reference_queued_at": reference.isoformat(), "source_observed_at": None,
                             "missing_evidence_action": freshness_contract["missing_evidence_action"]}
    else:
        observed = _aware(run.source_observed_at)
        raw_age = (reference - observed).total_seconds()
        age = max(raw_age, 0.0)
        future_clamped = raw_age < 0
        if age <= freshness_contract["warning_after_seconds"]:
            freshness_status, freshness_warning, freshness_reject = "FRESH", False, False
        elif age <= freshness_contract["reject_after_seconds"]:
            freshness_status, freshness_warning, freshness_reject = "STALE_WARNING", True, False
        else:
            freshness_status, freshness_warning, freshness_reject = "STALE_REJECTED", False, True
        freshness_details = {"reference_queued_at": reference.isoformat(), "source_observed_at": observed.isoformat(),
                             "age_seconds": age, "future_evidence_clamped_to_zero": future_clamped,
                             "warning_after_seconds": freshness_contract["warning_after_seconds"],
                             "reject_after_seconds": freshness_contract["reject_after_seconds"]}
    quality_rows = session.scalars(select(DataQualityResult).where(
        DataQualityResult.version_id == run.source_version_id).order_by(
            DataQualityResult.check_code, DataQualityResult.status,
            DataQualityResult.metric_name, DataQualityResult.metric_value,
        )).all()
    evidence = [{"check_code": row.check_code, "status": row.status,
                 "metric_name": row.metric_name, "metric_value": row.metric_value} for row in quality_rows]
    by_code: dict[str, list[str]] = {}
    for row in quality_rows: by_code.setdefault(row.check_code, []).append(row.status)
    missing = []; warned = []; failed = []
    for code in quality_contract["required_check_codes"]:
        states = by_code.get(code)
        if not states: missing.append(code)
        elif "fail" in states: failed.append(code)
        elif "warn" in states: warned.append(code)
    metrics = _metrics(session, run)
    ratio = metrics["quarantine_ratio"]
    quality_reject = bool(failed) or (bool(missing) and quality_contract["missing_required_check_action"] == "REJECT") or ratio > quality_contract["reject_quarantine_ratio"]
    quality_warning = (not quality_reject) and (bool(warned) or bool(missing) or ratio > quality_contract["warning_quarantine_ratio"])
    quality_status = "REJECTED" if quality_reject else "WARNING" if quality_warning else "PASS"
    quality_details = {"required_check_codes": quality_contract["required_check_codes"],
                       "missing_required_check_codes": missing, "warning_check_codes": warned,
                       "failed_check_codes": failed, "missing_required_check_action": quality_contract["missing_required_check_action"],
                       "warning_quarantine_ratio": quality_contract["warning_quarantine_ratio"],
                       "reject_quarantine_ratio": quality_contract["reject_quarantine_ratio"],
                       "quality_evidence": evidence}
    rejected = freshness_reject or quality_reject
    warning = freshness_warning or quality_warning
    dead_contract = _json(policy.dead_letter_contract_json)
    decision = "DEAD_LETTERED" if rejected and dead_contract["rejected_evaluation_to_dead_letter"] else "REJECTED" if rejected else "ACCEPTED_WITH_WARNING" if warning else "ACCEPTED"
    semantic = {"ingestion_run_id": str(run.id), "source_id": str(run.source_id),
                "source_version_id": str(run.source_version_id), "execution_mode": run.execution_mode,
                "connector_contract_version_id": str(run.connector_contract_version_id),
                "schema_mapping_version_id": str(run.schema_mapping_version_id),
                "record_governance_policy_version_id": str(run.record_governance_policy_version_id),
                "operational_policy_version_id": str(policy.id), "operational_policy_fingerprint": policy.fingerprint,
                "freshness_details": freshness_details, "quality_evidence": evidence, "record_metrics": metrics}
    row = DataIngestionEvaluation(source_id=run.source_id, ingestion_run_id=run.id,
        operational_policy_version_id=policy.id, organization_id=run.organization_id,
        workspace_id=run.workspace_id, product_code=run.product_code,
        freshness_status=freshness_status, quality_status=quality_status, decision=decision,
        freshness_details_json=_canonical(freshness_details), quality_details_json=_canonical(quality_details),
        record_metrics_json=_canonical(metrics), evidence_fingerprint=_fingerprint(semantic))
    session.add(row); session.flush()
    _audit(session, row, actor_id=None, event_type="data.ingestion_evaluation.created",
           detail=f"run_id={run.id}; decision={decision}; evidence_fingerprint={row.evidence_fingerprint}")
    if decision == "DEAD_LETTERED":
        record_ingestion_failure_dead_letter(session, run=run, reason_code="governed_evaluation_rejected",
            error_category="GOVERNANCE", details={"decision": decision}, evaluation_id=row.id, force=True)
    session.flush(); return _evaluation_response(row)


def _output_response(row: DataGovernedIngestionOutput) -> GovernedIngestionOutputResponse:
    return GovernedIngestionOutputResponse(**{name: getattr(row, name) for name in GovernedIngestionOutputResponse.model_fields})


def create_or_get_governed_ingestion_output(session: Session, *, run: DataIngestionRun) -> GovernedIngestionOutputResponse:
    existing = session.scalar(select(DataGovernedIngestionOutput).where(DataGovernedIngestionOutput.ingestion_run_id == run.id))
    if existing is not None: return _output_response(existing)
    if run.operational_policy_version_id is None or run.record_governance_policy_version_id is None:
        raise DataPlatformError("governed_output_requires_governed_run")
    evaluation = session.scalar(select(DataIngestionEvaluation).where(DataIngestionEvaluation.ingestion_run_id == run.id))
    if evaluation is None or evaluation.decision not in {"ACCEPTED", "ACCEPTED_WITH_WARNING"}:
        raise DataPlatformError("governed_output_decision_conflict")
    metrics = _json(evaluation.record_metrics_json)
    semantic = {"contract_version": 1, "source_id": str(run.source_id), "source_version_id": str(run.source_version_id),
        "ingestion_run_id": str(run.id), "evaluation_id": str(evaluation.id),
        "connector_contract_version_id": str(run.connector_contract_version_id),
        "schema_mapping_version_id": str(run.schema_mapping_version_id),
        "record_governance_policy_version_id": str(run.record_governance_policy_version_id),
        "operational_policy_version_id": str(run.operational_policy_version_id),
        "organization_id": str(run.organization_id), "workspace_id": str(run.workspace_id),
        "product_code": run.product_code, "record_metrics": metrics}
    row = DataGovernedIngestionOutput(source_id=run.source_id, source_version_id=run.source_version_id,
        ingestion_run_id=run.id, evaluation_id=evaluation.id,
        connector_contract_version_id=run.connector_contract_version_id,
        schema_mapping_version_id=run.schema_mapping_version_id,
        record_governance_policy_version_id=run.record_governance_policy_version_id,
        operational_policy_version_id=run.operational_policy_version_id,
        organization_id=run.organization_id, workspace_id=run.workspace_id, product_code=run.product_code,
        contract_version=1, record_count=metrics["materialized_record_count"],
        current_record_count=metrics["current_record_count"], duplicate_record_count=metrics["duplicate_record_count"],
        quarantined_record_count=metrics["quarantined_record_count"], superseded_record_count=metrics["superseded_record_count"],
        output_fingerprint=_fingerprint(semantic))
    session.add(row); session.flush()
    _audit(session, row, actor_id=None, event_type="data.governed_ingestion_output.created",
           detail=f"run_id={run.id}; output_fingerprint={row.output_fingerprint}")
    return _output_response(row)


def _dead_response(row: DataIngestionDeadLetter) -> IngestionDeadLetterResponse:
    return IngestionDeadLetterResponse(id=row.id, source_id=row.source_id, ingestion_run_id=row.ingestion_run_id,
        evaluation_id=row.evaluation_id, operational_policy_version_id=row.operational_policy_version_id,
        organization_id=row.organization_id, workspace_id=row.workspace_id, product_code=row.product_code,
        reason_code=row.reason_code, error_category=row.error_category, details=_json(row.details_json),
        status=row.status, created_at=row.created_at, resolved_at=row.resolved_at,
        resolver_membership_id=row.resolver_membership_id, resolution_note=row.resolution_note,
        replacement_run_id=row.replacement_run_id)


def record_ingestion_failure_dead_letter(session: Session, *, run: DataIngestionRun,
        reason_code: str, error_category: str, details: dict[str, object] | None = None,
        evaluation_id: uuid.UUID | None = None, force: bool = False):
    policy = validate_pinned_ingestion_operational_policy(session, run=run)
    if policy is None: return None
    contract = _json(policy.dead_letter_contract_json)
    terminal = reason_code in contract["terminal_error_codes"] or run.attempts >= contract["max_retry_attempts"]
    if not force and not terminal: return None
    existing = session.scalar(select(DataIngestionDeadLetter).where(
        DataIngestionDeadLetter.ingestion_run_id == run.id,
        DataIngestionDeadLetter.reason_code == reason_code,
        DataIngestionDeadLetter.status == "OPEN"))
    if existing is not None: return _dead_response(existing)
    safe_details = details or {"attempts": run.attempts}
    row = DataIngestionDeadLetter(source_id=run.source_id, ingestion_run_id=run.id,
        evaluation_id=evaluation_id, operational_policy_version_id=policy.id,
        organization_id=run.organization_id, workspace_id=run.workspace_id, product_code=run.product_code,
        reason_code=reason_code[:120], error_category=error_category[:120],
        details_json=_canonical(safe_details), status="OPEN")
    session.add(row); session.flush()
    _audit(session, row, actor_id=None, event_type="data.ingestion_dead_letter.opened",
           detail=f"run_id={run.id}; reason_code={row.reason_code}")
    return _dead_response(row)


def _scoped_run(session: Session, *, source_id: uuid.UUID, run_id: uuid.UUID,
                organization_id: uuid.UUID, workspace_id: uuid.UUID, product_code: str):
    source = get_scoped_source(session, source_id=source_id, organization_id=organization_id,
                               workspace_id=workspace_id, product_code=product_code)
    run = session.scalar(select(DataIngestionRun).where(DataIngestionRun.id == run_id,
        DataIngestionRun.source_id == source.id, DataIngestionRun.organization_id == source.organization_id,
        DataIngestionRun.workspace_id == source.workspace_id, DataIngestionRun.product_code == source.product_code))
    if run is None: raise DataPlatformError("ingestion_run_not_accessible")
    return run


def get_ingestion_evaluation(session: Session, *, source_id: uuid.UUID, run_id: uuid.UUID,
        organization_id: uuid.UUID, workspace_id: uuid.UUID, product_code: str):
    run = _scoped_run(session, source_id=source_id, run_id=run_id, organization_id=organization_id,
                      workspace_id=workspace_id, product_code=product_code)
    row = session.scalar(select(DataIngestionEvaluation).where(DataIngestionEvaluation.ingestion_run_id == run.id))
    if row is None: raise DataPlatformError("ingestion_evaluation_not_accessible")
    return _evaluation_response(row)


def get_governed_ingestion_output(session: Session, *, source_id: uuid.UUID, run_id: uuid.UUID,
        organization_id: uuid.UUID, workspace_id: uuid.UUID, product_code: str):
    run = _scoped_run(session, source_id=source_id, run_id=run_id, organization_id=organization_id,
                      workspace_id=workspace_id, product_code=product_code)
    row = session.scalar(select(DataGovernedIngestionOutput).where(DataGovernedIngestionOutput.ingestion_run_id == run.id))
    if row is None: raise DataPlatformError("governed_ingestion_output_not_accessible")
    return _output_response(row)


def list_ingestion_dead_letters(session: Session, *, source_id: uuid.UUID, organization_id: uuid.UUID,
        workspace_id: uuid.UUID, product_code: str):
    source = get_scoped_source(session, source_id=source_id, organization_id=organization_id,
                               workspace_id=workspace_id, product_code=product_code)
    rows = session.scalars(select(DataIngestionDeadLetter).where(
        DataIngestionDeadLetter.source_id == source.id,
        DataIngestionDeadLetter.organization_id == source.organization_id,
        DataIngestionDeadLetter.workspace_id == source.workspace_id,
        DataIngestionDeadLetter.product_code == source.product_code,
    ).order_by(DataIngestionDeadLetter.created_at.desc(), DataIngestionDeadLetter.id)).all()
    return [_dead_response(row) for row in rows]


def requeue_ingestion_dead_letter(session: Session, storage, *, source_id: uuid.UUID,
        dead_letter_id: uuid.UUID, request, actor_id: uuid.UUID | None, backend: str):
    source = _locked_source(session, source_id=source_id, organization_id=request.organization_id,
                            workspace_id=request.workspace_id, product_code=request.product_code)
    row = session.scalar(select(DataIngestionDeadLetter).where(DataIngestionDeadLetter.id == dead_letter_id,
        DataIngestionDeadLetter.source_id == source.id).with_for_update())
    if row is None: raise DataPlatformError("ingestion_dead_letter_not_accessible")
    if row.status == "REQUEUED":
        replacement = session.scalar(select(DataIngestionRun).where(
            DataIngestionRun.id == row.replacement_run_id,
            DataIngestionRun.source_id == source.id,
            DataIngestionRun.organization_id == source.organization_id,
            DataIngestionRun.workspace_id == source.workspace_id,
            DataIngestionRun.product_code == source.product_code,
        )) if row.replacement_run_id is not None else None
        if (replacement is None or replacement.execution_mode != "REPLAY"
                or replacement.replay_of_run_id != row.ingestion_run_id
                or replacement.idempotency_key != request.idempotency_key):
            raise DataPlatformError("ingestion_dead_letter_state_conflict")
        return _dead_response(row)
    if row.status != "OPEN": raise DataPlatformError("ingestion_dead_letter_state_conflict")
    from src.platform.data.ingestion_run_service import create_replay_ingestion_run
    replacement = create_replay_ingestion_run(session, storage, source_id=source.id,
        run_id=row.ingestion_run_id, request=request, actor_id=actor_id, backend=backend)
    row.status = "REQUEUED"; row.replacement_run_id = replacement.run.id
    row.resolved_at = _utcnow(); row.resolver_membership_id = actor_id
    row.resolution_note = "Requeued through controlled replay."
    _audit(session, row, actor_id=actor_id, event_type="data.ingestion_dead_letter.requeued",
           detail=f"replacement_run_id={replacement.run.id}")
    session.flush(); return _dead_response(row)


def resolve_ingestion_dead_letter(session: Session, *, source_id: uuid.UUID,
        dead_letter_id: uuid.UUID, request: IngestionDeadLetterResolveRequest,
        actor_id: uuid.UUID | None):
    source = _locked_source(session, source_id=source_id, organization_id=request.organization_id,
                            workspace_id=request.workspace_id, product_code=request.product_code)
    row = session.scalar(select(DataIngestionDeadLetter).where(DataIngestionDeadLetter.id == dead_letter_id,
        DataIngestionDeadLetter.source_id == source.id).with_for_update())
    if row is None: raise DataPlatformError("ingestion_dead_letter_not_accessible")
    if row.status != "OPEN": raise DataPlatformError("ingestion_dead_letter_state_conflict")
    row.status = request.status; row.resolution_note = request.resolution_note.strip()
    row.resolver_membership_id = actor_id; row.resolved_at = _utcnow()
    _audit(session, row, actor_id=actor_id, event_type="data.ingestion_dead_letter.resolved",
           detail=f"status={row.status}")
    session.flush(); return _dead_response(row)
