"""Append-only extraction provenance and human decisions; no domain numerical truth."""

from __future__ import annotations
import uuid
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, JSON, String, UniqueConstraint, event, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import inspect
from src.core.database import Base


class ExtractionRequest(Base):
    __tablename__ = "core_extraction_requests"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "workspace_id", "product_code", "request_key", name="uq_extraction_request_key"
        ),
        CheckConstraint("product_code IN ('SIMPA','ORDO')", name="ck_extraction_request_product"),
        CheckConstraint("state IN ('PENDING','CANCELLED')", name="ck_extraction_request_state"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), index=True)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"))
    request_key: Mapped[uuid.UUID] = mapped_column()
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_ai_jobs.id", ondelete="RESTRICT"), unique=True)
    binding: Mapped[dict] = mapped_column(JSON)
    fingerprint: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(16), default="PENDING")
    created_by_membership_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_memberships.id", ondelete="RESTRICT"))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExtractionArtifact(Base):
    __tablename__ = "core_extraction_artifacts"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_extraction_requests.id", ondelete="RESTRICT"), unique=True
    )
    payload: Mapped[dict] = mapped_column(JSON)
    fingerprint: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExtractionReview(Base):
    __tablename__ = "core_extraction_reviews"
    __table_args__ = (
        CheckConstraint("decision IN ('REVIEWED_ACCEPTED','REJECTED')", name="ck_extraction_review_decision"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    artifact_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_extraction_artifacts.id", ondelete="RESTRICT"), unique=True
    )
    decision: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict] = mapped_column(JSON)
    fingerprint: Mapped[str] = mapped_column(String(64))
    reviewer_membership_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_memberships.id", ondelete="RESTRICT"))
    reviewed_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


@event.listens_for(ExtractionArtifact, "before_update")
@event.listens_for(ExtractionReview, "before_update")
def immutable(_mapper, _connection, _target):
    raise ValueError("extraction_evidence_immutable")


@event.listens_for(ExtractionRequest, "before_update")
def request_immutable(_mapper, _connection, target):
    state = inspect(target)
    if any(
        state.attrs[k].history.has_changes()
        for k in [
            "organization_id",
            "workspace_id",
            "product_code",
            "request_key",
            "job_id",
            "binding",
            "fingerprint",
            "created_by_membership_id",
            "created_at",
        ]
    ):
        raise ValueError("extraction_request_binding_immutable")
    if state.attrs.state.history.has_changes() and (
        state.attrs.state.history.deleted != ["PENDING"] or target.state != "CANCELLED"
    ):
        raise ValueError("extraction_request_transition_invalid")
