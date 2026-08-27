from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Product(Base):
    __tablename__ = "core_products"

    code: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class OrganizationEntitlement(Base):
    __tablename__ = "core_organization_entitlements"
    __table_args__ = (UniqueConstraint("organization_id", "product_code", name="uq_core_org_entitlement_product"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    starts_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MembershipProductAccess(Base):
    __tablename__ = "core_membership_product_access"
    __table_args__ = (UniqueConstraint("membership_id", "product_code", name="uq_core_member_product_access"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    membership_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Role(Base):
    __tablename__ = "core_roles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False, default="", server_default="")
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class Permission(Base):
    __tablename__ = "core_permissions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False, default="", server_default="")


class RolePermission(Base):
    __tablename__ = "core_role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_permissions.id", ondelete="CASCADE"), primary_key=True
    )


class RoleAssignment(Base):
    __tablename__ = "core_role_assignments"
    __table_args__ = (
        UniqueConstraint("membership_id", "role_id", "product_code", name="uq_core_role_assignment_scope"),
        CheckConstraint("product_code IN ('*', 'SIMPA', 'ORDO')", name="ck_core_role_assignment_product_scope"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    membership_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_roles.id", ondelete="CASCADE"), nullable=False)
    product_code: Mapped[str] = mapped_column(String(16), nullable=False, default="*", server_default="*")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
