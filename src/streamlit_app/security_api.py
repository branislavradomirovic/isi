"""Typed self-account transports; private error bodies are never reflected."""

from __future__ import annotations

from typing import Any
from uuid import UUID
from pydantic import ValidationError
from src.platform.auth.schemas import SessionInventoryResponse, RevokeOtherSessionsResponse
from src.streamlit_app.api_client import ApiUnavailable, AuthenticationRequired, request


def _authenticated(response) -> None:
    if response.status_code == 401:
        raise AuthenticationRequired("Sesija je istekla.")
    if response.status_code >= 400:
        raise ApiUnavailable("Operacija bezbednosti naloga trenutno nije dostupna.")


def list_sessions(token: str) -> list[dict[str, Any]]:
    response = request("GET", "/api/v1/auth/sessions", token=token)
    _authenticated(response)
    try:
        data = response.json()
        if not isinstance(data, list):
            raise ValueError()
        return [SessionInventoryResponse.model_validate(row).model_dump(mode="json") for row in data]
    except (ValueError, TypeError, ValidationError):
        raise ApiUnavailable("Pregled sesija nije moguće pouzdano učitati.") from None


def revoke_session(token: str, session_id: str) -> dict:
    identity = str(UUID(str(session_id)))
    response = request("DELETE", f"/api/v1/auth/sessions/{identity}", token=token)
    _authenticated(response)
    if response.status_code != 204:
        raise ApiUnavailable("Opoziv sesije nije potvrđen. Osvežite pregled pre ponavljanja.")
    return {"completed": True}


def revoke_other_sessions(token: str) -> int:
    response = request("POST", "/api/v1/auth/sessions/revoke-others", token=token)
    _authenticated(response)
    try:
        return RevokeOtherSessionsResponse.model_validate(response.json()).revoked_count
    except (ValueError, TypeError, ValidationError):
        raise ApiUnavailable("Rezultat opoziva nije moguće potvrditi. Osvežite pregled.") from None


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
    try:
        return response.json().get("status") == "refreshed"
    except (ValueError, AttributeError):
        raise ApiUnavailable("Potvrda identiteta trenutno nije dostupna.") from None
