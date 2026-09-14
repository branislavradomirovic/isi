from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from src.domains.ordo import analytics_service as ordo_analytics_service
from src.domains.ordo import reporting_adapter as ordo_reporting_adapter
from src.domains.ordo.analytics_models import OrdoIndicatorMethodology
from src.domains.ordo.analytics_service import (
    compute_indicator as compute_ordo_indicator,
    create_analytics_run as create_ordo_run,
)
from src.domains.ordo.models import OrdoDimension, OrdoIndicatorDefinition, OrdoPillar
from src.domains.simpa import analytics_service as simpa_analytics_service
from src.domains.simpa import reporting_adapter as simpa_reporting_adapter
from src.domains.simpa.analytics_models import SimpaIndicatorMethodology
from src.domains.simpa.analytics_service import (
    compute_indicator as compute_simpa_indicator,
    create_analytics_run as create_simpa_run,
)
from src.domains.simpa.models import SimpaDimension, SimpaIndicatorDefinition
from src.platform.data.analytical_service import (
    activate_analytical_dataset_contract_version,
    create_analytical_dataset,
    create_analytical_dataset_contract_version,
    create_analytical_feature,
    create_analytical_feature_version,
    create_analytical_snapshot,
    load_governed_analytical_input,
    transition_analytical_feature_version,
    transition_analytical_snapshot,
)
from src.platform.ai.models import AIJob, AIModel, AIPolicyProfile, AIPrompt, AIPromptVersion
from src.platform.data.models import (
    AnalyticalDatasetSnapshot,
    AnalyticalFeatureVersion,
    DataGovernedIngestionOutput,
    DataSourceGovernanceProfile,
)
from src.platform.data.schemas import (
    AnalyticalDatasetContractVersionCreate,
    AnalyticalDatasetCreate,
    AnalyticalFeatureCreate,
    AnalyticalFeatureVersionCreate,
    AnalyticalSnapshotCreate,
)
from src.platform.data.service import DataPlatformError
from src.workers import data_jobs
from test_isi_22e_ingestion_operations import build_case, create_run


FIELDS = [
    {"field_key": "indicator_code", "logical_type": "STRING", "required": True, "semantic_role": "KEY"},
    {"field_key": "quality_status", "logical_type": "STRING", "required": True, "semantic_role": "ATTRIBUTE"},
    {"field_key": "value_numeric", "logical_type": "NUMBER", "required": False, "semantic_role": "MEASURE"},
    {"field_key": "value_text", "logical_type": "STRING", "required": False, "semantic_role": "MEASURE"},
]


