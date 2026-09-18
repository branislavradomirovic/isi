from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.platform.ai.models import (
    AIAuditEvent,
    AIModel,
    AIModelFallback,
    AIModelRegistration,
    AIPrompt,
    AIPromptRollbackTarget,
    AIPromptVersion,
)
from src.platform.ai.policy import EffectivePolicy, provider_allowed


SUPPORTED_MODEL_FAMILIES = frozenset({"statistical_ml", "embedding", "llm", "vlm"})
CREATABLE_LIFECYCLE_STATES = frozenset({"candidate", "challenger"})
CHAMPION_FORBIDDEN_REASON = "champion_promotion_requires_isi_25b_evaluation_and_approval_evidence"


class AIGovernanceError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _scope_compatible(left: str, right: str) -> bool:
    return left == right or "SHARED" in {left, right}


def _visible_in_product(product_scope: str, product_code: str) -> bool:
    return product_scope in {"SHARED", product_code}


def _audit(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    actor_id: uuid.UUID | None,
    event_type: str,
    entity_type: str,
    entity_id: uuid.UUID,
    detail: str,
) -> None:
    session.add(
        AIAuditEvent(
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
            actor_membership_id=actor_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            detail=detail,
        )
    )


def registration_identity(
    *,
    capability_key: str,
    product_scope: str,
    model_family: str,
    model_key: str,
    runtime_model_id: uuid.UUID | None,
    provider_name: str | None,
    runtime_name: str | None,
    version: str,
    revision: str | None,
    artifact_uri: str | None,
    artifact_checksum: str | None,
    provenance: dict[str, Any],
) -> dict[str, Any]:
    return {
        "artifact_checksum": artifact_checksum,
        "artifact_uri": artifact_uri,
        "capability_key": capability_key,
        "model_family": model_family,
        "model_key": model_key,
        "product_scope": product_scope,
        "provenance": provenance,
        "provider_name": provider_name,
        "revision": revision,
        "runtime_model_id": str(runtime_model_id) if runtime_model_id else None,
        "runtime_name": runtime_name,
        "version": version,
    }


