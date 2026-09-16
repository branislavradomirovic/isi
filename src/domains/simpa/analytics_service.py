from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from pydantic import ValidationError

from src.domains.simpa.analytics_models import (
    SimpaAISynthesis,
    SimpaAnalyticsRun,
    SimpaIndicatorMethodology,
    SimpaIndicatorResult,
    SimpaMethodologyReferenceCase,
    SimpaMethodologyReferenceSuite,
    SimpaStatisticalModelContract,
    SimpaStatisticalModelResult,
)
from src.domains.simpa.methodology_contracts import (
    contract_fingerprint,
    normalize_draft_methodology_contract,
    normalize_methodology_contract,
)
from src.domains.simpa.reference_calculations import (
    REFERENCE_SUITE_SCHEMA_VERSION,
    ReferenceCalculationError,
    calculate_direct_observation,
    compare_direct_observation,
    normalize_direct_observation_expected,
    reference_case_fingerprint,
    reference_case_result_fingerprint,
    reference_suite_fingerprint,
    reference_suite_result_fingerprint,
)
from src.domains.simpa.statistical_contracts import (
    STATISTICAL_MODEL_CONTRACT_SCHEMA_VERSION,
    SimpaStatisticalModelContractV1,
    contract_fingerprint as statistical_contract_fingerprint,
    normalize_statistical_model_contract,
)
from src.domains.simpa.statistical_models import (
    STATISTICAL_MODEL_ENGINE_SCHEMA_VERSION,
    StatisticalModelError,
    normalize_result as normalize_statistical_result,
    result_fingerprint as statistical_result_fingerprint,
    run_statistical_model as execute_statistical_model,
)
from src.domains.simpa.models import SimpaIndicatorDefinition, SimpaMonitoringCycle
from src.platform.ai.models import AIJob
from src.platform.ai.service import create_ai_job
from src.platform.data.analytical_service import GovernedAnalyticalInput, load_governed_analytical_input
from src.platform.data.service import DataPlatformError
from src.platform.identity.models import Membership


class SimpaAnalyticsError(ValueError):
    pass


def _utcnow():
    return datetime.now(timezone.utc)


def _ratio(num: int, den: int) -> float:
    return round(float(num) / float(den), 6) if den else 0.0


def _require_actor(session: Session, actor_id: uuid.UUID | None) -> uuid.UUID:
    membership = session.get(Membership, actor_id) if actor_id is not None else None
    if membership is None or membership.status != "active":
        raise SimpaAnalyticsError("methodology_actor_required")
    return membership.id


def _sync_indicator_methodology_status(session: Session, indicator: SimpaIndicatorDefinition) -> str:
    statuses = set(
        session.scalars(
            select(SimpaIndicatorMethodology.status).where(SimpaIndicatorMethodology.indicator_id == indicator.id)
        ).all()
    )
    for status in ("validated", "proposed", "draft", "retired"):
        if status in statuses:
            indicator.methodology_status = status
            return status
    indicator.methodology_status = "conceptual"
    return "conceptual"