def _governed_artifact(tmp_path, monkeypatch, *, product: str, feature: bool):
    case = build_case(tmp_path, product=product)
    schema = []
    mapping = []
    for ordinal, (name, logical_type, required) in enumerate(
        (("indicator_code", "STRING", True), ("quality_status", "STRING", True),
         ("value_numeric", "NUMBER", False), ("value_text", "STRING", False)), start=1,
    ):
        schema.append({"logical_type": logical_type, "missing_values": [""], "nullable": not required,
                       "ordinal": ordinal, "required": required, "source_field": name})
        mapping.append({"disposition": "MAP", "field_key": name, "source_field": name})
    case["mapping"].source_schema_json = json.dumps(schema, sort_keys=True, separators=(",", ":"))
    case["mapping"].field_mapping_json = json.dumps(mapping, sort_keys=True, separators=(",", ":"))
    case["record_policy"].identity_field_keys_json = '["indicator_code"]'
    case["db"].add(DataSourceGovernanceProfile(
        source_id=case["source"].id, organization_id=case["organization"].id,
        workspace_id=case["workspace"].id, product_code=product,
        classification="CONFIDENTIAL", privacy_category="AGGREGATE_NON_PERSONAL",
        processing_purpose="Synthetic governed domain evidence", data_owner_ref="owner:test",
        ai_use_policy="RAG_RETRIEVAL_ALLOWED", export_policy="PROHIBITED",
        governance_state="GOVERNED", created_by_membership_id=case["membership"].id,
        updated_by_membership_id=case["membership"].id,
    ))
    case["db"].flush()
    run = create_run(
        case, observed=datetime.now(timezone.utc),
        raw=b"indicator_code,quality_status,value_numeric,value_text\nTEST,validated,12.5,\n",
    )
    monkeypatch.setattr(data_jobs, "build_storage", lambda: case["storage"])
    monkeypatch.setattr(data_jobs, "get_settings", lambda: SimpleNamespace(
        data_max_xlsx_uncompressed_bytes=1024 * 1024))
    data_jobs.process_ingestion_job(case["db"], job_id=run.inspection_job_id)
    output = case["db"].scalar(select(DataGovernedIngestionOutput).where(
        DataGovernedIngestionOutput.ingestion_run_id == run.id))
    assert output is not None

    dataset = create_analytical_dataset(case["db"], payload=AnalyticalDatasetCreate(
        organization_id=case["organization"].id, workspace_id=case["workspace"].id,
        product_code=product, code="DOMAIN_EVIDENCE", name="Domain evidence",
        methodology_reference="method:approved", methodology_version="v1",
    ), actor_id=case["membership"].id)
    contract = create_analytical_dataset_contract_version(
        case["db"], dataset_id=dataset.id, payload=AnalyticalDatasetContractVersionCreate(
            organization_id=case["organization"].id, workspace_id=case["workspace"].id,
            product_code=product, field_contract=FIELDS, temporal_mode="STATIC",
            temporal_key_fields=[], granularity_key_fields=["indicator_code"],
            missing_value_policy="PRESERVE_MISSING",
        ), actor_id=case["membership"].id)
    activate_analytical_dataset_contract_version(
        case["db"], dataset_id=dataset.id, contract_version_id=contract.id,
        organization_id=case["organization"].id, workspace_id=case["workspace"].id,
        product_code=product, actor_id=case["membership"].id)
    snapshot = create_analytical_snapshot(case["db"], dataset_id=dataset.id,
        payload=AnalyticalSnapshotCreate(
            organization_id=case["organization"].id, workspace_id=case["workspace"].id,
            product_code=product, dataset_contract_version_id=contract.id,
            governed_output_ids=[output.id], methodology_reference="method:approved",
            methodology_version="v1", build_reference="worker:22e",
        ), actor_id=case["membership"].id)
    transition_analytical_snapshot(
        case["db"], snapshot_id=snapshot.id, organization_id=case["organization"].id,
        workspace_id=case["workspace"].id, product_code=product, expected_revision=1,
        target_state="VALIDATED", actor_id=case["membership"].id)
    if not feature:
        return case, "snapshot", snapshot
    feature_row = create_analytical_feature(case["db"], payload=AnalyticalFeatureCreate(
        organization_id=case["organization"].id, workspace_id=case["workspace"].id,
        product_code=product, code="DIRECT", name="Direct governed evidence",
        methodology_reference="method:approved", methodology_version="v1",
    ), actor_id=case["membership"].id)
    feature_version = create_analytical_feature_version(
        case["db"], feature_id=feature_row.id, payload=AnalyticalFeatureVersionCreate(
            organization_id=case["organization"].id, workspace_id=case["workspace"].id,
            product_code=product, snapshot_ids=[snapshot.id],
            methodology_reference="method:approved", methodology_version="v1",
        ), actor_id=case["membership"].id)
    transition_analytical_feature_version(
        case["db"], feature_version_id=feature_version.id,
        organization_id=case["organization"].id, workspace_id=case["workspace"].id,
        product_code=product, expected_revision=1, target_state="GOVERNED",
        actor_id=case["membership"].id)
    return case, "feature_version", feature_version



