from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.platform.access.catalog import PermissionCode
from src.platform.access.models import (
    MembershipProductAccess,
    OrganizationEntitlement,
    Permission,
    Product,
    Role,
    RoleAssignment,
    RolePermission,
)
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace
from src.platform.app_context.schemas import (
    AppContextResponse,
    InitialRoute,
    OrganizationOption,
    ProductOption,
    SelectionResponse,
    WorkspaceOption,
)


class AppContextError(ValueError):
    pass


def _entitlement_is_current(entitlement: OrganizationEntitlement, now: datetime) -> bool:
    if not entitlement.is_active:
        return False
    if entitlement.starts_at is not None and entitlement.starts_at > now:
        return False
    if entitlement.ends_at is not None and entitlement.ends_at <= now:
        return False
    return True


def _role_codes(session: Session, membership_id: uuid.UUID, product_code: str) -> list[str]:
    values = session.scalars(
        select(Role.code)
        .join(RoleAssignment, RoleAssignment.role_id == Role.id)
        .where(
            RoleAssignment.membership_id == membership_id,
            RoleAssignment.product_code.in_(["*", product_code]),
        )
        .distinct()
        .order_by(Role.code)
    ).all()
    return list(values)


def _permission_codes(session: Session, membership_id: uuid.UUID, product_code: str) -> list[str]:
    values = session.scalars(
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(RoleAssignment, RoleAssignment.role_id == RolePermission.role_id)
        .where(
            RoleAssignment.membership_id == membership_id,
            RoleAssignment.product_code.in_(["*", product_code]),
        )
        .distinct()
        .order_by(Permission.code)
    ).all()
    return list(values)


def _workspace_options(session: Session, organization_id: uuid.UUID, product_code: str) -> list[WorkspaceOption]:
    rows = session.scalars(
        select(Workspace)
        .where(
            Workspace.organization_id == organization_id,
            Workspace.product_code == product_code,
            Workspace.status == "active",
        )
        .order_by(Workspace.name, Workspace.id)
    ).all()
    return [WorkspaceOption(id=row.id, slug=row.slug, name=row.name) for row in rows]


def _member_product_options(
    session: Session,
    *,
    membership: Membership,
    now: datetime,
) -> list[ProductOption]:
    accesses = session.scalars(
        select(MembershipProductAccess).where(
            MembershipProductAccess.membership_id == membership.id,
            MembershipProductAccess.is_active.is_(True),
        )
    ).all()
    options: list[ProductOption] = []
    for access in accesses:
        product = session.get(Product, access.product_code)
        if product is None or not product.is_active or product.code not in {"SIMPA", "ORDO"}:
            continue
        entitlement = session.scalar(
            select(OrganizationEntitlement).where(
                OrganizationEntitlement.organization_id == membership.organization_id,
                OrganizationEntitlement.product_code == product.code,
            )
        )
        if entitlement is None or not _entitlement_is_current(entitlement, now):
            continue
        options.append(
            ProductOption(
                code=product.code,
                name=product.name,
                role_codes=_role_codes(session, membership.id, product.code),
                permission_codes=_permission_codes(session, membership.id, product.code),
                workspaces=_workspace_options(session, membership.organization_id, product.code),
            )
        )
    return sorted(options, key=lambda item: item.code)


def _platform_admin_product_options(session: Session, organization_id: uuid.UUID) -> list[ProductOption]:
    products = session.scalars(
        select(Product).where(Product.is_active.is_(True), Product.code.in_(["SIMPA", "ORDO"])).order_by(Product.code)
    ).all()
    all_permissions = sorted(code.value for code in PermissionCode)
    return [
        ProductOption(
            code=product.code,
            name=product.name,
            role_codes=["platform_admin"],
            permission_codes=all_permissions,
            workspaces=_workspace_options(session, organization_id, product.code),
        )
        for product in products
    ]


def _initial_route(organizations: list[OrganizationOption]) -> InitialRoute:
    if not organizations:
        return InitialRoute(mode="no_access")
    if len(organizations) != 1:
        return InitialRoute(mode="selector")

    organization = organizations[0]
    if len(organization.products) != 1:
        return InitialRoute(mode="selector")

    product = organization.products[0]
    if len(product.workspaces) == 1:
        return InitialRoute(
            mode="workspace",
            organization_id=organization.id,
            product_code=product.code,
            workspace_id=product.workspaces[0].id,
        )
    return InitialRoute(
        mode="product",
        organization_id=organization.id,
        product_code=product.code,
    )


def resolve_app_context(session: Session, user_id: uuid.UUID) -> AppContextResponse:
    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise AppContextError("inactive_or_missing_user")

    organizations: list[OrganizationOption] = []
    if user.is_platform_admin:
        org_rows = session.scalars(
            select(Organization).where(Organization.status == "active").order_by(Organization.name, Organization.id)
        ).all()
        organizations = [
            OrganizationOption(
                id=org.id,
                slug=org.slug,
                name=org.name,
                membership_id=None,
                products=_platform_admin_product_options(session, org.id),
            )
            for org in org_rows
        ]
    else:
        now = datetime.now(timezone.utc)
        memberships = session.scalars(
            select(Membership)
            .join(Organization, Organization.id == Membership.organization_id)
            .where(
                Membership.user_id == user.id,
                Membership.status == "active",
                Organization.status == "active",
            )
            .order_by(Organization.name, Membership.id)
        ).all()
        for membership in memberships:
            org = session.get(Organization, membership.organization_id)
            if org is None:
                continue
            products = _member_product_options(session, membership=membership, now=now)
            if not products:
                continue
            organizations.append(
                OrganizationOption(
                    id=org.id,
                    slug=org.slug,
                    name=org.name,
                    membership_id=membership.id,
                    products=products,
                )
            )

    return AppContextResponse(
        user_id=user.id,
        display_name=user.display_name,
        email=user.email,
        is_platform_admin=user.is_platform_admin,
        organizations=organizations,
        initial_route=_initial_route(organizations),
    )


def resolve_selection(
    session: Session,
    *,
    user_id: uuid.UUID,
    organization_id: uuid.UUID,
    product_code: str,
    workspace_id: uuid.UUID | None = None,
) -> SelectionResponse:
    context = resolve_app_context(session, user_id)
    organization = next((item for item in context.organizations if item.id == organization_id), None)
    if organization is None:
        raise AppContextError("organization_not_accessible")
    product = next((item for item in organization.products if item.code == product_code), None)
    if product is None:
        raise AppContextError("product_not_accessible")

    workspace = None
    if workspace_id is not None:
        workspace = next((item for item in product.workspaces if item.id == workspace_id), None)
        if workspace is None:
            raise AppContextError("workspace_not_accessible")

    return SelectionResponse(organization=organization, product=product, workspace=workspace)
