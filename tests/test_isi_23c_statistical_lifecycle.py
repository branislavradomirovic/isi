from __future__ import annotations

import hashlib
import json
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import src.platform.models  # noqa: F401 - register all FK targets
from src.core.database import Base
from src.domains.simpa import analytics_service
from src.domains.simpa.analytics_models import SimpaAnalyticsRun, SimpaIndicatorMethodology
from src.domains.simpa.analytics_service import (
    SimpaAnalyticsError,
    create_statistical_model_contract,
    propose_statistical_model_contract,
    retire_statistical_model_contract,
    run_statistical_model,
    validate_statistical_model_contract,
)
from src.domains.simpa.methodology_contracts import contract_fingerprint, normalize_methodology_contract
from src.domains.simpa.models import SimpaDimension, SimpaIndicatorDefinition
from src.platform.data.analytical_service import GovernedAnalyticalInput, GovernedAnalyticalRecord
from src.platform.identity.models import Membership, Organization, User


def _target_methodology_contract(unit="count"):
    return {
        "schema_version": "SIMPA-METHODOLOGY-CONTRACT-v1",
        "computation_type": "direct_observation",
        "purpose": "Aggregate target observations.",
        "interpretation": "Direct aggregate observation.",
        "unit": unit,
        "scale": "Aggregate local-system value.",
        "required_source_fields": ["indicator_code", "quality_status", "value_numeric"],
        "eligible_aggregate_scope": "Organization/local system only.",
        "time_aggregation": "Reported period.",
        "geographic_aggregation": "Authorized aggregate geography.",
        "missing_data_rule": "Missing remains missing.",
        "suppression_privacy_rule": "Aggregate-only data.",
        "quality_preconditions": "Validated rows only.",
        "reference_dataset": "ISI-23C target binding fixture.",
        "accepted_tolerance": 0.0,
        "limitations": "Non-causal.",
        "non_causal": True,
    }


def _spec(analysis_key="association"):
    return {
        "analysis_key": analysis_key,
        "target_field": "value_numeric",
        "target_semantic": "continuous",
        "model_family": "ols",
        "feature_fields": ["x"],
        "confidence_level": 0.95,
        "covariance_type": "HC3",
        "missing_data_rule": "complete_case",
        "feature_scaling": "none",
        "include_intercept": True,
        "aggregate_only": True,
        "non_causal": True,
        "purpose": "Estimate aggregate association.",
        "limitations": "Observational and non-causal.",
        "positive_outcome_definition": None,
    }


@pytest.fixture
def lifecycle_case():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        marker = uuid.uuid4().hex
        user = User(email=f"isi23c-{marker}@example.test", display_name="Reviewer")
        organization = Organization(slug=f"isi23c-{marker}", name="ISI-23C")
        db.add_all([user, organization])
        db.flush()
        membership = Membership(user_id=user.id, organization_id=organization.id)
        dimension = SimpaDimension(code=f"DIM_{marker}", name_sr="ISI-23C")
        db.add_all([membership, dimension])
        db.flush()
        indicator = SimpaIndicatorDefinition(
            code=f"TARGET_{marker}",
            name_sr="Target",
            dimension_code=dimension.code,
            unit_hint="count",
            methodology_status="validated",
            methodology_note="Human approved.",
        )
        db.add(indicator)
        db.flush()
        target_contract = normalize_methodology_contract(_target_methodology_contract(), indicator_unit_hint="count")
        methodology = SimpaIndicatorMethodology(
            indicator_id=indicator.id,
            version_no=1,
            status="validated",
            computation_type="direct_observation",
            computation_spec=target_contract.model_dump(mode="json"),
            contract_fingerprint=contract_fingerprint(target_contract),
            source_requirements={},
            methodology_note="Human approved.",
            validation_note="Approved target methodology.",
            reference_check_status="legacy_unknown",
            reference_evidence_mode="legacy_unknown",
            approved_by_membership_id=membership.id,
        )
        db.add(methodology)
        db.flush()
        yield db, organization, membership, indicator, methodology


