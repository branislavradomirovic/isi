from __future__ import annotations

from typing import Any

from src.streamlit_app.api_client import ApiUnavailable, AuthenticationRequired, request


def _authenticated(response) -> None:
    if response.status_code == 401:
        raise AuthenticationRequired("Sesija je istekla.")
    if response.status_code >= 400:
        raise ApiUnavailable("Operacija bezbednosti naloga trenutno nije dostupna.")


def list_sessions(token: str) -> list[dict[str, Any]]:
    response = request("GET", "/api/v1/auth/sessions", token=token)
    _authenticated(response)
    return list(response.json())


def revoke_session(token: str, session_id: str) -> None:
    response = request("DELETE", f"/api/v1/auth/sessions/{session_id}", token=token)
    _authenticated(response)


def revoke_other_sessions(token: str) -> int:
    response = request("POST", "/api/v1/auth/sessions/revoke-others", token=token)
    _authenticated(response)
    return int(response.json()["revoked_count"])


def refresh_password_assurance(token: str, password: str) -> bool:
    response = request(
        "POST",
        "/api/v1/auth/assurance/password",
        token=token,
        json={"password": password},
    )
    if response.status_code == 401:
        return False
    _authenticated(response)
    return response.json().get("status") == "refreshed"
