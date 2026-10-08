"""Authenticated spatial transport. No cache, source fetch, or token persistence."""

from src.streamlit_app.api_client import request, AccessDenied, AuthenticationRequired, ApiUnavailable


def call(
    token, product, action, *, organization_id, workspace_id, method="GET", payload=None, geometry_id=None, at_date=None
):
    if product not in {"SIMPA", "ORDO"}:
        raise AccessDenied("Nepodržan proizvod.")
    paths = {
        "list": "geometries",
        "targets": "targets",
        "create": "geometries",
        "units": "units",
        "unit_create": "units",
        "unit_review": f"units/{geometry_id}/review",
        "detail": f"geometries/{geometry_id}",
        "review": f"geometries/{geometry_id}/review",
        "export": f"geometries/{geometry_id}/export",
        "results": f"geometries/{geometry_id}/results",
    }
    params = {"organization_id": organization_id, "workspace_id": workspace_id}
    if at_date is not None:
        params["at_date"] = str(at_date)
    response = request(method, f"/api/v1/spatial/{product}/{paths[action]}", token=token, params=params, json=payload)
    if response.status_code == 401:
        raise AuthenticationRequired("Sesija je istekla.")
    if response.status_code == 403:
        raise AccessDenied("GIS pristup nije dozvoljen u izabranom kontekstu.")
    if response.status_code >= 500:
        raise ApiUnavailable("GIS servis ili skladište nije dostupno.")
    if response.status_code >= 400:
        # Never echo untrusted validation bodies (which may contain source upload).
        raise AccessDenied(f"GIS zahtev odbijen ({response.status_code}). Osvežite izbor/verziju i proverite Help.")
    return response.json()
