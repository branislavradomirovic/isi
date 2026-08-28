from __future__ import annotations

from typing import Any

from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired, request


def _checked(response, *, unavailable: str) -> Any:
    if response.status_code == 401: raise AuthenticationRequired("Sesija je istekla.")
    if response.status_code == 403: raise AccessDenied("ORDO pristup nije dozvoljen u izabranom kontekstu.")
    if response.status_code >= 500: raise ApiUnavailable(unavailable)
    if response.status_code >= 400:
        try: detail = response.json().get("detail", "ORDO request rejected")
        except Exception: detail = "ORDO request rejected"
        raise AccessDenied(str(detail))
    return response.json()


def catalog(token: str, organization_id: str, workspace_id: str):
    return _checked(request("GET", "/api/v1/ordo/catalog", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id}), unavailable="Nije moguće učitati ORDO katalog.")


def foundation(token: str, organization_id: str, workspace_id: str):
    return _checked(request("GET", "/api/v1/ordo/foundation", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id}), unavailable="Nije moguće učitati ORDO foundation.")


def assets(token: str, organization_id: str, workspace_id: str):
    return _checked(request("GET", "/api/v1/ordo/assets", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id}), unavailable="Nije moguće učitati ORDO resurse.")


def stakeholders(token: str, organization_id: str, workspace_id: str):
    return _checked(request("GET", "/api/v1/ordo/stakeholders", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id}), unavailable="Nije moguće učitati ORDO aktere.")


def cycles(token: str, organization_id: str, workspace_id: str):
    return _checked(request("GET", "/api/v1/ordo/cycles", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id}), unavailable="Nije moguće učitati ORDO monitoring cikluse.")


def observations(token: str, organization_id: str, workspace_id: str):
    return _checked(request("GET", "/api/v1/ordo/observations", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id}), unavailable="Nije moguće učitati ORDO opservacije.")


def upsert_profile(token: str, **payload):
    return _checked(request("PUT", "/api/v1/ordo/profile", token=token, json=payload), unavailable="Nije moguće sačuvati ORDO profil.")


def create_asset(token: str, **payload):
    return _checked(request("POST", "/api/v1/ordo/assets", token=token, json=payload), unavailable="Nije moguće sačuvati ORDO resurs.")


def create_stakeholder(token: str, **payload):
    return _checked(request("POST", "/api/v1/ordo/stakeholders", token=token, json=payload), unavailable="Nije moguće sačuvati ORDO aktera.")


def create_cycle(token: str, **payload):
    data = dict(payload); data["period_start"] = str(data["period_start"]); data["period_end"] = str(data["period_end"])
    return _checked(request("POST", "/api/v1/ordo/cycles", token=token, json=data), unavailable="Nije moguće sačuvati ORDO monitoring ciklus.")
