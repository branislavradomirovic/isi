from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class InvitationProductGrant(Base):
    __tablename__ = "core_invitation_product_grants"
    __table_args__ = (
        UniqueConstraint("invitation_id", "product_code", name="uq_core_invitation_product_grant"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    invitation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_invitations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False, index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class InvitationRoleGrant(Base):
    __tablename__ = "core_invitation_role_grants"
    __table_args__ = (
        UniqueConstraint("invitation_id", "role_id", "product_code", name="uq_core_invitation_role_grant"),
        CheckConstraint("product_code IN ('*', 'SIMPA', 'ORDO')", name="ck_core_invitation_role_grant_scope"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    invitation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_invitations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_roles.id", ondelete="CASCADE"), nullable=False)
    product_code: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AdminAuditEvent(Base):
    __tablename__ = "core_admin_audit_events"
    __table_args__ = (
        CheckConstraint(
            "product_code IS NULL OR product_code IN ('SIMPA', 'ORDO')",
            name="ck_core_admin_audit_product_scope",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    actor_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(80), nullable=False)
    target_id: Mapped[str] = mapped_column(String(160), nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    before_state: Mapped[dict] = mapped_column(JSON, nullable=False)
    after_state: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