def _install_fake_ai_job(case, monkeypatch, *, product: str):
    marker = uuid.uuid4().hex
    model = AIModel(
        model_key=f"isi22g-e2e-{product.lower()}-{marker}",
        provider_type="stub",
        provider_name="isi22g-e2e",
        model_name="deterministic-e2e",
        purpose="chat",
        product_scope=product,
        local_provider=True,
        enabled=True,
        timeout_seconds=5,
    )
    prompt = AIPrompt(
        prompt_key=f"isi22g.e2e.{product.lower()}.{marker}",
        product_scope=product,
        title="ISI-22G synthetic E2E",
        purpose="Synthetic governed provenance acceptance",
        is_active=True,
    )
    policy = AIPolicyProfile(
        policy_key=f"isi22g-e2e-{product.lower()}-{marker}",
        product_scope=product,
        sensitivity="sensitive" if product == "SIMPA" else "internal",
        provider_policy="local_only",
        allow_external=False,
        require_human_review=True,
        max_attempts=1,
        enabled=True,
    )
    case["db"].add_all([model, prompt, policy])
    case["db"].flush()
    prompt_version = AIPromptVersion(
        prompt_id=prompt.id,
        version_no=1,
        system_template="Synthetic acceptance only.",
        user_template="{input}",
        output_schema={"type": "object"},
        checksum="a" * 64,
        status="active",
        created_by_membership_id=case["membership"].id,
    )
    case["db"].add(prompt_version)
    case["db"].flush()

    captured: dict[str, str] = {}

    def fake_create_ai_job(session, **kwargs):
        assert session is case["db"]
        assert kwargs["product_code"] == product
        captured["input_text"] = kwargs["input_text"]
        job = AIJob(
            organization_id=case["organization"].id,
            workspace_id=case["workspace"].id,
            product_code=product,
            model_id=model.id,
            prompt_version_id=prompt_version.id,
            policy_profile_id=policy.id,
            job_type="structured",
            status="review_required",
            sensitivity=kwargs["sensitivity"],
            effective_provider_policy="local_only",
            request_sha256=hashlib.sha256(kwargs["input_text"].encode()).hexdigest(),
            request_text=kwargs["input_text"],
            structured_output={
                "executive_summary": "Synthetic governed evidence accepted for E2E.",
                "evidence_basis": "Pinned governed analytical artifact.",
                "development_opportunities": [],
                "tradeoffs": [],
                "limitations": [],
                "next_evidence_needed": [],
                "forecast_performed": False,
                "human_review_required": True,
            },
            provider_name="isi22g-e2e",
            model_name="deterministic-e2e",
            human_review_status="pending",
            created_by_membership_id=case["membership"].id,
        )
        session.add(job)
        session.flush()
        return job

    service = simpa_analytics_service if product == "SIMPA" else ordo_analytics_service
    monkeypatch.setattr(service, "create_ai_job", fake_create_ai_job)
    return captured


def _assert_ai_provenance(job: AIJob, *, product: str, artifact) -> None:
    request = json.loads(job.request_text)
    source = request["analytical_source"] if product == "SIMPA" else request["payload"]["analytical_source"]
    assert source["artifact_id"] == str(artifact.id)
    assert source["artifact_fingerprint"] == artifact.fingerprint


def _assert_manifest_provenance(manifest: list[dict], *, artifact_type: str, artifact) -> None:
    expected_kind = "analytical_snapshot" if artifact_type == "snapshot" else "analytical_feature_version"
    assert any(
        item["kind"] == expected_kind
        and item["id"] == str(artifact.id)
        and item["checksum"] == artifact.fingerprint
        for item in manifest
    )


