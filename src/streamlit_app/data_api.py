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


def list_analytical_datasets(token: str, *, organization_id: str, product_code: str, workspace_id: str):
    response = request("GET", "/api/v1/data/analytical-datasets", token=token, params={
        "organization_id": organization_id, "product_code": product_code, "workspace_id": workspace_id,
    })
    return _checked(response, unavailable="Nije moguće učitati analytical registry.")


def create_analytical_dataset(token: str, **payload):
    response = request("POST", "/api/v1/data/analytical-datasets", token=token, json=payload)
    return _checked(response, unavailable="Nije moguće registrovati analytical dataset.")


def list_analytical_snapshots(token: str, *, dataset_id: str, organization_id: str,
                              product_code: str, workspace_id: str):
    response = request(
        "GET",
        f"/api/v1/data/analytical-datasets/{dataset_id}/snapshots",
        token=token,
        params={
            "organization_id": organization_id,
            "product_code": product_code,
            "workspace_id": workspace_id,
        },
    )
    return _checked(response, unavailable="Nije moguće učitati verzije analytical dataset-a.")


def list_analytical_features(token: str, *, organization_id: str, product_code: str, workspace_id: str):
    response = request("GET", "/api/v1/data/analytical-features", token=token, params={
        "organization_id": organization_id, "product_code": product_code, "workspace_id": workspace_id,
    })
    return _checked(response, unavailable="Nije moguće učitati feature registry.")


def create_analytical_feature(token: str, **payload):
    response = request("POST", "/api/v1/data/analytical-features", token=token, json=payload)
    return _checked(response, unavailable="Nije moguće registrovati analytical feature.")


def list_analytical_feature_versions(token: str, *, feature_id: str, organization_id: str,
                                     product_code: str, workspace_id: str):
    response = request(
        "GET",
        f"/api/v1/data/analytical-features/{feature_id}/versions",
        token=token,
        params={
            "organization_id": organization_id,
            "product_code": product_code,
            "workspace_id": workspace_id,
        },
    )
    return _checked(response, unavailable="Nije moguće učitati verzije analytical feature-a.")


def get_analytical_lineage(token: str, *, snapshot_id: str, organization_id: str,
                           product_code: str, workspace_id: str):
    response = request("GET", f"/api/v1/data/analytical-snapshots/{snapshot_id}/lineage", token=token, params={
        "organization_id": organization_id, "product_code": product_code, "workspace_id": workspace_id,
    })
    return _checked(response, unavailable="Nije moguće učitati lineage/provenance.")


def evaluate_ai_eligibility(token: str, **payload):
    response = request("POST", "/api/v1/data/analytical-ai/eligibility", token=token, json=payload)
    return _checked(response, unavailable="Nije moguće proveriti AI/RAG eligibility.")
