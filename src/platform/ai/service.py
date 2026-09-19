from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.platform.ai.embeddings import persist_native_vector
from src.platform.ai.gateway import GatewayError, provider_for_model
from src.platform.ai.governance import (
    AIGovernanceError,
    authorized_runtime_fallbacks,
    resolve_bound_runtime_registration,
)
from src.platform.ai.models import (
    AIAuditEvent,
    AIEmbedding,
    AIJob,
    AIJobAttempt,
    AICapabilityRuntimeState,
    AIModel,
    AIModelFallback,
    AIModelRegistration,
    AIPolicyProfile,
    AIPrompt,
    AIPromptVersion,
)
from src.platform.ai.namespaces import assert_namespace_access
from src.platform.ai.policy import EffectivePolicy, provider_allowed, resolve_effective_policy
from src.platform.ai.providers import CompletionRequest, ProviderError
from src.platform.ai.schemas import AIEmbeddingResponse, AIJobResponse, AIModelResponse, AIPromptResponse, AIPromptVersionResponse
from src.platform.ai.structured import StructuredOutputError, parse_structured_output
from src.platform.identity.models import Membership


class AIServiceError(ValueError):
    pass


def _utcnow():
    return datetime.now(timezone.utc)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def actor_membership_id(session: Session, *, user_id: uuid.UUID, organization_id: uuid.UUID) -> uuid.UUID | None:
    membership = session.scalar(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.organization_id == organization_id,
            Membership.status == "active",
        )
    )
    return membership.id if membership is not None else None


def _product_matches(scope: str, product_code: str) -> bool:
    return scope == "SHARED" or scope == product_code