def test_draft_proposed_validated_retired_lifecycle_and_human_evidence(lifecycle_case):
    db, _organization, membership, indicator, methodology = lifecycle_case
    row = create_statistical_model_contract(
        db, indicator_code=indicator.code, specification=_spec(), actor_id=membership.id
    )
    assert row.status == "draft"
    assert row.target_methodology_id == methodology.id
    with pytest.raises(SimpaAnalyticsError, match="transition_forbidden"):
        validate_statistical_model_contract(
            db,
            contract_id=row.id,
            validation_note="Human approval.",
            validation_evidence_reference="evidence://review/1",
            actor_id=membership.id,
        )
    propose_statistical_model_contract(db, contract_id=row.id, actor_id=membership.id)
    with pytest.raises(SimpaAnalyticsError, match="validation_note_required"):
        validate_statistical_model_contract(
            db,
            contract_id=row.id,
            validation_note=" ",
            validation_evidence_reference="evidence://review/1",
            actor_id=membership.id,
        )
    with pytest.raises(SimpaAnalyticsError, match="validation_evidence_required"):
        validate_statistical_model_contract(
            db,
            contract_id=row.id,
            validation_note="Human approval.",
            validation_evidence_reference=" ",
            actor_id=membership.id,
        )
    validate_statistical_model_contract(
        db,
        contract_id=row.id,
        validation_note="Human methodology approval only.",
        validation_evidence_reference="evidence://methodology/review-1",
        actor_id=membership.id,
    )
    assert row.status == "validated"
    assert row.approved_by_membership_id == membership.id
    retire_statistical_model_contract(
        db, contract_id=row.id, retirement_note="Superseded specification.", actor_id=membership.id
    )
    assert row.status == "retired"


def test_active_actor_contract_integrity_and_stale_target_binding_fail_closed(lifecycle_case):
    db, _organization, membership, indicator, methodology = lifecycle_case
    row = create_statistical_model_contract(
        db, indicator_code=indicator.code, specification=_spec(), actor_id=membership.id
    )
    with pytest.raises(SimpaAnalyticsError, match="actor_required"):
        propose_statistical_model_contract(db, contract_id=row.id, actor_id=None)
    original = dict(row.contract_json)
    row.contract_json = {**original, "purpose": "Tampered"}
    with pytest.raises(SimpaAnalyticsError, match="fingerprint_mismatch"):
        propose_statistical_model_contract(db, contract_id=row.id, actor_id=membership.id)
    row.contract_json = original
    methodology.status = "retired"
    successor_contract = normalize_methodology_contract(_target_methodology_contract(), indicator_unit_hint="count")
    successor = SimpaIndicatorMethodology(
        indicator_id=indicator.id,
        version_no=2,
        status="validated",
        computation_type="direct_observation",
        computation_spec=successor_contract.model_dump(mode="json"),
        contract_fingerprint=contract_fingerprint(successor_contract),
        source_requirements={},
        methodology_note="Successor",
        validation_note="Approved successor",
        reference_check_status="legacy_unknown",
        reference_evidence_mode="legacy_unknown",
    )
    db.add(successor)
    db.flush()
    with pytest.raises(SimpaAnalyticsError, match="target_methodology_changed"):
        propose_statistical_model_contract(db, contract_id=row.id, actor_id=membership.id)