def _canonical_json(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _assert_draft_unit_matches_indicator(computation_spec: dict, indicator: SimpaIndicatorDefinition) -> None:
    unit = computation_spec.get("unit")
    if (
        isinstance(unit, str)
        and indicator.unit_hint.strip()
        and unit.casefold() != indicator.unit_hint.strip().casefold()
    ):
        raise SimpaAnalyticsError("methodology_contract_unit_mismatch")


def _load_input(
    session: Session, *, artifact_type: str, artifact_id: uuid.UUID, organization_id: uuid.UUID, workspace_id: uuid.UUID
) -> GovernedAnalyticalInput:
    try:
        return load_governed_analytical_input(
            session,
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code="SIMPA",
        )
    except DataPlatformError as exc:
        raise SimpaAnalyticsError(str(exc)) from None


def _analytical_source(value: GovernedAnalyticalInput) -> dict:
    return {
        "artifact_type": value.artifact_type,
        "artifact_id": str(value.artifact_id),
        "artifact_fingerprint": value.artifact_fingerprint,
        "dataset_contract_version_id": str(value.dataset_contract_version_id),
        "dataset_contract_fingerprint": value.dataset_contract_fingerprint,
        "analytical_quality_state": value.analytical_quality_state,
        "resolved_snapshot_id": str(value.snapshot_id),
        "resolved_snapshot_fingerprint": value.snapshot_fingerprint,
    }


def _validate_direct_observation_contract(value: GovernedAnalyticalInput, *, cycle: bool) -> None:
    fields = {str(item.get("field_key")): item for item in value.field_contract}
    expected = {
        "indicator_code": ("STRING", True),
        "quality_status": ("STRING", True),
        "value_numeric": ("NUMBER", False),
        "value_text": ("STRING", False),
    }
    for key, (logical_type, required) in expected.items():
        field = fields.get(key)
        if field is None or field.get("logical_type") != logical_type or bool(field.get("required")) != required:
            raise SimpaAnalyticsError("direct_observation_contract_invalid")
    field = fields.get("monitoring_cycle_id")
    if field is not None and (field.get("logical_type") != "STRING" or bool(field.get("required"))):
        raise SimpaAnalyticsError("direct_observation_contract_invalid")
    if cycle and field is None:
        raise SimpaAnalyticsError("direct_observation_cycle_contract_required")


def _records(value: GovernedAnalyticalInput, monitoring_cycle_id: uuid.UUID | None):
    _validate_direct_observation_contract(value, cycle=monitoring_cycle_id is not None)
    selected = []
    for record in value.records:
        quality = record.payload.get("quality_status")
        code = record.payload.get("indicator_code")
        if quality not in {"validated", "draft", "rejected"} or not isinstance(code, str) or not code.strip():
            raise SimpaAnalyticsError("direct_observation_record_invalid")
        if monitoring_cycle_id is not None and record.payload.get("monitoring_cycle_id") != str(monitoring_cycle_id):
            continue
        selected.append(record)
    return selected


def revalidate_analytics_run(
    session: Session, *, run: SimpaAnalyticsRun, organization_id: uuid.UUID, workspace_id: uuid.UUID
) -> GovernedAnalyticalInput:
    if run.status != "completed" or (run.organization_id, run.workspace_id) != (organization_id, workspace_id):
        raise SimpaAnalyticsError("analytics_run_not_accessible")
    if run.analytical_artifact_type == "ANALYTICAL_SNAPSHOT":
        artifact_type, artifact_id = "snapshot", run.analytical_snapshot_id
    elif run.analytical_artifact_type == "ANALYTICAL_FEATURE_VERSION":
        artifact_type, artifact_id = "feature_version", run.analytical_feature_version_id
    else:
        raise SimpaAnalyticsError("legacy_analytics_run_ineligible")
    if artifact_id is None:
        raise SimpaAnalyticsError("analytics_run_governed_binding_invalid")
    value = _load_input(
        session,
        artifact_type=artifact_type,
        artifact_id=artifact_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
    )
    if (
        run.analytical_artifact_fingerprint != value.artifact_fingerprint
        or run.dataset_contract_version_id != value.dataset_contract_version_id
        or run.dataset_contract_fingerprint != value.dataset_contract_fingerprint
        or run.analytical_quality_state != value.analytical_quality_state
        or (run.snapshot or {}).get("analytical_source") != _analytical_source(value)
    ):
        raise SimpaAnalyticsError("analytics_run_governed_binding_changed")
    return value


def _assert_cycle_scope(
    session: Session, *, cycle_id: uuid.UUID | None, organization_id: uuid.UUID, workspace_id: uuid.UUID
) -> None:
    if cycle_id is None:
        return
    cycle = session.scalar(
        select(SimpaMonitoringCycle).where(
            SimpaMonitoringCycle.id == cycle_id,
            SimpaMonitoringCycle.organization_id == organization_id,
            SimpaMonitoringCycle.workspace_id == workspace_id,
        )
    )
    if cycle is None:
        raise SimpaAnalyticsError("monitoring_cycle_not_accessible")


def build_monitoring_snapshot(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    analytical_artifact_type: str,
    analytical_artifact_id: uuid.UUID,
    monitoring_cycle_id: uuid.UUID | None = None,
) -> dict:
    _assert_cycle_scope(
        session, cycle_id=monitoring_cycle_id, organization_id=organization_id, workspace_id=workspace_id
    )
    analytical_input = _load_input(
        session,
        artifact_type=analytical_artifact_type,
        artifact_id=analytical_artifact_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
    )
    observations = _records(analytical_input, monitoring_cycle_id)
    active_indicators = list(
        session.scalars(select(SimpaIndicatorDefinition).where(SimpaIndicatorDefinition.active.is_(True))).all()
    )
    indicators_by_code = {row.code: row for row in active_indicators}
    for observation in observations:
        if observation.payload["indicator_code"] not in indicators_by_code:
            raise SimpaAnalyticsError("indicator_unknown")

    total = len(observations)
    validated = sum(1 for row in observations if row.payload["quality_status"] == "validated")
    draft = sum(1 for row in observations if row.payload["quality_status"] == "draft")
    rejected = sum(1 for row in observations if row.payload["quality_status"] == "rejected")
    provenance = total
    observed_indicator_ids = {indicators_by_code[str(row.payload["indicator_code"])].id for row in observations}
    conceptual = sum(1 for row in active_indicators if row.methodology_status == "conceptual")
    validated_methodology = sum(1 for row in active_indicators if row.methodology_status == "validated")

    validated_ratio = _ratio(validated, total)
    provenance_coverage = _ratio(provenance, total)
    indicator_coverage = _ratio(len(observed_indicator_ids), len(active_indicators))
    evidence_quality_score = round(
        (0.45 * validated_ratio) + (0.35 * provenance_coverage) + (0.20 * indicator_coverage), 6
    )
    if total == 0:
        quality_band = "no_evidence"
    elif evidence_quality_score < 0.50:
        quality_band = "weak"
    elif evidence_quality_score < 0.80:
        quality_band = "moderate"
    else:
        quality_band = "strong"

    return {
        "analytical_source": _analytical_source(analytical_input),
        "scope": {
            "organization_id": str(organization_id),
            "workspace_id": str(workspace_id),
            "monitoring_cycle_id": str(monitoring_cycle_id) if monitoring_cycle_id else None,
        },
        "observation_count": total,
        "validated_observation_count": validated,
        "draft_observation_count": draft,
        "rejected_observation_count": rejected,
        "active_indicator_count": len(active_indicators),
        "observed_indicator_count": len(observed_indicator_ids),
        "conceptual_indicator_count": conceptual,
        "validated_methodology_indicator_count": validated_methodology,
        "validated_observation_ratio": validated_ratio,
        "provenance_coverage": provenance_coverage,
        "indicator_coverage": indicator_coverage,
        "evidence_quality_score": evidence_quality_score,
        "evidence_quality_band": quality_band,
        "semantic_notice": "This score measures evidence quality and coverage only; it is not a social-risk or policy-outcome score.",
    }


def create_analytics_run(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    analytical_artifact_type: str,
    analytical_artifact_id: uuid.UUID,
    monitoring_cycle_id: uuid.UUID | None,
    actor_id: uuid.UUID | None,
) -> SimpaAnalyticsRun:
    snapshot = build_monitoring_snapshot(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
        analytical_artifact_type=analytical_artifact_type,
        analytical_artifact_id=analytical_artifact_id,
        monitoring_cycle_id=monitoring_cycle_id,
    )
    source = snapshot["analytical_source"]
    row = SimpaAnalyticsRun(
        organization_id=organization_id,
        workspace_id=workspace_id,
        monitoring_cycle_id=monitoring_cycle_id,
        analytical_artifact_type=(
            "ANALYTICAL_SNAPSHOT" if analytical_artifact_type == "snapshot" else "ANALYTICAL_FEATURE_VERSION"
        ),
        analytical_snapshot_id=analytical_artifact_id if analytical_artifact_type == "snapshot" else None,
        analytical_feature_version_id=analytical_artifact_id if analytical_artifact_type == "feature_version" else None,
        analytical_artifact_fingerprint=source["artifact_fingerprint"],
        dataset_contract_version_id=uuid.UUID(source["dataset_contract_version_id"]),
        dataset_contract_fingerprint=source["dataset_contract_fingerprint"],
        analytical_quality_state=source["analytical_quality_state"],
        status="completed",
        snapshot=snapshot,
        evidence_quality_score=snapshot["evidence_quality_score"],
        validated_observation_ratio=snapshot["validated_observation_ratio"],
        provenance_coverage=snapshot["provenance_coverage"],
        indicator_coverage=snapshot["indicator_coverage"],
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    return row


def list_analytics_runs(
    session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, limit: int = 50
) -> list[SimpaAnalyticsRun]:
    return list(
        session.scalars(
            select(SimpaAnalyticsRun)
            .where(SimpaAnalyticsRun.organization_id == organization_id, SimpaAnalyticsRun.workspace_id == workspace_id)
            .order_by(SimpaAnalyticsRun.created_at.desc())
            .limit(max(1, min(limit, 100)))
        ).all()
    )


def list_methodologies(session: Session) -> list[tuple[SimpaIndicatorMethodology, SimpaIndicatorDefinition]]:
    return list(
        session.execute(
            select(SimpaIndicatorMethodology, SimpaIndicatorDefinition)
            .join(SimpaIndicatorDefinition, SimpaIndicatorDefinition.id == SimpaIndicatorMethodology.indicator_id)
            .order_by(SimpaIndicatorDefinition.code, SimpaIndicatorMethodology.version_no.desc())
        ).all()
    )


def create_methodology(
    session: Session,
    *,
    indicator_code: str,
    computation_type: str,
    methodology_note: str,
    source_requirements: dict,
    actor_id: uuid.UUID | None,
    computation_spec: dict | None = None,
) -> SimpaIndicatorMethodology:
    indicator = session.scalar(
        select(SimpaIndicatorDefinition).where(
            SimpaIndicatorDefinition.code == indicator_code, SimpaIndicatorDefinition.active.is_(True)
        )
    )
    if indicator is None:
        raise SimpaAnalyticsError("indicator_unknown")
    if computation_type != "direct_observation":
        raise SimpaAnalyticsError("unsupported_computation_type")
    latest = session.scalar(
        select(func.max(SimpaIndicatorMethodology.version_no)).where(
            SimpaIndicatorMethodology.indicator_id == indicator.id
        )
    )
    try:
        raw_spec = normalize_draft_methodology_contract(dict(computation_spec or {}))
    except ValueError as exc:
        raise SimpaAnalyticsError("methodology_contract_invalid") from exc
    _assert_draft_unit_matches_indicator(raw_spec, indicator)
    fingerprint = ""
    if raw_spec:
        try:
            contract = normalize_methodology_contract(raw_spec, indicator_unit_hint=indicator.unit_hint)
        except (ValidationError, ValueError):
            # Drafts may be incomplete. Proposal is the strict production gate.
            pass
        else:
            raw_spec = contract.model_dump(mode="json")
            fingerprint = contract_fingerprint(contract)
    row = SimpaIndicatorMethodology(
        indicator_id=indicator.id,
        version_no=int(latest or 0) + 1,
        status="draft",
        computation_type=computation_type,
        computation_spec=raw_spec,
        contract_fingerprint=fingerprint,
        source_requirements=source_requirements,
        methodology_note=methodology_note.strip(),
        reference_check_status="not_run",
        reference_check_fingerprint="",
        reference_check_detail={},
        reference_evidence_mode="suite_v1",
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    _sync_indicator_methodology_status(session, indicator)
    session.flush()
    return row


def set_methodology_contract(
    session: Session, *, methodology_id: uuid.UUID, computation_spec: dict
) -> SimpaIndicatorMethodology:
    row = session.get(SimpaIndicatorMethodology, methodology_id)
    if row is None:
        raise SimpaAnalyticsError("methodology_not_found")
    indicator = session.get(SimpaIndicatorDefinition, row.indicator_id)
    if indicator is None or not indicator.active:
        raise SimpaAnalyticsError("indicator_unknown")
    if row.status != "draft":
        raise SimpaAnalyticsError("methodology_contract_immutable")
    try:
        draft_contract = normalize_draft_methodology_contract(computation_spec)
    except ValueError as exc:
        raise SimpaAnalyticsError("methodology_contract_invalid") from exc
    _assert_draft_unit_matches_indicator(draft_contract, indicator)
    row.computation_spec = draft_contract
    row.contract_fingerprint = ""
    try:
        contract = normalize_methodology_contract(draft_contract, indicator_unit_hint=indicator.unit_hint)
    except (ValidationError, ValueError):
        pass
    else:
        row.computation_spec = contract.model_dump(mode="json")
        row.contract_fingerprint = contract_fingerprint(contract)
        row.computation_type = contract.computation_type
    row.reference_check_status = "not_run"
    row.reference_check_fingerprint = ""
    row.reference_check_detail = {}
    session.flush()
    return row


def propose_methodology(
    session: Session, *, methodology_id: uuid.UUID, actor_id: uuid.UUID | None
) -> SimpaIndicatorMethodology:
    actor = _require_actor(session, actor_id)
    row = session.get(SimpaIndicatorMethodology, methodology_id)
    if row is None:
        raise SimpaAnalyticsError("methodology_not_found")
    if row.status != "draft":
        raise SimpaAnalyticsError("methodology_transition_forbidden")
    indicator = session.get(SimpaIndicatorDefinition, row.indicator_id)
    if indicator is None or not indicator.active:
        raise SimpaAnalyticsError("indicator_unknown")
    try:
        contract = normalize_methodology_contract(row.computation_spec, indicator_unit_hint=indicator.unit_hint)
    except (ValidationError, ValueError) as exc:
        raise SimpaAnalyticsError("methodology_contract_invalid") from exc
    row.computation_spec = contract.model_dump(mode="json")
    row.contract_fingerprint = contract_fingerprint(contract)
    row.computation_type = contract.computation_type
    row.status = "proposed"
    row.proposed_by_membership_id = actor
    row.proposed_at = _utcnow()
    row.reference_check_status = "not_run"
    row.reference_check_fingerprint = ""
    row.reference_check_detail = {}
    session.flush()
    _sync_indicator_methodology_status(session, indicator)
    session.flush()
    return row


def _intact_proposed_contract(
    session: Session, row: SimpaIndicatorMethodology
) -> tuple[SimpaIndicatorDefinition, object]:
    if row.status != "proposed":
        raise SimpaAnalyticsError("methodology_not_proposed")
    if row.reference_evidence_mode != "suite_v1":
        raise SimpaAnalyticsError("methodology_reference_suite_not_allowed")
    indicator = session.get(SimpaIndicatorDefinition, row.indicator_id)
    if indicator is None or not indicator.active:
        raise SimpaAnalyticsError("indicator_unknown")
    try:
        contract = normalize_methodology_contract(row.computation_spec, indicator_unit_hint=indicator.unit_hint)
    except (ValidationError, ValueError) as exc:
        raise SimpaAnalyticsError("methodology_contract_invalid") from exc
    if row.contract_fingerprint != contract_fingerprint(contract):
        raise SimpaAnalyticsError("methodology_contract_fingerprint_mismatch")
    return indicator, contract


def _normalized_case(*, case: dict, indicator_code: str) -> tuple[str, dict, dict, str]:
    if not isinstance(case, dict):
        raise SimpaAnalyticsError("reference_case_invalid")
    if set(case) != {"case_key", "reference_record", "expected_result"}:
        raise SimpaAnalyticsError("reference_case_invalid")
    key = case.get("case_key")
    if not isinstance(key, str) or not key.strip() or len(key.strip()) > 255:
        raise SimpaAnalyticsError("reference_case_key_required")
    record = case.get("reference_record")
    expected = case.get("expected_result")
    if not isinstance(record, dict) or not isinstance(expected, dict):
        raise SimpaAnalyticsError("reference_case_invalid")
    if set(record) - {"indicator_code", "quality_status", "value_numeric", "value_text"}:
        raise SimpaAnalyticsError("reference_case_invalid")
    if set(expected) - {"value_numeric", "value_text"}:
        raise SimpaAnalyticsError("reference_case_invalid")
    try:
        actual = calculate_direct_observation(record, indicator_code=indicator_code)
        normalized_expected = normalize_direct_observation_expected(
            expected.get("value_numeric"), expected.get("value_text")
        )
        normalized_record = {
            "indicator_code": indicator_code,
            "quality_status": "validated",
            **actual,
        }
        fingerprint = reference_case_fingerprint(
            case_key=key,
            indicator_code=indicator_code,
            reference_record=normalized_record,
            expected_result=normalized_expected,
        )
    except ReferenceCalculationError as exc:
        raise SimpaAnalyticsError(str(exc)) from None
    return key.strip(), normalized_record, normalized_expected, fingerprint


def create_methodology_reference_suite(
    session: Session,
    *,
    methodology_id: uuid.UUID,
    reference_dataset_version: str,
    cases: list[dict],
    actor_id: uuid.UUID | None,
) -> SimpaMethodologyReferenceSuite:
    actor = _require_actor(session, actor_id)
    methodology = session.get(SimpaIndicatorMethodology, methodology_id)
    if methodology is None:
        raise SimpaAnalyticsError("methodology_not_found")
    indicator, contract = _intact_proposed_contract(session, methodology)
    if not isinstance(reference_dataset_version, str):
        raise SimpaAnalyticsError("reference_dataset_version_required")
    dataset_version = reference_dataset_version.strip()
    if not dataset_version or len(dataset_version) > 255:
        raise SimpaAnalyticsError("reference_dataset_version_required")
    if not isinstance(cases, list) or not cases:
        raise SimpaAnalyticsError("reference_suite_cases_required")
    passed = session.scalar(
        select(SimpaMethodologyReferenceSuite.id).where(
            SimpaMethodologyReferenceSuite.methodology_id == methodology.id,
            SimpaMethodologyReferenceSuite.status == "passed",
        )
    )
    if passed is not None:
        raise SimpaAnalyticsError("methodology_reference_suite_already_passed")

    normalized = [_normalized_case(case=case, indicator_code=indicator.code) for case in cases]
    normalized.sort(key=lambda item: item[0])
    keys = [item[0] for item in normalized]
    if len(keys) != len(set(keys)):
        raise SimpaAnalyticsError("reference_case_keys_invalid")
    semantic_cases = [
        {"case_key": case_key, "case_fingerprint": fingerprint}
        for case_key, _record, _expected, fingerprint in normalized
    ]
    try:
        suite_fingerprint = reference_suite_fingerprint(
            methodology_contract_fingerprint=methodology.contract_fingerprint,
            reference_dataset=contract.reference_dataset,
            reference_dataset_version=dataset_version,
            cases=semantic_cases,
        )
    except ReferenceCalculationError as exc:
        raise SimpaAnalyticsError(str(exc)) from None
    latest = session.scalar(
        select(func.max(SimpaMethodologyReferenceSuite.version_no)).where(
            SimpaMethodologyReferenceSuite.methodology_id == methodology.id
        )
    )
    suite = SimpaMethodologyReferenceSuite(
        methodology_id=methodology.id,
        version_no=int(latest or 0) + 1,
        schema_version=REFERENCE_SUITE_SCHEMA_VERSION,
        methodology_contract_fingerprint=methodology.contract_fingerprint,
        reference_dataset=contract.reference_dataset,
        reference_dataset_version=dataset_version,
        suite_fingerprint=suite_fingerprint,
        case_count=len(normalized),
        status="not_run",
        result_fingerprint="",
        result_detail={},
        created_by_membership_id=actor,
    )
    session.add(suite)
    session.flush()
    for index, (case_key, record, expected, fingerprint) in enumerate(normalized):
        session.add(
            SimpaMethodologyReferenceCase(
                suite_id=suite.id,
                case_key=case_key,
                case_index=index,
                reference_record=record,
                expected_result=expected,
                case_fingerprint=fingerprint,
                status="not_run",
                result_fingerprint="",
                result_detail={},
            )
        )
    session.flush()
    return suite


def list_methodology_reference_suites(
    session: Session, *, methodology_id: uuid.UUID
) -> list[tuple[SimpaMethodologyReferenceSuite, list[SimpaMethodologyReferenceCase]]]:
    suites = list(
        session.scalars(
            select(SimpaMethodologyReferenceSuite)
            .where(SimpaMethodologyReferenceSuite.methodology_id == methodology_id)
            .order_by(SimpaMethodologyReferenceSuite.version_no.desc())
        ).all()
    )
    result = []
    for suite in suites:
        cases = list(
            session.scalars(
                select(SimpaMethodologyReferenceCase)
                .where(SimpaMethodologyReferenceCase.suite_id == suite.id)
                .order_by(SimpaMethodologyReferenceCase.case_index)
            ).all()
        )
        result.append((suite, cases))
    return result


def _expected_case_result_detail(
    *,
    suite: SimpaMethodologyReferenceSuite,
    case: SimpaMethodologyReferenceCase,
    indicator_code: str,
    accepted_tolerance: float,
) -> dict:
    try:
        actual = calculate_direct_observation(case.reference_record, indicator_code=indicator_code)
        comparison = compare_direct_observation(
            actual,
            case.expected_result,
            accepted_tolerance=accepted_tolerance,
        )
    except ReferenceCalculationError as exc:
        raise SimpaAnalyticsError(str(exc)) from None
    return {
        "schema_version": REFERENCE_SUITE_SCHEMA_VERSION,
        "suite_fingerprint": suite.suite_fingerprint,
        "case_key": case.case_key,
        "case_fingerprint": case.case_fingerprint,
        **comparison,
    }


def _verify_suite_semantics(
    methodology: SimpaIndicatorMethodology,
    indicator: SimpaIndicatorDefinition,
    contract,
    suite: SimpaMethodologyReferenceSuite,
    cases: list[SimpaMethodologyReferenceCase],
) -> None:
    if (
        suite.schema_version != REFERENCE_SUITE_SCHEMA_VERSION
        or suite.methodology_id != methodology.id
        or suite.methodology_contract_fingerprint != methodology.contract_fingerprint
        or suite.reference_dataset != contract.reference_dataset
        or not suite.reference_dataset_version.strip()
        or suite.case_count != len(cases)
        or not cases
        or [case.case_index for case in cases] != list(range(len(cases)))
    ):
        raise SimpaAnalyticsError("methodology_reference_suite_evidence_invalid")
    semantic_cases = []
    for case in cases:
        try:
            expected_fingerprint = reference_case_fingerprint(
                case_key=case.case_key,
                indicator_code=indicator.code,
                reference_record=case.reference_record,
                expected_result=case.expected_result,
            )
        except ReferenceCalculationError:
            raise SimpaAnalyticsError("methodology_reference_suite_evidence_invalid") from None
        if case.case_fingerprint != expected_fingerprint:
            raise SimpaAnalyticsError("methodology_reference_suite_evidence_invalid")
        semantic_cases.append({"case_key": case.case_key, "case_fingerprint": case.case_fingerprint})
    try:
        expected_suite_fingerprint = reference_suite_fingerprint(
            methodology_contract_fingerprint=methodology.contract_fingerprint,
            reference_dataset=contract.reference_dataset,
            reference_dataset_version=suite.reference_dataset_version,
            cases=semantic_cases,
        )
    except ReferenceCalculationError:
        raise SimpaAnalyticsError("methodology_reference_suite_evidence_invalid") from None
    if suite.suite_fingerprint != expected_suite_fingerprint:
        raise SimpaAnalyticsError("methodology_reference_suite_evidence_invalid")


def run_methodology_reference_suite(
    session: Session,
    *,
    methodology_id: uuid.UUID,
    suite_id: uuid.UUID,
    actor_id: uuid.UUID | None,
) -> SimpaMethodologyReferenceSuite:
    actor = _require_actor(session, actor_id)
    methodology = session.get(SimpaIndicatorMethodology, methodology_id)
    if methodology is None:
        raise SimpaAnalyticsError("methodology_not_found")
    indicator, contract = _intact_proposed_contract(session, methodology)
    suite = session.scalar(
        select(SimpaMethodologyReferenceSuite).where(
            SimpaMethodologyReferenceSuite.id == suite_id,
            SimpaMethodologyReferenceSuite.methodology_id == methodology.id,
        )
    )
    if suite is None:
        raise SimpaAnalyticsError("methodology_reference_suite_not_found")
    if suite.status != "not_run":
        raise SimpaAnalyticsError("methodology_reference_suite_terminal")
    cases = list_methodology_reference_suites(session, methodology_id=methodology.id)
    case_rows = next(items for candidate, items in cases if candidate.id == suite.id)
    _verify_suite_semantics(methodology, indicator, contract, suite, case_rows)

    case_results = []
    for case in case_rows:
        detail = _expected_case_result_detail(
            suite=suite,
            case=case,
            indicator_code=indicator.code,
            accepted_tolerance=contract.accepted_tolerance,
        )
        case.status = "passed" if detail["passed"] else "failed"
        case.result_detail = detail
        case.result_fingerprint = reference_case_result_fingerprint(detail)
        case_results.append(
            {
                "case_key": case.case_key,
                "status": case.status,
                "result_fingerprint": case.result_fingerprint,
            }
        )
    passed = all(case.status == "passed" for case in case_rows)
    suite_detail = {
        "schema_version": REFERENCE_SUITE_SCHEMA_VERSION,
        "suite_fingerprint": suite.suite_fingerprint,
        "methodology_contract_fingerprint": methodology.contract_fingerprint,
        "case_count": len(case_rows),
        "case_results": case_results,
        "passed": passed,
    }
    suite.status = "passed" if passed else "failed"
    suite.result_detail = suite_detail
    suite.result_fingerprint = reference_suite_result_fingerprint(suite_detail)
    suite.executed_by_membership_id = actor
    suite.executed_at = _utcnow()
    methodology.reference_check_status = suite.status
    methodology.reference_check_fingerprint = suite.result_fingerprint
    methodology.reference_check_detail = {
        "reference_evidence_mode": "suite_v1",
        "suite_id": str(suite.id),
        "suite_version_no": suite.version_no,
        "suite_fingerprint": suite.suite_fingerprint,
        "result_fingerprint": suite.result_fingerprint,
        "case_count": suite.case_count,
        "passed": passed,
    }
    session.flush()
    return suite


def _verify_passed_suite(
    session: Session,
    *,
    methodology: SimpaIndicatorMethodology,
    indicator: SimpaIndicatorDefinition,
    contract,
) -> SimpaMethodologyReferenceSuite:
    passed_suites = list(
        session.scalars(
            select(SimpaMethodologyReferenceSuite).where(
                SimpaMethodologyReferenceSuite.methodology_id == methodology.id,
                SimpaMethodologyReferenceSuite.status == "passed",
            )
        ).all()
    )
    if len(passed_suites) != 1:
        raise SimpaAnalyticsError("methodology_reference_suite_required")
    suite = passed_suites[0]
    all_suites = list_methodology_reference_suites(session, methodology_id=methodology.id)
    cases = next(items for candidate, items in all_suites if candidate.id == suite.id)
    _verify_suite_semantics(methodology, indicator, contract, suite, cases)
    case_results = []
    for case in cases:
        detail = _expected_case_result_detail(
            suite=suite,
            case=case,
            indicator_code=indicator.code,
            accepted_tolerance=contract.accepted_tolerance,
        )
        fingerprint = reference_case_result_fingerprint(detail)
        expected_status = "passed" if detail["passed"] else "failed"
        if (
            expected_status != "passed"
            or case.status != expected_status
            or case.result_detail != detail
            or case.result_fingerprint != fingerprint
        ):
            raise SimpaAnalyticsError("methodology_reference_suite_evidence_invalid")
        case_results.append({"case_key": case.case_key, "status": case.status, "result_fingerprint": fingerprint})
    suite_detail = {
        "schema_version": REFERENCE_SUITE_SCHEMA_VERSION,
        "suite_fingerprint": suite.suite_fingerprint,
        "methodology_contract_fingerprint": methodology.contract_fingerprint,
        "case_count": len(cases),
        "case_results": case_results,
        "passed": True,
    }
    if (
        suite.result_detail != suite_detail
        or suite.result_fingerprint != reference_suite_result_fingerprint(suite_detail)
        or methodology.reference_check_status != "passed"
        or methodology.reference_check_fingerprint != suite.result_fingerprint
    ):
        raise SimpaAnalyticsError("methodology_reference_suite_evidence_invalid")
    return suite


def run_methodology_reference_check(
    session: Session,
    *,
    methodology_id: uuid.UUID,
    reference_record: dict,
    expected_result: dict,
) -> SimpaIndicatorMethodology:
    row = session.get(SimpaIndicatorMethodology, methodology_id)
    if row is None:
        raise SimpaAnalyticsError("methodology_not_found")
    if row.reference_evidence_mode != "legacy_inline":
        raise SimpaAnalyticsError("methodology_reference_suite_required")
    if row.status != "proposed":
        raise SimpaAnalyticsError("methodology_not_proposed")
    if row.reference_check_status == "failed":
        raise SimpaAnalyticsError("methodology_reference_check_failed")
    if row.reference_check_status == "passed":
        raise SimpaAnalyticsError("methodology_reference_check_already_run")
    indicator = session.get(SimpaIndicatorDefinition, row.indicator_id)
    if indicator is None or not indicator.active:
        raise SimpaAnalyticsError("indicator_unknown")
    try:
        contract = normalize_methodology_contract(row.computation_spec, indicator_unit_hint=indicator.unit_hint)
    except (ValidationError, ValueError) as exc:
        raise SimpaAnalyticsError("methodology_contract_invalid") from exc
    fresh_fingerprint = contract_fingerprint(contract)
    if row.contract_fingerprint != fresh_fingerprint:
        raise SimpaAnalyticsError("methodology_contract_fingerprint_mismatch")
    try:
        actual = calculate_direct_observation(reference_record, indicator_code=indicator.code)
        comparison_detail = compare_direct_observation(
            actual,
            expected_result,
            accepted_tolerance=contract.accepted_tolerance,
        )
    except ReferenceCalculationError as exc:
        raise SimpaAnalyticsError(str(exc)) from None
    passed = bool(comparison_detail["passed"])
    detail = {
        "schema_version": contract.schema_version,
        "computation_type": contract.computation_type,
        "contract_fingerprint": fresh_fingerprint,
        "indicator_code": indicator.code,
        "quality_status": "validated",
        "actual": comparison_detail["actual"],
        "expected": comparison_detail["expected"],
        "accepted_tolerance": comparison_detail["accepted_tolerance"],
        "comparison": comparison_detail["comparison"],
        "passed": passed,
    }
    row.reference_check_status = "passed" if passed else "failed"
    row.reference_check_fingerprint = hashlib.sha256(_canonical_json(detail).encode("utf-8")).hexdigest()
    row.reference_check_detail = detail
    session.flush()
    return row


def validate_methodology(
    session: Session, *, methodology_id: uuid.UUID, validation_note: str, actor_id: uuid.UUID | None
) -> SimpaIndicatorMethodology:
    actor = _require_actor(session, actor_id)
    row = session.get(SimpaIndicatorMethodology, methodology_id)
    if row is None:
        raise SimpaAnalyticsError("methodology_not_found")
    indicator = session.get(SimpaIndicatorDefinition, row.indicator_id)
    if indicator is None or not indicator.active:
        raise SimpaAnalyticsError("indicator_unknown")
    if row.status != "proposed":
        raise SimpaAnalyticsError("methodology_transition_forbidden")
    note = validation_note.strip()
    if not note:
        raise SimpaAnalyticsError("validation_note_required")
    try:
        contract = normalize_methodology_contract(row.computation_spec, indicator_unit_hint=indicator.unit_hint)
    except (ValidationError, ValueError) as exc:
        raise SimpaAnalyticsError("methodology_contract_invalid") from exc
    if row.contract_fingerprint != contract_fingerprint(contract):
        raise SimpaAnalyticsError("methodology_contract_fingerprint_mismatch")
    if row.reference_evidence_mode == "suite_v1":
        _verify_passed_suite(
            session,
            methodology=row,
            indicator=indicator,
            contract=contract,
        )
    elif row.reference_evidence_mode == "legacy_inline":
        detail = row.reference_check_detail if isinstance(row.reference_check_detail, dict) else {}
        expected_reference_fingerprint = hashlib.sha256(_canonical_json(detail).encode("utf-8")).hexdigest()
        if (
            row.reference_check_status != "passed"
            or detail.get("passed") is not True
            or detail.get("contract_fingerprint") != row.contract_fingerprint
            or row.reference_check_fingerprint != expected_reference_fingerprint
        ):
            raise SimpaAnalyticsError("methodology_reference_check_required")
    else:
        raise SimpaAnalyticsError("methodology_reference_evidence_mode_ineligible")
    for other in session.scalars(
        select(SimpaIndicatorMethodology).where(
            SimpaIndicatorMethodology.indicator_id == row.indicator_id,
            SimpaIndicatorMethodology.status == "validated",
            SimpaIndicatorMethodology.id != row.id,
        )
    ).all():
        other.status = "retired"
        other.retired_by_membership_id = actor
        other.retired_at = _utcnow()
        other.retirement_note = f"Superseded by validated methodology version {row.version_no}."
    row.status = "validated"
    row.validation_note = note
    row.approved_by_membership_id = actor
    row.approved_at = _utcnow()
    indicator.methodology_note = row.methodology_note
    session.flush()
    _sync_indicator_methodology_status(session, indicator)
    session.flush()
    return row


def retire_methodology(
    session: Session,
    *,
    methodology_id: uuid.UUID,
    retirement_note: str,
    actor_id: uuid.UUID | None,
) -> SimpaIndicatorMethodology:
    actor = _require_actor(session, actor_id)
    row = session.get(SimpaIndicatorMethodology, methodology_id)
    if row is None:
        raise SimpaAnalyticsError("methodology_not_found")
    if row.status not in {"draft", "proposed", "validated"}:
        raise SimpaAnalyticsError("methodology_transition_forbidden")
    note = retirement_note.strip()
    if not note:
        raise SimpaAnalyticsError("retirement_note_required")
    indicator = session.get(SimpaIndicatorDefinition, row.indicator_id)
    if indicator is None:
        raise SimpaAnalyticsError("indicator_unknown")
    row.status = "retired"
    row.retired_by_membership_id = actor
    row.retired_at = _utcnow()
    row.retirement_note = note
    session.flush()
    _sync_indicator_methodology_status(session, indicator)
    session.flush()
    return row


def compute_indicator(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    indicator_code: str,
    monitoring_cycle_id: uuid.UUID | None,
    analytics_run_id: uuid.UUID,
    actor_id: uuid.UUID | None,
) -> SimpaIndicatorResult:
    _assert_cycle_scope(
        session, cycle_id=monitoring_cycle_id, organization_id=organization_id, workspace_id=workspace_id
    )
    indicator = session.scalar(
        select(SimpaIndicatorDefinition).where(
            SimpaIndicatorDefinition.code == indicator_code, SimpaIndicatorDefinition.active.is_(True)
        )
    )
    if indicator is None:
        raise SimpaAnalyticsError("indicator_unknown")
    if indicator.methodology_status != "validated":
        raise SimpaAnalyticsError("methodology_not_validated")
    methodology = session.scalar(
        select(SimpaIndicatorMethodology)
        .where(SimpaIndicatorMethodology.indicator_id == indicator.id, SimpaIndicatorMethodology.status == "validated")
        .order_by(SimpaIndicatorMethodology.version_no.desc())
    )
    if methodology is None:
        raise SimpaAnalyticsError("methodology_not_validated")
    if methodology.computation_type != "direct_observation":
        raise SimpaAnalyticsError("unsupported_computation_type")
    if methodology.contract_fingerprint:
        try:
            production_contract = normalize_methodology_contract(
                methodology.computation_spec, indicator_unit_hint=indicator.unit_hint
            )
        except (ValidationError, ValueError) as exc:
            raise SimpaAnalyticsError("methodology_contract_invalid") from exc
        if methodology.contract_fingerprint != contract_fingerprint(production_contract):
            raise SimpaAnalyticsError("methodology_contract_fingerprint_mismatch")
    run = session.scalar(
        select(SimpaAnalyticsRun).where(
            SimpaAnalyticsRun.id == analytics_run_id,
            SimpaAnalyticsRun.organization_id == organization_id,
            SimpaAnalyticsRun.workspace_id == workspace_id,
        )
    )
    if run is None:
        raise SimpaAnalyticsError("analytics_run_not_accessible")
    if monitoring_cycle_id != run.monitoring_cycle_id:
        raise SimpaAnalyticsError("monitoring_cycle_run_mismatch")
    analytical_input = revalidate_analytics_run(
        session, run=run, organization_id=organization_id, workspace_id=workspace_id
    )
    matches = [
        row
        for row in _records(analytical_input, monitoring_cycle_id)
        if row.payload["indicator_code"] == indicator.code and row.payload["quality_status"] == "validated"
    ]
    if not matches:
        raise SimpaAnalyticsError("validated_observation_required")
    if len(matches) > 1:
        raise SimpaAnalyticsError("validated_observation_ambiguous")
    observation = matches[0]
    try:
        calculated = calculate_direct_observation(observation.payload, indicator_code=indicator.code)
    except ReferenceCalculationError as exc:
        raise SimpaAnalyticsError(str(exc)) from None
    result = SimpaIndicatorResult(
        organization_id=organization_id,
        workspace_id=workspace_id,
        analytics_run_id=analytics_run_id,
        indicator_id=indicator.id,
        methodology_id=methodology.id,
        value_numeric=calculated["value_numeric"],
        value_text=str(calculated["value_text"] or ""),
        unit=indicator.unit_hint,
        quality_score=1.0,
        source_observation_ids=[],
        computation_trace={
            "type": "direct_observation",
            "artifact_type": analytical_input.artifact_type,
            "artifact_id": str(analytical_input.artifact_id),
            "artifact_fingerprint": analytical_input.artifact_fingerprint,
            "dataset_contract_fingerprint": analytical_input.dataset_contract_fingerprint,
            "normalized_record_id": str(observation.normalized_record_id),
            "identity_fingerprint": observation.identity_fingerprint,
            "content_fingerprint": observation.content_fingerprint,
            "methodology_version": methodology.version_no,
            "methodology_contract_fingerprint": methodology.contract_fingerprint,
            "analytical_quality_state": analytical_input.analytical_quality_state,
            "observation_quality": "validated",
            "provenance_present": True,
        },
        status="computed",
        created_by_membership_id=actor_id,
    )
    session.add(result)
    session.flush()
    return result


def _require_statistical_actor(session: Session, actor_id: uuid.UUID | None) -> uuid.UUID:
    membership = session.get(Membership, actor_id) if actor_id is not None else None
    if membership is None or membership.status != "active":
        raise SimpaAnalyticsError("statistical_model_actor_required")
    return membership.id


def _current_validated_target_methodology(
    session: Session, *, indicator_code: str
) -> tuple[SimpaIndicatorDefinition, SimpaIndicatorMethodology]:
    code = indicator_code.strip().casefold()
    indicator = session.scalar(
        select(SimpaIndicatorDefinition).where(
            func.lower(SimpaIndicatorDefinition.code) == code,
            SimpaIndicatorDefinition.active.is_(True),
        )
    )
    if indicator is None:
        raise SimpaAnalyticsError("statistical_model_target_not_found")
    methodologies = list(
        session.scalars(
            select(SimpaIndicatorMethodology)
            .where(
                SimpaIndicatorMethodology.indicator_id == indicator.id,
                SimpaIndicatorMethodology.status == "validated",
            )
            .order_by(SimpaIndicatorMethodology.version_no.desc())
        ).all()
    )
    if indicator.methodology_status != "validated" or len(methodologies) != 1:
        raise SimpaAnalyticsError("statistical_model_target_methodology_not_validated")
    methodology = methodologies[0]
    try:
        target_contract = normalize_methodology_contract(
            methodology.computation_spec,
            indicator_unit_hint=indicator.unit_hint,
        )
    except (ValidationError, ValueError) as exc:
        raise SimpaAnalyticsError("statistical_model_target_methodology_invalid") from exc
    if (
        len(methodology.contract_fingerprint) != 64
        or methodology.contract_fingerprint != contract_fingerprint(target_contract)
    ):
        raise SimpaAnalyticsError("statistical_model_target_methodology_invalid")
    return indicator, methodology


def _verified_statistical_contract(
    session: Session,
    *,
    contract_id: uuid.UUID,
    require_current_target: bool = True,
) -> tuple[
    SimpaStatisticalModelContract,
    SimpaIndicatorDefinition,
    SimpaIndicatorMethodology,
    SimpaStatisticalModelContractV1,
]:
    row = session.get(SimpaStatisticalModelContract, contract_id)
    if row is None:
        raise SimpaAnalyticsError("statistical_model_contract_not_found")
    indicator = session.get(SimpaIndicatorDefinition, row.target_indicator_id)
    methodology = session.get(SimpaIndicatorMethodology, row.target_methodology_id)
    if indicator is None or methodology is None:
        raise SimpaAnalyticsError("statistical_model_contract_binding_invalid")
    try:
        contract = normalize_statistical_model_contract(row.contract_json)
    except (ValidationError, ValueError) as exc:
        raise SimpaAnalyticsError("statistical_model_contract_invalid") from exc
    fingerprint = statistical_contract_fingerprint(contract)
    if (
        contract.target_indicator_code != indicator.code.strip().casefold()
        or contract.target_methodology_id != methodology.id
        or contract.target_methodology_version != methodology.version_no
        or contract.target_methodology_contract_fingerprint != row.target_methodology_contract_fingerprint
        or methodology.contract_fingerprint != row.target_methodology_contract_fingerprint
        or row.analysis_key != contract.analysis_key
        or row.schema_version != contract.schema_version
        or row.target_semantic != contract.target_semantic
        or row.model_family != contract.model_family
        or row.contract_fingerprint != fingerprint
    ):
        raise SimpaAnalyticsError("statistical_model_contract_fingerprint_mismatch")
    if require_current_target:
        current_indicator, current_methodology = _current_validated_target_methodology(
            session, indicator_code=indicator.code
        )
        if (
            current_indicator.id != indicator.id
            or current_methodology.id != methodology.id
            or current_methodology.contract_fingerprint != row.target_methodology_contract_fingerprint
        ):
            raise SimpaAnalyticsError("statistical_model_target_methodology_changed")
    return row, indicator, methodology, contract


def list_statistical_model_contracts(
    session: Session,
) -> list[tuple[SimpaStatisticalModelContract, SimpaIndicatorDefinition, SimpaIndicatorMethodology]]:
    return list(
        session.execute(
            select(
                SimpaStatisticalModelContract,
                SimpaIndicatorDefinition,
                SimpaIndicatorMethodology,
            )
            .join(
                SimpaIndicatorDefinition,
                SimpaIndicatorDefinition.id == SimpaStatisticalModelContract.target_indicator_id,
            )
            .join(
                SimpaIndicatorMethodology,
                SimpaIndicatorMethodology.id == SimpaStatisticalModelContract.target_methodology_id,
            )
            .order_by(
                SimpaIndicatorDefinition.code,
                SimpaStatisticalModelContract.analysis_key,
                SimpaStatisticalModelContract.version_no.desc(),
            )
        ).all()
    )


def create_statistical_model_contract(
    session: Session,
    *,
    indicator_code: str,
    specification: dict,
    actor_id: uuid.UUID | None,
) -> SimpaStatisticalModelContract:
    actor = _require_statistical_actor(session, actor_id)
    indicator, methodology = _current_validated_target_methodology(session, indicator_code=indicator_code)
    raw = {
        **specification,
        "schema_version": STATISTICAL_MODEL_CONTRACT_SCHEMA_VERSION,
        "target_indicator_code": indicator.code,
        "target_methodology_id": methodology.id,
        "target_methodology_version": methodology.version_no,
        "target_methodology_contract_fingerprint": methodology.contract_fingerprint,
    }
    try:
        contract = normalize_statistical_model_contract(raw)
    except (ValidationError, ValueError) as exc:
        raise SimpaAnalyticsError("statistical_model_contract_invalid") from exc
    latest = session.scalar(
        select(func.max(SimpaStatisticalModelContract.version_no)).where(
            SimpaStatisticalModelContract.target_indicator_id == indicator.id,
            SimpaStatisticalModelContract.analysis_key == contract.analysis_key,
        )
    )
    row = SimpaStatisticalModelContract(
        target_indicator_id=indicator.id,
        target_methodology_id=methodology.id,
        target_methodology_contract_fingerprint=methodology.contract_fingerprint,
        analysis_key=contract.analysis_key,
        version_no=int(latest or 0) + 1,
        status="draft",
        schema_version=contract.schema_version,
        target_semantic=contract.target_semantic,
        model_family=contract.model_family,
        contract_json=contract.model_dump(mode="json"),
        contract_fingerprint=statistical_contract_fingerprint(contract),
        created_by_membership_id=actor,
    )
    session.add(row)
    session.flush()
    return row


def propose_statistical_model_contract(
    session: Session, *, contract_id: uuid.UUID, actor_id: uuid.UUID | None
) -> SimpaStatisticalModelContract:
    actor = _require_statistical_actor(session, actor_id)
    row, _indicator, _methodology, _contract = _verified_statistical_contract(
        session, contract_id=contract_id
    )
    if row.status != "draft":
        raise SimpaAnalyticsError("statistical_model_transition_forbidden")
    row.status = "proposed"
    row.proposed_by_membership_id = actor
    row.proposed_at = _utcnow()
    session.flush()
    return row


def validate_statistical_model_contract(
    session: Session,
    *,
    contract_id: uuid.UUID,
    validation_note: str,
    validation_evidence_reference: str,
    actor_id: uuid.UUID | None,
) -> SimpaStatisticalModelContract:
    actor = _require_statistical_actor(session, actor_id)
    row, _indicator, _methodology, _contract = _verified_statistical_contract(
        session, contract_id=contract_id
    )
    if row.status != "proposed":
        raise SimpaAnalyticsError("statistical_model_transition_forbidden")
    note = validation_note.strip()
    evidence = validation_evidence_reference.strip()
    if not note:
        raise SimpaAnalyticsError("statistical_model_validation_note_required")
    if not evidence:
        raise SimpaAnalyticsError("statistical_model_validation_evidence_required")
    for predecessor in session.scalars(
        select(SimpaStatisticalModelContract).where(
            SimpaStatisticalModelContract.target_indicator_id == row.target_indicator_id,
            SimpaStatisticalModelContract.analysis_key == row.analysis_key,
            SimpaStatisticalModelContract.status == "validated",
            SimpaStatisticalModelContract.id != row.id,
        )
    ).all():
        predecessor.status = "retired"
        predecessor.retired_by_membership_id = actor
        predecessor.retired_at = _utcnow()
        predecessor.retirement_note = f"Superseded by validated statistical contract version {row.version_no}."
    row.status = "validated"
    row.validation_note = note
    row.validation_evidence_reference = evidence
    row.approved_by_membership_id = actor
    row.approved_at = _utcnow()
    session.flush()
    return row


def retire_statistical_model_contract(
    session: Session,
    *,
    contract_id: uuid.UUID,
    retirement_note: str,
    actor_id: uuid.UUID | None,
) -> SimpaStatisticalModelContract:
    actor = _require_statistical_actor(session, actor_id)
    row, _indicator, _methodology, _contract = _verified_statistical_contract(
        session,
        contract_id=contract_id,
        require_current_target=False,
    )
    if row.status not in {"draft", "proposed", "validated"}:
        raise SimpaAnalyticsError("statistical_model_transition_forbidden")
    note = retirement_note.strip()
    if not note:
        raise SimpaAnalyticsError("statistical_model_retirement_note_required")
    row.status = "retired"
    row.retired_by_membership_id = actor
    row.retired_at = _utcnow()
    row.retirement_note = note
    session.flush()
    return row


def list_statistical_model_results(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    limit: int = 50,
) -> list[SimpaStatisticalModelResult]:
    return list(
        session.scalars(
            select(SimpaStatisticalModelResult)
            .where(
                SimpaStatisticalModelResult.organization_id == organization_id,
                SimpaStatisticalModelResult.workspace_id == workspace_id,
            )
            .order_by(SimpaStatisticalModelResult.created_at.desc())
            .limit(max(1, min(limit, 100)))
        ).all()
    )


def run_statistical_model(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    analytics_run_id: uuid.UUID,
    statistical_model_contract_id: uuid.UUID,
    controlled_testing_ack: bool,
    actor_id: uuid.UUID | None,
) -> SimpaStatisticalModelResult:
    actor = _require_statistical_actor(session, actor_id)
    row, indicator, methodology, contract = _verified_statistical_contract(
        session,
        contract_id=statistical_model_contract_id,
    )
    if row.status not in {"proposed", "validated"}:
        raise SimpaAnalyticsError("statistical_model_contract_not_executable")
    if row.status == "proposed" and controlled_testing_ack is not True:
        raise SimpaAnalyticsError("statistical_model_controlled_testing_ack_required")
    run = session.scalar(
        select(SimpaAnalyticsRun).where(
            SimpaAnalyticsRun.id == analytics_run_id,
            SimpaAnalyticsRun.organization_id == organization_id,
            SimpaAnalyticsRun.workspace_id == workspace_id,
        )
    )
    if run is None:
        raise SimpaAnalyticsError("analytics_run_not_accessible")
    analytical_input = revalidate_analytics_run(
        session,
        run=run,
        organization_id=organization_id,
        workspace_id=workspace_id,
    )
    matches = [
        record
        for record in _records(analytical_input, run.monitoring_cycle_id)
        if record.payload["indicator_code"] == indicator.code
        and record.payload["quality_status"] == "validated"
    ]
    if not matches:
        raise SimpaAnalyticsError("statistical_model_validated_target_records_required")
    existing = session.scalar(
        select(SimpaStatisticalModelResult.id).where(
            SimpaStatisticalModelResult.analytics_run_id == analytics_run_id,
            SimpaStatisticalModelResult.statistical_model_contract_id == row.id,
        )
    )
    if existing is not None:
        raise SimpaAnalyticsError("statistical_model_result_already_exists")
    try:
        detail = execute_statistical_model(
            contract,
            [dict(record.payload) for record in matches],
            analytical_input.field_contract,
        )
    except StatisticalModelError as exc:
        code = str(exc)
        if code in {
            "target_not_estimable",
            "positive_residual_degrees_of_freedom_required",
            "rank_deficient_design",
            "count_target_invalid",
            "binary_target_invalid",
            "proportion_target_invalid",
        }:
            raise SimpaAnalyticsError("statistical_model_not_estimable") from None
        if code in {"perfect_separation", "non_convergence", "numerical_failure"}:
            raise SimpaAnalyticsError("statistical_model_numerical_failure") from None
        raise SimpaAnalyticsError("statistical_model_input_invalid") from None
    input_content_fingerprint = hashlib.sha256(
        _canonical_json({"content_fingerprints": [record.content_fingerprint for record in matches]}).encode(
            "utf-8"
        )
    ).hexdigest()
    detail["reproducibility_trace"] = {
        "statistical_contract_id": str(row.id),
        "statistical_contract_version_no": row.version_no,
        "statistical_contract_status": row.status,
        "statistical_contract_fingerprint": row.contract_fingerprint,
        "target_indicator_id": str(indicator.id),
        "target_indicator_code": indicator.code,
        "target_methodology_id": str(methodology.id),
        "target_methodology_version": methodology.version_no,
        "target_methodology_contract_fingerprint": methodology.contract_fingerprint,
        "analytical_artifact_fingerprint": analytical_input.artifact_fingerprint,
        "dataset_contract_fingerprint": analytical_input.dataset_contract_fingerprint,
        "input_content_fingerprint": input_content_fingerprint,
    }
    detail = normalize_statistical_result(detail)
    result = SimpaStatisticalModelResult(
        organization_id=organization_id,
        workspace_id=workspace_id,
        analytics_run_id=run.id,
        statistical_model_contract_id=row.id,
        target_indicator_id=indicator.id,
        target_methodology_id=methodology.id,
        target_methodology_contract_fingerprint=methodology.contract_fingerprint,
        statistical_contract_fingerprint=row.contract_fingerprint,
        statistical_contract_version_no=row.version_no,
        statistical_contract_status=row.status,
        analytical_artifact_fingerprint=analytical_input.artifact_fingerprint,
        dataset_contract_fingerprint=analytical_input.dataset_contract_fingerprint,
        input_content_fingerprint=input_content_fingerprint,
        engine_schema_version=STATISTICAL_MODEL_ENGINE_SCHEMA_VERSION,
        statsmodels_version=detail["statsmodels_version"],
        sample_size=detail["sample_size"],
        dropped_missing_count=detail["dropped_missing_count"],
        result_detail=detail,
        result_fingerprint=statistical_result_fingerprint(detail),
        production_eligible=row.status == "validated",
        created_by_membership_id=actor,
    )
    session.add(result)
    session.flush()
    return result


def _synthesis_input(run: SimpaAnalyticsRun) -> str:
    payload = {
        "analytics_run_id": str(run.id),
        "analytical_source": (run.snapshot or {}).get("analytical_source"),
        "snapshot": run.snapshot,
        "instruction": "Synthesize only the evidence-quality state. Do not infer citizen-level facts, eligibility, diagnosis, or institutional decisions.",
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def create_synthesis(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    analytics_run_id: uuid.UUID,
    sensitivity: str,
    model_key: str | None,
    actor_id: uuid.UUID | None,
) -> tuple[SimpaAISynthesis, AIJob]:
    run = session.scalar(
        select(SimpaAnalyticsRun).where(
            SimpaAnalyticsRun.id == analytics_run_id,
            SimpaAnalyticsRun.organization_id == organization_id,
            SimpaAnalyticsRun.workspace_id == workspace_id,
        )
    )
    if run is None:
        raise SimpaAnalyticsError("analytics_run_not_accessible")
    revalidate_analytics_run(session, run=run, organization_id=organization_id, workspace_id=workspace_id)
    input_text = _synthesis_input(run)
    job = create_ai_job(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code="SIMPA",
        input_text=input_text,
        prompt_key="simpa.monitoring.synthesis",
        model_key=model_key,
        policy_key="simpa-sensitive-local" if sensitivity == "sensitive" else "shared-local-only",
        sensitivity=sensitivity,
        actor_id=actor_id,
    )
    row = SimpaAISynthesis(
        organization_id=organization_id,
        workspace_id=workspace_id,
        analytics_run_id=run.id,
        ai_job_id=job.id,
        source_snapshot_sha256=hashlib.sha256(input_text.encode("utf-8")).hexdigest(),
        review_status="pending",
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    return row, job


def list_syntheses(
    session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, limit: int = 50
) -> list[tuple[SimpaAISynthesis, AIJob]]:
    return list(
        session.execute(
            select(SimpaAISynthesis, AIJob)
            .join(AIJob, AIJob.id == SimpaAISynthesis.ai_job_id)
            .where(SimpaAISynthesis.organization_id == organization_id, SimpaAISynthesis.workspace_id == workspace_id)
            .order_by(SimpaAISynthesis.created_at.desc())
            .limit(max(1, min(limit, 100)))
        ).all()
    )


def review_synthesis(
    session: Session,
    *,
    synthesis_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    decision: str,
    reviewer_note: str,
    actor_id: uuid.UUID | None,
) -> tuple[SimpaAISynthesis, AIJob]:
    row = session.scalar(
        select(SimpaAISynthesis).where(
            SimpaAISynthesis.id == synthesis_id,
            SimpaAISynthesis.organization_id == organization_id,
            SimpaAISynthesis.workspace_id == workspace_id,
        )
    )
    if row is None:
        raise SimpaAnalyticsError("synthesis_not_accessible")
    run = session.scalar(
        select(SimpaAnalyticsRun).where(
            SimpaAnalyticsRun.id == row.analytics_run_id,
            SimpaAnalyticsRun.organization_id == organization_id,
            SimpaAnalyticsRun.workspace_id == workspace_id,
        )
    )
    if run is None:
        raise SimpaAnalyticsError("analytics_run_not_accessible")
    revalidate_analytics_run(session, run=run, organization_id=organization_id, workspace_id=workspace_id)
    job = session.get(AIJob, row.ai_job_id)
    if (
        job is None
        or job.product_code != "SIMPA"
        or job.organization_id != organization_id
        or job.workspace_id != workspace_id
    ):
        raise SimpaAnalyticsError("synthesis_ai_job_not_accessible")
    if job.status not in {"review_required", "succeeded"}:
        raise SimpaAnalyticsError("synthesis_not_reviewable")
    row.review_status = decision
    row.reviewer_note = reviewer_note.strip()
    row.reviewed_by_membership_id = actor_id
    row.reviewed_at = _utcnow()
    job.human_review_status = "accepted" if decision == "accepted" else "rejected"
    session.flush()
    return row, job