def bootstrap_ai_registry(session: Session, *, include_dev_stub: bool | None = None) -> None:
    settings = get_settings()
    if include_dev_stub is None:
        include_dev_stub = bool(getattr(settings, "ai_allow_dev_stub", False)) and str(getattr(settings, "isi_env", "development")).lower() != "production"

    model_rows = [
        {
            "model_key": "isi-ollama-chat-default",
            "provider_type": "ollama",
            "provider_name": "ollama",
            "model_name": str(getattr(settings, "ai_ollama_chat_model", "qwen2.5:7b-instruct")),
            "purpose": "chat",
            "product_scope": "SHARED",
            "local_provider": True,
            "timeout_seconds": int(getattr(settings, "ai_request_timeout_seconds", 120)),
        },
        {
            "model_key": "isi-ollama-embedding-default",
            "provider_type": "ollama",
            "provider_name": "ollama",
            "model_name": str(getattr(settings, "ai_ollama_embedding_model", "nomic-embed-text")),
            "purpose": "embedding",
            "product_scope": "SHARED",
            "local_provider": True,
            "timeout_seconds": int(getattr(settings, "ai_request_timeout_seconds", 120)),
        },
    ]
    if include_dev_stub:
        model_rows.extend(
            [
                {
                    "model_key": "isi-dev-stub-chat",
                    "provider_type": "stub",
                    "provider_name": "development-stub",
                    "model_name": "isi07-deterministic-diagnostic",
                    "purpose": "chat",
                    "product_scope": "SHARED",
                    "local_provider": True,
                    "timeout_seconds": 5,
                },
                {
                    "model_key": "isi-dev-stub-embedding",
                    "provider_type": "stub",
                    "provider_name": "development-stub",
                    "model_name": "isi07-deterministic-embedding",
                    "purpose": "embedding",
                    "product_scope": "SHARED",
                    "local_provider": True,
                    "embedding_dimensions": 16,
                    "timeout_seconds": 5,
                },
            ]
        )
    for values in model_rows:
        row = session.scalar(select(AIModel).where(AIModel.model_key == values["model_key"]))
        if row is None:
            row = AIModel(**values, enabled=True)
            session.add(row)
        else:
            for key, value in values.items():
                setattr(row, key, value)
            row.enabled = True

    prompt = session.scalar(select(AIPrompt).where(AIPrompt.prompt_key == "foundation.diagnostic"))
    if prompt is None:
        prompt = AIPrompt(
            prompt_key="foundation.diagnostic",
            product_scope="SHARED",
            title="Shared AI foundation diagnostic",
            purpose="Infrastructure-only structured diagnostic; not domain intelligence",
            is_active=True,
        )
        session.add(prompt)
        session.flush()
    schema = {
        "type": "object",
        "required": ["status", "message"],
        "properties": {
            "status": {"type": "string", "enum": ["ok"]},
            "message": {"type": "string"},
        },
    }
    system_template = (
        "You are running an ISI shared AI infrastructure diagnostic. "
        "Do not provide SIMPA or ORDO domain advice. Return only a JSON object with status='ok' and a short message."
    )
    user_template = "Infrastructure diagnostic input: {input}"
    checksum = _sha256(system_template + "\n" + user_template + "\n" + json.dumps(schema, sort_keys=True))
    version = session.scalar(
        select(AIPromptVersion).where(AIPromptVersion.prompt_id == prompt.id, AIPromptVersion.version_no == 1)
    )
    if version is None:
        session.add(
            AIPromptVersion(
                prompt_id=prompt.id,
                version_no=1,
                system_template=system_template,
                user_template=user_template,
                output_schema=schema,
                checksum=checksum,
                status="active",
            )
        )
    else:
        version.system_template = system_template
        version.user_template = user_template
        version.output_schema = schema
        version.checksum = checksum
        version.status = "active"

    policies = [
        ("shared-local-only", "SHARED", "internal", "local_only", False, False, 2),
        ("shared-local-preferred", "SHARED", "internal", "local_preferred", True, True, 2),
        ("simpa-sensitive-local", "SIMPA", "sensitive", "local_only", False, True, 2),
    ]
    for key, scope, sensitivity, provider_policy, allow_external, review, attempts in policies:
        row = session.scalar(select(AIPolicyProfile).where(AIPolicyProfile.policy_key == key))
        values = {
            "product_scope": scope,
            "sensitivity": sensitivity,
            "provider_policy": provider_policy,
            "allow_external": allow_external,
            "require_human_review": review,
            "max_attempts": attempts,
            "enabled": True,
        }
        if row is None:
            session.add(AIPolicyProfile(policy_key=key, **values))
        else:
            for field, value in values.items():
                setattr(row, field, value)
    session.flush()


def list_models(session: Session, *, product_code: str, purpose: str | None = None) -> list[AIModel]:
    rows = list(session.scalars(select(AIModel).where(AIModel.enabled.is_(True)).order_by(AIModel.model_key)).all())
    result = [row for row in rows if _product_matches(row.product_scope, product_code)]
    if purpose is not None:
        result = [row for row in result if row.purpose == purpose]
    settings = get_settings()
    if str(getattr(settings, "isi_env", "development")).lower() == "production" or not bool(getattr(settings, "ai_allow_dev_stub", False)):
        result = [row for row in result if row.provider_type != "stub"]
    return result


def list_prompts(session: Session, *, product_code: str) -> list[AIPromptResponse]:
    prompts = list(session.scalars(select(AIPrompt).where(AIPrompt.is_active.is_(True)).order_by(AIPrompt.prompt_key)).all())
    result: list[AIPromptResponse] = []
    for prompt in prompts:
        if not _product_matches(prompt.product_scope, product_code):
            continue
        version = session.scalar(
            select(AIPromptVersion)
            .where(AIPromptVersion.prompt_id == prompt.id, AIPromptVersion.status == "active")
            .order_by(AIPromptVersion.version_no.desc())
        )
        result.append(
            AIPromptResponse(
                id=prompt.id,
                prompt_key=prompt.prompt_key,
                product_scope=prompt.product_scope,
                title=prompt.title,
                purpose=prompt.purpose,
                active_version=(
                    AIPromptVersionResponse(
                        id=version.id,
                        version_no=version.version_no,
                        checksum=version.checksum,
                        status=version.status,
                        output_schema=version.output_schema,
                    )
                    if version is not None
                    else None
                ),
            )
        )
    return result


