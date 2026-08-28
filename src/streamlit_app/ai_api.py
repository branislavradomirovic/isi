from __future__ import annotations

from typing import Any

from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired, request


def _checked(response, *, unavailable: str) -> Any:
    if response.status_code == 401:
        raise AuthenticationRequired("Sesija je istekla.")
    if response.status_code == 403:
        raise AccessDenied("Nemate dozvolu za ovu AI operaciju.")
    if response.status_code >= 500:
        raise ApiUnavailable(unavailable)
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", "AI request rejected")
        except Exception:
            detail = "AI request rejected"
        raise AccessDenied(str(detail))
    return response.json()


def _scope_params(*, organization_id: str, product_code: str, workspace_id: str) -> dict[str, str]:
    return {
        "organization_id": organization_id,
        "product_code": product_code,
        "workspace_id": workspace_id,
    }


def capabilities(token: str, *, organization_id: str, product_code: str, workspace_id: str):
    response = request(
        "GET",
        "/api/v1/ai/capabilities",
        token=token,
        params=_scope_params(organization_id=organization_id, product_code=product_code, workspace_id=workspace_id),
    )
    return _checked(response, unavailable="Nije moguće učitati AI capability stanje.")


def models(token: str, *, organization_id: str, product_code: str, workspace_id: str):
    response = request(
        "GET",
        "/api/v1/ai/models",
        token=token,
        params=_scope_params(organization_id=organization_id, product_code=product_code, workspace_id=workspace_id),
    )
    return _checked(response, unavailable="Nije moguće učitati AI model registry.")


def prompts(token: str, *, organization_id: str, product_code: str, workspace_id: str):
    response = request(
        "GET",
        "/api/v1/ai/prompts",
        token=token,
        params=_scope_params(organization_id=organization_id, product_code=product_code, workspace_id=workspace_id),
    )
    return _checked(response, unavailable="Nije moguće učitati AI prompt registry.")


def jobs(token: str, *, organization_id: str, product_code: str, workspace_id: str):
    response = request(
        "GET",
        "/api/v1/ai/jobs",
        token=token,
        params=_scope_params(organization_id=organization_id, product_code=product_code, workspace_id=workspace_id),
    )
    return _checked(response, unavailable="Nije moguće učitati AI job istoriju.")


def create_job(
    token: str,
    *,
    organization_id: str,
    product_code: str,
    workspace_id: str,
    input_text: str,
    sensitivity: str = "internal",
    model_key: str | None = None,
    prompt_key: str = "foundation.diagnostic",
):
    payload: dict[str, Any] = {
        "organization_id": organization_id,
        "product_code": product_code,
        "workspace_id": workspace_id,
        "input_text": input_text,
        "sensitivity": sensitivity,
        "prompt_key": prompt_key,
    }
    if model_key:
        payload["model_key"] = model_key
    response = request("POST", "/api/v1/ai/jobs", token=token, json=payload)
    return _checked(response, unavailable="AI job nije moguće izvršiti.")
