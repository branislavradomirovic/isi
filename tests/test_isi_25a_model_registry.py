from __future__ import annotations

import hashlib
import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import src.platform.models  # noqa: F401
from src.core.database import Base
from src.platform.access.models import Product
from src.platform.ai.governance import (
    AIGovernanceError,
    CHAMPION_FORBIDDEN_REASON,
    SUPPORTED_MODEL_FAMILIES,
    register_fallback,
    register_model,
    register_prompt_rollback,
    retire_registration,
    transition_registration_lifecycle,
)
from src.platform.ai.models import AIModel, AIModelRegistration, AIPrompt, AIPromptVersion
from src.platform.ai.policy import resolve_effective_policy
from src.platform.ai.service import _candidate_models
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace


@pytest.fixture
def registry_case():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        marker = uuid.uuid4().hex
        db.add_all([Product(code="SIMPA", name="SIMPA"), Product(code="ORDO", name="ORDO")])
        user = User(email=f"{marker}@example.test", display_name="Registry owner")
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
        yield db, organization, workspace, actor


def _register(db, organization, workspace, actor, **changes):
    values = {
        "organization_id": organization.id,
        "workspace_id": workspace.id,
        "product_code": "SIMPA",
        "capability_key": "shared.text.synthesis",
        "product_scope": "SHARED",
        "model_family": "llm",
        "model_key": f"model-{uuid.uuid4().hex}",
        "version": "1.0.0",
        "lifecycle_state": "candidate",
        "actor_id": actor.id,
        "provenance": {"source": "synthetic-test"},
    }
    values.update(changes)
    return register_model(db, **values)


def test_registration_identity_supported_families_and_lifecycle(registry_case):
    db, organization, workspace, actor = registry_case
    assert SUPPORTED_MODEL_FAMILIES == {"statistical_ml", "embedding", "llm", "vlm"}
    rows = []
    for family in sorted(SUPPORTED_MODEL_FAMILIES):
        row = _register(
            db,
            organization,
            workspace,
            actor,
            capability_key=f"simpa.{family}.test",
            product_scope="SIMPA",
            model_family=family,
            lifecycle_state="challenger" if family == "vlm" else "candidate",
        )
        assert len(row.registry_fingerprint) == 64
        rows.append(row)
    assert len({row.registry_fingerprint for row in rows}) == 4
    retired = retire_registration(
        db,
        registration_id=rows[0].id,
        product_code="SIMPA",
        actor_id=actor.id,
        organization_id=organization.id,
        workspace_id=workspace.id,
    )
    assert retired.lifecycle_state == "retired" and retired.enabled is False and retired.retired_at


def test_champion_is_vocabulary_only_and_never_hard_coded(registry_case):
    db, organization, workspace, actor = registry_case
    with pytest.raises(AIGovernanceError, match=CHAMPION_FORBIDDEN_REASON):
        _register(
            db,
            organization,
            workspace,
            actor,
            lifecycle_state="champion",
        )
    with pytest.raises(AIGovernanceError, match=CHAMPION_FORBIDDEN_REASON):
        transition_registration_lifecycle(target_state="champion")
    assert db.scalar(select(AIModelRegistration).where(AIModelRegistration.lifecycle_state == "champion")) is None