def model_response(model: AIModel) -> AIModelResponse:
    return AIModelResponse(
        id=model.id,
        model_key=model.model_key,
        provider_type=model.provider_type,
        provider_name=model.provider_name,
        model_name=model.model_name,
        purpose=model.purpose,
        product_scope=model.product_scope,
        local_provider=model.local_provider,
        enabled=model.enabled,
        development_only=model.provider_type == "stub",
    )


def _resolve_prompt_version(session: Session, *, prompt_key: str, product_code: str) -> tuple[AIPrompt, AIPromptVersion]:
    prompt = session.scalar(select(AIPrompt).where(AIPrompt.prompt_key == prompt_key, AIPrompt.is_active.is_(True)))
    if prompt is None or not _product_matches(prompt.product_scope, product_code):
        raise AIServiceError("prompt_not_accessible")
    version = session.scalar(
        select(AIPromptVersion)
        .where(AIPromptVersion.prompt_id == prompt.id, AIPromptVersion.status == "active")
        .order_by(AIPromptVersion.version_no.desc())
    )
    if version is None:
        raise AIServiceError("prompt_has_no_active_version")
    return prompt, version


def _resolve_policy(
    session: Session,
    *,
    product_code: str,
    sensitivity: str,
    policy_key: str | None,
) -> tuple[AIPolicyProfile, EffectivePolicy]:
    if product_code == "SIMPA" and sensitivity == "sensitive":
        policy_key = "simpa-sensitive-local"
    if not policy_key:
        policy_key = str(getattr(get_settings(), "ai_default_policy", "shared-local-only"))
    profile = session.scalar(select(AIPolicyProfile).where(AIPolicyProfile.policy_key == policy_key, AIPolicyProfile.enabled.is_(True)))
    if profile is None or not _product_matches(profile.product_scope, product_code):
        raise AIServiceError("policy_not_accessible")
    effective = resolve_effective_policy(
        product_code=product_code,
        sensitivity=sensitivity,
        provider_policy=profile.provider_policy,
        allow_external=profile.allow_external,
        require_human_review=profile.require_human_review,
        max_attempts=profile.max_attempts,
    )
    return profile, effective


def _default_model_key(*, purpose: str) -> str:
    settings = get_settings()
    provider_default = str(getattr(settings, "ai_provider_default", "ollama")).lower()
    if provider_default == "stub":
        return "isi-dev-stub-chat" if purpose == "chat" else "isi-dev-stub-embedding"
    return "isi-ollama-chat-default" if purpose == "chat" else "isi-ollama-embedding-default"


def _resolve_model(session: Session, *, model_key: str | None, product_code: str, purpose: str) -> AIModel:
    key = model_key or _default_model_key(purpose=purpose)
    model = session.scalar(select(AIModel).where(AIModel.model_key == key, AIModel.enabled.is_(True)))
    if model is None or model.purpose != purpose or not _product_matches(model.product_scope, product_code):
        raise AIServiceError("model_not_accessible")
    if model.provider_type == "stub":
        settings = get_settings()
        if str(getattr(settings, "isi_env", "development")).lower() == "production" or not bool(getattr(settings, "ai_allow_dev_stub", False)):
            raise AIServiceError("development_stub_not_allowed")
    return model


def _candidate_models(
    session: Session,
    *,
    selected: AIModel,
    product_code: str,
    purpose: str,
    policy: EffectivePolicy,
) -> list[AIModel]:
    if (
        not selected.enabled
        or selected.purpose != purpose
        or not _product_matches(selected.product_scope, product_code)
        or not provider_allowed(policy=policy, local_provider=selected.local_provider)
    ):
        return []
    # ISI-25A fails closed to the explicitly selected/default runtime model.
    # Persisted fallback edges are governance evidence only until ISI-25B binds
    # execution to an unambiguous capability/registration and enforces every
    # edge review and semantic-equivalence gate.
    return [selected]


