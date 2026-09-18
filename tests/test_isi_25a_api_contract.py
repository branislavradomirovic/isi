from __future__ import annotations

import inspect
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import src.api.ai_routes as ai_routes
from src.api.ai_routes import router
from src.platform.ai.schemas import AIModelRegistrationCreateRequest
from src.platform.app_context.service import AppContextError


def _route_pairs() -> set[tuple[str, str]]:
    return {(route.path, method) for route in router.routes for method in route.methods}


def test_governance_and_evaluation_routes_stay_inside_existing_ai_boundary():
    paths = _route_pairs()
    required = {
        ("/api/v1/ai/governance/registrations", "GET"),
        ("/api/v1/ai/governance/registrations", "POST"),
        ("/api/v1/ai/governance/registrations/{registration_id}/retire", "POST"),
        ("/api/v1/ai/governance/fallbacks", "GET"),
        ("/api/v1/ai/governance/fallbacks", "POST"),
        ("/api/v1/ai/governance/prompt-rollbacks", "GET"),
        ("/api/v1/ai/governance/prompt-rollbacks", "POST"),
        ("/api/v1/ai/evaluation/datasets", "GET"),
        ("/api/v1/ai/evaluation/datasets", "POST"),
        ("/api/v1/ai/evaluation/runs", "GET"),
        ("/api/v1/ai/evaluation/runs", "POST"),
        ("/api/v1/ai/evaluation/runs/{run_id}/results", "POST"),
        ("/api/v1/ai/evaluation/runs/{run_id}/complete", "POST"),
        ("/api/v1/ai/evaluation/runs/{run_id}/fail", "POST"),
        ("/api/v1/ai/evaluation/runs/{run_id}/reviews", "POST"),
    }
    assert required <= paths
    assert all(path.startswith("/api/v1/ai") for path, _method in paths)
    assert not any(any(word in path for word in ("promote", "champion", "winner", "deploy", "server")) for path, _ in paths)


def test_api_uses_existing_permissions_for_each_authority():
    source = open("src/api/ai_routes.py", encoding="utf-8").read()
    assert 'permission_code="organization.manage"' in source
    assert 'permission_code="analysis.read"' in source
    assert 'permission_code="analysis.run"' in source
    assert 'permission_code="report.publish"' in source
    assert 'permission_code="ai.run"' in source
    assert "ai.manage" not in source


def test_shared_governance_mutation_requires_platform_admin_after_scope_resolution(monkeypatch):
    calls: list[str] = []

    def resolved(*_args, **_kwargs):
        calls.append("scope")
        return object()

    def permitted(*_args, **_kwargs):
        calls.append("permission")
        return True

    monkeypatch.setattr(ai_routes, "resolve_selection", resolved)
    monkeypatch.setattr(ai_routes, "has_permission", permitted)
    scope = {
        "organization_id": uuid.uuid4(),
        "workspace_id": uuid.uuid4(),
        "product_code": "SIMPA",
    }
    organization_manager = SimpleNamespace(user=SimpleNamespace(id=uuid.uuid4(), is_platform_admin=False))
    with pytest.raises(HTTPException) as denied:
        ai_routes._require_platform_admin_mutation(object(), organization_manager, **scope)
    assert denied.value.status_code == 403
    assert calls == ["scope", "permission"]

    calls.clear()
    platform_admin = SimpleNamespace(user=SimpleNamespace(id=uuid.uuid4(), is_platform_admin=True))
    ai_routes._require_platform_admin_mutation(object(), platform_admin, **scope)
    assert calls == ["scope", "permission"]

    for mutation in (
        ai_routes.post_model_registration,
        ai_routes.post_retire_model_registration,
        ai_routes.post_registered_fallback,
        ai_routes.post_prompt_rollback,
        ai_routes.post_evaluation_dataset,
    ):
        assert "_require_platform_admin_mutation(" in inspect.getsource(mutation)


def test_evaluation_review_write_requires_report_publish_while_get_remains_read_only():
    post_source = inspect.getsource(ai_routes.post_evaluation_review)
    get_source = inspect.getsource(ai_routes.get_evaluation_reviews)
    assert 'permission_code="report.publish"' in post_source
    assert 'permission_code="analysis.read"' not in post_source
    assert 'permission_code="analysis.read"' in get_source


def test_analysis_read_alone_cannot_authorize_review_write(monkeypatch):
    context = SimpleNamespace(user=SimpleNamespace(id=uuid.uuid4(), is_platform_admin=False))
    monkeypatch.setattr(ai_routes, "resolve_selection", lambda *_args, **_kwargs: object())

    def viewer_permissions(*args, **_kwargs):
        return args[3] == "analysis.read"

    monkeypatch.setattr(ai_routes, "has_permission", viewer_permissions)
    scope = {
        "organization_id": uuid.uuid4(),
        "workspace_id": uuid.uuid4(),
        "product_code": "ORDO",
    }
    ai_routes._require_permission(
        object(),
        context,
        **scope,
        permission_code="analysis.read",
    )
    with pytest.raises(HTTPException) as denied:
        ai_routes._require_permission(
            object(),
            context,
            **scope,
            permission_code="report.publish",
        )
    assert denied.value.status_code == 403


def test_scope_and_permission_checks_fail_closed(monkeypatch):
    context = SimpleNamespace(user=SimpleNamespace(id=uuid.uuid4()))
    organization_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    monkeypatch.setattr(ai_routes, "resolve_selection", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(ai_routes, "has_permission", lambda *_args, **_kwargs: False)
    with pytest.raises(HTTPException) as denied:
        ai_routes._require_permission(
            object(),
            context,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code="SIMPA",
            permission_code="organization.manage",
        )
    assert denied.value.status_code == 403

    def reject_scope(*_args, **_kwargs):
        raise AppContextError("cross_tenant_or_product")

    monkeypatch.setattr(ai_routes, "resolve_selection", reject_scope)
    monkeypatch.setattr(ai_routes, "has_permission", lambda *_args, **_kwargs: True)
    with pytest.raises(HTTPException) as cross_scope:
        ai_routes._require_permission(
            object(),
            context,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code="ORDO",
            permission_code="analysis.read",
        )
    assert cross_scope.value.status_code == 403 and cross_scope.value.detail == "ai scope not accessible"


def test_champion_request_is_parsed_but_service_must_fail_closed():
    payload = AIModelRegistrationCreateRequest(
        organization_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        product_code="SIMPA",
        capability_key="simpa.llm.test",
        product_scope="SIMPA",
        model_family="llm",
        model_key="synthetic",
        version="1.0.0",
        lifecycle_state="champion",
    )
    assert payload.lifecycle_state == "champion"
    source = open("src/platform/ai/governance.py", encoding="utf-8").read()
    assert "champion_promotion_requires_isi_25b_evaluation_and_approval_evidence" in source


def test_api_exposes_foundation_lifecycle_without_evaluator_or_promotion_engine():
    source = open("src/api/ai_routes.py", encoding="utf-8").read()
    for operation in (
        "register_fallback",
        "register_prompt_rollback",
        "register_evaluation_dataset",
        "create_evaluation_run",
        "append_evaluation_result",
        "finalize_evaluation_run",
        "append_evaluation_review",
    ):
        assert operation in source
    for forbidden in ("select_winner", "promote_to_champion", "deploy_model", "execute_forecast"):
        assert forbidden not in source