def test_fallback_requires_registered_compatible_acyclic_edge(registry_case):
    db, organization, workspace, actor = registry_case
    first = _register(db, organization, workspace, actor)
    second = _register(db, organization, workspace, actor, lifecycle_state="challenger")
    with pytest.raises(AIGovernanceError, match="fallback_self_reference_forbidden"):
        register_fallback(
            db,
            source_registration_id=first.id,
            target_registration_id=first.id,
            priority=1,
            trigger_codes=["timeout"],
            semantically_equivalent=True,
            requires_human_review=True,
            provenance="synthetic",
            actor_id=actor.id,
            organization_id=organization.id,
            workspace_id=workspace.id,
            product_code="SIMPA",
        )
    edge = register_fallback(
        db,
        source_registration_id=first.id,
        target_registration_id=second.id,
        priority=1,
        trigger_codes=["timeout", "timeout"],
        semantically_equivalent=True,
        requires_human_review=True,
        provenance="synthetic",
        actor_id=actor.id,
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
    )
    assert edge.trigger_codes == ["timeout"] and len(edge.fingerprint) == 64
    with pytest.raises(AIGovernanceError, match="fallback_cycle_forbidden"):
        register_fallback(
            db,
            source_registration_id=second.id,
            target_registration_id=first.id,
            priority=1,
            trigger_codes=["timeout"],
            semantically_equivalent=True,
            requires_human_review=True,
            provenance="synthetic",
            actor_id=actor.id,
            organization_id=organization.id,
            workspace_id=workspace.id,
            product_code="SIMPA",
        )
    mismatch = _register(
        db,
        organization,
        workspace,
        actor,
        capability_key="simpa.embedding.retrieval",
        model_family="embedding",
    )
    with pytest.raises(AIGovernanceError, match="fallback_capability_mismatch"):
        register_fallback(
            db,
            source_registration_id=second.id,
            target_registration_id=mismatch.id,
            priority=2,
            trigger_codes=[],
            semantically_equivalent=False,
            requires_human_review=True,
            provenance="synthetic",
            actor_id=actor.id,
            organization_id=organization.id,
            workspace_id=workspace.id,
            product_code="SIMPA",
        )
    ordo = _register(
        db,
        organization,
        workspace,
        actor,
        product_code="ORDO",
        product_scope="ORDO",
        capability_key=second.capability_key,
    )
    with pytest.raises(AIGovernanceError, match="fallback_product_scope_mismatch"):
        register_fallback(
            db,
            source_registration_id=second.id,
            target_registration_id=ordo.id,
            priority=2,
            trigger_codes=[],
            semantically_equivalent=False,
            requires_human_review=True,
            provenance="synthetic",
            actor_id=actor.id,
            organization_id=organization.id,
            workspace_id=workspace.id,
            product_code="SIMPA",
        )


def test_25a_runtime_stays_on_selected_model_despite_persisted_fallback_graph(registry_case):
    db, organization, workspace, actor = registry_case
    selected = AIModel(
        model_key="selected",
        provider_type="ollama",
        provider_name="ollama",
        model_name="selected-runtime",
        purpose="chat",
        product_scope="SHARED",
        local_provider=True,
    )
    external = AIModel(
        model_key="external",
        provider_type="external",
        provider_name="external",
        model_name="external-runtime",
        purpose="chat",
        product_scope="SHARED",
        local_provider=False,
    )
    unregistered = AIModel(
        model_key="unregistered",
        provider_type="ollama",
        provider_name="ollama",
        model_name="unregistered-runtime",
        purpose="chat",
        product_scope="SHARED",
        local_provider=True,
    )
    db.add_all([selected, external, unregistered])
    db.flush()
    permissive = resolve_effective_policy(
        product_code="SIMPA",
        sensitivity="internal",
        provider_policy="any",
        allow_external=True,
        require_human_review=True,
        max_attempts=3,
    )
    assert _candidate_models(db, selected=selected, product_code="SIMPA", purpose="chat", policy=permissive) == [
        selected
    ]
    source = _register(db, organization, workspace, actor, runtime_model_id=selected.id)
    target = _register(
        db,
        organization,
        workspace,
        actor,
        runtime_model_id=external.id,
        lifecycle_state="challenger",
    )
    register_fallback(
        db,
        source_registration_id=source.id,
        target_registration_id=target.id,
        priority=1,
        trigger_codes=["timeout"],
        semantically_equivalent=True,
        requires_human_review=True,
        provenance="synthetic",
        actor_id=actor.id,
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
    )
    _register(
        db,
        organization,
        workspace,
        actor,
        runtime_model_id=selected.id,
        capability_key="shared.text.second-capability",
    )
    registrations = list(
        db.scalars(
            select(AIModelRegistration).where(AIModelRegistration.runtime_model_id == selected.id)
        ).all()
    )
    assert len(registrations) == 2
    assert {row.capability_key for row in registrations} == {
        "shared.text.synthesis",
        "shared.text.second-capability",
    }
    assert _candidate_models(db, selected=selected, product_code="SIMPA", purpose="chat", policy=permissive) == [
        selected
    ]
    assert external not in _candidate_models(
        db, selected=selected, product_code="SIMPA", purpose="chat", policy=permissive
    )
    assert unregistered not in _candidate_models(
        db, selected=selected, product_code="SIMPA", purpose="chat", policy=permissive
    )
    local_only = resolve_effective_policy(
        product_code="SIMPA",
        sensitivity="sensitive",
        provider_policy="any",
        allow_external=True,
        require_human_review=False,
        max_attempts=3,
    )
    assert _candidate_models(db, selected=selected, product_code="SIMPA", purpose="chat", policy=local_only) == [
        selected
    ]
    assert _candidate_models(db, selected=external, product_code="SIMPA", purpose="chat", policy=local_only) == []