def register_model(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    capability_key: str,
    product_scope: str,
    model_family: str,
    model_key: str,
    version: str,
    lifecycle_state: str,
    actor_id: uuid.UUID | None,
    runtime_model_id: uuid.UUID | None = None,
    provider_name: str | None = None,
    runtime_name: str | None = None,
    revision: str | None = None,
    artifact_uri: str | None = None,
    artifact_checksum: str | None = None,
    provenance: dict[str, Any] | None = None,
) -> AIModelRegistration:
    scope = product_scope.upper()
    family = model_family.lower()
    state = lifecycle_state.lower()
    if scope not in {"SHARED", "SIMPA", "ORDO"} or not _visible_in_product(scope, product_code):
        raise AIGovernanceError("model_registration_product_scope_mismatch")
    if family not in SUPPORTED_MODEL_FAMILIES:
        raise AIGovernanceError("unsupported_model_family")
    if state == "champion":
        raise AIGovernanceError(CHAMPION_FORBIDDEN_REASON)
    if state not in CREATABLE_LIFECYCLE_STATES:
        raise AIGovernanceError("model_registration_lifecycle_not_creatable")
    runtime_model = session.get(AIModel, runtime_model_id) if runtime_model_id else None
    if runtime_model_id and runtime_model is None:
        raise AIGovernanceError("runtime_model_not_found")
    if runtime_model is not None:
        expected_purpose = "embedding" if family == "embedding" else "chat"
        if family != "statistical_ml" and runtime_model.purpose != expected_purpose:
            raise AIGovernanceError("runtime_model_family_mismatch")
        if family == "statistical_ml":
            raise AIGovernanceError("statistical_model_cannot_reference_provider_runtime")
        if not _scope_compatible(scope, runtime_model.product_scope):
            raise AIGovernanceError("runtime_model_product_scope_mismatch")
        provider_name = provider_name or runtime_model.provider_name
        runtime_name = runtime_name or runtime_model.model_name
    if artifact_checksum is not None and (len(artifact_checksum) != 64 or any(c not in "0123456789abcdef" for c in artifact_checksum.lower())):
        raise AIGovernanceError("artifact_checksum_must_be_sha256")
    if artifact_checksum is not None:
        artifact_checksum = artifact_checksum.lower()
    provenance_value = provenance or {}
    identity = registration_identity(
        capability_key=capability_key,
        product_scope=scope,
        model_family=family,
        model_key=model_key,
        runtime_model_id=runtime_model_id,
        provider_name=provider_name,
        runtime_name=runtime_name,
        version=version,
        revision=revision,
        artifact_uri=artifact_uri,
        artifact_checksum=artifact_checksum,
        provenance=provenance_value,
    )
    registry_fingerprint = fingerprint(identity)
    if session.scalar(
        select(AIModelRegistration).where(AIModelRegistration.registry_fingerprint == registry_fingerprint)
    ) is not None:
        raise AIGovernanceError("model_registration_already_exists")
    row = AIModelRegistration(
        capability_key=capability_key,
        product_scope=scope,
        model_family=family,
        model_key=model_key,
        runtime_model_id=runtime_model_id,
        provider_name=provider_name,
        runtime_name=runtime_name,
        version=version,
        revision=revision,
        artifact_uri=artifact_uri,
        artifact_checksum=artifact_checksum,
        provenance=provenance_value,
        registry_fingerprint=registry_fingerprint,
        lifecycle_state=state,
        enabled=True,
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    _audit(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        actor_id=actor_id,
        event_type="ai.governance.model_registered",
        entity_type="ai_model_registration",
        entity_id=row.id,
        detail=f"capability={capability_key};state={state};fingerprint={registry_fingerprint}",
    )
    session.flush()
    return row


def list_registrations(
    session: Session, *, product_code: str, capability_key: str | None = None
) -> list[AIModelRegistration]:
    statement = select(AIModelRegistration).order_by(
        AIModelRegistration.capability_key, AIModelRegistration.created_at, AIModelRegistration.id
    )
    if capability_key is not None:
        statement = statement.where(AIModelRegistration.capability_key == capability_key)
    return [row for row in session.scalars(statement).all() if _visible_in_product(row.product_scope, product_code)]


def retire_registration(
    session: Session,
    *,
    registration_id: uuid.UUID,
    product_code: str,
    actor_id: uuid.UUID | None,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> AIModelRegistration:
    row = session.get(AIModelRegistration, registration_id)
    if row is None or not _visible_in_product(row.product_scope, product_code):
        raise AIGovernanceError("model_registration_not_accessible")
    if row.lifecycle_state == "champion":
        raise AIGovernanceError(CHAMPION_FORBIDDEN_REASON)
    if row.lifecycle_state == "retired":
        return row
    row.lifecycle_state = "retired"
    row.enabled = False
    row.retired_by_membership_id = actor_id
    row.retired_at = _utcnow()
    _audit(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        actor_id=actor_id,
        event_type="ai.governance.model_retired",
        entity_type="ai_model_registration",
        entity_id=row.id,
        detail=f"fingerprint={row.registry_fingerprint}",
    )
    session.flush()
    return row


def transition_registration_lifecycle(*_: Any, target_state: str, **__: Any) -> None:
    if target_state.lower() == "champion":
        raise AIGovernanceError(CHAMPION_FORBIDDEN_REASON)
    raise AIGovernanceError("lifecycle_transition_not_available_in_isi_25a")


def _would_create_cycle(
    session: Session, *, source_registration_id: uuid.UUID, target_registration_id: uuid.UUID
) -> bool:
    adjacency: dict[uuid.UUID, set[uuid.UUID]] = {}
    for edge in session.scalars(select(AIModelFallback)).all():
        adjacency.setdefault(edge.source_registration_id, set()).add(edge.target_registration_id)
    adjacency.setdefault(source_registration_id, set()).add(target_registration_id)
    pending = [target_registration_id]
    seen: set[uuid.UUID] = set()
    while pending:
        current = pending.pop()
        if current == source_registration_id:
            return True
        if current in seen:
            continue
        seen.add(current)
        pending.extend(adjacency.get(current, ()))
    return False


def register_fallback(
    session: Session,
    *,
    source_registration_id: uuid.UUID,
    target_registration_id: uuid.UUID,
    priority: int,
    trigger_codes: list[str],
    semantically_equivalent: bool,
    requires_human_review: bool,
    provenance: str,
    actor_id: uuid.UUID | None,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> AIModelFallback:
    source = session.get(AIModelRegistration, source_registration_id)
    target = session.get(AIModelRegistration, target_registration_id)
    if source is None or target is None:
        raise AIGovernanceError("fallback_registration_not_found")
    if source.id == target.id:
        raise AIGovernanceError("fallback_self_reference_forbidden")
    if not _visible_in_product(source.product_scope, product_code) or not _visible_in_product(
        target.product_scope, product_code
    ):
        raise AIGovernanceError("fallback_product_scope_mismatch")
    if source.capability_key != target.capability_key or source.model_family != target.model_family:
        raise AIGovernanceError("fallback_capability_mismatch")
    if not _scope_compatible(source.product_scope, target.product_scope):
        raise AIGovernanceError("fallback_product_scope_mismatch")
    if source.lifecycle_state == "retired" or target.lifecycle_state == "retired" or not source.enabled or not target.enabled:
        raise AIGovernanceError("fallback_registration_not_enabled")
    if priority < 1:
        raise AIGovernanceError("fallback_priority_invalid")
    if not trigger_codes:
        raise AIGovernanceError("fallback_trigger_codes_required")
    if session.scalar(
        select(AIModelFallback).where(
            AIModelFallback.source_registration_id == source.id,
            AIModelFallback.target_registration_id == target.id,
        )
    ) is not None:
        raise AIGovernanceError("fallback_relationship_already_registered")
    if session.scalar(
        select(AIModelFallback).where(
            AIModelFallback.source_registration_id == source.id,
            AIModelFallback.priority == priority,
        )
    ) is not None:
        raise AIGovernanceError("fallback_priority_already_registered")
    if _would_create_cycle(
        session, source_registration_id=source_registration_id, target_registration_id=target_registration_id
    ):
        raise AIGovernanceError("fallback_cycle_forbidden")
    normalized_triggers = sorted(set(trigger_codes))
    identity = {
        "priority": priority,
        "requires_human_review": bool(requires_human_review),
        "semantically_equivalent": bool(semantically_equivalent),
        "source_fingerprint": source.registry_fingerprint,
        "target_fingerprint": target.registry_fingerprint,
        "trigger_codes": normalized_triggers,
    }
    row = AIModelFallback(
        source_registration_id=source.id,
        target_registration_id=target.id,
        priority=priority,
        trigger_codes=normalized_triggers,
        semantically_equivalent=semantically_equivalent,
        requires_human_review=requires_human_review,
        fingerprint=fingerprint(identity),
        provenance=provenance,
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    _audit(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        actor_id=actor_id,
        event_type="ai.governance.fallback_registered",
        entity_type="ai_model_fallback",
        entity_id=row.id,
        detail=f"source={source.registry_fingerprint};target={target.registry_fingerprint};priority={priority}",
    )
    session.flush()
    return row


def list_fallbacks(
    session: Session, *, product_code: str, source_registration_id: uuid.UUID | None = None
) -> list[AIModelFallback]:
    statement = select(AIModelFallback).order_by(AIModelFallback.source_registration_id, AIModelFallback.priority)
    if source_registration_id is not None:
        statement = statement.where(AIModelFallback.source_registration_id == source_registration_id)
    result: list[AIModelFallback] = []
    for row in session.scalars(statement).all():
        source = session.get(AIModelRegistration, row.source_registration_id)
        target = session.get(AIModelRegistration, row.target_registration_id)
        if source and target and _visible_in_product(source.product_scope, product_code) and _visible_in_product(
            target.product_scope, product_code
        ):
            result.append(row)
    return result


def authorized_runtime_fallbacks(
    session: Session,
    *,
    selected: AIModel,
    product_code: str,
    policy: EffectivePolicy,
) -> list[AIModel]:
    """Return only explicitly registered runtime fallbacks, in deterministic priority order."""

    source = session.scalar(
        select(AIModelRegistration)
        .where(
            AIModelRegistration.runtime_model_id == selected.id,
            AIModelRegistration.enabled.is_(True),
            AIModelRegistration.lifecycle_state != "retired",
        )
        .order_by(AIModelRegistration.created_at, AIModelRegistration.id)
        .limit(1)
    )
    if source is None or not _visible_in_product(source.product_scope, product_code):
        return []
    result: list[AIModel] = []
    for edge in session.scalars(
        select(AIModelFallback)
        .where(AIModelFallback.source_registration_id == source.id)
        .order_by(AIModelFallback.priority, AIModelFallback.id)
    ).all():
        target = session.get(AIModelRegistration, edge.target_registration_id)
        if (
            target is None
            or not target.enabled
            or target.lifecycle_state == "retired"
            or target.capability_key != source.capability_key
            or not _visible_in_product(target.product_scope, product_code)
            or target.runtime_model_id is None
        ):
            continue
        runtime = session.get(AIModel, target.runtime_model_id)
        if runtime is None or not runtime.enabled or runtime.purpose != selected.purpose:
            continue
        if not _visible_in_product(runtime.product_scope, product_code):
            continue
        if not provider_allowed(policy=policy, local_provider=runtime.local_provider):
            continue
        result.append(runtime)
    return result


def runtime_fallback_allows_error(
    session: Session,
    *,
    selected: AIModel,
    target: AIModel,
    product_code: str,
    error_code: str,
) -> bool:
    source_registration = session.scalar(
        select(AIModelRegistration)
        .where(
            AIModelRegistration.runtime_model_id == selected.id,
            AIModelRegistration.enabled.is_(True),
            AIModelRegistration.lifecycle_state != "retired",
        )
        .order_by(AIModelRegistration.created_at, AIModelRegistration.id)
        .limit(1)
    )
    if source_registration is None or not _visible_in_product(source_registration.product_scope, product_code):
        return False
    target_registration = session.scalar(
        select(AIModelRegistration)
        .where(
            AIModelRegistration.runtime_model_id == target.id,
            AIModelRegistration.enabled.is_(True),
            AIModelRegistration.lifecycle_state != "retired",
            AIModelRegistration.capability_key == source_registration.capability_key,
        )
        .order_by(AIModelRegistration.created_at, AIModelRegistration.id)
        .limit(1)
    )
    if target_registration is None:
        return False
    edge = session.scalar(
        select(AIModelFallback).where(
            AIModelFallback.source_registration_id == source_registration.id,
            AIModelFallback.target_registration_id == target_registration.id,
        )
    )
    return edge is not None and ("*" in edge.trigger_codes or error_code in edge.trigger_codes)


def register_prompt_rollback(
    session: Session,
    *,
    source_prompt_version_id: uuid.UUID,
    target_prompt_version_id: uuid.UUID,
    provenance: str,
    actor_id: uuid.UUID | None,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> AIPromptRollbackTarget:
    source = session.get(AIPromptVersion, source_prompt_version_id)
    target = session.get(AIPromptVersion, target_prompt_version_id)
    if source is None or target is None:
        raise AIGovernanceError("prompt_version_not_found")
    if source.id == target.id:
        raise AIGovernanceError("prompt_rollback_self_reference_forbidden")
    if source.prompt_id != target.prompt_id:
        raise AIGovernanceError("prompt_rollback_requires_same_prompt")
    prompt = session.get(AIPrompt, source.prompt_id)
    if prompt is None or not _visible_in_product(prompt.product_scope, product_code):
        raise AIGovernanceError("prompt_rollback_not_accessible")
    if target.version_no >= source.version_no:
        raise AIGovernanceError("prompt_rollback_target_must_be_prior_version")
    identity = {
        "source_checksum": source.checksum,
        "source_prompt_version_id": str(source.id),
        "source_version": source.version_no,
        "target_checksum": target.checksum,
        "target_prompt_version_id": str(target.id),
        "target_version": target.version_no,
    }
    if session.scalar(
        select(AIPromptRollbackTarget).where(
            AIPromptRollbackTarget.source_prompt_version_id == source_prompt_version_id
        )
    ) is not None:
        raise AIGovernanceError("prompt_rollback_source_already_registered")
    row = AIPromptRollbackTarget(
        source_prompt_version_id=source.id,
        target_prompt_version_id=target.id,
        source_checksum=source.checksum,
        target_checksum=target.checksum,
        fingerprint=fingerprint(identity),
        provenance=provenance,
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    _audit(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        actor_id=actor_id,
        event_type="ai.governance.prompt_rollback_registered",
        entity_type="ai_prompt_rollback_target",
        entity_id=row.id,
        detail=f"fingerprint={row.fingerprint};source_checksum={source.checksum};target_checksum={target.checksum}",
    )
    session.flush()
    return row


def list_prompt_rollbacks(session: Session, *, product_code: str) -> list[AIPromptRollbackTarget]:
    rows = list(
        session.scalars(
            select(AIPromptRollbackTarget).order_by(AIPromptRollbackTarget.created_at, AIPromptRollbackTarget.id)
        ).all()
    )
    result: list[AIPromptRollbackTarget] = []
    for row in rows:
        version = session.get(AIPromptVersion, row.source_prompt_version_id)
        prompt = session.get(AIPrompt, version.prompt_id) if version else None
        if prompt is not None and _visible_in_product(prompt.product_scope, product_code):
            result.append(row)
    return result
