"""No payload cache or credentials persistence."""

from src.streamlit_app.api_client import request, AuthenticationRequired, AccessDenied, ApiUnavailable


def call(token, product, path, *, organization_id, workspace_id, method="GET", payload=None, filters=None):
    if product not in {"SIMPA", "ORDO"}:
        raise AccessDenied("Proizvod nije podržan.")
    response = request(
        method,
        f"/api/v1/extraction/{product}/{path}",
        token=token,
        params={"organization_id": organization_id, "workspace_id": workspace_id, **(filters or {})},
        json=payload,
    )
    if response.status_code == 401:
        raise AuthenticationRequired("Sesija je istekla.")
    if response.status_code >= 500:
        raise ApiUnavailable("Ekstrakcija trenutno nije dostupna.")
    if response.status_code >= 400:
        raise AccessDenied("Dokaz nije dostupan ili zahtev nije dozvoljen. Osvežite izbor i proverite poreklo/Help.")
    return response.json()
