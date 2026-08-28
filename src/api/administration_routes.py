from __future__ import annotations

from src.platform.auth.delivery import auth_delivery_configured, get_auth_delivery

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies import AuthContext, get_auth_context, get_db
from src.core.config import get_settings
from src.platform.access.service import has_permission
from src.platform.administration.schemas import (
    InvitationCreateRequest,
    MemberStatusRequest,
    OrganizationNameRequest,
    ProductAccessRequest,
    RoleAssignmentRequest,
    WorkspaceCreateRequest,
    WorkspaceStatusRequest,
)
from src.platform.administration.service import (
    AdministrationError,
    administration_snapshot,
    assign_member_role,
    create_admin_invitation,
    create_workspace,
    has_org_wide_permission,
    remove_member_role,
    rename_organization,
    revoke_admin_invitation,
    set_member_product_access,
    set_membership_status,
    set_workspace_status,
)
from src.platform.app_context.service import AppContextError, resolve_selection


router = APIRouter(prefix="/api/v1/administration", tags=["administration"])
ADMIN_PERMISSIONS = ("organization.manage", "members.manage", "workspace.manage", "audit.read")


def _scope(
    db: Session,
    context: AuthContext,
    *,
    organization_id: uuid.UUID,
    product_code: str,
    permission_code: str | None = None,
) -> None:
    try:
        resolve_selection(
            db,
            user_id=context.user.id,
            organization_id=organization_id,
            product_code=product_code,
            workspace_id=None,
        )
    except AppContextError:
        raise HTTPException(status_code=403, detail="administration_scope_not_accessible") from None
    if permission_code and not has_permission(db, context.user.id, organization_id, permission_code, product_code):
        raise HTTPException(status_code=403, detail="administration_permission_denied")


def _orgwide(db: Session, context: AuthContext, organization_id: uuid.UUID, permission_code: str) -> None:
    if not has_org_wide_permission(
        db,
        user_id=context.user.id,
        organization_id=organization_id,
        permission_code=permission_code,
    ):
        raise HTTPException(status_code=403, detail="organization_wide_permission_required")


def _error(exc: AdministrationError) -> HTTPException:
    conflict = {
        "last_organization_admin_required",
        "last_organization_admin_product_access_required",
        "organization_entitlement_not_active",
        "organization_admin_invitation_forbidden",
        "role_requires_product_access",
        "workspace_slug_exists",
    }
    return HTTPException(status_code=409 if exc.code in conflict else 400, detail=exc.code)


