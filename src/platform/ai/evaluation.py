from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.platform.ai.governance import canonical_json, fingerprint
from src.platform.ai.models import (
    AIEvaluationDataset,
    AIEvaluationResult,
    AIEvaluationReview,
    AIEvaluationRun,
    AIModelRegistration,
    AIPolicyProfile,
    AIPrompt,
    AIPromptVersion,
)


FOUNDATION_ONLY_MARKER = "foundation_only_not_production_promotion_evidence"
TERMINAL_RUN_STATUSES = frozenset({"completed", "failed"})
MUTABLE_RUN_STATUSES = frozenset({"created", "running"})


class AIEvaluationError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def cases_sha256(cases: list[dict[str, Any]]) -> str:
    return hashlib.sha256(canonical_json(cases).encode("utf-8")).hexdigest()


def validate_evaluation_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    required = {
        "dataset_key",
        "version",
        "product_code",
        "schema_version",
        "capability_coverage",
        "cases_sha256",
        "case_count",
        "source_provenance",
        "sensitivity_classification",
        "frozen",
        "frozen_at",
        "owner",
        "approval_state",
        FOUNDATION_ONLY_MARKER,
        "cases",
    }
    if not isinstance(manifest, dict) or not required.issubset(manifest):
        raise AIEvaluationError("evaluation_manifest_missing_required_fields")
    if manifest["product_code"] not in {"SIMPA", "ORDO"}:
        raise AIEvaluationError("evaluation_manifest_product_invalid")
    cases = manifest["cases"]
    if not isinstance(cases, list) or not cases or not all(isinstance(item, dict) for item in cases):
        raise AIEvaluationError("evaluation_manifest_cases_invalid")
    if manifest["case_count"] != len(cases):
        raise AIEvaluationError("evaluation_manifest_case_count_mismatch")
    if manifest["cases_sha256"] != cases_sha256(cases):
        raise AIEvaluationError("evaluation_manifest_cases_hash_mismatch")
    case_ids = [item.get("case_id") for item in cases]
    if any(not isinstance(case_id, str) or not case_id for case_id in case_ids) or len(case_ids) != len(
        set(case_ids)
    ):
        raise AIEvaluationError("evaluation_manifest_case_identity_invalid")
    if manifest["frozen"] is not True or manifest[FOUNDATION_ONLY_MARKER] is not True:
        raise AIEvaluationError("evaluation_manifest_foundation_contract_invalid")
    if manifest["approval_state"] != "approved":
        raise AIEvaluationError("evaluation_manifest_not_approved")
    if manifest["sensitivity_classification"] != "synthetic_non_production":
        raise AIEvaluationError("evaluation_manifest_sensitivity_invalid")
    if not isinstance(manifest["capability_coverage"], list) or not manifest["capability_coverage"]:
        raise AIEvaluationError("evaluation_manifest_capability_coverage_invalid")
    try:
        datetime.fromisoformat(str(manifest["frozen_at"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise AIEvaluationError("evaluation_manifest_frozen_at_invalid") from exc
    return manifest


def load_evaluation_manifest(path: str | Path) -> dict[str, Any]:
    try:
        manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AIEvaluationError("evaluation_manifest_unreadable") from exc
    if not isinstance(manifest, dict):
        raise AIEvaluationError("evaluation_manifest_missing_required_fields")
    return validate_evaluation_manifest(manifest)


def dataset_fingerprint(manifest: dict[str, Any]) -> str:
    return fingerprint(manifest)


def register_evaluation_dataset(
    session: Session,
    *,
    manifest: dict[str, Any],
    product_code: str,
    actor_id: uuid.UUID | None,
) -> AIEvaluationDataset:
    manifest = validate_evaluation_manifest(manifest)
    if manifest["product_code"] != product_code:
        raise AIEvaluationError("evaluation_dataset_product_scope_mismatch")
    existing = session.scalar(
        select(AIEvaluationDataset).where(
            AIEvaluationDataset.dataset_key == manifest["dataset_key"],
            AIEvaluationDataset.version == manifest["version"],
        )
    )
    identity_fingerprint = dataset_fingerprint(manifest)
    if existing is not None:
        if existing.dataset_fingerprint != identity_fingerprint or existing.manifest_json != manifest:
            raise AIEvaluationError("frozen_evaluation_dataset_immutable_new_version_required")
        return existing
    try:
        frozen_at = datetime.fromisoformat(str(manifest["frozen_at"]).replace("Z", "+00:00"))
    except (KeyError, ValueError) as exc:
        raise AIEvaluationError("evaluation_manifest_frozen_at_invalid") from exc
    row = AIEvaluationDataset(
        dataset_key=str(manifest["dataset_key"]),
        version=str(manifest["version"]),
        product_code=product_code,
        schema_version=str(manifest["schema_version"]),
        capability_coverage=list(manifest["capability_coverage"]),
        cases_sha256=str(manifest["cases_sha256"]),
        case_count=int(manifest["case_count"]),
        source_provenance=str(manifest["source_provenance"]),
        sensitivity=str(manifest["sensitivity_classification"]),
        frozen=True,
        frozen_at=frozen_at,
        approval_state="approved",
        owner=str(manifest["owner"]),
        foundation_only_not_production_promotion_evidence=True,
        manifest_json=manifest,
        dataset_fingerprint=identity_fingerprint,
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    return row


def list_evaluation_datasets(session: Session, *, product_code: str) -> list[AIEvaluationDataset]:
    return list(
        session.scalars(
            select(AIEvaluationDataset)
            .where(AIEvaluationDataset.product_code == product_code)
            .order_by(AIEvaluationDataset.dataset_key, AIEvaluationDataset.version)
        ).all()
    )


def _registration_for_product(
    session: Session, registration_id: uuid.UUID, product_code: str
) -> AIModelRegistration:
    registration = session.get(AIModelRegistration, registration_id)
    if registration is None or registration.product_scope not in {"SHARED", product_code}:
        raise AIEvaluationError("evaluation_model_registration_not_accessible")
    if registration.lifecycle_state == "retired" or not registration.enabled:
        raise AIEvaluationError("evaluation_model_registration_not_enabled")
    return registration


def create_evaluation_run(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    dataset_id: uuid.UUID,
    model_registration_id: uuid.UUID,
    baseline_registration_id: uuid.UUID | None,
    prompt_version_id: uuid.UUID | None,
    policy_profile_id: uuid.UUID | None,
    input_fingerprint: str,
    environment_fingerprint: str,
    provenance: dict[str, Any],
    actor_id: uuid.UUID | None,
) -> AIEvaluationRun:
    dataset = session.get(AIEvaluationDataset, dataset_id)
    if dataset is None or dataset.product_code != product_code:
        raise AIEvaluationError("evaluation_dataset_not_accessible")
    if not dataset.frozen or dataset.approval_state != "approved":
        raise AIEvaluationError("evaluation_dataset_not_frozen")
    registration = _registration_for_product(session, model_registration_id, product_code)
    baseline = None
    if baseline_registration_id is not None:
        baseline = _registration_for_product(session, baseline_registration_id, product_code)
        if baseline.capability_key != registration.capability_key or baseline.model_family != registration.model_family:
            raise AIEvaluationError("evaluation_baseline_capability_mismatch")
    if prompt_version_id is not None:
        prompt_version = session.get(AIPromptVersion, prompt_version_id)
        if prompt_version is None:
            raise AIEvaluationError("evaluation_prompt_version_not_found")
        prompt = session.get(AIPrompt, prompt_version.prompt_id)
        if prompt is None or prompt.product_scope not in {"SHARED", product_code}:
            raise AIEvaluationError("evaluation_prompt_not_accessible")
    if policy_profile_id is not None:
        profile = session.get(AIPolicyProfile, policy_profile_id)
        if profile is None or profile.product_scope not in {"SHARED", product_code}:
            raise AIEvaluationError("evaluation_policy_not_accessible")
    for value, code in (
        (input_fingerprint, "evaluation_input_fingerprint_invalid"),
        (environment_fingerprint, "evaluation_environment_fingerprint_invalid"),
    ):
        if len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower()):
            raise AIEvaluationError(code)
    row = AIEvaluationRun(
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        dataset_id=dataset.id,
        model_registration_id=registration.id,
        baseline_registration_id=baseline.id if baseline else None,
        prompt_version_id=prompt_version_id,
        policy_profile_id=policy_profile_id,
        input_fingerprint=input_fingerprint.lower(),
        environment_fingerprint=environment_fingerprint.lower(),
        provenance=provenance,
        status="created",
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    return row


def get_evaluation_run(
    session: Session,
    *,
    run_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> AIEvaluationRun:
    row = session.scalar(
        select(AIEvaluationRun).where(
            AIEvaluationRun.id == run_id,
            AIEvaluationRun.organization_id == organization_id,
            AIEvaluationRun.workspace_id == workspace_id,
            AIEvaluationRun.product_code == product_code,
        )
    )
    if row is None:
        raise AIEvaluationError("evaluation_run_not_accessible")
    return row


def list_evaluation_runs(
    session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, product_code: str
) -> list[AIEvaluationRun]:
    return list(
        session.scalars(
            select(AIEvaluationRun)
            .where(
                AIEvaluationRun.organization_id == organization_id,
                AIEvaluationRun.workspace_id == workspace_id,
                AIEvaluationRun.product_code == product_code,
            )
            .order_by(AIEvaluationRun.created_at.desc(), AIEvaluationRun.id)
        ).all()
    )


def append_evaluation_result(
    session: Session,
    *,
    run: AIEvaluationRun,
    result_type: str,
    result_key: str,
    payload: dict[str, Any],
    actor_id: uuid.UUID | None,
) -> AIEvaluationResult:
    if run.status not in MUTABLE_RUN_STATUSES:
        raise AIEvaluationError("terminal_evaluation_run_immutable")
    if result_type not in {"metric", "safety", "reliability", "provenance", "evidence"}:
        raise AIEvaluationError("evaluation_result_type_invalid")
    sequence_no = int(
        session.scalar(
            select(func.coalesce(func.max(AIEvaluationResult.sequence_no), 0)).where(
                AIEvaluationResult.evaluation_run_id == run.id
            )
        )
        or 0
    ) + 1
    identity = {
        "payload": payload,
        "result_key": result_key,
        "result_type": result_type,
        "run_id": str(run.id),
        "sequence_no": sequence_no,
    }
    row = AIEvaluationResult(
        evaluation_run_id=run.id,
        sequence_no=sequence_no,
        result_type=result_type,
        result_key=result_key,
        payload=payload,
        fingerprint=fingerprint(identity),
        created_by_membership_id=actor_id,
    )
    session.add(row)
    if run.status == "created":
        run.status = "running"
        run.started_at = _utcnow()
    session.flush()
    return row


def list_evaluation_results(session: Session, *, run_id: uuid.UUID) -> list[AIEvaluationResult]:
    return list(
        session.scalars(
            select(AIEvaluationResult)
            .where(AIEvaluationResult.evaluation_run_id == run_id)
            .order_by(AIEvaluationResult.sequence_no)
        ).all()
    )


def finalize_evaluation_run(
    session: Session, *, run: AIEvaluationRun, status: str, failure_reason: str = ""
) -> AIEvaluationRun:
    if run.status in TERMINAL_RUN_STATUSES:
        raise AIEvaluationError("terminal_evaluation_run_immutable")
    if status not in TERMINAL_RUN_STATUSES:
        raise AIEvaluationError("evaluation_terminal_status_invalid")
    if status == "failed" and not failure_reason:
        raise AIEvaluationError("evaluation_failure_reason_required")
    if status == "completed" and failure_reason:
        raise AIEvaluationError("completed_evaluation_cannot_have_failure_reason")
    results = list_evaluation_results(session, run_id=run.id)
    terminal_identity = {
        "dataset_id": str(run.dataset_id),
        "environment_fingerprint": run.environment_fingerprint,
        "failure_reason": failure_reason,
        "input_fingerprint": run.input_fingerprint,
        "model_registration_id": str(run.model_registration_id),
        "result_fingerprints": [row.fingerprint for row in results],
        "run_id": str(run.id),
        "status": status,
    }
    run.status = status
    run.failure_reason = failure_reason
    run.result_fingerprint = fingerprint(terminal_identity)
    run.completed_at = _utcnow()
    if run.started_at is None:
        run.started_at = run.created_at if isinstance(run.created_at, datetime) else _utcnow()
    session.flush()
    return run


def append_evaluation_review(
    session: Session,
    *,
    run: AIEvaluationRun,
    reviewer_membership_id: uuid.UUID,
    decision: str,
    notes: str,
    evidence_reference: str,
) -> AIEvaluationReview:
    normalized = decision.lower()
    if normalized not in {"pending", "approved", "changes_requested", "rejected"}:
        raise AIEvaluationError("evaluation_review_decision_invalid")
    if normalized != "pending" and run.status not in TERMINAL_RUN_STATUSES:
        raise AIEvaluationError("final_evaluation_review_requires_terminal_run")
    existing_final = session.scalar(
        select(AIEvaluationReview).where(
            AIEvaluationReview.evaluation_run_id == run.id,
            AIEvaluationReview.reviewer_membership_id == reviewer_membership_id,
            AIEvaluationReview.is_final.is_(True),
        )
    )
    if existing_final is not None:
        raise AIEvaluationError("final_evaluation_review_immutable")
    reviewed_at = _utcnow()
    is_final = normalized != "pending"
    identity = {
        "decision": normalized,
        "evidence_reference": evidence_reference,
        "is_final": is_final,
        "notes": notes,
        "reviewed_at": reviewed_at.isoformat(),
        "reviewer_membership_id": str(reviewer_membership_id),
        "run_id": str(run.id),
    }
    row = AIEvaluationReview(
        evaluation_run_id=run.id,
        reviewer_membership_id=reviewer_membership_id,
        decision=normalized,
        is_final=is_final,
        notes=notes,
        evidence_reference=evidence_reference,
        fingerprint=fingerprint(identity),
        reviewed_at=reviewed_at,
    )
    session.add(row)
    session.flush()
    return row


def list_evaluation_reviews(session: Session, *, run_id: uuid.UUID) -> list[AIEvaluationReview]:
    return list(
        session.scalars(
            select(AIEvaluationReview)
            .where(AIEvaluationReview.evaluation_run_id == run_id)
            .order_by(AIEvaluationReview.reviewed_at, AIEvaluationReview.id)
        ).all()
    )