def test_validating_successor_retires_only_same_indicator_and_analysis_key(lifecycle_case):
    db, _organization, membership, indicator, _methodology = lifecycle_case
    first = create_statistical_model_contract(
        db, indicator_code=indicator.code, specification=_spec(), actor_id=membership.id
    )
    propose_statistical_model_contract(db, contract_id=first.id, actor_id=membership.id)
    validate_statistical_model_contract(
        db,
        contract_id=first.id,
        validation_note="Approved first.",
        validation_evidence_reference="evidence://first",
        actor_id=membership.id,
    )
    other = create_statistical_model_contract(
        db, indicator_code=indicator.code, specification=_spec("different"), actor_id=membership.id
    )
    propose_statistical_model_contract(db, contract_id=other.id, actor_id=membership.id)
    validate_statistical_model_contract(
        db,
        contract_id=other.id,
        validation_note="Approved different analysis.",
        validation_evidence_reference="evidence://different",
        actor_id=membership.id,
    )
    successor = create_statistical_model_contract(
        db, indicator_code=indicator.code, specification=_spec(), actor_id=membership.id
    )
    propose_statistical_model_contract(db, contract_id=successor.id, actor_id=membership.id)
    validate_statistical_model_contract(
        db,
        contract_id=successor.id,
        validation_note="Approved successor.",
        validation_evidence_reference="evidence://successor",
        actor_id=membership.id,
    )
    assert first.status == "retired"
    assert other.status == "validated"
    assert successor.status == "validated"


def _governed_input(indicator_code: str) -> GovernedAnalyticalInput:
    records = []
    for index, value in enumerate([1.2, 2.5, 2.1, 4.4, 3.9, 5.8]):
        payload = {"indicator_code": indicator_code, "quality_status": "validated", "value_numeric": value, "x": index}
        content = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        records.append(
            GovernedAnalyticalRecord(
                governed_output_id=uuid.uuid4(),
                normalized_record_id=uuid.uuid4(),
                source_id=uuid.uuid4(),
                source_version_id=uuid.uuid4(),
                ingestion_run_id=uuid.uuid4(),
                identity_fingerprint="b" * 64,
                content_fingerprint=content,
                source_record_ordinal=index,
                source_locator=f"row:{index}",
                payload=payload,
            )
        )
    for index, payload in enumerate(
        [
            {"indicator_code": indicator_code, "quality_status": "draft", "value_numeric": 999, "x": 99},
            {"indicator_code": "OTHER", "quality_status": "validated", "value_numeric": 999, "x": 99},
        ],
        start=len(records),
    ):
        records.append(
            GovernedAnalyticalRecord(
                governed_output_id=uuid.uuid4(),
                normalized_record_id=uuid.uuid4(),
                source_id=uuid.uuid4(),
                source_version_id=uuid.uuid4(),
                ingestion_run_id=uuid.uuid4(),
                identity_fingerprint="b" * 64,
                content_fingerprint=hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
                source_record_ordinal=index,
                source_locator=f"row:{index}",
                payload=payload,
            )
        )
    return GovernedAnalyticalInput(
        artifact_type="snapshot",
        artifact_id=uuid.uuid4(),
        artifact_fingerprint="c" * 64,
        dataset_contract_version_id=uuid.uuid4(),
        dataset_contract_fingerprint="d" * 64,
        analytical_quality_state="ACCEPTED_CLEAN",
        snapshot_id=uuid.uuid4(),
        snapshot_fingerprint="e" * 64,
        field_contract=(
            {"field_key": "indicator_code", "logical_type": "STRING", "required": True},
            {"field_key": "quality_status", "logical_type": "STRING", "required": True},
            {"field_key": "value_numeric", "logical_type": "NUMBER", "required": False},
            {"field_key": "value_text", "logical_type": "STRING", "required": False},
            {"field_key": "x", "logical_type": "NUMBER", "required": False},
        ),
        records=tuple(records),
    )