@pytest.mark.parametrize("product,feature", [("SIMPA", False), ("ORDO", True)])
def test_worker_to_governed_artifact_to_domain_compute(tmp_path, monkeypatch, product, feature):
    case, artifact_type, artifact = _governed_artifact(
        tmp_path, monkeypatch, product=product, feature=feature)
    if product == "SIMPA":
        dimension = SimpaDimension(code="TEST_DIM", name_sr="Test")
        case["db"].add(dimension); case["db"].flush()
        indicator = SimpaIndicatorDefinition(
            code="TEST", name_sr="Test", dimension_code=dimension.code, unit_hint="unit",
            methodology_status="validated", methodology_note="approved")
        case["db"].add(indicator); case["db"].flush()
        case["db"].add(SimpaIndicatorMethodology(
            indicator_id=indicator.id, version_no=1, status="validated",
            computation_type="direct_observation", methodology_note="approved",
            validation_note="human approved"))
        create_domain_run, compute = create_simpa_run, compute_simpa_indicator
    else:
        pillar = OrdoPillar(code="TEST_PILLAR", name_sr="Test")
        dimension = OrdoDimension(code="TEST_DIM", name_sr="Test")
        case["db"].add_all([pillar, dimension]); case["db"].flush()
        indicator = OrdoIndicatorDefinition(
            code="TEST", name_sr="Test", dimension_code=dimension.code,
            pillar_code=pillar.code, unit_hint="unit", methodology_status="validated",
            methodology_note="approved")
        case["db"].add(indicator); case["db"].flush()
        case["db"].add(OrdoIndicatorMethodology(
            indicator_id=indicator.id, version_no=1, status="validated",
            computation_type="direct_observation", methodology_note="approved",
            validation_note="human approved"))
        create_domain_run, compute = create_ordo_run, compute_ordo_indicator
    case["db"].flush()
    domain_run = create_domain_run(
        case["db"], organization_id=case["organization"].id,
        workspace_id=case["workspace"].id, analytical_artifact_type=artifact_type,
        analytical_artifact_id=artifact.id, monitoring_cycle_id=None,
        actor_id=case["membership"].id)
    result = compute(
        case["db"], organization_id=case["organization"].id,
        workspace_id=case["workspace"].id, indicator_code="TEST",
        monitoring_cycle_id=None, analytics_run_id=domain_run.id,
        actor_id=case["membership"].id)
    assert result.value_numeric == 12.5
    assert result.source_observation_ids == []
    assert domain_run.snapshot["analytical_source"]["artifact_id"] == str(artifact.id)
    assert result.computation_trace["artifact_fingerprint"] == artifact.fingerprint

    captured = _install_fake_ai_job(case, monkeypatch, product=product)
    if product == "SIMPA":
        synthesis, job = simpa_analytics_service.create_synthesis(
            case["db"],
            organization_id=case["organization"].id,
            workspace_id=case["workspace"].id,
            analytics_run_id=domain_run.id,
            sensitivity="sensitive",
            model_key=None,
            actor_id=case["membership"].id,
        )
        _assert_ai_provenance(job, product=product, artifact=artifact)
        assert captured["input_text"] == job.request_text
        reviewed, reviewed_job = simpa_analytics_service.review_synthesis(
            case["db"],
            synthesis_id=synthesis.id,
            organization_id=case["organization"].id,
            workspace_id=case["workspace"].id,
            decision="accepted",
            reviewer_note="Synthetic E2E human review",
            actor_id=case["membership"].id,
        )
        assert reviewed.review_status == "accepted"
        assert reviewed_job.human_review_status == "accepted"
        content, manifest = simpa_reporting_adapter.build_report_payload(
            case["db"],
            organization_id=case["organization"].id,
            workspace_id=case["workspace"].id,
            report_type="monitoring_summary",
            source_kind="analytics_run",
            source_id=domain_run.id,
        )
        assert any(section.get("key") == "reviewed_ai_synthesis" for section in content["sections"])
        assert any(item["kind"] == "simpa_ai_synthesis_reviewed" for item in manifest)
        error_type = simpa_analytics_service.SimpaAnalyticsError

        def create_new_synthesis(run_id=domain_run.id):
            return simpa_analytics_service.create_synthesis(
                case["db"],
                organization_id=case["organization"].id,
                workspace_id=case["workspace"].id,
                analytics_run_id=run_id,
                sensitivity="sensitive",
                model_key=None,
                actor_id=case["membership"].id,
            )
    else:
        goal = ordo_analytics_service.create_goal(
            case["db"],
            organization_id=case["organization"].id,
            workspace_id=case["workspace"].id,
            code="E2E_GOAL",
            title="Synthetic E2E goal",
            description="Acceptance-only goal",
            focus_area="destination_development",
            target_horizon=None,
            status="active",
            actor_id=case["membership"].id,
        )
        scenario = ordo_analytics_service.create_scenario(
            case["db"],
            organization_id=case["organization"].id,
            workspace_id=case["workspace"].id,
            goal_id=goal.id,
            name="Synthetic E2E scenario",
            description="Evidence-only scenario",
            assumptions=["Synthetic assumption"],
            measures=["Synthetic measure"],
            actor_id=case["membership"].id,
        )
        assessment = ordo_analytics_service.create_scenario_assessment(
            case["db"],
            organization_id=case["organization"].id,
            workspace_id=case["workspace"].id,
            scenario_id=scenario.id,
            analytics_run_id=domain_run.id,
            actor_id=case["membership"].id,
        )
        assert assessment.status == "evidence_only"
        assert assessment.forecast_performed is False
        assert assessment.assessment["forecast_performed"] is False
        synthesis, job = ordo_analytics_service.create_synthesis(
            case["db"],
            organization_id=case["organization"].id,
            workspace_id=case["workspace"].id,
            analytics_run_id=domain_run.id,
            scenario_id=scenario.id,
            synthesis_type="scenario_review",
            model_key=None,
            actor_id=case["membership"].id,
        )
        _assert_ai_provenance(job, product=product, artifact=artifact)
        assert captured["input_text"] == job.request_text
        reviewed, reviewed_job = ordo_analytics_service.review_synthesis(
            case["db"],
            synthesis_id=synthesis.id,
            organization_id=case["organization"].id,
            workspace_id=case["workspace"].id,
            decision="accepted",
            reviewer_note="Synthetic E2E human review",
            actor_id=case["membership"].id,
        )
        assert reviewed.review_status == "accepted"
        assert reviewed_job.human_review_status == "accepted"
        content, manifest = ordo_reporting_adapter.build_report_payload(
            case["db"],
            organization_id=case["organization"].id,
            workspace_id=case["workspace"].id,
            report_type="scenario_review",
            source_kind="scenario_assessment",
            source_id=assessment.id,
        )
        assert content["forecast_performed"] is False
        assert any(section.get("key") == "reviewed_ai_synthesis" for section in content["sections"])
        assert any(item["kind"] == "ordo_ai_synthesis_reviewed" for item in manifest)
        assert any(item["kind"] == "ordo_scenario_assessment" for item in manifest)
        error_type = ordo_analytics_service.OrdoAnalyticsError

        def create_new_synthesis(run_id=domain_run.id):
            return ordo_analytics_service.create_synthesis(
                case["db"],
                organization_id=case["organization"].id,
                workspace_id=case["workspace"].id,
                analytics_run_id=run_id,
                scenario_id=scenario.id,
                synthesis_type="scenario_review",
                model_key=None,
                actor_id=case["membership"].id,
            )

    _assert_manifest_provenance(manifest, artifact_type=artifact_type, artifact=artifact)

    legacy_run = type(domain_run)(
        organization_id=case["organization"].id,
        workspace_id=case["workspace"].id,
        monitoring_cycle_id=None,
        analytical_artifact_type="LEGACY_OBSERVATION",
        analytical_snapshot_id=None,
        analytical_feature_version_id=None,
        analytical_artifact_fingerprint="",
        dataset_contract_version_id=None,
        dataset_contract_fingerprint="",
        analytical_quality_state="LEGACY_UNKNOWN",
        status="completed",
        snapshot={},
        created_by_membership_id=case["membership"].id,
    )
    case["db"].add(legacy_run)
    case["db"].flush()
    assert legacy_run.analytical_snapshot_id is None
    assert legacy_run.analytical_feature_version_id is None
    with pytest.raises(error_type, match="legacy_analytics_run_ineligible"):
        create_new_synthesis(legacy_run.id)

    original_fingerprint = domain_run.analytical_artifact_fingerprint
    domain_run.analytical_artifact_fingerprint = "f" * 64
    case["db"].flush()
    with pytest.raises(error_type, match="analytics_run_governed_binding_changed"):
        create_new_synthesis()
    domain_run.analytical_artifact_fingerprint = original_fingerprint
    case["db"].flush()

    artifact_model = AnalyticalFeatureVersion if feature else AnalyticalDatasetSnapshot
    artifact_row = case["db"].get(artifact_model, artifact.id)
    assert artifact_row is not None
    artifact_row.invalidated = True
    artifact_row.invalidation_reason = "synthetic_e2e"
    case["db"].flush()
    with pytest.raises(error_type, match="analytical_artifact_invalidated"):
        create_new_synthesis()
    artifact_row.invalidated = False
    artifact_row.invalidation_reason = ""
    artifact_row.invalidated_at = None
    artifact_row.invalidated_by_membership_id = None
    case["db"].flush()

    with pytest.raises(DataPlatformError):
        load_governed_analytical_input(
            case["db"], artifact_type=artifact_type, artifact_id=artifact.id,
            organization_id=case["organization"].id, workspace_id=case["workspace"].id,
            product_code="ORDO" if product == "SIMPA" else "SIMPA")
