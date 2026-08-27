from __future__ import annotations

import base64
from typing import Any

from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired, request


def _checked(response, *, unavailable: str) -> Any:
    if response.status_code == 401:
        raise AuthenticationRequired("Sesija je istekla.")
    if response.status_code == 403:
        raise AccessDenied("Nemate dozvolu za ovu data operaciju.")
    if response.status_code >= 500:
        raise ApiUnavailable(unavailable)
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", "data request rejected")
        except Exception:
            detail = "data request rejected"
        raise AccessDenied(str(detail))
    return response.json()


def list_data_sources(token: str, *, organization_id: str, product_code: str, workspace_id: str):
    response = request(
        "GET",
        "/api/v1/data/sources",
        token=token,
        params={"organization_id": organization_id, "product_code": product_code, "workspace_id": workspace_id},
    )
    return _checked(response, unavailable="Nije moguće učitati data katalog.")


def create_data_source(
    token: str,
    *,
    organization_id: str,
    product_code: str,
    workspace_id: str,
    source_name: str,
    filename: str,
    content_type: str,
    payload: bytes,
):
    response = request(
        "POST",
        "/api/v1/data/sources",
        token=token,
        json={
            "organization_id": organization_id,
            "product_code": product_code,
            "workspace_id": workspace_id,
            "source_name": source_name,
            "filename": filename,
            "content_type": content_type,
            "content_base64": base64.b64encode(payload).decode("ascii"),
        },
    )
    return _checked(response, unavailable="Nije moguće učitati izvor podataka.")
