from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from src.core.database import build_engine
from src.domains.simpa.analytics_models import (
    SimpaAnalyticsRun,
    SimpaIndicatorMethodology,
    SimpaStatisticalModelResult,
)
from src.domains.simpa.analytics_service import (
    create_statistical_model_contract,
    propose_statistical_model_contract,
    validate_statistical_model_contract,
)
from src.domains.simpa.methodology_contracts import contract_fingerprint, normalize_methodology_contract
from src.domains.simpa.models import SimpaDimension, SimpaIndicatorDefinition
from src.platform.access.models import Product
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace


pytestmark = pytest.mark.skipif(
    os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1",
    reason="native PostgreSQL acceptance only",
)


def _target_contract():
    return {
        "schema_version": "SIMPA-METHODOLOGY-CONTRACT-v1",
        "computation_type": "direct_observation",
        "purpose": "Aggregate target.",
        "interpretation": "Direct aggregate observation.",
        "unit": "count",
        "scale": "Aggregate.",
        "required_source_fields": ["indicator_code", "quality_status", "value_numeric"],
        "eligible_aggregate_scope": "Local system.",
        "time_aggregation": "Reported period.",
        "geographic_aggregation": "Approved aggregate.",
        "missing_data_rule": "Preserve missing.",
        "suppression_privacy_rule": "Aggregate only.",
        "quality_preconditions": "Validated only.",
        "reference_dataset": "Native ISI-23C fixture.",
        "accepted_tolerance": 0.0,
        "limitations": "Non-causal.",
        "non_causal": True,
    }


def _spec():
    return {
        "analysis_key": "native-association",
        "target_field": "value_numeric",
        "target_semantic": "continuous",
        "model_family": "ols",
        "feature_fields": ["capacity"],
        "confidence_level": 0.95,
        "covariance_type": "HC3",
        "missing_data_rule": "complete_case",
        "feature_scaling": "none",
        "include_intercept": True,
        "aggregate_only": True,
        "non_causal": True,
        "purpose": "Native aggregate association.",
        "limitations": "Non-causal.",
        "positive_outcome_definition": None,
    }


def test_native_postgres_0029_tables_checks_foreign_keys_uniques_and_indexes():
    inspector = inspect(build_engine())
    tables = set(inspector.get_table_names())
    assert {"simpa_statistical_model_contracts", "simpa_statistical_model_results"} <= tables
    contract_checks = {
        item["name"] for item in inspector.get_check_constraints("simpa_statistical_model_contracts")
    }
    assert {
        "ck_simpa_statistical_contract_status",
        "ck_simpa_statistical_contract_family",
        "ck_simpa_statistical_contract_validation_trace",
    } <= contract_checks
    result_checks = {
        item["name"] for item in inspector.get_check_constraints("simpa_statistical_model_results")
    }
    assert {
        "ck_simpa_statistical_result_contract_status",
        "ck_simpa_statistical_result_production_eligible",
        "ck_simpa_statistical_result_fingerprints",
    } <= result_checks
    uniques = {
        tuple(item["column_names"])
        for item in inspector.get_unique_constraints("simpa_statistical_model_results")
    }
    assert ("analytics_run_id", "statistical_model_contract_id") in uniques
    fks = {
        tuple(item["constrained_columns"]): (item["referred_table"], item["options"].get("ondelete"))
        for item in inspector.get_foreign_keys("simpa_statistical_model_results")
    }
    assert fks["analytics_run_id",] == ("simpa_analytics_runs", "RESTRICT")
    assert fks["statistical_model_contract_id",] == ("simpa_statistical_model_contracts", "RESTRICT")
    assert fks["target_methodology_id",] == ("simpa_indicator_methodologies", "RESTRICT")
    indexes = {item["name"] for item in inspector.get_indexes("simpa_statistical_model_results")}
    assert {"ix_simpa_statistical_result_scope_created", "ix_simpa_statistical_result_contract"} <= indexes


