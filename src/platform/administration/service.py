from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from src.platform.access.models import (
    MembershipProductAccess,
    OrganizationEntitlement,
    Permission,
    Role,
    RoleAssignment,
    RolePermission,
)
from src.platform.access.service import AccessInvariantError, grant_product_access
from src.platform.administration.models import AdminAuditEvent, InvitationProductGrant, InvitationRoleGrant
from src.platform.auth.models import AuthSession, Invitation
from src.platform.auth.security import hash_token
from src.platform.auth.service import SessionInventoryItem, list_user_sessions
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace


class AdministrationError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


ADMIN_SESSION_REVOCATION_REASON = "organization_administrator_revocation"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _current_entitlement(session: Session, organization_id: uuid.UUID, product_code: str) -> OrganizationEntitlement:
    entitlement = session.scalar(
        select(OrganizationEntitlement).where(
            OrganizationEntitlement.organization_id == organization_id,
            OrganizationEntitlement.product_code == product_code,
        )
    )
    now = utcnow()
    if (
        entitlement is None
        or not entitlement.is_active
        or (entitlement.starts_at is not None and _aware(entitlement.starts_at) > now)
        or (entitlement.ends_at is not None and _aware(entitlement.ends_at) <= now)
    ):
        raise AdministrationError("organization_entitlement_not_active")
    return entitlement


def _membership(session: Session, organization_id: uuid.UUID, membership_id: uuid.UUID) -> Membership:
    membership = session.scalar(
        select(Membership).where(
            Membership.id == membership_id,
            Membership.organization_id == organization_id,
        )
    )
    if membership is None:
        raise AdministrationError("membership_not_accessible")
    return membership


def _require_single_organization_session_target(
    session: Session,
    *,
    membership: Membership,
    organization_id: uuid.UUID,
) -> None:
    other_active_membership = session.scalar(
        select(Membership.id)
        .where(
            Membership.user_id == membership.user_id,
            Membership.organization_id != organization_id,
            Membership.status == "active",
        )
        .limit(1)
    )
    if other_active_membership is not None:
        raise AdministrationError("global_session_multi_organization_target_not_supported")


def _role(session: Session, role_code: str) -> Role:
    role = session.scalar(select(Role).where(Role.code == role_code))
    if role is None:
        raise AdministrationError("role_not_found")
    return role


def _actor_membership_id(session: Session, organization_id: uuid.UUID, actor_user_id: uuid.UUID | None) -> uuid.UUID | None:
    if actor_user_id is None:
        return None
    return session.scalar(
        select(Membership.id).where(
            Membership.user_id == actor_user_id,
            Membership.organization_id == organization_id,
            Membership.status == "active",
        )
    )


def _audit(
    session: Session,
    *,
    organization_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
    action: str,
    target_type: str,
    target_id: object,
    product_code: str | None,
    before: dict,
    after: dict,
) -> AdminAuditEvent:
    event = AdminAuditEvent(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        actor_membership_id=_actor_membership_id(session, organization_id, actor_user_id),
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        product_code=product_code,
        before_state=before,
        after_state=after,
    )
    session.add(event)
    session.flush()
    return event


def has_org_wide_permission(
    session: Session,
    *,
    user_id: uuid.UUID,
    organization_id: uuid.UUID,
    permission_code: str,
) -> bool:
    user = session.get(User, user_id)
    if user is None or not user.is_active:
        return False
    if user.is_platform_admin:
        return True
    membership = session.scalar(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.organization_id == organization_id,
            Membership.status == "active",
        )
    )
    if membership is None:
        return False
    permission = session.scalar(select(Permission).where(Permission.code == permission_code))
    if permission is None:
        return False
    return session.scalar(
        select(RolePermission.role_id)
        .join(RoleAssignment, RoleAssignment.role_id == RolePermission.role_id)
        .where(
            RolePermission.permission_id == permission.id,
            RoleAssignment.membership_id == membership.id,
            RoleAssignment.product_code == "*",
        )
        .limit(1)
    ) is not None


def role_assignment_requires_org_wide(
    session: Session,
    *,
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
    assignment_id: uuid.UUID,
) -> bool:
    membership = _membership(session, organization_id, membership_id)
    assignment = session.scalar(
        select(RoleAssignment).where(
            RoleAssignment.id == assignment_id,
            RoleAssignment.membership_id == membership.id,
        )
    )
    if assignment is None:
        raise AdministrationError("role_assignment_not_accessible")
    return assignment.product_code == "*"


