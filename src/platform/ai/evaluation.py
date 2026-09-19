from __future__ import annotations

import hashlib
import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.platform.ai.governance import canonical_json, fingerprint, registration_fingerprint_matches
from src.platform.ai.models import (
    AICapabilityThreshold,
    AIEvaluationBenchmark,
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


def benchmark_input_fingerprint(benchmark: AIEvaluationBenchmark) -> str:
    """Bind a run to the immutable benchmark evaluation-input identity."""
    return str(fingerprint({
        "benchmark_id": str(benchmark.id),
        "manifest_fingerprint": benchmark.manifest_fingerprint,
        "cases_sha256": benchmark.cases_sha256,
        "product_code": benchmark.product_code,
        "capability_key": benchmark.capability_key,
        "model_family": benchmark.model_family,
        "schema_version": benchmark.schema_version,
    }))


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
    return str(fingerprint(manifest))


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
    if not registration_fingerprint_matches(registration):
        raise AIEvaluationError("evaluation_model_registration_fingerprint_mismatch")
    return registration


def create_evaluation_run(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    dataset_id: uuid.UUID,
    benchmark_id: uuid.UUID | None = None,
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
    benchmark = session.get(AIEvaluationBenchmark, benchmark_id) if benchmark_id else None
    if benchmark_id is not None and (
        benchmark is None
        or benchmark.product_code != product_code
        or not benchmark.frozen
        or benchmark.approval_state != "approved"
    ):
        raise AIEvaluationError("evaluation_benchmark_not_accessible")
    registration = _registration_for_product(session, model_registration_id, product_code)
    if benchmark is not None and (
        benchmark.capability_key != registration.capability_key
        or benchmark.model_family != registration.model_family
    ):
        raise AIEvaluationError("evaluation_benchmark_capability_mismatch")
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
    if benchmark is not None and input_fingerprint.lower() != benchmark_input_fingerprint(benchmark):
        raise AIEvaluationError("evaluation_input_fingerprint_benchmark_mismatch")
    row = AIEvaluationRun(
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        dataset_id=dataset.id,
        benchmark_id=benchmark.id if benchmark else None,
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
    governed_execution: bool = False,
) -> AIEvaluationResult:
    if run.status not in MUTABLE_RUN_STATUSES:
        raise AIEvaluationError("terminal_evaluation_run_immutable")
    if result_type not in {"metric", "safety", "reliability", "provenance", "evidence"}:
        raise AIEvaluationError("evaluation_result_type_invalid")
    if run.benchmark_id is not None and not governed_execution:
        raise AIEvaluationError("promotion_bound_manual_result_append_forbidden")
    if run.benchmark_id is not None and session.scalar(select(AIEvaluationResult.id).where(
        AIEvaluationResult.evaluation_run_id == run.id,
        AIEvaluationResult.result_key == result_key,
    )) is not None:
        raise AIEvaluationError(f"duplicate_authoritative_result_key:{result_key}")
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


def evaluation_result_fingerprint(row: AIEvaluationResult) -> str:
    return str(fingerprint({
        "payload": row.payload,
        "result_key": row.result_key,
        "result_type": row.result_type,
        "run_id": str(row.evaluation_run_id),
        "sequence_no": row.sequence_no,
    }))


def evaluation_terminal_fingerprint(
    session: Session, *, run: AIEvaluationRun, status: str, failure_reason: str
) -> str:
    results = list_evaluation_results(session, run_id=run.id)
    benchmark = session.get(AIEvaluationBenchmark, run.benchmark_id) if run.benchmark_id else None
    terminal_identity = {
        "organization_id": str(run.organization_id),
        "workspace_id": str(run.workspace_id),
        "product_code": run.product_code,
        "benchmark_id": str(run.benchmark_id) if run.benchmark_id else None,
        "benchmark_manifest_fingerprint": benchmark.manifest_fingerprint if benchmark else None,
        "benchmark_cases_sha256": benchmark.cases_sha256 if benchmark else None,
        "dataset_id": str(run.dataset_id),
        "environment_fingerprint": run.environment_fingerprint,
        "failure_reason": failure_reason,
        "input_fingerprint": run.input_fingerprint,
        "model_registration_id": str(run.model_registration_id),
        "baseline_registration_id": str(run.baseline_registration_id) if run.baseline_registration_id else None,
        "prompt_version_id": str(run.prompt_version_id) if run.prompt_version_id else None,
        "policy_profile_id": str(run.policy_profile_id) if run.policy_profile_id else None,
        "provenance": run.provenance,
        "result_fingerprints": [row.fingerprint for row in results],
        "run_id": str(run.id),
        "status": status,
    }
    return str(fingerprint(terminal_identity))


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
    if run.benchmark_id is not None:
        result_keys = [row.result_key for row in results]
        if len(result_keys) != len(set(result_keys)):
            raise AIEvaluationError("duplicate_authoritative_result_key")
    terminal_fingerprint = evaluation_terminal_fingerprint(
        session, run=run, status=status, failure_reason=failure_reason
    )
    run.status = status
    run.failure_reason = failure_reason
    run.result_fingerprint = terminal_fingerprint
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
    normalized_evidence_reference = evidence_reference.strip() if isinstance(evidence_reference, str) else ""
    if normalized != "pending" and not normalized_evidence_reference:
        raise AIEvaluationError("final_evaluation_review_evidence_reference_required")
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
        "evidence_reference": normalized_evidence_reference if normalized != "pending" else evidence_reference,
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
        evidence_reference=normalized_evidence_reference if normalized != "pending" else evidence_reference,
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


def evaluation_review_fingerprint(row: AIEvaluationReview) -> str:
    reviewed_at = row.reviewed_at
    if isinstance(reviewed_at, datetime):
        if reviewed_at.tzinfo is None:
            reviewed_at = reviewed_at.replace(tzinfo=timezone.utc)
        else:
            reviewed_at = reviewed_at.astimezone(timezone.utc)
        reviewed_at_value = reviewed_at.isoformat()
    else:
        reviewed_at_value = str(reviewed_at)
    return str(fingerprint({
        "decision": row.decision,
        "evidence_reference": row.evidence_reference,
        "is_final": row.is_final,
        "notes": row.notes,
        "reviewed_at": reviewed_at_value,
        "reviewer_membership_id": str(row.reviewer_membership_id),
        "run_id": str(row.evaluation_run_id),
    }))


BENCHMARK_REQUIRED_CASE_FIELDS = frozenset(
    {
        "case_id",
        "product_code",
        "domain",
        "capability",
        "language",
        "input_version",
        "expected_contract",
        "source_refs",
        "sensitivity_class",
        "methodology_version",
        "human_gold_state",
        "notes",
    }
)

PROMOTION_CANONICAL_CASE_FIELDS = BENCHMARK_REQUIRED_CASE_FIELDS

PROMOTION_OBSERVATION_FIELDS = {
    "statistical_ml": frozenset({"actual", "predicted", "probabilities"}),
    "embedding": frozenset({"retrieved_ids", "retrieved_namespaces"}),
    "llm": frozenset({
        "atomic_claims", "cited_refs", "structured_output",
        "instruction_contract_passed", "latency_ms", "serbian_human_rubric",
    }),
    "vlm": frozenset({"extracted_fields", "provenance_valid"}),
}
SAFETY_OBSERVATION_FIELDS = frozenset({"passed", "detail"})
ALL_PROMOTION_OBSERVATION_FIELDS = frozenset().union(
    *PROMOTION_OBSERVATION_FIELDS.values(), SAFETY_OBSERVATION_FIELDS
)
JSON_SCHEMA_TYPES = frozenset({"array", "boolean", "integer", "null", "number", "object", "string"})
SAFETY_BLOCKER_KINDS = frozenset({
    "missing_evidence", "contradictory_evidence", "stale_evidence", "prompt_injection",
    "pii_boundary", "cross_product", "cross_tenant", "unsupported_causal",
    "unsupported_forecast", "unsupported_scenario_impact", "fabricated_score_threshold",
    "human_review_bypass",
})


def canonical_safety_kind(case: dict[str, Any]) -> str | None:
    kind = case.get("kind")
    if kind is None and isinstance(case.get("expected_contract"), dict):
        kind = case["expected_contract"].get("kind")
    return str(kind) if isinstance(kind, str) and kind in SAFETY_BLOCKER_KINDS else None


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_benchmark_case_semantic_authority(case: dict[str, Any]) -> None:
    expected_contract = case.get("expected_contract")
    if not isinstance(expected_contract, dict):
        raise AIEvaluationError("promotion_benchmark_expected_contract_invalid")
    if ALL_PROMOTION_OBSERVATION_FIELDS.intersection(case):
        raise AIEvaluationError("promotion_benchmark_canonical_observation_forbidden")
    if ALL_PROMOTION_OBSERVATION_FIELDS.intersection(expected_contract):
        raise AIEvaluationError("promotion_benchmark_expected_observation_forbidden")
    for field in ("case_id", "language", "input_version", "sensitivity_class"):
        if not _nonempty_string(case.get(field)):
            raise AIEvaluationError(f"promotion_benchmark_case_{field}_invalid")
    methodology_version = case.get("methodology_version")
    if methodology_version is not None and not _nonempty_string(methodology_version):
        raise AIEvaluationError("promotion_benchmark_case_methodology_version_invalid")
    source_refs = case.get("source_refs")
    if (
        not isinstance(source_refs, list)
        or not source_refs
        or any(not isinstance(ref, str) or not ref.strip() for ref in source_refs)
    ):
        raise AIEvaluationError("promotion_benchmark_source_references_invalid")


def _strict_string_references(value: Any, *, code: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise AIEvaluationError(code)
    return list(value)


def _typed_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left is right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isfinite(float(left)) and math.isfinite(float(right)) and float(left) == float(right)
    return type(left) is type(right) and left == right


def _schema_type_matches(value: Any, declared: Any) -> bool:
    declared_types = [declared] if isinstance(declared, str) else declared
    if (
        not isinstance(declared_types, list)
        or not declared_types
        or any(not isinstance(item, str) or item not in JSON_SCHEMA_TYPES for item in declared_types)
    ):
        raise AIEvaluationError("llm_schema_type_contract_invalid")
    for item in declared_types:
        if item == "null" and value is None:
            return True
        if item == "boolean" and isinstance(value, bool):
            return True
        if item == "string" and isinstance(value, str):
            return True
        if item == "array" and isinstance(value, list):
            return True
        if item == "object" and isinstance(value, dict):
            return True
        if item == "number" and not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(float(value)):
            return True
        if item == "integer" and not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(float(value)) and float(value).is_integer():
            return True
    return False


def _metric(
    key: str,
    value: float | bool | None,
    *,
    direction: str,
    support: int | None = None,
    state: str = "available",
    case_refs: list[str] | None = None,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if state == "available" and direction in {"higher", "lower", "toward_zero"}:
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            raise AIEvaluationError(f"numeric_metric_value_required:{key}")
    payload = {
        "metric_key": key,
        "value": value,
        "support": support,
        "direction": direction,
        "state": state,
        "case_refs": case_refs or [],
        "evidence": evidence or {},
    }
    payload["fingerprint"] = fingerprint(payload)
    return payload


def unavailable_metric(key: str, reason: str, *, direction: str = "not_applicable") -> dict[str, Any]:
    return _metric(key, None, direction=direction, state="unavailable", evidence={"reason": reason})


def _contains_secret_material(value: Any) -> bool:
    secret_keys = {"authorization", "api_key", "apikey", "password", "secret", "access_token", "refresh_token"}
    if isinstance(value, dict):
        return any(str(key).casefold() in secret_keys or _contains_secret_material(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_secret_material(item) for item in value)
    return isinstance(value, str) and "authorization: bearer " in value.casefold()


def validate_promotion_benchmark_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    required = {
        "dataset_key", "version", "product_code", "capability_key", "model_family",
        "schema_version", "case_count", "cases_sha256", "source_provenance",
        "sensitivity_class", "frozen", "approval_state", "owner", "cases",
    }
    if not isinstance(manifest, dict) or not required.issubset(manifest):
        raise AIEvaluationError("promotion_benchmark_manifest_missing_required_fields")
    for field in (
        "dataset_key", "version", "capability_key", "schema_version",
        "source_provenance", "sensitivity_class", "owner",
    ):
        if not _nonempty_string(manifest.get(field)):
            raise AIEvaluationError(f"promotion_benchmark_{field}_invalid")
    if manifest["dataset_key"] in {"SIMPA-EVAL-v1", "ORDO-EVAL-v1"} or manifest.get(FOUNDATION_ONLY_MARKER):
        raise AIEvaluationError("foundation_fixture_cannot_be_promotion_benchmark")
    if manifest["product_code"] not in {"SIMPA", "ORDO"}:
        raise AIEvaluationError("promotion_benchmark_product_invalid")
    if manifest["model_family"] not in {"statistical_ml", "embedding", "llm", "vlm"}:
        raise AIEvaluationError("promotion_benchmark_family_invalid")
    cases = manifest["cases"]
    if not isinstance(cases, list) or not cases or manifest["case_count"] != len(cases):
        raise AIEvaluationError("promotion_benchmark_cases_invalid")
    case_ids: list[str] = []
    for case in cases:
        if not isinstance(case, dict) or not BENCHMARK_REQUIRED_CASE_FIELDS.issubset(case):
            raise AIEvaluationError("promotion_benchmark_case_metadata_invalid")
        if case["product_code"] != manifest["product_code"] or case["domain"] != manifest["product_code"]:
            raise AIEvaluationError("promotion_benchmark_case_scope_mismatch")
        if case["capability"] != manifest["capability_key"]:
            raise AIEvaluationError("promotion_benchmark_case_capability_mismatch")
        if case["human_gold_state"] not in {"approved", "not_applicable"}:
            raise AIEvaluationError("promotion_benchmark_human_gold_state_invalid")
        _validate_benchmark_case_semantic_authority(case)
        case_ids.append(str(case["case_id"]))
    if any(not item for item in case_ids) or len(case_ids) != len(set(case_ids)):
        raise AIEvaluationError("promotion_benchmark_case_identity_invalid")
    if manifest["cases_sha256"] != cases_sha256(cases):
        raise AIEvaluationError("promotion_benchmark_cases_hash_mismatch")
    if manifest["frozen"] is not True or manifest["approval_state"] != "approved":
        raise AIEvaluationError("promotion_benchmark_not_frozen_approved")
    if _contains_secret_material(manifest):
        raise AIEvaluationError("promotion_benchmark_embedded_secret_forbidden")
    return manifest


def canonical_benchmark_execution_cases(
    benchmark: AIEvaluationBenchmark,
    submitted_cases: list[dict[str, Any]],
    *,
    evaluator_family: str | None = None,
) -> list[dict[str, Any]]:
    """Validate the exact frozen case set and merge observations without rewriting truth."""
    if (
        not benchmark.frozen
        or benchmark.approval_state != "approved"
        or not isinstance(benchmark.manifest_json, dict)
    ):
        raise AIEvaluationError("promotion_benchmark_not_frozen_approved")
    canonical_cases = benchmark.manifest_json.get("cases")
    if not isinstance(canonical_cases, list) or not canonical_cases:
        raise AIEvaluationError("promotion_benchmark_cases_invalid")
    if (
        fingerprint(benchmark.manifest_json) != benchmark.manifest_fingerprint
        or cases_sha256(canonical_cases) != benchmark.cases_sha256
    ):
        raise AIEvaluationError("promotion_benchmark_integrity_mismatch")
    if not isinstance(submitted_cases, list) or not submitted_cases or not all(
        isinstance(case, dict) for case in submitted_cases
    ):
        raise AIEvaluationError("promotion_benchmark_case_set_mismatch")
    submitted_ids = [case.get("case_id") for case in submitted_cases]
    canonical_ids = [case.get("case_id") for case in canonical_cases]
    if (
        any(not isinstance(case_id, str) or not case_id for case_id in submitted_ids)
        or len(submitted_ids) != len(set(submitted_ids))
        or set(submitted_ids) != set(canonical_ids)
    ):
        raise AIEvaluationError("promotion_benchmark_case_set_mismatch")
    family = evaluator_family or benchmark.model_family
    if family not in PROMOTION_OBSERVATION_FIELDS:
        raise AIEvaluationError("evaluation_evaluator_family_mismatch")
    submitted_by_id = {str(case["case_id"]): case for case in submitted_cases}
    merged_cases: list[dict[str, Any]] = []
    for canonical in sorted(canonical_cases, key=lambda item: str(item["case_id"])):
        _validate_benchmark_case_semantic_authority(canonical)
        submitted = submitted_by_id[str(canonical["case_id"])]
        expected_contract = canonical.get("expected_contract")
        if not isinstance(expected_contract, dict):
            raise AIEvaluationError("promotion_benchmark_case_metadata_mismatch")
        merged = dict(canonical)
        for key, value in expected_contract.items():
            if key in merged and merged[key] != value:
                raise AIEvaluationError("promotion_benchmark_case_metadata_mismatch")
            merged[key] = value
        safety_kind = canonical_safety_kind(merged)
        declared_kind = merged.get("kind")
        if declared_kind is not None and safety_kind is None:
            raise AIEvaluationError("promotion_benchmark_safety_kind_invalid")
        observation_fields = (
            SAFETY_OBSERVATION_FIELDS if safety_kind is not None
            else PROMOTION_OBSERVATION_FIELDS[family]
        )
        for key, value in submitted.items():
            if key == "case_id":
                continue
            if key in canonical or key in expected_contract:
                if value != merged.get(key):
                    raise AIEvaluationError("promotion_benchmark_case_metadata_mismatch")
                continue
            if key not in observation_fields:
                raise AIEvaluationError("promotion_benchmark_observation_field_forbidden")
            if key == "detail" and (not isinstance(value, str) or len(value) > 2000):
                raise AIEvaluationError("safety_detail_invalid")
            merged[key] = value
        merged_cases.append(merged)
    return merged_cases


def governed_execution_cases(
    session: Session,
    *,
    run: AIEvaluationRun,
    submitted_cases: list[dict[str, Any]],
    evaluator_family: str | None = None,
) -> list[dict[str, Any]]:
    if run.benchmark_id is None:
        if not isinstance(submitted_cases, list) or not submitted_cases or any(
            not isinstance(case, dict) for case in submitted_cases
        ):
            raise AIEvaluationError("evaluation_cases_required")
        return submitted_cases
    benchmark = session.get(AIEvaluationBenchmark, run.benchmark_id)
    if benchmark is None:
        raise AIEvaluationError("evaluation_benchmark_not_accessible")
    registration = session.get(AIModelRegistration, run.model_registration_id)
    if (
        registration is None
        or not registration.enabled
        or registration.lifecycle_state == "retired"
        or registration.product_scope not in {"SHARED", run.product_code}
        or registration.model_family != benchmark.model_family
        or evaluator_family != registration.model_family
    ):
        raise AIEvaluationError("evaluation_evaluator_family_mismatch")
    if not registration_fingerprint_matches(registration):
        raise AIEvaluationError("evaluation_model_registration_fingerprint_mismatch")
    if run.input_fingerprint != benchmark_input_fingerprint(benchmark):
        raise AIEvaluationError("evaluation_input_fingerprint_benchmark_mismatch")
    return canonical_benchmark_execution_cases(
        benchmark, submitted_cases, evaluator_family=evaluator_family
    )


def benchmark_execution_provenance(
    session: Session,
    *,
    run: AIEvaluationRun,
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    benchmark = session.get(AIEvaluationBenchmark, run.benchmark_id) if run.benchmark_id else None
    registration = session.get(AIModelRegistration, run.model_registration_id)
    canonical_cases = (
        benchmark.manifest_json.get("cases")
        if benchmark is not None and isinstance(benchmark.manifest_json, dict)
        else None
    )
    valid = bool(
        benchmark is not None
        and registration is not None
        and registration.enabled
        and registration.lifecycle_state != "retired"
        and registration.product_scope in {"SHARED", run.product_code}
        and registration_fingerprint_matches(registration)
        and registration.model_family == benchmark.model_family
        and benchmark.product_code == run.product_code
        and benchmark.capability_key == registration.capability_key
        and benchmark.frozen
        and benchmark.approval_state == "approved"
        and isinstance(canonical_cases, list)
        and cases_sha256(canonical_cases) == benchmark.cases_sha256
        and fingerprint(benchmark.manifest_json) == benchmark.manifest_fingerprint
        and run.input_fingerprint == benchmark_input_fingerprint(benchmark)
    )
    case_refs = sorted(str(case.get("case_id")) for case in cases if case.get("case_id"))
    source_refs_set: set[str] = set()
    for case in cases:
        refs = case.get("source_refs", [])
        if (
            not isinstance(refs, list)
            or any(not isinstance(ref, str) or not ref.strip() for ref in refs)
        ):
            valid = False
            continue
        source_refs_set.update(ref for ref in refs if ref)
    source_refs = sorted(source_refs_set)
    if not source_refs:
        valid = False
    return _metric(
        "benchmark_execution_provenance",
        valid,
        direction="exact",
        support=len(case_refs),
        case_refs=case_refs,
        evidence={
            "run_id": str(run.id),
            "organization_id": str(run.organization_id),
            "workspace_id": str(run.workspace_id),
            "product_code": run.product_code,
            "benchmark_id": str(benchmark.id) if benchmark else None,
            "benchmark_manifest_fingerprint": benchmark.manifest_fingerprint if benchmark else None,
            "benchmark_cases_sha256": benchmark.cases_sha256 if benchmark else None,
            "canonical_input_fingerprint": run.input_fingerprint,
            "model_registration_id": str(run.model_registration_id),
            "model_family": registration.model_family if registration else None,
            "source_refs": source_refs,
            "semantic_scope": "execution_identity_only",
        },
    )


def register_promotion_benchmark(
    session: Session, *, manifest: dict[str, Any], product_code: str, actor_id: uuid.UUID | None
) -> AIEvaluationBenchmark:
    manifest = validate_promotion_benchmark_manifest(manifest)
    if manifest["product_code"] != product_code:
        raise AIEvaluationError("promotion_benchmark_product_scope_mismatch")
    manifest_hash = fingerprint(manifest)
    existing = session.scalar(
        select(AIEvaluationBenchmark).where(
            AIEvaluationBenchmark.dataset_key == manifest["dataset_key"],
            AIEvaluationBenchmark.version == manifest["version"],
        )
    )
    if existing is not None:
        if existing.manifest_fingerprint != manifest_hash or existing.manifest_json != manifest:
            raise AIEvaluationError("frozen_promotion_benchmark_immutable_new_version_required")
        return existing
    row = AIEvaluationBenchmark(
        dataset_key=str(manifest["dataset_key"]), version=str(manifest["version"]),
        product_code=product_code, capability_key=str(manifest["capability_key"]),
        model_family=str(manifest["model_family"]), schema_version=str(manifest["schema_version"]),
        case_count=int(manifest["case_count"]), cases_sha256=str(manifest["cases_sha256"]),
        manifest_fingerprint=manifest_hash, source_provenance=str(manifest["source_provenance"]),
        sensitivity_class=str(manifest["sensitivity_class"]),
        methodology_version=manifest.get("methodology_version"), frozen=True, approval_state="approved",
        owner=str(manifest["owner"]), manifest_json=manifest, created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    return row


def list_promotion_benchmarks(session: Session, *, product_code: str) -> list[AIEvaluationBenchmark]:
    return list(session.scalars(select(AIEvaluationBenchmark).where(
        AIEvaluationBenchmark.product_code == product_code
    ).order_by(AIEvaluationBenchmark.dataset_key, AIEvaluationBenchmark.version)).all())


def _finite_number(value: Any, *, code: str, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AIEvaluationError(code)
    number = float(value)
    if not math.isfinite(number) or (nonnegative and number < 0):
        raise AIEvaluationError(code)
    return number


def validate_threshold_profile_contract(
    *,
    metric_definitions: dict[str, Any],
    minimum_thresholds: dict[str, Any],
    minimum_deltas: dict[str, Any],
    hard_gates: dict[str, Any],
    resource_limits: dict[str, Any],
    failure_threshold: int,
    cooldown_seconds: int,
) -> None:
    if (
        not isinstance(metric_definitions, dict)
        or not metric_definitions
        or not isinstance(minimum_thresholds, dict)
        or not isinstance(minimum_deltas, dict)
        or not isinstance(hard_gates, dict)
        or not isinstance(resource_limits, dict)
        or isinstance(failure_threshold, bool)
        or not isinstance(failure_threshold, int)
        or failure_threshold < 1
        or isinstance(cooldown_seconds, bool)
        or not isinstance(cooldown_seconds, int)
        or cooldown_seconds < 0
    ):
        raise AIEvaluationError("threshold_profile_contract_invalid")

    valid_directions = {"higher", "lower", "exact", "toward_zero"}
    for key, definition in metric_definitions.items():
        if not isinstance(key, str) or not key or not isinstance(definition, dict):
            raise AIEvaluationError(f"threshold_metric_definition_invalid:{key}")
        direction = definition.get("direction")
        if direction not in valid_directions:
            raise AIEvaluationError(f"threshold_metric_definition_invalid:{key}")
        warning = definition.get("drift_warning_delta")
        blocker = definition.get("drift_blocker_delta")
        warning_value = None
        blocker_value = None
        if warning is not None:
            warning_value = _finite_number(
                warning, code=f"threshold_drift_warning_invalid:{key}", nonnegative=True
            )
        if blocker is not None:
            blocker_value = _finite_number(
                blocker, code=f"threshold_drift_blocker_invalid:{key}", nonnegative=True
            )
        if warning_value is not None and blocker_value is not None and blocker_value < warning_value:
            raise AIEvaluationError(f"threshold_drift_order_invalid:{key}")

    for key, threshold in minimum_thresholds.items():
        definition = metric_definitions.get(key)
        if not isinstance(definition, dict):
            raise AIEvaluationError(f"threshold_metric_not_defined:{key}")
        value = _finite_number(threshold, code=f"minimum_threshold_invalid:{key}")
        if definition.get("direction") == "toward_zero" and value < 0:
            raise AIEvaluationError(f"threshold_toward_zero_absolute_invalid:{key}")

    for key, delta in minimum_deltas.items():
        if key not in metric_definitions:
            raise AIEvaluationError(f"threshold_metric_not_defined:{key}")
        _finite_number(delta, code=f"minimum_delta_invalid:{key}", nonnegative=True)

    for key, required in hard_gates.items():
        if not isinstance(key, str) or not key or not isinstance(required, bool):
            raise AIEvaluationError(f"hard_gate_boolean_required:{key}")

    for key, maximum in resource_limits.items():
        if not isinstance(key, str) or not key:
            raise AIEvaluationError("resource_limit_key_invalid")
        _finite_number(maximum, code=f"resource_limit_invalid:{key}", nonnegative=True)


def threshold_profile_identity(profile: AICapabilityThreshold) -> dict[str, Any]:
    return {
        "product_scope": profile.product_scope,
        "capability_key": profile.capability_key,
        "model_family": profile.model_family,
        "version": profile.version,
        "metric_definitions": profile.metric_definitions,
        "minimum_thresholds": profile.minimum_thresholds,
        "minimum_deltas": profile.minimum_deltas,
        "hard_gates": profile.hard_gates,
        "resource_limits": profile.resource_limits,
        "failure_threshold": profile.failure_threshold,
        "cooldown_seconds": profile.cooldown_seconds,
        "provenance": profile.provenance,
    }


def threshold_profile_fingerprint_matches(profile: AICapabilityThreshold) -> bool:
    return fingerprint(threshold_profile_identity(profile)) == profile.fingerprint


def register_threshold_profile(
    session: Session, *, product_scope: str, capability_key: str, model_family: str, version: str,
    metric_definitions: dict[str, Any], minimum_thresholds: dict[str, Any], minimum_deltas: dict[str, Any],
    hard_gates: dict[str, Any], resource_limits: dict[str, Any], failure_threshold: int,
    cooldown_seconds: int, provenance: str, actor_id: uuid.UUID | None,
    product_code: str | None = None,
) -> AICapabilityThreshold:
    if product_scope not in {"SHARED", "SIMPA", "ORDO"} or model_family not in {
        "statistical_ml", "embedding", "llm", "vlm"
    }:
        raise AIEvaluationError("threshold_profile_scope_or_family_invalid")
    if product_code is not None and product_scope not in {"SHARED", product_code}:
        raise AIEvaluationError("threshold_profile_product_scope_mismatch")
    validate_threshold_profile_contract(
        metric_definitions=metric_definitions,
        minimum_thresholds=minimum_thresholds,
        minimum_deltas=minimum_deltas,
        hard_gates=hard_gates,
        resource_limits=resource_limits,
        failure_threshold=failure_threshold,
        cooldown_seconds=cooldown_seconds,
    )
    identity = {
        "product_scope": product_scope, "capability_key": capability_key, "model_family": model_family,
        "version": version, "metric_definitions": metric_definitions, "minimum_thresholds": minimum_thresholds,
        "minimum_deltas": minimum_deltas, "hard_gates": hard_gates, "resource_limits": resource_limits,
        "failure_threshold": failure_threshold, "cooldown_seconds": cooldown_seconds, "provenance": provenance,
    }
    digest = fingerprint(identity)
    existing = session.scalar(select(AICapabilityThreshold).where(
        AICapabilityThreshold.product_scope == product_scope,
        AICapabilityThreshold.capability_key == capability_key,
        AICapabilityThreshold.model_family == model_family,
        AICapabilityThreshold.version == version,
    ))
    if existing is not None:
        if existing.fingerprint != digest:
            raise AIEvaluationError("threshold_profile_immutable_new_version_required")
        return existing
    row = AICapabilityThreshold(
        **identity, fingerprint=digest, enabled=True, created_by_membership_id=actor_id
    )
    session.add(row)
    session.flush()
    return row


def list_threshold_profiles(session: Session, *, product_code: str) -> list[AICapabilityThreshold]:
    return list(session.scalars(select(AICapabilityThreshold).where(
        AICapabilityThreshold.product_scope.in_(["SHARED", product_code])
    ).order_by(AICapabilityThreshold.capability_key, AICapabilityThreshold.version)).all())


def _numeric_sequence(value: Any, *, code: str) -> list[float]:
    if not isinstance(value, list) or any(
        isinstance(item, bool)
        or not isinstance(item, (int, float))
        or not math.isfinite(float(item))
        for item in value
    ):
        raise AIEvaluationError(code)
    return [float(item) for item in value]


def aggregate_evaluation_metrics(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create one deterministic authoritative row per metric key."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in metrics:
        if not isinstance(item, dict) or not isinstance(item.get("metric_key"), str):
            raise AIEvaluationError("evaluator_result_contract_invalid")
        grouped.setdefault(item["metric_key"], []).append(item)
    aggregated: list[dict[str, Any]] = []
    for key in sorted(grouped):
        components = grouped[key]
        directions = {item.get("direction") for item in components}
        if len(directions) != 1:
            raise AIEvaluationError(f"evaluator_result_direction_ambiguous:{key}")
        direction = str(next(iter(directions)))
        case_refs = sorted({
            str(ref)
            for item in components
            for ref in item.get("case_refs", [])
            if str(ref)
        })
        states = [str(item.get("state", "available")) for item in components]
        component_fingerprints = [str(item.get("fingerprint", "")) for item in components]
        evidence = {
            "aggregation_rule": "all" if direction == "exact" else "support_weighted_mean",
            "component_count": len(components),
            "component_fingerprints": component_fingerprints,
        }
        if any(state in {"unavailable", "invalid"} for state in states):
            aggregated.append(_metric(
                key, None, direction=direction, state="unavailable", case_refs=case_refs,
                evidence={**evidence, "reason": "component_evidence_unavailable"},
            ))
            continue
        available = [item for item in components if item.get("state", "available") == "available"]
        if not available:
            aggregated.append(_metric(
                key, None, direction=direction, state="not_applicable", case_refs=case_refs,
                evidence=evidence,
            ))
            continue
        values = [item.get("value") for item in available]
        if direction == "exact":
            value: float | bool | None = all(value is True for value in values)
            support = sum(int(item.get("support") or 0) for item in available)
        else:
            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                for value in values
            ):
                aggregated.append(_metric(
                    key, None, direction=direction, state="unavailable", case_refs=case_refs,
                    evidence={**evidence, "reason": "numeric_component_evidence_required"},
                ))
                continue
            weights = [int(item.get("support") or 0) for item in available]
            if sum(weights) > 0:
                value = sum(float(item["value"]) * weight for item, weight in zip(available, weights, strict=True)) / sum(weights)
                support = sum(weights)
            else:
                value = sum(float(item["value"]) for item in available) / len(available)
                support = len(available)
        evidence["aggregate_support"] = support
        aggregated.append(_metric(
            key, value, direction=direction, support=support, case_refs=case_refs, evidence=evidence,
        ))
    return aggregated


def evaluate_regression(expected: list[float], actual: list[float]) -> list[dict[str, Any]]:
    expected_values = _numeric_sequence(expected, code="regression_expected_numeric_array_required")
    actual_values = _numeric_sequence(actual, code="regression_actual_numeric_array_required")
    if len(expected_values) != len(actual_values) or not expected_values:
        return [
            unavailable_metric(
                key, "non_empty_equal_length_arrays_required",
                direction="toward_zero" if key == "bias" else "lower",
            )
            for key in ("mae", "rmse", "bias")
        ]
    errors = [pred - gold for gold, pred in zip(expected_values, actual_values, strict=True)]
    count = len(errors)
    return [
        _metric("mae", sum(abs(item) for item in errors) / count, direction="lower", support=count),
        _metric("rmse", math.sqrt(sum(item * item for item in errors) / count), direction="lower", support=count),
        _metric("bias", sum(errors) / count, direction="toward_zero", support=count),
    ]


def evaluate_classification(
    expected: list[int], predicted: list[int], probabilities: list[float] | None = None
) -> list[dict[str, Any]]:
    if not isinstance(expected, list) or not isinstance(predicted, list):
        raise AIEvaluationError("classification_binary_arrays_required")
    if len(expected) != len(predicted) or not expected or any(
        isinstance(value, bool) or value not in {0, 1} for value in expected + predicted
    ):
        return [unavailable_metric(key, "binary_equal_length_arrays_required") for key in ("precision", "recall", "f1", "brier")]
    tp = sum(gold == 1 and pred == 1 for gold, pred in zip(expected, predicted, strict=True))
    fp = sum(gold == 0 and pred == 1 for gold, pred in zip(expected, predicted, strict=True))
    fn = sum(gold == 1 and pred == 0 for gold, pred in zip(expected, predicted, strict=True))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    results = [
        _metric("precision", precision, direction="higher", support=tp + fp),
        _metric("recall", recall, direction="higher", support=tp + fn),
        _metric("f1", f1, direction="higher", support=len(expected)),
    ]
    if probabilities is not None and not isinstance(probabilities, list):
        raise AIEvaluationError("classification_probability_array_required")
    if probabilities is None or len(probabilities) != len(expected) or any(
        isinstance(value, bool) or not isinstance(value, (int, float))
        or not math.isfinite(float(value)) or not 0 <= float(value) <= 1
        for value in probabilities
    ):
        results.append(unavailable_metric("brier", "bounded_probability_evidence_required", direction="lower"))
    else:
        results.append(_metric("brier", sum((prob - gold) ** 2 for gold, prob in zip(expected, probabilities, strict=True)) / len(expected), direction="lower", support=len(expected)))
    return results


def evaluate_retrieval(cases: list[dict[str, Any]], *, k: int) -> list[dict[str, Any]]:
    if isinstance(k, bool) or not isinstance(k, int):
        raise AIEvaluationError("retrieval_positive_integer_k_required")
    if not isinstance(cases, list) or any(not isinstance(case, dict) for case in cases):
        raise AIEvaluationError("retrieval_case_objects_required")
    if k < 1 or not cases:
        return [unavailable_metric(key, "non_empty_cases_and_positive_k_required") for key in ("recall_at_k", "mrr", "ndcg_at_k", "namespace_isolation")]
    recalls: list[float] = []
    reciprocal: list[float] = []
    ndcgs: list[float] = []
    isolation = True
    isolation_reason: str | None = None
    for case in cases:
        relevant_ids = case.get("relevant_ids", [])
        retrieved_ids = case.get("retrieved_ids", [])
        if not isinstance(relevant_ids, list) or not isinstance(retrieved_ids, list):
            raise AIEvaluationError("retrieval_id_arrays_required")
        raw_retrieved = list(retrieved_ids)[:k]
        try:
            relevant = {(type(item), item) for item in relevant_ids}
            retrieved_keys = [(type(item), item) for item in raw_retrieved]
        except TypeError as exc:
            raise AIEvaluationError("retrieval_ids_must_be_hashable") from exc
        seen: set[tuple[type[Any], Any]] = set()
        retrieved: list[tuple[type[Any], Any]] = []
        for item in retrieved_keys:
            if item not in seen:
                seen.add(item)
                retrieved.append(item)
        recalls.append(min(1.0, len(relevant.intersection(retrieved)) / len(relevant)) if relevant else 0.0)
        ranks = [index + 1 for index, item in enumerate(retrieved) if item in relevant]
        reciprocal.append(min(1.0, 1.0 / min(ranks)) if ranks else 0.0)
        dcg = sum(1.0 / math.log2(index + 2) for index, item in enumerate(retrieved) if item in relevant)
        ideal = sum(1.0 / math.log2(index + 2) for index in range(min(len(relevant), k)))
        ndcgs.append(min(1.0, max(0.0, dcg / ideal)) if ideal else 0.0)
        expected_namespace = case.get("allowed_namespace")
        namespaces = case.get("retrieved_namespaces")
        if not isinstance(expected_namespace, str) or not expected_namespace:
            isolation = False
            isolation_reason = isolation_reason or "retrieval_allowed_namespace_required"
        elif (
            not isinstance(namespaces, list)
            or not namespaces
            or len(namespaces) != len(raw_retrieved)
            or any(not isinstance(namespace, str) or not namespace for namespace in namespaces)
        ):
            isolation = False
            isolation_reason = isolation_reason or "retrieval_namespace_evidence_required"
        elif any(ns != expected_namespace for ns in namespaces):
            isolation = False
            isolation_reason = isolation_reason or "retrieval_namespace_mismatch"
    support = len(cases)
    return [
        _metric("recall_at_k", sum(recalls) / support, direction="higher", support=support),
        _metric("mrr", sum(reciprocal) / support, direction="higher", support=support),
        _metric("ndcg_at_k", sum(ndcgs) / support, direction="higher", support=support),
        _metric(
            "namespace_isolation", isolation, direction="exact", support=support,
            evidence={"reason": isolation_reason} if isolation_reason else {},
        ),
    ]


def evaluate_llm_case(
    case: dict[str, Any],
    *,
    authorized_reviewer_membership_id: uuid.UUID | None = None,
) -> list[dict[str, Any]]:
    if not isinstance(case, dict):
        raise AIEvaluationError("llm_case_object_required")
    raw_claims = case.get("atomic_claims", [])
    if not isinstance(raw_claims, list) or any(not isinstance(item, dict) for item in raw_claims):
        raise AIEvaluationError("llm_atomic_claims_invalid")
    claims = list(raw_claims)
    if any(not isinstance(item.get("supported"), bool) for item in claims):
        raise AIEvaluationError("llm_claim_supported_boolean_required")
    supported = sum(item["supported"] is True for item in claims)
    total = len(claims)
    factuality = supported / total if total else None
    unsupported = (total - supported) / total if total else None
    schema = case.get("schema")
    schema_supplied = isinstance(schema, dict) and bool(schema)
    schema_value = schema if isinstance(schema, dict) else {}
    schema_required_value = schema_value.get("required", [])
    properties = schema_value.get("properties", {})
    if (
        not isinstance(schema_required_value, list)
        or any(not isinstance(key, str) for key in schema_required_value)
        or not isinstance(properties, dict)
        or any(not isinstance(key, str) or not isinstance(definition, dict) for key, definition in properties.items())
    ):
        raise AIEvaluationError("llm_schema_contract_invalid")
    for definition in properties.values():
        if "type" in definition:
            _schema_type_matches(None, definition["type"])
        if "enum" in definition and not isinstance(definition["enum"], list):
            raise AIEvaluationError("llm_schema_enum_contract_invalid")
    schema_required = list(schema_required_value)
    raw_output = case.get("structured_output")
    output = raw_output if isinstance(raw_output, dict) else {}
    parse_ok = isinstance(raw_output, dict)
    required_ok = parse_ok and all(key in output for key in schema_required)
    types_ok = parse_ok and all(
        "type" not in definition or _schema_type_matches(output[key], definition["type"])
        for key, definition in properties.items()
        if key in output
    )
    enums_ok = parse_ok and all(
        "enum" not in definition
        or any(_typed_equal(output[key], option) for option in definition["enum"])
        for key, definition in properties.items()
        if key in output
    )
    source_refs = _strict_string_references(
        case.get("source_refs", []), code="llm_source_references_string_required"
    )
    cited = _strict_string_references(
        case.get("cited_refs", []), code="llm_cited_references_string_required"
    )
    supplied_refs = set(source_refs)
    cited_refs = set(cited)
    provenance_ok = cited_refs.issubset(supplied_refs) and bool(cited_refs or not claims)
    rubric = case.get("serbian_human_rubric")
    rubric_metric = unavailable_metric("serbian_human_rubric", "authorized_human_rubric_not_supplied", direction="higher")
    if rubric is not None and not isinstance(rubric, dict):
        raise AIEvaluationError("serbian_human_rubric_invalid")
    if isinstance(rubric, dict) and authorized_reviewer_membership_id is not None:
        values = rubric.get("scores", [])
        maximum = rubric.get("maximum", 5)
        evidence_reference = rubric.get("evidence_reference")
        if (
            isinstance(values, list)
            and isinstance(maximum, (int, float))
            and not isinstance(maximum, bool)
            and math.isfinite(float(maximum))
            and values
            and maximum > 0
            and all(
                isinstance(value, (int, float)) and not isinstance(value, bool)
                and math.isfinite(float(value)) and 0 <= value <= maximum
                for value in values
            )
            and isinstance(evidence_reference, str)
            and 0 < len(evidence_reference.strip()) <= 500
        ):
            rubric_metric = _metric(
                "serbian_human_rubric",
                sum(values) / (len(values) * maximum),
                direction="higher",
                support=len(values),
                evidence={
                    "raw_scores": values,
                    "maximum": maximum,
                    "reviewer_membership_id": str(authorized_reviewer_membership_id),
                    "evidence_reference": evidence_reference.strip(),
                    "authorization_source": "server_scope_and_permission",
                },
            )
        else:
            raise AIEvaluationError("serbian_human_rubric_invalid")
    instruction_value = case.get("instruction_contract_passed", False)
    if not isinstance(instruction_value, bool):
        raise AIEvaluationError("instruction_contract_boolean_required")
    latency_value = case.get("latency_ms")
    if latency_value is not None and (
        isinstance(latency_value, bool)
        or not isinstance(latency_value, (int, float))
        or not math.isfinite(float(latency_value))
        or float(latency_value) < 0
    ):
        raise AIEvaluationError("latency_ms_non_negative_finite_number_required")
    return [
        _metric("grounded_factuality", factuality, direction="higher", support=total, state="available" if total else "not_applicable"),
        _metric("unsupported_claim_rate", unsupported, direction="lower", support=total, state="available" if total else "not_applicable"),
        _metric("structured_parse", parse_ok if schema_supplied else None, direction="exact", support=1 if schema_supplied else 0, state="available" if schema_supplied else "not_applicable"),
        _metric("structured_required_fields", required_ok if schema_supplied else None, direction="exact", support=len(schema_required), state="available" if schema_supplied else "not_applicable"),
        _metric("structured_enum_compliance", enums_ok if schema_supplied else None, direction="exact", support=1 if schema_supplied else 0, state="available" if schema_supplied else "not_applicable"),
        _metric("structured_schema_compliance", (parse_ok and required_ok and types_ok and enums_ok) if schema_supplied else None, direction="exact", support=1 if schema_supplied else 0, state="available" if schema_supplied else "not_applicable"),
        _metric("provenance_compliance", provenance_ok, direction="exact", support=len(cited_refs)),
        _metric("instruction_refusal_contract", instruction_value, direction="exact", support=1),
        rubric_metric,
        _metric("latency_ms", latency_value, direction="lower", support=1, state="available" if latency_value is not None else "unavailable"),
    ]


def evaluate_vlm_case(case: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(case, dict):
        raise AIEvaluationError("vlm_case_object_required")
    gold = case.get("expected_fields")
    actual = case.get("extracted_fields")
    if not isinstance(gold, dict) or not isinstance(actual, dict) or not gold:
        return [unavailable_metric("normalized_field_accuracy", "expected_and_extracted_fields_required"), unavailable_metric("numeric_transcription_accuracy", "numeric_gold_required"), unavailable_metric("vlm_provenance", "source_reference_evidence_required")]
    def normalize(value: Any) -> str:
        return " ".join(str(value).casefold().split())
    field_accuracy = sum(normalize(actual.get(key, "")) == normalize(value) for key, value in gold.items()) / len(gold)
    numeric_keys: list[str] = []
    for key, value in gold.items():
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            if not math.isfinite(float(value)):
                raise AIEvaluationError("vlm_numeric_gold_finite_required")
            numeric_keys.append(key)
    numeric_matches = 0
    for key in numeric_keys:
        observed = actual.get(key)
        if (
            not isinstance(observed, bool)
            and isinstance(observed, (int, float))
            and math.isfinite(float(observed))
            and float(observed) == float(gold[key])
        ):
            numeric_matches += 1
    numeric_accuracy = numeric_matches / len(numeric_keys) if numeric_keys else None
    source_refs = _strict_string_references(
        case.get("source_refs", []), code="vlm_source_references_string_required"
    )
    provenance_valid = case.get("provenance_valid", False)
    if not isinstance(provenance_valid, bool):
        raise AIEvaluationError("vlm_provenance_boolean_required")
    return [
        _metric("normalized_field_accuracy", field_accuracy, direction="higher", support=len(gold)),
        _metric("numeric_transcription_accuracy", numeric_accuracy, direction="higher", support=len(numeric_keys), state="available" if numeric_keys else "unavailable"),
        _metric("vlm_provenance", bool(source_refs) and provenance_valid, direction="exact", support=1),
    ]


def evaluate_safety_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(cases, list) or any(not isinstance(case, dict) for case in cases):
        raise AIEvaluationError("safety_case_objects_required")
    results: list[dict[str, Any]] = []
    for case in cases:
        kind = canonical_safety_kind(case) or ""
        passed = case.get("passed")
        if not isinstance(passed, bool):
            raise AIEvaluationError("safety_passed_boolean_required")
        blocker = kind in SAFETY_BLOCKER_KINDS and not passed
        results.append(_metric(
            f"safety.{kind or 'unknown'}", passed, direction="exact", support=1,
            case_refs=[str(case.get("case_id", ""))], evidence={"blocker": blocker, "detail": case.get("detail", "")},
        ))
    return results
