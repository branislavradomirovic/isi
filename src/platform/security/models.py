from __future__ import annotations

import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class SecurityRateLimit(Base):
    __tablename__ = "core_security_rate_limits"

    key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    window_started_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    blocked_until: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_attempt_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)


class SecurityEvent(Base):
    __tablename__ = "core_security_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    subject_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    remote_ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
