from __future__ import annotations

from typing import Any

from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired, request


def _checked(response, *, unavailable: str) -> Any:
    if response.status_code == 401:
        raise AuthenticationRequired("Sesija je istekla.")
    if response.status_code == 403:
        raise AccessDenied("Administrativni pristup nije dozvoljen u izabranom kontekstu.")
    if response.status_code >= 500:
        try:
            detail = response.json().get("detail")
        except Exception:
            detail = None
        raise ApiUnavailable(str(detail or unavailable))
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", "Administration request rejected")
        except Exception:
            detail = "Administration request rejected"
        raise AccessDenied(str(detail))
    if response.status_code == 204:
        return None
    return response.json()


def snapshot(token: str, organization_id: str, product_code: str):
    return _checked(request("GET", "/api/v1/administration/snapshot", token=token, params={"organization_id": organization_id, "product_code": product_code}), unavailable="Nije moguće učitati administraciju.")


def invite(token: str, *, organization_id: str, product_code: str, email: str, role_code: str):
    return _checked(request("POST", "/api/v1/administration/invitations", token=token, json={"organization_id": organization_id, "product_code": product_code, "email": email, "role_code": role_code}), unavailable="Nije moguće kreirati poziv.")


def revoke_invite(token: str, *, invitation_id: str, organization_id: str, product_code: str):
    return _checked(request("POST", f"/api/v1/administration/invitations/{invitation_id}/revoke", token=token, params={"organization_id": organization_id, "product_code": product_code}), unavailable="Nije moguće opozvati poziv.")


def member_status(token: str, *, membership_id: str, organization_id: str, product_code: str, status: str):
    return _checked(request("POST", f"/api/v1/administration/members/{membership_id}/status", token=token, json={"organization_id": organization_id, "product_code": product_code, "status": status}), unavailable="Nije moguće promeniti status člana.")


def product_access(token: str, *, membership_id: str, organization_id: str, product_code: str, active: bool):
    return _checked(request("POST", f"/api/v1/administration/members/{membership_id}/product-access", token=token, json={"organization_id": organization_id, "product_code": product_code, "active": active}), unavailable="Nije moguće promeniti product access.")


def assign_role(token: str, *, membership_id: str, organization_id: str, product_code: str, role_code: str, scope: str):
    return _checked(request("POST", f"/api/v1/administration/members/{membership_id}/roles", token=token, json={"organization_id": organization_id, "product_code": product_code, "role_code": role_code, "scope": scope}), unavailable="Nije moguće dodeliti rolu.")


def remove_role(token: str, *, membership_id: str, assignment_id: str, organization_id: str, product_code: str):
    return _checked(request("DELETE", f"/api/v1/administration/members/{membership_id}/roles/{assignment_id}", token=token, params={"organization_id": organization_id, "product_code": product_code}), unavailable="Nije moguće ukloniti rolu.")


def create_workspace(token: str, *, organization_id: str, product_code: str, name: str, slug: str):
    return _checked(request("POST", "/api/v1/administration/workspaces", token=token, json={"organization_id": organization_id, "product_code": product_code, "name": name, "slug": slug}), unavailable="Nije moguće kreirati workspace.")


def workspace_status(token: str, *, workspace_id: str, organization_id: str, product_code: str, status: str):
    return _checked(request("POST", f"/api/v1/administration/workspaces/{workspace_id}/status", token=token, json={"organization_id": organization_id, "product_code": product_code, "status": status}), unavailable="Nije moguće promeniti workspace status.")


def rename_organization(token: str, *, organization_id: str, product_code: str, name: str):
    return _checked(request("PATCH", "/api/v1/administration/organization", token=token, json={"organization_id": organization_id, "product_code": product_code, "name": name}), unavailable="Nije moguće promeniti naziv organizacije.")
