from __future__ import annotations

import copy
import hashlib
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import src.platform.models  # noqa: F401
from src.core.database import Base
from src.platform.access.models import Product
from src.platform.ai.evaluation import (
    AIEvaluationError,
    append_evaluation_result,
    append_evaluation_review,
    cases_sha256,
    create_evaluation_run,
    dataset_fingerprint,
    finalize_evaluation_run,
    load_evaluation_manifest,
    register_evaluation_dataset,
)
from src.platform.ai.governance import register_model
from src.platform.ai.models import AIEvaluationResult, AIEvaluationReview, AIModelRegistration
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def evaluation_case():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        marker = uuid.uuid4().hex
        db.add_all([Product(code="SIMPA", name="SIMPA"), Product(code="ORDO", name="ORDO")])
        user = User(email=f"{marker}@example.test", display_name="Evaluator")
        organization = Organization(slug=f"org-{marker}", name="Organization")
        db.add_all([user, organization])
        db.flush()
        actor = Membership(user_id=user.id, organization_id=organization.id)
        db.add(actor)
        db.flush()
        workspace = Workspace(
            organization_id=organization.id,
            product_code="SIMPA",
            slug="simpa",
            name="SIMPA",
            created_by_membership_id=actor.id,
        )
        db.add(workspace)
        db.flush()
        registration = register_model(
            db,
            organization_id=organization.id,
            workspace_id=workspace.id,
            product_code="SIMPA",
            capability_key="simpa.llm.grounded_synthesis",
            product_scope="SIMPA",
            model_family="llm",
            model_key="synthetic-foundation-model",
            version="1.0.0",
            lifecycle_state="candidate",
            actor_id=actor.id,
            provenance={"source": "synthetic-test"},
        )
        yield db, organization, workspace, actor, registration


def test_frozen_manifests_have_deterministic_hash_and_contract_markers():
    for name, product in (("SIMPA-EVAL-v1.json", "SIMPA"), ("ORDO-EVAL-v1.json", "ORDO")):
        manifest = load_evaluation_manifest(ROOT / "tests/evals" / name)
        assert manifest["product_code"] == product
        assert manifest["cases_sha256"] == cases_sha256(manifest["cases"])
        assert manifest["case_count"] == len(manifest["cases"])
        assert manifest["frozen"] is True
        assert manifest["foundation_only_not_production_promotion_evidence"] is True
        assert len(dataset_fingerprint(manifest)) == 64


def test_dataset_version_identity_is_idempotent_and_frozen(evaluation_case):
    db, _organization, _workspace, actor, _registration = evaluation_case
    manifest = load_evaluation_manifest(ROOT / "tests/evals/SIMPA-EVAL-v1.json")
    first = register_evaluation_dataset(db, manifest=manifest, product_code="SIMPA", actor_id=actor.id)
    same = register_evaluation_dataset(db, manifest=manifest, product_code="SIMPA", actor_id=actor.id)
    assert same.id == first.id and first.version == "1.0.0"
    changed = copy.deepcopy(manifest)
    changed["cases"][0]["notes"] = "Changed content requires a new version."
    changed["cases_sha256"] = cases_sha256(changed["cases"])
    with pytest.raises(AIEvaluationError, match="new_version_required"):
        register_evaluation_dataset(db, manifest=changed, product_code="SIMPA", actor_id=actor.id)


def test_run_result_terminal_and_review_foundation_is_immutable(evaluation_case):
    db, organization, workspace, actor, registration = evaluation_case
    manifest = load_evaluation_manifest(ROOT / "tests/evals/SIMPA-EVAL-v1.json")
    dataset = register_evaluation_dataset(db, manifest=manifest, product_code="SIMPA", actor_id=actor.id)
    run = create_evaluation_run(
        db,
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
        dataset_id=dataset.id,
        model_registration_id=registration.id,
        baseline_registration_id=None,
        prompt_version_id=None,
        policy_profile_id=None,
        input_fingerprint=hashlib.sha256(b"synthetic-input-provenance").hexdigest(),
        environment_fingerprint=hashlib.sha256(b"synthetic-environment").hexdigest(),
        provenance={"code_sha": "synthetic-not-a-production-sha"},
        actor_id=actor.id,
    )
    assert run.status == "created" and run.baseline_registration_id is None
    result = append_evaluation_result(
        db,
        run=run,
        result_type="evidence",
        result_key="loader_contract",
        payload={"validated": True, "scoring_performed": False},
        actor_id=actor.id,
    )
    assert run.status == "running" and result.sequence_no == 1 and len(result.fingerprint) == 64
    finalize_evaluation_run(db, run=run, status="completed")
    terminal_fingerprint = run.result_fingerprint
    assert terminal_fingerprint and len(terminal_fingerprint) == 64 and run.completed_at
    with pytest.raises(AIEvaluationError, match="terminal_evaluation_run_immutable"):
        append_evaluation_result(
            db,
            run=run,
            result_type="metric",
            result_key="not_calculated",
            payload={},
            actor_id=actor.id,
        )
    with pytest.raises(AIEvaluationError, match="terminal_evaluation_run_immutable"):
        finalize_evaluation_run(db, run=run, status="failed", failure_reason="cannot rewrite terminal state")
    review = append_evaluation_review(
        db,
        run=run,
        reviewer_membership_id=actor.id,
        decision="approved",
        notes="Foundation persistence reviewed; no quality or promotion conclusion.",
        evidence_reference="synthetic://review/1",
    )
    assert review.is_final and len(review.fingerprint) == 64
    with pytest.raises(AIEvaluationError, match="final_evaluation_review_immutable"):
        append_evaluation_review(
            db,
            run=run,
            reviewer_membership_id=actor.id,
            decision="rejected",
            notes="Attempted rewrite",
            evidence_reference="synthetic://review/2",
        )
    assert run.result_fingerprint == terminal_fingerprint
    assert db.scalar(select(AIModelRegistration).where(AIModelRegistration.lifecycle_state == "champion")) is None
    assert db.query(AIEvaluationResult).count() == 1
    assert db.query(AIEvaluationReview).count() == 1


def test_failed_run_has_stable_bounded_terminal_outcome(evaluation_case):
    db, organization, workspace, actor, registration = evaluation_case
    dataset = register_evaluation_dataset(
        db,
        manifest=load_evaluation_manifest(ROOT / "tests/evals/SIMPA-EVAL-v1.json"),
        product_code="SIMPA",
        actor_id=actor.id,
    )
    run = create_evaluation_run(
        db,
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
        dataset_id=dataset.id,
        model_registration_id=registration.id,
        baseline_registration_id=None,
        prompt_version_id=None,
        policy_profile_id=None,
        input_fingerprint="a" * 64,
        environment_fingerprint="b" * 64,
        provenance={},
        actor_id=actor.id,
    )
    finalize_evaluation_run(db, run=run, status="failed", failure_reason="synthetic_foundation_failure")
    assert run.status == "failed" and run.failure_reason == "synthetic_foundation_failure"
    assert len(run.result_fingerprint or "") == 64
