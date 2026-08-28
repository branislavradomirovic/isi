from __future__ import annotations

from typing import Any

from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired, request


def _checked(response, *, unavailable: str) -> Any:
    if response.status_code == 401:
        raise AuthenticationRequired("Sesija je istekla.")
    if response.status_code == 403:
        raise AccessDenied("SIMPA pristup nije dozvoljen u izabranom kontekstu.")
    if response.status_code >= 500:
        raise ApiUnavailable(unavailable)
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", "SIMPA request rejected")
        except Exception:
            detail = "SIMPA request rejected"
        raise AccessDenied(str(detail))
    return response.json()


def catalog(token: str, organization_id: str, workspace_id: str):
    return _checked(request("GET", "/api/v1/simpa/catalog", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id}), unavailable="Nije moguće učitati SIMPA katalog.")


def foundation(token: str, organization_id: str, workspace_id: str):
    return _checked(request("GET", "/api/v1/simpa/foundation", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id}), unavailable="Nije moguće učitati SIMPA foundation.")


def actors(token: str, organization_id: str, workspace_id: str):
    return _checked(request("GET", "/api/v1/simpa/actors", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id}), unavailable="Nije moguće učitati SIMPA aktere.")


def cycles(token: str, organization_id: str, workspace_id: str):
    return _checked(request("GET", "/api/v1/simpa/cycles", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id}), unavailable="Nije moguće učitati SIMPA monitoring cikluse.")


def mappings(token: str, organization_id: str, workspace_id: str):
    return _checked(request("GET", "/api/v1/simpa/mappings", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id}), unavailable="Nije moguće učitati SIMPA mapiranja.")


def observations(token: str, organization_id: str, workspace_id: str):
    return _checked(request("GET", "/api/v1/simpa/observations", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id}), unavailable="Nije moguće učitati SIMPA opservacije.")


def upsert_profile(token: str, *, organization_id: str, workspace_id: str, jurisdiction_name: str, jurisdiction_code: str, reference_year: int | None, notes: str):
    return _checked(request("PUT", "/api/v1/simpa/profile", token=token, json={"organization_id": organization_id, "workspace_id": workspace_id, "jurisdiction_name": jurisdiction_name, "jurisdiction_code": jurisdiction_code, "reference_year": reference_year, "notes": notes}), unavailable="Nije moguće sačuvati SIMPA profil.")


def create_actor(token: str, *, organization_id: str, workspace_id: str, actor_type: str, name: str, external_code: str = ""):
    return _checked(request("POST", "/api/v1/simpa/actors", token=token, json={"organization_id": organization_id, "workspace_id": workspace_id, "actor_type": actor_type, "name": name, "external_code": external_code}), unavailable="Nije moguće sačuvati SIMPA aktera.")


def create_cycle(token: str, *, organization_id: str, workspace_id: str, code: str, title: str, period_start, period_end, status: str = "planned"):
    return _checked(request("POST", "/api/v1/simpa/cycles", token=token, json={"organization_id": organization_id, "workspace_id": workspace_id, "code": code, "title": title, "period_start": str(period_start), "period_end": str(period_end), "status": status}), unavailable="Nije moguće sačuvati SIMPA monitoring ciklus.")
