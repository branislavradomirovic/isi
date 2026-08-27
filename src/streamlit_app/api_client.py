from __future__ import annotations

import os
from typing import Any

import httpx


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


class ApiUnavailable(RuntimeError):
    pass


class AuthenticationRequired(RuntimeError):
    pass


class AccessDenied(RuntimeError):
    pass


def request(method: str, path: str, *, token: str | None = None, **kwargs: Any) -> httpx.Response:
    headers = dict(kwargs.pop("headers", {}) or {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        return httpx.request(
            method,
            f"{API_BASE_URL}{path}",
            headers=headers,
            timeout=10.0,
            **kwargs,
        )
    except httpx.HTTPError as exc:
        raise ApiUnavailable("ISI API trenutno nije dostupan.") from exc


def login(email: str, password: str) -> dict[str, Any]:
    response = request("POST", "/api/v1/auth/login", json={"email": email, "password": password})
    if response.status_code != 200:
        raise AuthenticationRequired("Email ili lozinka nisu ispravni, ili nalog nije spreman za prijavu.")
    return response.json()


def logout(token: str) -> None:
    response = request("POST", "/api/v1/auth/logout", token=token)
    if response.status_code not in {204, 401}:
        response.raise_for_status()


def app_context(token: str) -> dict[str, Any]:
    response = request("GET", "/api/v1/app-context", token=token)
    if response.status_code == 401:
        raise AuthenticationRequired("Sesija je istekla.")
    if response.status_code == 403:
        raise AccessDenied("Pristup aplikaciji nije dostupan.")
    if response.status_code != 200:
        raise ApiUnavailable("Nije moguće učitati pristupni kontekst.")
    return response.json()


def app_shell(
    token: str,
    *,
    organization_id: str,
    product_code: str,
    workspace_id: str | None = None,
) -> dict[str, Any]:
    params: dict[str, str] = {
        "organization_id": organization_id,
        "product_code": product_code,
    }
    if workspace_id:
        params["workspace_id"] = workspace_id
    response = request("GET", "/api/v1/app-shell", token=token, params=params)
    if response.status_code == 401:
        raise AuthenticationRequired("Sesija je istekla.")
    if response.status_code == 403:
        raise AccessDenied("Izabrani organizacioni, platformski ili workspace kontekst nije dostupan.")
    if response.status_code != 200:
        raise ApiUnavailable("Nije moguće učitati aplikacioni shell.")
    return response.json()