def test_native_postgres_representative_validated_lifecycle_and_result_persistence():
    connection = build_engine().connect()
    transaction = connection.begin()
    try:
        db = Session(bind=connection)
        marker = uuid.uuid4().hex
        product = db.scalar(select(Product).where(Product.code == "SIMPA"))
        if product is None:
            product = Product(code="SIMPA", name="SIMPA", is_active=True)
            db.add(product)
        user = User(email=f"isi23c-{marker}@example.test", display_name="ISI-23C")
        organization = Organization(slug=f"isi23c-{marker}", name="ISI-23C")
        db.add_all([user, organization])
        db.flush()
        membership = Membership(user_id=user.id, organization_id=organization.id)
        workspace = Workspace(
            organization_id=organization.id,
            product_code="SIMPA",
            slug=f"isi23c-{marker}",
            name="ISI-23C",
        )
        dimension = SimpaDimension(code=f"ISI23C_{marker}", name_sr="ISI-23C")
        db.add_all([membership, workspace, dimension])
        db.flush()
        indicator = SimpaIndicatorDefinition(
            code=f"ISI23C_TARGET_{marker}",
            name_sr="Target",
            dimension_code=dimension.code,
            unit_hint="count",
            methodology_status="validated",
            methodology_note="Approved",
        )
        db.add(indicator)
        db.flush()
        target = normalize_methodology_contract(_target_contract(), indicator_unit_hint="count")
        methodology = SimpaIndicatorMethodology(
            indicator_id=indicator.id,
            version_no=1,
            status="validated",
            computation_type="direct_observation",
            computation_spec=target.model_dump(mode="json"),
            contract_fingerprint=contract_fingerprint(target),
            source_requirements={},
            methodology_note="Approved",
            validation_note="Human approved",
            reference_check_status="legacy_unknown",
            reference_evidence_mode="legacy_unknown",
        )
        db.add(methodology)
        db.flush()
        contract = create_statistical_model_contract(
            db, indicator_code=indicator.code, specification=_spec(), actor_id=membership.id
        )
        propose_statistical_model_contract(db, contract_id=contract.id, actor_id=membership.id)
        validate_statistical_model_contract(
            db,
            contract_id=contract.id,
            validation_note="Human methodology approval, not champion certification.",
            validation_evidence_reference="evidence://native/isi23c",
            actor_id=membership.id,
        )
        run = SimpaAnalyticsRun(
            organization_id=organization.id,
            workspace_id=workspace.id,
            analytical_artifact_type="LEGACY_OBSERVATION",
            status="completed",
            snapshot={},
        )
        db.add(run)
        db.flush()
        result = SimpaStatisticalModelResult(
            organization_id=organization.id,
            workspace_id=workspace.id,
            analytics_run_id=run.id,
            statistical_model_contract_id=contract.id,
            target_indicator_id=indicator.id,
            target_methodology_id=methodology.id,
            target_methodology_contract_fingerprint=methodology.contract_fingerprint,
            statistical_contract_fingerprint=contract.contract_fingerprint,
            statistical_contract_version_no=contract.version_no,
            statistical_contract_status="validated",
            analytical_artifact_fingerprint="a" * 64,
            dataset_contract_fingerprint="b" * 64,
            input_content_fingerprint="c" * 64,
            engine_schema_version="SIMPA-STATISTICAL-MODEL-v1",
            statsmodels_version="0.14.6",
            sample_size=4,
            dropped_missing_count=0,
            result_detail={"non_causal": True},
            result_fingerprint="d" * 64,
            production_eligible=True,
            created_by_membership_id=membership.id,
        )
        db.add(result)
        db.flush()
        db.expire_all()
        assert db.get(type(contract), contract.id).status == "validated"
        assert db.get(SimpaStatisticalModelResult, result.id).production_eligible is True
    finally:
        transaction.rollback()
        connection.close()
