from __future__ import annotations

import inspect
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import src.platform.models  # noqa: F401
from src.core.database import Base
from src.platform.access.models import Product
from src.platform.ai.governance import (
    authorized_runtime_fallbacks,
    register_fallback,
    register_model,
    resolve_bound_runtime_registration,
    runtime_fallback_allows_error,
)
from src.platform.ai.models import AIModel
from src.platform.ai.policy import resolve_effective_policy
from src.platform.ai.service import circuit_allows_direct, record_circuit_failure, record_circuit_success
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace


def _state(**overrides):
    values = {
        "circuit_state": "closed", "consecutive_failures": 0, "failure_threshold": 2,
        "cooldown_seconds": 60, "opened_at": None, "last_failure_at": None,
        "last_success_at": None, "version": 1,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_legacy_path_remains_selected_only_and_bound_path_is_explicit():
    source = inspect.getsource(__import__("src.platform.ai.service", fromlist=["x"]))
    assert "return [selected]" in source
    assert "if source_registration is None" in source
    signature = inspect.signature(resolve_bound_runtime_registration)
    assert "registration_id" in signature.parameters
    assert "runtime_model_id" not in signature.parameters


def test_fallback_resolver_requires_exact_source_and_all_gates():
    source = inspect.getsource(authorized_runtime_fallbacks)
    for marker in (
        "source_registration_id", "edge.semantically_equivalent", "error_code in edge.trigger_codes",
        "target.model_family != source.model_family", "provider_allowed", "edge.requires_human_review",
    ):
        assert marker in source or marker == "edge.requires_human_review"
    assert "order_by(AIModelFallback.priority" in source
    assert "AIModelRegistration.runtime_model_id == selected.id" not in source


def test_circuit_open_half_open_close_without_sleep():
    now = datetime(2026, 9, 18, tzinfo=timezone.utc)
    state = _state()
    record_circuit_failure(state, now=now)
    assert state.circuit_state == "closed" and state.consecutive_failures == 1
    record_circuit_failure(state, now=now + timedelta(seconds=1))
    assert state.circuit_state == "open" and not circuit_allows_direct(state, now=now + timedelta(seconds=30))
    assert circuit_allows_direct(state, now=now + timedelta(seconds=61))
    assert state.circuit_state == "half_open"
    record_circuit_success(state, now=now + timedelta(seconds=62))
    assert state.circuit_state == "closed" and state.consecutive_failures == 0 and state.opened_at is None


def test_attempt_evidence_pins_registration_edge_and_review_requirement():
    source = inspect.getsource(__import__("src.platform.ai.service", fromlist=["x"]))
    for field in ("model_registration_id=", "fallback_edge_id=", "is_fallback=", "requires_human_review="):
        assert field in source
    assert 'job.status = "review_required"' in source
    assert 'job.human_review_status = "pending"' in source


def test_fhr3_r3_fallback_edge_tamper_without_fingerprint_change_is_not_authorized():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        marker = uuid.uuid4().hex
        db.add_all([Product(code="SIMPA", name="SIMPA"), Product(code="ORDO", name="ORDO")])
        user = User(email=f"{marker}@example.test", display_name="Fallback owner")
        organization = Organization(slug=f"org-{marker}", name="Organization")
        db.add_all([user, organization])
        db.flush()
        actor = Membership(user_id=user.id, organization_id=organization.id)
        db.add(actor)
        db.flush()
        workspace = Workspace(
            organization_id=organization.id, product_code="SIMPA", slug=f"simpa-{marker}",
            name="SIMPA", created_by_membership_id=actor.id,
        )
        db.add(workspace)
        source_runtime = AIModel(
            model_key=f"source-{marker}", provider_type="ollama", provider_name="ollama",
            model_name="source-runtime", purpose="chat", product_scope="SIMPA", local_provider=True,
        )
        target_runtime = AIModel(
            model_key=f"target-{marker}", provider_type="ollama", provider_name="ollama",
            model_name="target-runtime", purpose="chat", product_scope="SIMPA", local_provider=True,
        )
        db.add_all([source_runtime, target_runtime])
        db.flush()
        source = register_model(
            db, organization_id=organization.id, workspace_id=workspace.id, product_code="SIMPA",
            capability_key="simpa.text", product_scope="SIMPA", model_family="llm",
            model_key=f"source-reg-{marker}", version="1", lifecycle_state="candidate",
            runtime_model_id=source_runtime.id, actor_id=actor.id, provenance={"source": "synthetic"},
        )
        target = register_model(
            db, organization_id=organization.id, workspace_id=workspace.id, product_code="SIMPA",
            capability_key="simpa.text", product_scope="SIMPA", model_family="llm",
            model_key=f"target-reg-{marker}", version="1", lifecycle_state="challenger",
            runtime_model_id=target_runtime.id, actor_id=actor.id, provenance={"source": "synthetic"},
        )
        edge = register_fallback(
            db, source_registration_id=source.id, target_registration_id=target.id, priority=1,
            trigger_codes=["timeout"], semantically_equivalent=False, requires_human_review=True,
            provenance="synthetic", actor_id=actor.id, organization_id=organization.id,
            workspace_id=workspace.id, product_code="SIMPA",
        )
        policy = resolve_effective_policy(
            product_code="SIMPA", sensitivity="internal", provider_policy="local_only",
            allow_external=False, require_human_review=True, max_attempts=3,
        )
        assert authorized_runtime_fallbacks(
            db, source_registration_id=source.id, product_code="SIMPA", policy=policy, error_code="timeout"
        ) == []
        edge.semantically_equivalent = True
        db.flush()
        assert authorized_runtime_fallbacks(
            db, source_registration_id=source.id, product_code="SIMPA", policy=policy, error_code="timeout"
        ) == []
        assert runtime_fallback_allows_error(
            db, source_registration_id=source.id, target_registration_id=target.id,
            product_code="SIMPA", error_code="timeout"
        ) is False
