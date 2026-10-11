from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import ValidationError

from src.platform.administration.schemas import (
    AdminSessionInventoryResponse,
    InvitationCreateRequest,
    MemberStatusRequest,
    OrganizationNameRequest,
    ProductAccessRequest,
    RoleAssignmentRequest,
    WorkspaceCreateRequest,
    WorkspaceStatusRequest,
)
from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired, request

_MESSAGES = {
    "step_up_authentication_required": "Potrebna je dodatna autentifikacija. Ova operacija ostaje blokirana bez zahtevanog nivoa sigurnosti.",
    "invitation_delivery_not_configured": "SMTP je pending; poziv nije poslat. Ne ponavljajte zahtev pre podešavanja isporuke.",
    "last_organization_admin_required": "Poslednji administrator mora ostati aktivan.",
    "last_organization_admin_product_access_required": "Poslednjem administratoru ne možete oduzeti pristup proizvodu.",
    "organization_entitlement_not_active": "Organizacija nema aktivno pravo na ovaj proizvod.",
    "role_requires_product_access": "Pre role potreban je aktivan pristup proizvodu.",
    "workspace_slug_exists": "Slug već postoji. Izaberite drugi slug.",
    "global_session_multi_organization_target_not_supported": "Globalne sesije člana više organizacija nisu dostupne za ovu administrativnu operaciju.",
    "other_user_session_target_required": "Za svoje sesije koristite sopstveni pregled sesija.",
    "organization_wide_permission_required": "Potrebno je ovlašćenje za celu organizaciju.",
}


def _checked(response, *, unavailable: str) -> Any:
    if response.status_code == 401:
        raise AuthenticationRequired("Sesija je istekla.")
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail")
        except (ValueError, AttributeError):
            detail = None
        message = _MESSAGES.get(detail) if isinstance(detail, str) else None
        if response.status_code >= 500:
            raise ApiUnavailable(message or unavailable)
        raise AccessDenied(
            message or "Zahtev je odbijen. Proverite ovlašćenja, polja i aktuelno stanje; zatim osvežite pregled."
        )
    if response.status_code == 204:
        return {"completed": True}
    return response.json()


def _scope(organization_id: str, product_code: str) -> dict:
    try:
        organization_id = str(UUID(organization_id))
    except (ValueError, TypeError, AttributeError):
        raise AccessDenied("Izaberite važeću organizaciju.") from None
    if product_code not in {"SIMPA", "ORDO"}:
        raise AccessDenied("Izaberite SIMPA ili ORDO.")
    return {"organization_id": organization_id, "product_code": product_code}


def _id(value: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise AccessDenied("Izaberite važeći zapis.") from None


def _body(schema, values: dict) -> dict:
    try:
        return schema.model_validate(values).model_dump(mode="json")
    except ValidationError:
        raise AccessDenied("Popunite sva polja važećim vrednostima. Zahtev nije poslat.") from None


def _mutation(method: str, path: str, token: str, schema, values: dict):
    return _checked(
        request(method, path, token=token, json=_body(schema, values)),
        unavailable="Promena nije potvrđena. Osvežite pregled pre ponavljanja.",
    )


def snapshot(token: str, organization_id: str, product_code: str):
    return _checked(
        request("GET", "/api/v1/administration/snapshot", token=token, params=_scope(organization_id, product_code)),
        unavailable="Nije moguće učitati administraciju.",
    )


def invite(token: str, *, organization_id: str, product_code: str, email: str, role_code: str):
    result = _mutation(
        "POST",
        "/api/v1/administration/invitations",
        token,
        InvitationCreateRequest,
        dict(**_scope(organization_id, product_code), email=email.strip(), role_code=role_code),
    )
    # Development delivery credentials must never enter UI state, screenshots or receipts.
    return {
        key: result.get(key) for key in ("id", "status", "product_code", "role_code", "expires_at", "delivery_status")
    }


def revoke_invite(token: str, *, invitation_id: str, organization_id: str, product_code: str):
    return _checked(
        request(
            "POST",
            f"/api/v1/administration/invitations/{_id(invitation_id)}/revoke",
            token=token,
            params=_scope(organization_id, product_code),
        ),
        unavailable="Opoziv nije potvrđen; osvežite pregled.",
    )


def member_status(token: str, *, membership_id: str, organization_id: str, product_code: str, status: str):
    return _mutation(
        "POST",
        f"/api/v1/administration/members/{_id(membership_id)}/status",
        token,
        MemberStatusRequest,
        dict(**_scope(organization_id, product_code), status=status),
    )


def product_access(token: str, *, membership_id: str, organization_id: str, product_code: str, active: bool):
    return _mutation(
        "POST",
        f"/api/v1/administration/members/{_id(membership_id)}/product-access",
        token,
        ProductAccessRequest,
        dict(**_scope(organization_id, product_code), active=active),
    )


def assign_role(token: str, *, membership_id: str, organization_id: str, product_code: str, role_code: str, scope: str):
    return _mutation(
        "POST",
        f"/api/v1/administration/members/{_id(membership_id)}/roles",
        token,
        RoleAssignmentRequest,
        dict(**_scope(organization_id, product_code), role_code=role_code, scope=scope),
    )


def remove_role(token: str, *, membership_id: str, assignment_id: str, organization_id: str, product_code: str):
    return _checked(
        request(
            "DELETE",
            f"/api/v1/administration/members/{_id(membership_id)}/roles/{_id(assignment_id)}",
            token=token,
            params=_scope(organization_id, product_code),
        ),
        unavailable="Uklanjanje role nije potvrđeno; osvežite pregled.",
    )


def create_workspace(token: str, *, organization_id: str, product_code: str, name: str, slug: str):
    return _mutation(
        "POST",
        "/api/v1/administration/workspaces",
        token,
        WorkspaceCreateRequest,
        dict(**_scope(organization_id, product_code), name=name.strip(), slug=slug.strip()),
    )


def workspace_status(token: str, *, workspace_id: str, organization_id: str, product_code: str, status: str):
    return _mutation(
        "POST",
        f"/api/v1/administration/workspaces/{_id(workspace_id)}/status",
        token,
        WorkspaceStatusRequest,
        dict(**_scope(organization_id, product_code), status=status),
    )


def rename_organization(token: str, *, organization_id: str, product_code: str, name: str):
    return _mutation(
        "PATCH",
        "/api/v1/administration/organization",
        token,
        OrganizationNameRequest,
        dict(**_scope(organization_id, product_code), name=name.strip()),
    )


def member_sessions(token: str, *, membership_id: str, organization_id: str, product_code: str):
    rows = _checked(
        request(
            "GET",
            f"/api/v1/administration/members/{_id(membership_id)}/sessions",
            token=token,
            params=_scope(organization_id, product_code),
        ),
        unavailable="Nije moguće učitati sesije.",
    )
    try:
        return [AdminSessionInventoryResponse.model_validate(row).model_dump(mode="json") for row in rows]
    except (ValidationError, TypeError):
        raise ApiUnavailable("Pregled sesija nije važeći. Osvežite pregled.") from None


def revoke_member_session(token: str, *, membership_id: str, session_id: str, organization_id: str, product_code: str):
    return _checked(
        request(
            "DELETE",
            f"/api/v1/administration/members/{_id(membership_id)}/sessions/{_id(session_id)}",
            token=token,
            params=_scope(organization_id, product_code),
        ),
        unavailable="Opoziv sesije nije potvrđen; osvežite pregled.",
    )
