from __future__ import annotations
import uuid
from datetime import date
from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base


class SpatialGeometryVersion(Base):
    __tablename__ = "core_spatial_geometry_versions"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "workspace_id",
            "product_code",
            "domain_kind",
            "domain_id",
            "version",
            name="uq_spatial_geometry_version",
        ),
        CheckConstraint("product_code IN ('SIMPA','ORDO')", name="ck_spatial_geometry_product"),
        CheckConstraint("state IN ('DRAFT','PROPOSED','VALIDATED','RETIRED')", name="ck_spatial_geometry_state"),
        CheckConstraint("valid_to IS NULL OR valid_to >= valid_from", name="ck_spatial_geometry_validity"),
        CheckConstraint("revision >= 1", name="ck_spatial_geometry_revision"),
        CheckConstraint("geometry_type IN ('Point','Polygon','MultiPolygon')", name="ck_spatial_geometry_type"),
        CheckConstraint(
            "(product_code = 'SIMPA' AND domain_kind IN ('local_system','local_actor')) OR (product_code = 'ORDO' AND domain_kind IN ('spatial_unit','asset'))",
            name="ck_spatial_geometry_domain",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), index=True)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"))
    domain_kind: Mapped[str] = mapped_column(String(40))
    domain_id: Mapped[uuid.UUID] = mapped_column()
    version: Mapped[str] = mapped_column(String(120))
    source_uri: Mapped[str] = mapped_column(String(500))
    source_version: Mapped[str] = mapped_column(String(120))
    declared_source_sha256: Mapped[str] = mapped_column(String(64))
    license_identifier: Mapped[str] = mapped_column(String(120))
    original_crs: Mapped[str] = mapped_column(String(40))
    axis_order: Mapped[str] = mapped_column(String(40))
    render_crs: Mapped[str] = mapped_column(String(40), default="OGC:CRS84")
    transformation: Mapped[str] = mapped_column(String(80), default="IDENTITY_WGS84_LON_LAT")
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    geometry_type: Mapped[str] = mapped_column(String(32))
    geometry_sha256: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(500))
    domain_binding: Mapped[dict] = mapped_column(JSON)
    fingerprint: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(24), default="DRAFT")
    revision: Mapped[int] = mapped_column(Integer, default=1)
    created_by_membership_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_memberships.id", ondelete="RESTRICT"))
    reviewed_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="RESTRICT"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __mapper_args__ = {"version_id_col": revision}