def create_ai_job(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    input_text: str,
    prompt_key: str,
    model_key: str | None,
    policy_key: str | None,
    sensitivity: str,
    actor_id: uuid.UUID | None,
    model_registration_id: uuid.UUID | None = None,
) -> AIJob:
    prompt, prompt_version = _resolve_prompt_version(session, prompt_key=prompt_key, product_code=product_code)
    profile, effective = _resolve_policy(session, product_code=product_code, sensitivity=sensitivity, policy_key=policy_key)
    registration: AIModelRegistration | None = None
    if model_registration_id is not None:
        selected = (
            _resolve_model(session, model_key=model_key, product_code=product_code, purpose="chat")
            if model_key is not None
            else None
        )
        try:
            registration, model = resolve_bound_runtime_registration(
                session,
                registration_id=model_registration_id,
                product_code=product_code,
                selected_model_id=selected.id if selected is not None else None,
            )
        except AIGovernanceError as exc:
            raise AIServiceError(str(exc)) from exc
        if registration.model_family not in {"llm", "vlm"}:
            raise AIServiceError("bound_registration_not_chat_capable")
    else:
        model = _resolve_model(session, model_key=model_key, product_code=product_code, purpose="chat")
    if not provider_allowed(policy=effective, local_provider=model.local_provider):
        raise AIServiceError("provider_blocked_by_policy")
    job = AIJob(
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        model_id=model.id,
        model_registration_id=registration.id if registration else None,
        prompt_version_id=prompt_version.id,
        policy_profile_id=profile.id,
        job_type="structured" if prompt_version.output_schema else "chat",
        status="queued",
        sensitivity=sensitivity,
        effective_provider_policy=effective.provider_policy,
        request_sha256=_sha256(input_text),
        request_text=input_text,
        human_review_status="pending" if effective.require_human_review else "not_required",
        created_by_membership_id=actor_id,
    )
    session.add(job)
    session.flush()
    session.add(
        AIAuditEvent(
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
            actor_membership_id=actor_id,
            event_type="ai.job.created",
            entity_type="ai_job",
            entity_id=job.id,
            detail=f"prompt={prompt.prompt_key};policy={profile.policy_key};request_sha256={job.request_sha256}",
        )
    )
    session.flush()
    return job


def _runtime_state_for_registration(
    session: Session, registration: AIModelRegistration
) -> AICapabilityRuntimeState | None:
    return session.scalar(select(AICapabilityRuntimeState).where(
        AICapabilityRuntimeState.product_scope == registration.product_scope,
        AICapabilityRuntimeState.capability_key == registration.capability_key,
    ))


def circuit_allows_direct(
    state: AICapabilityRuntimeState | None, *, now: datetime
) -> bool:
    if state is None or state.circuit_state == "closed":
        return True
    if state.circuit_state == "half_open":
        return True
    if state.opened_at is not None and now >= state.opened_at + timedelta(seconds=state.cooldown_seconds):
        state.circuit_state = "half_open"
        state.version += 1
        return True
    return False


def record_circuit_failure(
    state: AICapabilityRuntimeState | None, *, now: datetime
) -> None:
    if state is None:
        return
    state.consecutive_failures += 1
    state.last_failure_at = now
    if state.circuit_state == "half_open" or state.consecutive_failures >= state.failure_threshold:
        state.circuit_state = "open"
        state.opened_at = now
    state.version += 1


def record_circuit_success(
    state: AICapabilityRuntimeState | None, *, now: datetime
) -> None:
    if state is None:
        return
    state.circuit_state = "closed"
    state.consecutive_failures = 0
    state.opened_at = None
    state.last_success_at = now
    state.version += 1


