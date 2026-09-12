from __future__ import annotations

from src.platform.ai.namespaces import private_namespace
from src.platform.data.analytical_service import evaluate_analytical_ai_eligibility, transition_analytical_snapshot
from test_isi_21c_analytical_governance import build_analytical_case


def test_eligibility_is_frozen_namespace_bound_and_training_denied(tmp_path):
    db, org, ws, _ws2, _ordo, member, _source, _version, _dataset, snapshot = build_analytical_case(tmp_path)
    namespace = private_namespace(org.id, "SIMPA")
    draft = evaluate_analytical_ai_eligibility(db, artifact_type="snapshot", artifact_id=snapshot.id,
        action="LOCAL_ANALYSIS", organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", namespace=namespace)
    assert not draft.allowed and draft.reason_code == "LIFECYCLE_INELIGIBLE"
    validated = transition_analytical_snapshot(db, snapshot_id=snapshot.id, organization_id=org.id, workspace_id=ws.id,
        product_code="SIMPA", expected_revision=1, target_state="VALIDATED", actor_id=member.id)
    frozen = transition_analytical_snapshot(db, snapshot_id=snapshot.id, organization_id=org.id, workspace_id=ws.id,
        product_code="SIMPA", expected_revision=validated.revision, target_state="FROZEN", actor_id=member.id)
    assert evaluate_analytical_ai_eligibility(db, artifact_type="snapshot", artifact_id=frozen.id,
        action="RAG_RETRIEVAL", organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", namespace=namespace).allowed
    mismatch = evaluate_analytical_ai_eligibility(db, artifact_type="snapshot", artifact_id=frozen.id,
        action="RAG_RETRIEVAL", organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        namespace=private_namespace(org.id, "ORDO"))
    assert not mismatch.allowed and mismatch.reason_code == "NAMESPACE_SCOPE_MISMATCH"
    training = evaluate_analytical_ai_eligibility(db, artifact_type="snapshot", artifact_id=frozen.id,
        action="MODEL_TRAINING", organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", namespace=namespace)
    assert not training.allowed and not training.requires_separate_approval
    evaluation = evaluate_analytical_ai_eligibility(db, artifact_type="snapshot", artifact_id=frozen.id,
        action="MODEL_EVALUATION", organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", namespace=namespace)
    assert not evaluation.allowed and evaluation.reason_code == "UPSTREAM_POLICY_DENIES_ACTION"


def test_training_policy_still_requires_separate_approval(tmp_path):
    db, org, ws, _ws2, _ordo, member, _source, _version, _dataset, snapshot = build_analytical_case(
        tmp_path, policy="MODEL_TRAINING_REQUIRES_SEPARATE_APPROVAL")
    validated = transition_analytical_snapshot(db, snapshot_id=snapshot.id, organization_id=org.id,
        workspace_id=ws.id, product_code="SIMPA", expected_revision=1, target_state="VALIDATED", actor_id=member.id)
    frozen = transition_analytical_snapshot(db, snapshot_id=snapshot.id, organization_id=org.id,
        workspace_id=ws.id, product_code="SIMPA", expected_revision=validated.revision,
        target_state="FROZEN", actor_id=member.id)
    decision = evaluate_analytical_ai_eligibility(db, artifact_type="snapshot", artifact_id=frozen.id,
        action="MODEL_TRAINING", organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        namespace=private_namespace(org.id, "SIMPA"))
    assert not decision.allowed and decision.requires_separate_approval
    assert decision.reason_code == "MODEL_TRAINING_SEPARATE_APPROVAL_REQUIRED"