def list_member_sessions(
    session: Session,
    *,
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    current_session_id: uuid.UUID,
) -> list[SessionInventoryItem]:
    """Return global login sessions only after resolving an organization-owned target membership."""
    membership = _membership(session, organization_id, membership_id)
    if membership.user_id == actor_user_id:
        raise AdministrationError("other_user_session_target_required")
    _require_single_organization_session_target(
        session,
        membership=membership,
        organization_id=organization_id,
    )
    return list_user_sessions(
        session,
        user_id=membership.user_id,
        current_session_id=current_session_id,
    )


def revoke_member_session(
    session: Session,
    *,
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
    target_session_id: uuid.UUID,
    actor_user_id: uuid.UUID,
) -> bool:
    """Idempotently revoke a target member's global login session."""
    membership = _membership(session, organization_id, membership_id)
    if membership.user_id == actor_user_id:
        raise AdministrationError("other_user_session_target_required")
    _require_single_organization_session_target(
        session,
        membership=membership,
        organization_id=organization_id,
    )
    auth_session = session.scalar(
        select(AuthSession)
        .where(AuthSession.id == target_session_id, AuthSession.user_id == membership.user_id)
        .with_for_update()
    )
    if auth_session is None:
        return False
    if auth_session.revoked_at is None:
        auth_session.revoked_at = utcnow()
        auth_session.revoked_reason = ADMIN_SESSION_REVOCATION_REASON
        session.flush()
    return True


def _active_admin_ids_for_product(
    session: Session,
    organization_id: uuid.UUID,
    product_code: str,
) -> list[uuid.UUID]:
    values = session.scalars(
        select(Membership.id)
        .join(User, User.id == Membership.user_id)
        .join(MembershipProductAccess, MembershipProductAccess.membership_id == Membership.id)
        .join(RoleAssignment, RoleAssignment.membership_id == Membership.id)
        .join(Role, Role.id == RoleAssignment.role_id)
        .where(
            Membership.organization_id == organization_id,
            Membership.status == "active",
            User.is_active.is_(True),
            MembershipProductAccess.product_code == product_code,
            MembershipProductAccess.is_active.is_(True),
            RoleAssignment.product_code.in_(["*", product_code]),
            Role.code == "organization_admin",
        )
        .distinct()
    ).all()
    return list(values)


def _protect_last_admin_for_product(
    session: Session,
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
    product_code: str,
) -> None:
    admin_ids = _active_admin_ids_for_product(session, organization_id, product_code)
    if membership_id in admin_ids and len(admin_ids) <= 1:
        raise AdministrationError("last_organization_admin_required")