def execute_ai_job(session: Session, *, job_id: uuid.UUID, now: datetime | None = None) -> AIJob:
    job = session.get(AIJob, job_id)
    if job is None:
        raise AIServiceError("ai_job_missing")
    model = session.get(AIModel, job.model_id)
    prompt_version = session.get(AIPromptVersion, job.prompt_version_id)
    profile = session.get(AIPolicyProfile, job.policy_profile_id)
    if model is None or prompt_version is None or profile is None:
        raise AIServiceError("ai_job_registry_reference_missing")
    effective = resolve_effective_policy(
        product_code=job.product_code,
        sensitivity=job.sensitivity,
        provider_policy=profile.provider_policy,
        allow_external=profile.allow_external,
        require_human_review=profile.require_human_review,
        max_attempts=profile.max_attempts,
    )
    current_time = now or _utcnow()
    source_registration = session.get(AIModelRegistration, job.model_registration_id) if job.model_registration_id else None
    runtime_state = _runtime_state_for_registration(session, source_registration) if source_registration else None
    direct_allowed = circuit_allows_direct(runtime_state, now=current_time)
    if source_registration is None:
        candidates: list[tuple[AIModel, AIModelRegistration | None, AIModelFallback | None]] = [
            (candidate, None, None) for candidate in _candidate_models(
                session, selected=model, product_code=job.product_code, purpose="chat", policy=effective
            )
        ]
    elif direct_allowed:
        try:
            source_registration, bound_runtime = resolve_bound_runtime_registration(
                session, registration_id=source_registration.id, product_code=job.product_code,
                selected_model_id=job.model_id,
            )
        except AIGovernanceError as exc:
            raise AIServiceError(str(exc)) from exc
        if not provider_allowed(policy=effective, local_provider=bound_runtime.local_provider):
            raise AIServiceError("provider_blocked_by_policy")
        candidates = [(bound_runtime, source_registration, None)]
    else:
        candidates = []
    if not candidates and source_registration is None:
        raise AIServiceError("no_provider_candidate")

    job.status = "running"
    job.started_at = _utcnow()
    job.error_code = ""
    job.error_message = ""
    session.flush()

    last_error_code = "circuit_open" if source_registration is not None and not direct_allowed else "unknown_error"
    last_error_message = "AI job failed"
    if source_registration is not None and not direct_allowed:
        for edge, target_registration, fallback_model in authorized_runtime_fallbacks(
            session, source_registration_id=source_registration.id, product_code=job.product_code,
            policy=effective, error_code="circuit_open",
        ):
            candidates.append((fallback_model, target_registration, edge))
    attempt_no = 0
    while candidates and attempt_no < effective.max_attempts:
        candidate, candidate_registration, fallback_edge = candidates.pop(0)
        attempt_no += 1
        attempt = AIJobAttempt(
            job_id=job.id,
            attempt_no=attempt_no,
            provider_name=candidate.provider_name,
            model_name=candidate.model_name,
            model_registration_id=candidate_registration.id if candidate_registration else None,
            fallback_edge_id=fallback_edge.id if fallback_edge else None,
            is_fallback=fallback_edge is not None,
            requires_human_review=bool(fallback_edge and fallback_edge.requires_human_review),
            status="running",
        )
        session.add(attempt)
        session.flush()
        started = datetime.now(timezone.utc)
        try:
            provider = provider_for_model(candidate)
            user_prompt = prompt_version.user_template.replace("{input}", job.request_text)
            result = provider.complete(
                CompletionRequest(
                    model_name=candidate.model_name,
                    system_prompt=prompt_version.system_template,
                    user_prompt=user_prompt,
                    timeout_seconds=candidate.timeout_seconds,
                    structured=bool(prompt_version.output_schema),
                )
            )
            structured = parse_structured_output(result.text, prompt_version.output_schema) if prompt_version.output_schema else None
            attempt.status = "succeeded"
            attempt.latency_ms = result.latency_ms
            job.provider_name = result.provider_name
            job.model_name = result.model_name
            job.attempts = attempt_no
            job.latency_ms = result.latency_ms
            job.input_tokens = result.input_tokens
            job.output_tokens = result.output_tokens
            job.output_text = result.text
            job.structured_output = structured
            review_required = effective.require_human_review or bool(
                fallback_edge and fallback_edge.requires_human_review
            )
            job.status = "review_required" if review_required else "succeeded"
            job.human_review_status = "pending" if review_required else "not_required"
            job.finished_at = _utcnow()
            if fallback_edge is None:
                record_circuit_success(runtime_state, now=current_time)
            if not bool(getattr(get_settings(), "ai_store_request_text", True)):
                job.request_text = ""
            session.add(
                AIAuditEvent(
                    organization_id=job.organization_id,
                    workspace_id=job.workspace_id,
                    product_code=job.product_code,
                    actor_membership_id=job.created_by_membership_id,
                    event_type="ai.job.completed",
                    entity_type="ai_job",
                    entity_id=job.id,
                    detail=f"provider={job.provider_name};model={job.model_name};attempts={job.attempts};status={job.status}",
                )
            )
            session.flush()
            return job
        except (ProviderError, GatewayError, StructuredOutputError) as exc:
            if isinstance(exc, ProviderError):
                code = exc.code
                message = exc.message
            else:
                code = str(exc).split(":", 1)[0] or exc.__class__.__name__
                message = str(exc)
            elapsed = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
            attempt.status = "failed"
            attempt.latency_ms = max(elapsed, 0)
            attempt.error_code = code[:120]
            attempt.error_message = message[:2000]
            job.attempts = attempt_no
            last_error_code = code
            last_error_message = message
            if fallback_edge is None and source_registration is not None:
                record_circuit_failure(runtime_state, now=current_time)
                for edge, target_registration, fallback_model in authorized_runtime_fallbacks(
                    session, source_registration_id=source_registration.id, product_code=job.product_code,
                    policy=effective, error_code=code,
                ):
                    if all(existing[1] is None or existing[1].id != target_registration.id for existing in candidates):
                        candidates.append((fallback_model, target_registration, edge))
            session.flush()

    job.status = "failed"
    job.error_code = last_error_code[:120]
    job.error_message = last_error_message[:2000]
    job.finished_at = _utcnow()
    if not bool(getattr(get_settings(), "ai_store_request_text", True)):
        job.request_text = ""
    session.add(
        AIAuditEvent(
            organization_id=job.organization_id,
            workspace_id=job.workspace_id,
            product_code=job.product_code,
            actor_membership_id=job.created_by_membership_id,
            event_type="ai.job.failed",
            entity_type="ai_job",
            entity_id=job.id,
            detail=f"error_code={job.error_code};attempts={job.attempts}",
        )
    )
    session.flush()
    return job