@router.get("/snapshot")
def get_snapshot(
    organization_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    product_code = product_code.upper()
    _scope(db, context, organization_id=organization_id, product_code=product_code)
    capabilities = {
        "organization_manage": has_permission(db, context.user.id, organization_id, "organization.manage", product_code),
        "members_read": has_permission(db, context.user.id, organization_id, "members.read", product_code),
        "members_manage": has_permission(db, context.user.id, organization_id, "members.manage", product_code),
        "workspace_manage": has_permission(db, context.user.id, organization_id, "workspace.manage", product_code),
        "audit_read": has_permission(db, context.user.id, organization_id, "audit.read", product_code),
        "org_wide_manage": has_org_wide_permission(db, user_id=context.user.id, organization_id=organization_id, permission_code="organization.manage"),
        "org_wide_members_manage": has_org_wide_permission(db, user_id=context.user.id, organization_id=organization_id, permission_code="members.manage"),
    }
    if not any(capabilities[key] for key in ("organization_manage", "members_read", "members_manage", "workspace_manage", "audit_read")):
        raise HTTPException(status_code=403, detail="administration_permission_denied")
    try:
        result = administration_snapshot(
            db,
            organization_id=organization_id,
            product_code=product_code,
            include_members=capabilities["members_read"] or capabilities["members_manage"],
            include_workspaces=True,
            include_audit=capabilities["audit_read"],
        )
        if not (capabilities["members_read"] or capabilities["members_manage"]):
            result["invitations"] = []
        result["capabilities"] = capabilities
        return result
    except AdministrationError as exc:
        raise _error(exc) from None


@router.post("/invitations", status_code=status.HTTP_201_CREATED)
def post_invitation(
    payload: InvitationCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _scope(db, context, organization_id=payload.organization_id, product_code=payload.product_code, permission_code="members.manage")
    if get_settings().isi_env.casefold() == "production" and not auth_delivery_configured():
        raise HTTPException(status_code=503, detail="invitation_delivery_not_configured")
    try:
        invitation, token = create_admin_invitation(
            db,
            organization_id=payload.organization_id,
            product_code=payload.product_code,
            email=str(payload.email),
            role_code=payload.role_code,
            actor_user_id=context.user.id,
        )
        if get_settings().isi_env.strip().casefold() == "production":
            get_auth_delivery().send_invitation(email=invitation.email, token=token)
        db.commit(); db.refresh(invitation)
        response = {
            "id": str(invitation.id),
            "email": invitation.email,
            "status": invitation.status,
            "product_code": payload.product_code,
            "role_code": payload.role_code,
            "expires_at": invitation.expires_at,
            "delivery_status": "smtp",
        }
        if get_settings().isi_env.strip().casefold() != "production":
            response.update({
                "delivery_status": "development_token",
                "development_token": token,
            })
        return response
    except AdministrationError as exc:
        db.rollback(); raise _error(exc) from None


@router.post("/invitations/{invitation_id}/revoke")
def post_revoke_invitation(
    invitation_id: uuid.UUID,
    organization_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    product_code = product_code.upper()
    _scope(db, context, organization_id=organization_id, product_code=product_code, permission_code="members.manage")
    try:
        invitation = revoke_admin_invitation(db, organization_id=organization_id, product_code=product_code, invitation_id=invitation_id, actor_user_id=context.user.id)
        db.commit(); db.refresh(invitation)
        return {"id": str(invitation.id), "status": invitation.status}
    except AdministrationError as exc:
        db.rollback(); raise _error(exc) from None


@router.post("/members/{membership_id}/status")
def post_member_status(
    membership_id: uuid.UUID,
    payload: MemberStatusRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _scope(db, context, organization_id=payload.organization_id, product_code=payload.product_code, permission_code="members.manage")
    # Membership status is organization-wide: suspending a membership affects every product.
    _orgwide(db, context, payload.organization_id, "members.manage")
    try:
        membership = set_membership_status(db, organization_id=payload.organization_id, membership_id=membership_id, status=payload.status, actor_user_id=context.user.id, product_code=payload.product_code)
        db.commit(); db.refresh(membership)
        return {"membership_id": str(membership.id), "status": membership.status}
    except AdministrationError as exc:
        db.rollback(); raise _error(exc) from None


@router.post("/members/{membership_id}/product-access")
def post_product_access(
    membership_id: uuid.UUID,
    payload: ProductAccessRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _scope(db, context, organization_id=payload.organization_id, product_code=payload.product_code, permission_code="members.manage")
    try:
        access = set_member_product_access(db, organization_id=payload.organization_id, membership_id=membership_id, product_code=payload.product_code, active=payload.active, actor_user_id=context.user.id)
        db.commit(); db.refresh(access)
        return {"membership_id": str(membership_id), "product_code": access.product_code, "active": access.is_active}
    except AdministrationError as exc:
        db.rollback(); raise _error(exc) from None


@router.post("/members/{membership_id}/roles", status_code=status.HTTP_201_CREATED)
def post_role(
    membership_id: uuid.UUID,
    payload: RoleAssignmentRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _scope(db, context, organization_id=payload.organization_id, product_code=payload.product_code, permission_code="members.manage")
    if payload.scope == "organization":
        _orgwide(db, context, payload.organization_id, "members.manage")
    try:
        assignment = assign_member_role(db, organization_id=payload.organization_id, membership_id=membership_id, product_code=payload.product_code, role_code=payload.role_code, scope=payload.scope, actor_user_id=context.user.id)
        db.commit(); db.refresh(assignment)
        return {"id": str(assignment.id), "membership_id": str(membership_id), "role_code": payload.role_code, "scope": assignment.product_code}
    except AdministrationError as exc:
        db.rollback(); raise _error(exc) from None


@router.delete("/members/{membership_id}/roles/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    membership_id: uuid.UUID,
    assignment_id: uuid.UUID,
    organization_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> None:
    product_code = product_code.upper()
    _scope(db, context, organization_id=organization_id, product_code=product_code, permission_code="members.manage")
    allow_org_wide = has_org_wide_permission(
        db, user_id=context.user.id, organization_id=organization_id, permission_code="members.manage"
    )
    try:
        remove_member_role(
            db,
            organization_id=organization_id,
            membership_id=membership_id,
            assignment_id=assignment_id,
            actor_user_id=context.user.id,
            allow_org_wide=allow_org_wide,
        )
        db.commit(); return None
    except AdministrationError as exc:
        db.rollback(); raise _error(exc) from None


@router.post("/workspaces", status_code=status.HTTP_201_CREATED)
def post_workspace(
    payload: WorkspaceCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _scope(db, context, organization_id=payload.organization_id, product_code=payload.product_code, permission_code="workspace.manage")
    try:
        workspace = create_workspace(db, organization_id=payload.organization_id, product_code=payload.product_code, name=payload.name, slug=payload.slug, actor_user_id=context.user.id)
        db.commit(); db.refresh(workspace)
        return {"id": str(workspace.id), "slug": workspace.slug, "name": workspace.name, "status": workspace.status, "product_code": workspace.product_code}
    except AdministrationError as exc:
        db.rollback(); raise _error(exc) from None


@router.post("/workspaces/{workspace_id}/status")
def post_workspace_status(
    workspace_id: uuid.UUID,
    payload: WorkspaceStatusRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _scope(db, context, organization_id=payload.organization_id, product_code=payload.product_code, permission_code="workspace.manage")
    try:
        workspace = set_workspace_status(db, organization_id=payload.organization_id, product_code=payload.product_code, workspace_id=workspace_id, status=payload.status, actor_user_id=context.user.id)
        db.commit(); db.refresh(workspace)
        return {"id": str(workspace.id), "status": workspace.status}
    except AdministrationError as exc:
        db.rollback(); raise _error(exc) from None


@router.patch("/organization")
def patch_organization(
    payload: OrganizationNameRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _scope(db, context, organization_id=payload.organization_id, product_code=payload.product_code, permission_code="organization.manage")
    _orgwide(db, context, payload.organization_id, "organization.manage")
    try:
        organization = rename_organization(db, organization_id=payload.organization_id, name=payload.name, actor_user_id=context.user.id)
        db.commit(); db.refresh(organization)
        return {"id": str(organization.id), "name": organization.name, "slug": organization.slug, "status": organization.status}
    except AdministrationError as exc:
        db.rollback(); raise _error(exc) from None
