from __future__ import annotations

import base64
from typing import Any
from urllib.parse import quote

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


def get_source_detail(token: str, *, source_id: str, organization_id: str,
                      product_code: str, workspace_id: str):
    return _source_request(token, source_id=source_id, organization_id=organization_id,
                           product_code=product_code, workspace_id=workspace_id)


def _source_request(token: str, *, source_id: str, organization_id: str,
                    product_code: str, workspace_id: str, suffix: str = "",
                    method: str = "GET", body: dict | None = None):
    scope = dict(organization_id=organization_id, product_code=product_code, workspace_id=workspace_id)
    args = {"params": scope} if method == "GET" else {"json": {**(body or {}), **scope}}
    response = request(method, f"/api/v1/data/sources/{quote(source_id, safe='')}{suffix}",
                       token=token, **args)
    return _checked(response, unavailable="Servis obrade nije dostupan. Osvežite stanje pre ponavljanja operacije.")


def create_source_version(token: str, *, source_id: str, organization_id: str,
                          product_code: str, workspace_id: str, filename: str,
                          content_type: str, payload: bytes):
    return _source_request(token, source_id=source_id, organization_id=organization_id,
        product_code=product_code, workspace_id=workspace_id, suffix="/versions", method="POST",
        body=dict(filename=filename, content_type=content_type,
                  content_base64=base64.b64encode(payload).decode("ascii")))


def list_ingestion_runs(token: str, *, source_id: str, organization_id: str,
                        product_code: str, workspace_id: str):
    return _source_request(token, source_id=source_id, organization_id=organization_id,
        product_code=product_code, workspace_id=workspace_id, suffix="/ingestion-runs")


def get_ingestion_run(token: str, *, source_id: str, run_id: str, organization_id: str,
                       product_code: str, workspace_id: str):
    return _source_request(token, source_id=source_id, organization_id=organization_id,
        product_code=product_code, workspace_id=workspace_id,
        suffix=f"/ingestion-runs/{quote(run_id, safe='')}")


def get_run_evaluation(token: str, *, source_id: str, run_id: str, organization_id: str,
                       product_code: str, workspace_id: str):
    return _source_request(token, source_id=source_id, organization_id=organization_id,
        product_code=product_code, workspace_id=workspace_id,
        suffix=f"/ingestion-runs/{quote(run_id, safe='')}/evaluation")


def get_run_governed_output(token: str, *, source_id: str, run_id: str, organization_id: str,
                            product_code: str, workspace_id: str):
    return _source_request(token, source_id=source_id, organization_id=organization_id,
        product_code=product_code, workspace_id=workspace_id,
        suffix=f"/ingestion-runs/{quote(run_id, safe='')}/governed-output")


def retry_ingestion_run(token: str, *, source_id: str, run_id: str, organization_id: str,
                        product_code: str, workspace_id: str):
    return _source_request(token, source_id=source_id, organization_id=organization_id,
        product_code=product_code, workspace_id=workspace_id, method="POST",
        suffix=f"/ingestion-runs/{quote(run_id, safe='')}/retry")


def get_inspection_job(token: str, *, job_id: str, organization_id: str,
                        product_code: str, workspace_id: str):
    response = request("GET", f"/api/v1/data/jobs/{quote(job_id, safe='')}", token=token,
        params=dict(organization_id=organization_id, product_code=product_code, workspace_id=workspace_id))
    return _checked(response, unavailable="Nije moguće učitati status obrade.")