def list_jobs(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    limit: int = 50,
) -> list[AIJob]:
    return list(
        session.scalars(
            select(AIJob)
            .where(
                AIJob.organization_id == organization_id,
                AIJob.workspace_id == workspace_id,
                AIJob.product_code == product_code,
            )
            .order_by(AIJob.created_at.desc())
            .limit(max(1, min(limit, 100)))
        ).all()
    )


def get_scoped_job(
    session: Session,
    *,
    job_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> AIJob:
    job = session.scalar(
        select(AIJob).where(
            AIJob.id == job_id,
            AIJob.organization_id == organization_id,
            AIJob.workspace_id == workspace_id,
            AIJob.product_code == product_code,
        )
    )
    if job is None:
        raise AIServiceError("ai_job_not_accessible")
    return job


def job_response(session: Session, job: AIJob) -> AIJobResponse:
    model = session.get(AIModel, job.model_id)
    prompt_version = session.get(AIPromptVersion, job.prompt_version_id)
    prompt = session.get(AIPrompt, prompt_version.prompt_id) if prompt_version else None
    policy = session.get(AIPolicyProfile, job.policy_profile_id)
    if model is None or prompt_version is None or prompt is None or policy is None:
        raise AIServiceError("ai_job_registry_reference_missing")
    return AIJobResponse(
        id=job.id,
        organization_id=job.organization_id,
        workspace_id=job.workspace_id,
        product_code=job.product_code,
        status=job.status,
        job_type=job.job_type,
        sensitivity=job.sensitivity,
        effective_provider_policy=job.effective_provider_policy,
        request_sha256=job.request_sha256,
        output_text=job.output_text,
        structured_output=job.structured_output,
        provider_name=job.provider_name,
        model_name=job.model_name,
        attempts=job.attempts,
        latency_ms=job.latency_ms,
        input_tokens=job.input_tokens,
        output_tokens=job.output_tokens,
        error_code=job.error_code,
        error_message=job.error_message,
        human_review_status=job.human_review_status,
        prompt_key=prompt.prompt_key,
        prompt_version=prompt_version.version_no,
        policy_key=policy.policy_key,
        model_key=model.model_key,
        model_registration_id=job.model_registration_id,
    )


def create_embedding(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    namespace: str,
    source_type: str,
    source_id: str,
    chunk_index: int,
    text: str,
    model_key: str | None,
    sensitivity: str,
    actor_id: uuid.UUID | None,
) -> AIEmbeddingResponse:
    assert_namespace_access(namespace, organization_id=organization_id, product_code=product_code)
    _, effective = _resolve_policy(session, product_code=product_code, sensitivity=sensitivity, policy_key=None)
    model = _resolve_model(session, model_key=model_key, product_code=product_code, purpose="embedding")
    if not provider_allowed(policy=effective, local_provider=model.local_provider):
        raise AIServiceError("embedding_provider_blocked_by_policy")
    try:
        provider = provider_for_model(model)
        result = provider.embed(model_name=model.model_name, text=text, timeout_seconds=model.timeout_seconds)
    except (ProviderError, GatewayError) as exc:
        if isinstance(exc, ProviderError):
            raise AIServiceError(exc.code) from exc
        raise AIServiceError(str(exc)) from exc
    digest = _sha256(text)
    existing = session.scalar(
        select(AIEmbedding).where(
            AIEmbedding.namespace == namespace,
            AIEmbedding.source_type == source_type,
            AIEmbedding.source_id == source_id,
            AIEmbedding.chunk_index == chunk_index,
            AIEmbedding.content_sha256 == digest,
            AIEmbedding.model_id == model.id,
        )
    )
    if existing is None:
        existing = AIEmbedding(
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
            namespace=namespace,
            source_type=source_type,
            source_id=source_id,
            chunk_index=chunk_index,
            content_sha256=digest,
            model_id=model.id,
            dimensions=len(result.vector),
            vector_data=result.vector,
            created_by_membership_id=actor_id,
        )
        session.add(existing)
        session.flush()
    native_written = persist_native_vector(session, existing.id, result.vector)
    session.add(
        AIAuditEvent(
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
            actor_membership_id=actor_id,
            event_type="ai.embedding.created",
            entity_type="ai_embedding",
            entity_id=existing.id,
            detail=f"namespace={namespace};source_type={source_type};content_sha256={digest};dimensions={len(result.vector)}",
        )
    )
    session.flush()
    return AIEmbeddingResponse(
        id=existing.id,
        namespace=namespace,
        source_type=source_type,
        source_id=source_id,
        chunk_index=chunk_index,
        content_sha256=digest,
        dimensions=len(result.vector),
        model_key=model.model_key,
        provider_name=result.provider_name,
        model_name=result.model_name,
        native_pgvector_written=native_written,
    )