def test_prompt_rollback_is_prior_same_prompt_and_checksum_bound(registry_case):
    db, organization, workspace, actor = registry_case
    prompt = AIPrompt(prompt_key="simpa.test", product_scope="SIMPA", title="Test", purpose="Synthetic")
    other = AIPrompt(prompt_key="simpa.other", product_scope="SIMPA", title="Other", purpose="Synthetic")
    db.add_all([prompt, other])
    db.flush()
    v1 = AIPromptVersion(
        prompt_id=prompt.id,
        version_no=1,
        user_template="v1",
        checksum=hashlib.sha256(b"v1").hexdigest(),
        status="retired",
    )
    v2 = AIPromptVersion(
        prompt_id=prompt.id,
        version_no=2,
        user_template="v2",
        checksum=hashlib.sha256(b"v2").hexdigest(),
        status="active",
    )
    other_v1 = AIPromptVersion(
        prompt_id=other.id,
        version_no=1,
        user_template="other",
        checksum=hashlib.sha256(b"other").hexdigest(),
        status="active",
    )
    db.add_all([v1, v2, other_v1])
    db.flush()
    with pytest.raises(AIGovernanceError, match="prompt_rollback_self_reference_forbidden"):
        register_prompt_rollback(
            db,
            source_prompt_version_id=v2.id,
            target_prompt_version_id=v2.id,
            provenance="synthetic",
            actor_id=actor.id,
            organization_id=organization.id,
            workspace_id=workspace.id,
            product_code="SIMPA",
        )
    with pytest.raises(AIGovernanceError, match="prompt_rollback_requires_same_prompt"):
        register_prompt_rollback(
            db,
            source_prompt_version_id=v2.id,
            target_prompt_version_id=other_v1.id,
            provenance="synthetic",
            actor_id=actor.id,
            organization_id=organization.id,
            workspace_id=workspace.id,
            product_code="SIMPA",
        )
    row = register_prompt_rollback(
        db,
        source_prompt_version_id=v2.id,
        target_prompt_version_id=v1.id,
        provenance="synthetic",
        actor_id=actor.id,
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
    )
    assert row.source_checksum == v2.checksum and row.target_checksum == v1.checksum
    assert v2.status == "active" and len(row.fingerprint) == 64


def test_25a_unbound_attempt_and_audit_compatibility_is_preserved():
    source = open("src/platform/ai/service.py", encoding="utf-8").read()
    assert "AIJobAttempt(" in source
    assert 'event_type="ai.job.completed"' in source
    assert 'event_type="ai.job.failed"' in source
    assert "if source_registration is None" in source
    assert "authorized_runtime_fallbacks" in source
    assert "source_registration_id=source_registration.id" in source
    assert "return [selected]" in source
    assert "rest.sort" not in source
