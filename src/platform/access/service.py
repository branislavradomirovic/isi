from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.platform.access.catalog import PermissionCode, ProductCode, ROLE_PERMISSION_MAP, RoleCode
from src.platform.access.models import (
    MembershipProductAccess,
    OrganizationEntitlement,
    Permission,
    Product,
    Role,
    RoleAssignment,
    RolePermission,
)
from src.platform.identity.models import Membership, User


class AccessInvariantError(ValueError):
    pass


def _product_value(product_code: str | ProductCode) -> str:
    return product_code.value if isinstance(product_code, ProductCode) else str(product_code)


def bootstrap_reference_catalog(session: Session) -> None:
    for code, name in ((ProductCode.SIMPA, "SIMPA"), (ProductCode.ORDO, "ORDO")):
        existing = session.get(Product, code.value)
        if existing is None:
            session.add(Product(code=code.value, name=name, is_active=True))

    permissions: dict[str, Permission] = {}
    for permission_code in PermissionCode:
        permission = session.scalar(select(Permission).where(Permission.code == permission_code.value))
        if permission is None:
            permission = Permission(code=permission_code.value, description=permission_code.value)
            session.add(permission)
            session.flush()
        permissions[permission_code.value] = permission

    roles: dict[str, Role] = {}
    for role_code in RoleCode:
        role = session.scalar(select(Role).where(Role.code == role_code.value))
        if role is None:
            role = Role(code=role_code.value, name=role_code.value.replace("_", " ").title())
            session.add(role)
            session.flush()
        roles[role_code.value] = role

    session.flush()
    for role_code, permission_codes in ROLE_PERMISSION_MAP.items():
        role = roles[role_code.value]
        for permission_code in permission_codes:
            permission = permissions[permission_code.value]
            existing = session.get(RolePermission, (role.id, permission.id))
            if existing is None:
                session.add(RolePermission(role_id=role.id, permission_id=permission.id))

    session.commit()


def grant_product_access(session: Session, membership: Membership, product_code: str | ProductCode) -> MembershipProductAccess:
    code = _product_value(product_code)
    entitlement = session.scalar(
        select(OrganizationEntitlement).where(
            OrganizationEntitlement.organization_id == membership.organization_id,
            OrganizationEntitlement.product_code == code,
            OrganizationEntitlement.is_active.is_(True),
        )
    )
    if entitlement is None:
        raise AccessInvariantError("membership product access requires an active organization entitlement")

    existing = session.scalar(
        select(MembershipProductAccess).where(
            MembershipProductAccess.membership_id == membership.id,
            MembershipProductAccess.product_code == code,
        )
    )
    if existing is not None:
        existing.is_active = True
        session.flush()
        return existing

    access = MembershipProductAccess(membership_id=membership.id, product_code=code, is_active=True)
    session.add(access)
    session.flush()
    return access


def can_access_product(
    session: Session,
    user_id: uuid.UUID,
    organization_id: uuid.UUID,
    product_code: str | ProductCode,
) -> bool:
    code = _product_value(product_code)
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

    entitlement = session.scalar(
        select(OrganizationEntitlement).where(
            OrganizationEntitlement.organization_id == organization_id,
            OrganizationEntitlement.product_code == code,
            OrganizationEntitlement.is_active.is_(True),
        )
    )
    if entitlement is None:
        return False

    now = datetime.now(timezone.utc)
    if entitlement.starts_at is not None and entitlement.starts_at > now:
        return False
    if entitlement.ends_at is not None and entitlement.ends_at <= now:
        return False

    member_access = session.scalar(
        select(MembershipProductAccess).where(
            MembershipProductAccess.membership_id == membership.id,
            MembershipProductAccess.product_code == code,
            MembershipProductAccess.is_active.is_(True),
        )
    )
    return member_access is not None


def has_permission(
    session: Session,
    user_id: uuid.UUID,
    organization_id: uuid.UUID,
    permission_code: str | PermissionCode,
    product_code: str | ProductCode | None = None,
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

    requested_product = _product_value(product_code) if product_code is not None else None
    if requested_product is not None and not can_access_product(session, user_id, organization_id, requested_product):
        return False

    code = permission_code.value if isinstance(permission_code, PermissionCode) else str(permission_code)
    permission = session.scalar(select(Permission).where(Permission.code == code))
    if permission is None:
        return False

    scope_values = ["*"] if requested_product is None else ["*", requested_product]
    query = (
        select(RolePermission.role_id)
        .join(RoleAssignment, RoleAssignment.role_id == RolePermission.role_id)
        .where(
            RolePermission.permission_id == permission.id,
            RoleAssignment.membership_id == membership.id,
            RoleAssignment.product_code.in_(scope_values),
        )
        .limit(1)
    )
    return session.scalar(query) is not None
