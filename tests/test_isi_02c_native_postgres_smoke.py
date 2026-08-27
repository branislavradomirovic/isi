from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import build_engine
from src.platform.access.models import MembershipProductAccess, OrganizationEntitlement, Product
from src.platform.app_context.service import resolve_app_context
from src.platform.auth.service import provision_user
from src.platform.identity.models import Membership, Organization
from src.platform.workspaces.models import Workspace


@pytest.mark.skipif(os.getenv("ISI_RUN_NATIVE_DB_TESTS") != "1", reason="native PostgreSQL smoke is runner-gated")
def test_native_postgres_app_context_transaction_smoke():
    engine = build_engine()
    connection = engine.connect()
    transaction = connection.begin()
    try:
        with Session(bind=connection) as db:
            if db.get(Product, "SIMPA") is None:
                db.add(Product(code="SIMPA", name="SIMPA", is_active=True))
                db.flush()
            suffix = uuid.uuid4().hex
            user = provision_user(
                db,
                email=f"isi02c-{suffix}@example.invalid",
                display_name="ISI-02C DB Smoke",
                password="Native-Context-password-2026",
                email_verified=True,
            )
            org = Organization(slug=f"isi02c-{suffix}", name="ISI-02C DB Smoke", status="active")
            db.add(org)
            db.flush()
            membership = Membership(user_id=user.id, organization_id=org.id, status="active")
            db.add(membership)
            db.flush()
            db.add(OrganizationEntitlement(organization_id=org.id, product_code="SIMPA", is_active=True))
            db.add(MembershipProductAccess(membership_id=membership.id, product_code="SIMPA", is_active=True))
            workspace = Workspace(
                organization_id=org.id,
                product_code="SIMPA",
                slug="main",
                name="Main",
                status="active",
                created_by_membership_id=membership.id,
            )
            db.add(workspace)
            db.flush()

            context = resolve_app_context(db, user.id)
            assert context.initial_route.mode == "workspace"
            assert context.initial_route.product_code == "SIMPA"
            assert context.initial_route.workspace_id == workspace.id
            assert db.scalar(select(Organization).where(Organization.id == org.id)) is not None
    finally:
        transaction.rollback()
        connection.close()
