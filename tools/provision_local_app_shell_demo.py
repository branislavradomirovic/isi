from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone

from sqlalchemy import select

from src.core.config import get_settings
from src.core.database import build_engine, build_session_factory
from src.platform.access.models import (
    MembershipProductAccess,
    OrganizationEntitlement,
    Role,
    RoleAssignment,
)
from src.platform.access.service import bootstrap_reference_catalog, grant_product_access
from src.platform.auth.service import provision_user, set_password
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace


DEMO_ORG_SLUG = "isi-app-shell-demo"
PROFILE_PRODUCTS = {
    "simpa": ("SIMPA",),
    "ordo": ("ORDO",),
    "dual": ("SIMPA", "ORDO"),
}
PROFILE_EMAILS = {
    "simpa": "isi05-simpa@example.com",
    "ordo": "isi05-ordo@example.com",
    "dual": "isi05-dual@example.com",
}
LEGACY_PROFILE_EMAILS = {
    "simpa": "isi05-simpa@isi.local",
    "ordo": "isi05-ordo@isi.local",
    "dual": "isi05-dual@isi.local",
}


def _guard_environment() -> None:
    env = get_settings().isi_env.casefold()
    if env in {"production", "prod", "staging"}:
        raise SystemExit("Refusing to seed app-shell demo data outside local/development/test environment")


def cleanup(session) -> None:
    org = session.scalar(select(Organization).where(Organization.slug == DEMO_ORG_SLUG))
    if org is None:
        print("No ISI-05 demo organization to remove")
        return
    users = session.scalars(
        select(User)
        .join(Membership, Membership.user_id == User.id)
        .where(Membership.organization_id == org.id)
    ).all()
    session.delete(org)
    session.flush()
    for user in users:
        membership_count = session.scalar(select(Membership.id).where(Membership.user_id == user.id).limit(1))
        if membership_count is None:
            session.delete(user)
    session.commit()
    print("ISI-05 demo data removed")


def _ensure_demo_org_products(session, org: Organization) -> None:
    """The demo organization owns both flagship entitlements and workspaces.

    Per-user product visibility is controlled by membership access and roles, not by
    repeatedly toggling organization entitlements while provisioning test profiles.
    """
    for product_code in ("SIMPA", "ORDO"):
        entitlement = session.scalar(
            select(OrganizationEntitlement).where(
                OrganizationEntitlement.organization_id == org.id,
                OrganizationEntitlement.product_code == product_code,
            )
        )
        if entitlement is None:
            session.add(
                OrganizationEntitlement(
                    organization_id=org.id,
                    product_code=product_code,
                    is_active=True,
                )
            )
        else:
            entitlement.is_active = True

        workspace = session.scalar(
            select(Workspace).where(
                Workspace.organization_id == org.id,
                Workspace.product_code == product_code,
                Workspace.slug == f"demo-{product_code.lower()}",
            )
        )
        if workspace is None:
            session.add(
                Workspace(
                    organization_id=org.id,
                    product_code=product_code,
                    slug=f"demo-{product_code.lower()}",
                    name=f"{product_code} Demo Workspace",
                    status="active",
                )
            )
        else:
            workspace.status = "active"


def provision(session, profile: str, password: str) -> str:
    products = PROFILE_PRODUCTS[profile]
    bootstrap_reference_catalog(session)

    org = session.scalar(select(Organization).where(Organization.slug == DEMO_ORG_SLUG))
    if org is None:
        org = Organization(slug=DEMO_ORG_SLUG, name="ISI App Shell Demo", status="active")
        session.add(org)
        session.flush()
    else:
        org.status = "active"

    _ensure_demo_org_products(session, org)
    session.flush()

    email = PROFILE_EMAILS[profile]
    user = session.scalar(select(User).where(User.email == email))
    if user is None:
        user = provision_user(
            session,
            email=email,
            display_name=f"ISI 05 {profile.upper()} Demo",
            password=password,
            email_verified=True,
        )
    else:
        user.is_active = True
        user.email_verified_at = user.email_verified_at or datetime.now(timezone.utc)
        set_password(user, password)

    # Deactivate legacy .local demo users so the launcher never advertises identities
    # that FastAPI's EmailStr contract cannot accept.
    legacy_user = session.scalar(select(User).where(User.email == LEGACY_PROFILE_EMAILS[profile]))
    if legacy_user is not None:
        legacy_user.is_active = False

    membership = session.scalar(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.organization_id == org.id,
        )
    )
    if membership is None:
        membership = Membership(user_id=user.id, organization_id=org.id, status="active")
        session.add(membership)
        session.flush()
    else:
        membership.status = "active"

    role = session.scalar(select(Role).where(Role.code == "organization_admin"))
    if role is None:
        raise SystemExit("organization_admin role missing after bootstrap")

    for product_code in ("SIMPA", "ORDO"):
        access = session.scalar(
            select(MembershipProductAccess).where(
                MembershipProductAccess.membership_id == membership.id,
                MembershipProductAccess.product_code == product_code,
            )
        )
        if product_code in products:
            session.flush()
            grant_product_access(session, membership, product_code)
        elif access is not None:
            access.is_active = False

        assignment = session.scalar(
            select(RoleAssignment).where(
                RoleAssignment.membership_id == membership.id,
                RoleAssignment.role_id == role.id,
                RoleAssignment.product_code == product_code,
            )
        )
        if product_code in products and assignment is None:
            session.add(
                RoleAssignment(
                    membership_id=membership.id,
                    role_id=role.id,
                    product_code=product_code,
                )
            )
        elif product_code not in products and assignment is not None:
            session.delete(assignment)

    session.commit()
    return email


def provision_all(session, password: str) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    for profile in ("simpa", "ordo", "dual"):
        email = provision(session, profile, password)
        results.append((profile, email))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision explicit local QA identities for ISI-05")
    parser.add_argument("--profile", choices=sorted(PROFILE_PRODUCTS), default="dual")
    parser.add_argument("--all", action="store_true", help="Provision SIMPA-only, ORDO-only and dual profiles")
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--password", default=os.getenv("ISI_DEMO_PASSWORD"))
    args = parser.parse_args()

    _guard_environment()
    engine = build_engine()
    SessionLocal = build_session_factory(engine)
    with SessionLocal() as session:
        if args.cleanup:
            cleanup(session)
            return
        if not args.password:
            raise SystemExit("Provide --password or ISI_DEMO_PASSWORD; no password is hard-coded")
        if len(args.password) < 12:
            raise SystemExit("Demo password must satisfy the minimum 12-character policy")
        if args.all:
            results = provision_all(session, args.password)
        else:
            results = [(args.profile, provision(session, args.profile, args.password))]

    print("ISI-05 local demo profile(s) ready")
    for profile, email in results:
        print(f"profile={profile} email={email}")
    print("password=<the explicit value you supplied>")
    print("organization=ISI App Shell Demo")
    print("This tool is development-only and is never executed by the normal application runtime.")


if __name__ == "__main__":
    main()