def test_proposed_execution_requires_ack_revalidates_governed_run_and_is_immutable(lifecycle_case, monkeypatch):
    db, organization, membership, indicator, _methodology = lifecycle_case
    contract = create_statistical_model_contract(
        db, indicator_code=indicator.code, specification=_spec(), actor_id=membership.id
    )
    propose_statistical_model_contract(db, contract_id=contract.id, actor_id=membership.id)
    analytical_input = _governed_input(indicator.code)
    run = SimpaAnalyticsRun(
        organization_id=organization.id,
        workspace_id=uuid.uuid4(),
        analytical_artifact_type="ANALYTICAL_SNAPSHOT",
        analytical_snapshot_id=analytical_input.artifact_id,
        analytical_artifact_fingerprint=analytical_input.artifact_fingerprint,
        dataset_contract_version_id=analytical_input.dataset_contract_version_id,
        dataset_contract_fingerprint=analytical_input.dataset_contract_fingerprint,
        analytical_quality_state="ACCEPTED_CLEAN",
        status="completed",
        snapshot={},
    )
    db.add(run)
    db.flush()
    calls = []

    def revalidate(*_args, **_kwargs):
        calls.append(True)
        return analytical_input

    monkeypatch.setattr(analytics_service, "revalidate_analytics_run", revalidate)
    with pytest.raises(SimpaAnalyticsError, match="controlled_testing_ack_required"):
        run_statistical_model(
            db,
            organization_id=organization.id,
            workspace_id=run.workspace_id,
            analytics_run_id=run.id,
            statistical_model_contract_id=contract.id,
            controlled_testing_ack=False,
            actor_id=membership.id,
        )
    result = run_statistical_model(
        db,
        organization_id=organization.id,
        workspace_id=run.workspace_id,
        analytics_run_id=run.id,
        statistical_model_contract_id=contract.id,
        controlled_testing_ack=True,
        actor_id=membership.id,
    )
    assert calls == [True]
    assert result.production_eligible is False
    assert result.result_detail["selected_count"] == 6
    assert len(result.input_content_fingerprint) == len(result.result_fingerprint) == 64
    with pytest.raises(SimpaAnalyticsError, match="already_exists"):
        run_statistical_model(
            db,
            organization_id=organization.id,
            workspace_id=run.workspace_id,
            analytics_run_id=run.id,
            statistical_model_contract_id=contract.id,
            controlled_testing_ack=True,
            actor_id=membership.id,
        )
    validated = create_statistical_model_contract(
        db, indicator_code=indicator.code, specification=_spec("validated-association"), actor_id=membership.id
    )
    propose_statistical_model_contract(db, contract_id=validated.id, actor_id=membership.id)
    validate_statistical_model_contract(
        db,
        contract_id=validated.id,
        validation_note="Human methodology approval.",
        validation_evidence_reference="evidence://validated",
        actor_id=membership.id,
    )
    validated_run = SimpaAnalyticsRun(
        organization_id=organization.id,
        workspace_id=run.workspace_id,
        analytical_artifact_type="ANALYTICAL_SNAPSHOT",
        analytical_snapshot_id=analytical_input.artifact_id,
        analytical_artifact_fingerprint=analytical_input.artifact_fingerprint,
        dataset_contract_version_id=analytical_input.dataset_contract_version_id,
        dataset_contract_fingerprint=analytical_input.dataset_contract_fingerprint,
        analytical_quality_state="ACCEPTED_CLEAN",
        status="completed",
        snapshot={},
    )
    db.add(validated_run)
    db.flush()
    validated_result = run_statistical_model(
        db,
        organization_id=organization.id,
        workspace_id=validated_run.workspace_id,
        analytics_run_id=validated_run.id,
        statistical_model_contract_id=validated.id,
        controlled_testing_ack=False,
        actor_id=membership.id,
    )
    assert validated_result.production_eligible is True


def test_historical_pre_22g_run_cannot_authorize_statistical_execution(lifecycle_case):
    db, organization, membership, indicator, _methodology = lifecycle_case
    contract = create_statistical_model_contract(
        db, indicator_code=indicator.code, specification=_spec(), actor_id=membership.id
    )
    propose_statistical_model_contract(db, contract_id=contract.id, actor_id=membership.id)
    legacy = SimpaAnalyticsRun(
        organization_id=organization.id,
        workspace_id=uuid.uuid4(),
        analytical_artifact_type="LEGACY_OBSERVATION",
        status="completed",
        snapshot={},
    )
    db.add(legacy)
    db.flush()
    with pytest.raises(SimpaAnalyticsError, match="legacy_analytics_run_ineligible"):
        run_statistical_model(
            db,
            organization_id=organization.id,
            workspace_id=legacy.workspace_id,
            analytics_run_id=legacy.id,
            statistical_model_contract_id=contract.id,
            controlled_testing_ack=True,
            actor_id=membership.id,
        )