def administration_snapshot(
    session: Session,
    *,
    organization_id: uuid.UUID,
    product_code: str,
    include_members: bool = True,
    include_workspaces: bool = True,
    include_audit: bool = False,
) -> dict:
    organization = session.get(Organization, organization_id)
    if organization is None:
        raise AdministrationError("organization_not_accessible")
    entitlement = session.scalar(
        select(OrganizationEntitlement).where(
            OrganizationEntitlement.organization_id == organization_id,
            OrganizationEntitlement.product_code == product_code,
        )
    )
    entitlement_data = None
    if entitlement is not None:
        entitlement_data = {
            "product_code": entitlement.product_code,
            "is_active": entitlement.is_active,
            "starts_at": entitlement.starts_at,
            "ends_at": entitlement.ends_at,
        }

    members: list[dict] = []
    if include_members:
        rows = session.execute(
            select(Membership, User)
            .join(User, User.id == Membership.user_id)
            .where(Membership.organization_id == organization_id)
            .order_by(User.display_name, User.email)
        ).all()
        for membership, user in rows:
            access = session.scalar(
                select(MembershipProductAccess).where(
                    MembershipProductAccess.membership_id == membership.id,
                    MembershipProductAccess.product_code == product_code,
                )
            )
            assignments = session.execute(
                select(RoleAssignment, Role)
                .join(Role, Role.id == RoleAssignment.role_id)
                .where(
                    RoleAssignment.membership_id == membership.id,
                    RoleAssignment.product_code.in_(["*", product_code]),
                )
                .order_by(RoleAssignment.product_code, Role.code)
            ).all()
            members.append(
                {
                    "membership_id": str(membership.id),
                    "user_id": str(user.id),
                    "display_name": user.display_name,
                    "email": user.email,
                    "membership_status": membership.status,
                    "user_active": user.is_active,
                    "product_access_active": bool(access and access.is_active),
                    "roles": [
                        {
                            "assignment_id": str(assignment.id),
                            "role_code": role.code,
                            "scope": assignment.product_code,
                        }
                        for assignment, role in assignments
                    ],
                }
            )

    invitation_rows = session.execute(
        select(Invitation, InvitationProductGrant)
        .join(InvitationProductGrant, InvitationProductGrant.invitation_id == Invitation.id)
        .where(
            Invitation.organization_id == organization_id,
            InvitationProductGrant.product_code == product_code,
        )
        .order_by(Invitation.created_at.desc())
    ).all()
    invitations: list[dict] = []
    for invitation, grant in invitation_rows:
        role_grants = session.execute(
            select(InvitationRoleGrant, Role)
            .join(Role, Role.id == InvitationRoleGrant.role_id)
            .where(InvitationRoleGrant.invitation_id == invitation.id)
        ).all()
        invitations.append(
            {
                "id": str(invitation.id),
                "email": invitation.email,
                "status": invitation.status,
                "product_code": grant.product_code,
                "roles": [{"role_code": role.code, "scope": role_grant.product_code} for role_grant, role in role_grants],
                "expires_at": invitation.expires_at,
                "created_at": invitation.created_at,
            }
        )

    workspaces: list[dict] = []
    if include_workspaces:
        rows = session.scalars(
            select(Workspace)
            .where(Workspace.organization_id == organization_id, Workspace.product_code == product_code)
            .order_by(Workspace.status, Workspace.name)
        ).all()
        workspaces = [
            {
                "id": str(row.id),
                "slug": row.slug,
                "name": row.name,
                "status": row.status,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    audit: list[dict] = []
    if include_audit:
        rows = session.scalars(
            select(AdminAuditEvent)
            .where(
                AdminAuditEvent.organization_id == organization_id,
                or_(AdminAuditEvent.product_code == product_code, AdminAuditEvent.product_code.is_(None)),
            )
            .order_by(AdminAuditEvent.created_at.desc())
            .limit(100)
        ).all()
        audit = [
            {
                "id": str(row.id),
                "action": row.action,
                "target_type": row.target_type,
                "target_id": row.target_id,
                "product_code": row.product_code,
                "actor_user_id": str(row.actor_user_id) if row.actor_user_id else None,
                "before_state": row.before_state,
                "after_state": row.after_state,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    roles = session.scalars(select(Role).order_by(Role.code)).all()
    return {
        "organization": {"id": str(organization.id), "slug": organization.slug, "name": organization.name, "status": organization.status},
        "product_code": product_code,
        "entitlement": entitlement_data,
        "members": members,
        "invitations": invitations,
        "workspaces": workspaces,
        "role_catalog": [{"code": role.code, "name": role.name, "is_system": role.is_system} for role in roles],
        "audit": audit,
    }


def create_admin_invitation(
    session: Session,
    *,
    organization_id: uuid.UUID,
    product_code: str,
    email: str,
    role_code: str,
    actor_user_id: uuid.UUID,
) -> tuple[Invitation, str]:
    _current_entitlement(session, organization_id, product_code)
    if role_code == "organization_admin":
        raise AdministrationError("organization_admin_invitation_forbidden")
    role = _role(session, role_code)
    from src.platform.auth.service import create_invitation

    issued = create_invitation(
        session,
        organization_id=organization_id,
        email=email,
        invited_by_user_id=actor_user_id,
    )
    invitation = session.scalar(select(Invitation).where(Invitation.token_hash == hash_token(issued.token)))
    if invitation is None:
        raise AdministrationError("invitation_not_created")
    session.add(InvitationProductGrant(invitation_id=invitation.id, product_code=product_code))
    session.add(InvitationRoleGrant(invitation_id=invitation.id, role_id=role.id, product_code=product_code))
    _audit(
        session,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action="invitation.created",
        target_type="invitation",
        target_id=invitation.id,
        product_code=product_code,
        before={},
        after={"email": invitation.email, "status": invitation.status, "role_code": role.code},
    )
    session.flush()
    return invitation, issued.token


def revoke_admin_invitation(
    session: Session,
    *,
    organization_id: uuid.UUID,
    product_code: str,
    invitation_id: uuid.UUID,
    actor_user_id: uuid.UUID,
) -> Invitation:
    invitation = session.scalar(
        select(Invitation)
        .join(InvitationProductGrant, InvitationProductGrant.invitation_id == Invitation.id)
        .where(
            Invitation.id == invitation_id,
            Invitation.organization_id == organization_id,
            InvitationProductGrant.product_code == product_code,
        )
    )
    if invitation is None:
        raise AdministrationError("invitation_not_accessible")
    before = {"status": invitation.status}
    if invitation.status == "pending":
        invitation.status = "revoked"
        invitation.revoked_at = utcnow()
    _audit(
        session,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action="invitation.revoked",
        target_type="invitation",
        target_id=invitation.id,
        product_code=product_code,
        before=before,
        after={"status": invitation.status},
    )
    session.flush()
    return invitation


def apply_invitation_grants(session: Session, *, invitation: Invitation, membership: Membership) -> None:
    product_grants = session.scalars(
        select(InvitationProductGrant).where(InvitationProductGrant.invitation_id == invitation.id)
    ).all()
    for grant in product_grants:
        try:
            grant_product_access(session, membership, grant.product_code)
        except AccessInvariantError as exc:
            raise AdministrationError("invitation_entitlement_not_active") from exc

    role_grants = session.scalars(
        select(InvitationRoleGrant).where(InvitationRoleGrant.invitation_id == invitation.id)
    ).all()
    for grant in role_grants:
        if grant.product_code == "*":
            raise AdministrationError("invitation_org_wide_role_forbidden")
        access = session.scalar(
            select(MembershipProductAccess).where(
                MembershipProductAccess.membership_id == membership.id,
                MembershipProductAccess.product_code == grant.product_code,
                MembershipProductAccess.is_active.is_(True),
            )
        )
        if access is None:
            raise AdministrationError("invitation_product_access_missing")
        existing = session.scalar(
            select(RoleAssignment).where(
                RoleAssignment.membership_id == membership.id,
                RoleAssignment.role_id == grant.role_id,
                RoleAssignment.product_code == grant.product_code,
            )
        )
        if existing is None:
            session.add(
                RoleAssignment(
                    membership_id=membership.id,
                    role_id=grant.role_id,
                    product_code=grant.product_code,
                )
            )
    session.flush()


def set_membership_status(
    session: Session,
    *,
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
    status: str,
    actor_user_id: uuid.UUID,
    product_code: str,
) -> Membership:
    membership = _membership(session, organization_id, membership_id)
    if status not in {"active", "suspended"}:
        raise AdministrationError("membership_status_invalid")
    if status != "active" and membership.status == "active":
        for guarded_product in ("SIMPA", "ORDO"):
            _protect_last_admin_for_product(session, organization_id, membership.id, guarded_product)
    before = {"status": membership.status}
    membership.status = status
    _audit(
        session,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action="membership.status_changed",
        target_type="membership",
        target_id=membership.id,
        product_code=product_code,
        before=before,
        after={"status": membership.status},
    )
    session.flush()
    return membership


def set_member_product_access(
    session: Session,
    *,
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
    product_code: str,
    active: bool,
    actor_user_id: uuid.UUID,
) -> MembershipProductAccess:
    membership = _membership(session, organization_id, membership_id)
    existing = session.scalar(
        select(MembershipProductAccess).where(
            MembershipProductAccess.membership_id == membership.id,
            MembershipProductAccess.product_code == product_code,
        )
    )
    before = {"active": bool(existing and existing.is_active)}
    if active:
        _current_entitlement(session, organization_id, product_code)
        try:
            access = grant_product_access(session, membership, product_code)
        except AccessInvariantError as exc:
            raise AdministrationError("organization_entitlement_not_active") from exc
    else:
        if existing is None:
            raise AdministrationError("membership_product_access_not_found")
        try:
            _protect_last_admin_for_product(session, organization_id, membership.id, product_code)
        except AdministrationError as exc:
            if exc.code == "last_organization_admin_required":
                raise AdministrationError("last_organization_admin_product_access_required") from exc
            raise
        existing.is_active = False
        access = existing
    _audit(
        session,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action="membership.product_access_changed",
        target_type="membership_product_access",
        target_id=access.id,
        product_code=product_code,
        before=before,
        after={"active": access.is_active},
    )
    session.flush()
    return access


def assign_member_role(
    session: Session,
    *,
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
    product_code: str,
    role_code: str,
    scope: str,
    actor_user_id: uuid.UUID,
) -> RoleAssignment:
    membership = _membership(session, organization_id, membership_id)
    role = _role(session, role_code)
    assignment_scope = "*" if scope == "organization" else product_code
    if assignment_scope != "*":
        access = session.scalar(
            select(MembershipProductAccess).where(
                MembershipProductAccess.membership_id == membership.id,
                MembershipProductAccess.product_code == product_code,
                MembershipProductAccess.is_active.is_(True),
            )
        )
        if access is None:
            raise AdministrationError("role_requires_product_access")
    existing = session.scalar(
        select(RoleAssignment).where(
            RoleAssignment.membership_id == membership.id,
            RoleAssignment.role_id == role.id,
            RoleAssignment.product_code == assignment_scope,
        )
    )
    if existing is not None:
        return existing
    assignment = RoleAssignment(membership_id=membership.id, role_id=role.id, product_code=assignment_scope)
    session.add(assignment)
    session.flush()
    _audit(
        session,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action="membership.role_assigned",
        target_type="role_assignment",
        target_id=assignment.id,
        product_code=None if assignment_scope == "*" else product_code,
        before={},
        after={"role_code": role.code, "scope": assignment_scope},
    )
    return assignment


def remove_member_role(
    session: Session,
    *,
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
    assignment_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    allow_org_wide: bool = False,
) -> None:
    membership = _membership(session, organization_id, membership_id)
    row = session.execute(
        select(RoleAssignment, Role)
        .join(Role, Role.id == RoleAssignment.role_id)
        .where(RoleAssignment.id == assignment_id, RoleAssignment.membership_id == membership.id)
    ).one_or_none()
    if row is None:
        raise AdministrationError("role_assignment_not_accessible")
    assignment, role = row
    if assignment.product_code == "*" and not allow_org_wide:
        raise AdministrationError("organization_wide_permission_required")
    if role.code == "organization_admin":
        guarded_products = ("SIMPA", "ORDO") if assignment.product_code == "*" else (assignment.product_code,)
        for guarded_product in guarded_products:
            _protect_last_admin_for_product(session, organization_id, membership.id, guarded_product)
    before = {"role_code": role.code, "scope": assignment.product_code}
    product_scope = None if assignment.product_code == "*" else assignment.product_code
    session.delete(assignment)
    session.flush()
    _audit(
        session,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action="membership.role_removed",
        target_type="role_assignment",
        target_id=assignment_id,
        product_code=product_scope,
        before=before,
        after={},
    )


def create_workspace(
    session: Session,
    *,
    organization_id: uuid.UUID,
    product_code: str,
    name: str,
    slug: str,
    actor_user_id: uuid.UUID,
) -> Workspace:
    _current_entitlement(session, organization_id, product_code)
    normalized = slug.strip().lower()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", normalized):
        raise AdministrationError("workspace_slug_invalid")
    existing = session.scalar(
        select(Workspace).where(
            Workspace.organization_id == organization_id,
            Workspace.product_code == product_code,
            Workspace.slug == normalized,
        )
    )
    if existing is not None:
        raise AdministrationError("workspace_slug_exists")
    workspace = Workspace(
        organization_id=organization_id,
        product_code=product_code,
        slug=normalized,
        name=name.strip(),
        status="active",
        created_by_membership_id=_actor_membership_id(session, organization_id, actor_user_id),
    )
    session.add(workspace)
    session.flush()
    _audit(
        session,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action="workspace.created",
        target_type="workspace",
        target_id=workspace.id,
        product_code=product_code,
        before={},
        after={"slug": workspace.slug, "name": workspace.name, "status": workspace.status},
    )
    return workspace


def set_workspace_status(
    session: Session,
    *,
    organization_id: uuid.UUID,
    product_code: str,
    workspace_id: uuid.UUID,
    status: str,
    actor_user_id: uuid.UUID,
) -> Workspace:
    workspace = session.scalar(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.organization_id == organization_id,
            Workspace.product_code == product_code,
        )
    )
    if workspace is None:
        raise AdministrationError("workspace_not_accessible")
    if status not in {"active", "archived"}:
        raise AdministrationError("workspace_status_invalid")
    if status == "active":
        _current_entitlement(session, organization_id, product_code)
    before = {"status": workspace.status}
    workspace.status = status
    _audit(
        session,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action="workspace.status_changed",
        target_type="workspace",
        target_id=workspace.id,
        product_code=product_code,
        before=before,
        after={"status": workspace.status},
    )
    session.flush()
    return workspace


def rename_organization(
    session: Session,
    *,
    organization_id: uuid.UUID,
    name: str,
    actor_user_id: uuid.UUID,
) -> Organization:
    organization = session.get(Organization, organization_id)
    if organization is None:
        raise AdministrationError("organization_not_accessible")
    before = {"name": organization.name}
    organization.name = name.strip()
    _audit(
        session,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action="organization.renamed",
        target_type="organization",
        target_id=organization.id,
        product_code=None,
        before=before,
        after={"name": organization.name},
    )
    session.flush()
    return organization
