from datetime import date
from uuid import uuid4
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from src.core.database import Base
from src.platform import models as registered_models  # noqa: F401
from src.platform.access.models import OrganizationEntitlement, Role, RoleAssignment
from src.platform.access.service import bootstrap_reference_catalog, grant_product_access
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace
from src.domains.simpa.models import SimpaLocalSystemProfile, SimpaLocalActor
from src.domains.ordo.models import OrdoSpatialUnit, OrdoAsset
from src.platform.data.models import DataAuditEvent
from src.platform.data.storage import LocalFilesystemStorage
from src.platform.spatial.contracts import GeometryError, GeometryReview
from src.platform.spatial.service import (
    create_geometry,
    review_geometry,
    get_geometry,
    metadata,
    GeometryAccessError,
    GeometryConflict,
)
from test_isi_29b_geometry_contract import request


def setup_db(db):
    bootstrap_reference_catalog(db)
    user = User(email="synthetic-spatial@example.com", display_name="Synthetic spatial", is_active=True)
    org = Organization(slug="synthetic-spatial", name="Synthetic spatial", status="active")
    db.add_all([user, org])
    db.flush()
    member = Membership(user_id=user.id, organization_id=org.id, status="active")
    db.add(member)
    db.flush()
    for product in ["SIMPA", "ORDO"]:
        db.add(OrganizationEntitlement(organization_id=org.id, product_code=product, is_active=True))
        db.flush()
        grant_product_access(db, member, product)
    role = db.scalar(select(Role).where(Role.code == "organization_admin"))
    db.add(RoleAssignment(membership_id=member.id, role_id=role.id, product_code="*"))
    simpa = Workspace(organization_id=org.id, product_code="SIMPA", slug="simpa", name="S", status="active")
    ordo = Workspace(organization_id=org.id, product_code="ORDO", slug="ordo", name="O", status="active")
    db.add_all([simpa, ordo])
    db.flush()
    local = SimpaLocalSystemProfile(
        organization_id=org.id, workspace_id=simpa.id, jurisdiction_name="Synthetic", jurisdiction_code="SYNTHETIC"
    )
    unit = OrdoSpatialUnit(
        organization_id=org.id,
        workspace_id=ordo.id,
        spatial_unit_key="SYNTHETIC",
        spatial_unit_type="custom",
        name="Synthetic",
        boundary_source="https://example.org/synthetic",
        boundary_version="v1",
        lifecycle_status="validated",
    )
    actor = SimpaLocalActor(
        organization_id=org.id,
        workspace_id=simpa.id,
        actor_type="social_service_provider",
        name="Synthetic facility",
        external_code="FACILITY",
    )
    asset = OrdoAsset(
        organization_id=org.id, workspace_id=ordo.id, asset_type="other", name="Synthetic asset", external_code="ASSET"
    )
    db.add_all([local, unit, actor, asset])
    db.commit()
    return dict(
        user=user, org=org, member=member, simpa=simpa, ordo=ordo, local=local, unit=unit, actor=actor, asset=asset
    )


@pytest.fixture
def context(tmp_path):
    engine = create_engine("sqlite+pysqlite://")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine, expire_on_commit=False)() as db:
        ctx = setup_db(db)
        ctx["db"] = db
        ctx["storage"] = LocalFilesystemStorage(tmp_path)
        yield ctx
    engine.dispose()


def args(c, product="SIMPA"):
    return dict(
        user_id=c["user"].id, organization_id=c["org"].id, workspace_id=c[product.lower()].id, product_code=product
    )


def create(c, product="SIMPA", kind=None):
    kind = kind or ("local_system" if product == "SIMPA" else "spatial_unit")
    domain = c[{"local_system": "local", "spatial_unit": "unit", "local_actor": "actor", "asset": "asset"}[kind]]
    changes = {"geometry": {"type": "Point", "coordinates": [20, 44]}} if kind in {"local_actor", "asset"} else {}
    payload = request(
        organization_id=c["org"].id,
        workspace_id=c[product.lower()].id,
        domain_id=domain.id,
        domain_kind=kind,
        **changes,
    )
    row = create_geometry(c["db"], user_id=c["user"].id, product_code=product, payload=payload, storage=c["storage"])
    c["db"].commit()
    return row


def validate(c, row, product="SIMPA"):
    for state in ["PROPOSED", "VALIDATED"]:
        review_geometry(
            c["db"],
            **args(c, product),
            geometry_id=row.id,
            payload=GeometryReview(revision=row.revision, state=state, source_license_location_attested=True),
            storage=c["storage"],
        )
        c["db"].commit()


@pytest.mark.parametrize(
    "product,kind", [("SIMPA", "local_system"), ("SIMPA", "local_actor"), ("ORDO", "spatial_unit"), ("ORDO", "asset")]
)
def test_both_products_boundary_and_facility_lifecycle(context, product, kind):
    c = context
    row = create(c, product, kind)
    with pytest.raises(GeometryError, match="not_validated"):
        get_geometry(c["db"], **args(c, product), geometry_id=row.id, at_date=date(2026, 1, 1), storage=c["storage"])
    validate(c, row, product)
    result = get_geometry(
        c["db"], **args(c, product), geometry_id=row.id, at_date=date(2026, 1, 1), storage=c["storage"]
    )
    assert result["metadata"]["source_verification"] == "HUMAN_ATTESTED"
    assert "storage_key" not in metadata(row)
    assert len(c["db"].scalars(select(DataAuditEvent).where(DataAuditEvent.entity_id == row.id)).all()) == 3
    with pytest.raises(GeometryError, match="date"):
        get_geometry(c["db"], **args(c, product), geometry_id=row.id, at_date=date(2025, 1, 1), storage=c["storage"])


def test_stale_revision_attestation_and_retirement(context):
    c = context
    row = create(c)
    with pytest.raises(GeometryConflict):
        review_geometry(
            c["db"],
            **args(c),
            geometry_id=row.id,
            payload=GeometryReview(revision=99, state="PROPOSED"),
            storage=c["storage"],
        )
    review_geometry(
        c["db"],
        **args(c),
        geometry_id=row.id,
        payload=GeometryReview(revision=row.revision, state="PROPOSED"),
        storage=c["storage"],
    )
    with pytest.raises(GeometryError, match="attestation"):
        review_geometry(
            c["db"],
            **args(c),
            geometry_id=row.id,
            payload=GeometryReview(revision=row.revision, state="VALIDATED"),
            storage=c["storage"],
        )
    validate_payload = GeometryReview(revision=row.revision, state="VALIDATED", source_license_location_attested=True)
    review_geometry(c["db"], **args(c), geometry_id=row.id, payload=validate_payload, storage=c["storage"])
    review_geometry(
        c["db"],
        **args(c),
        geometry_id=row.id,
        payload=GeometryReview(revision=row.revision, state="RETIRED"),
        storage=c["storage"],
    )
    with pytest.raises(GeometryError, match="transition"):
        review_geometry(
            c["db"],
            **args(c),
            geometry_id=row.id,
            payload=GeometryReview(revision=row.revision, state="VALIDATED", source_license_location_attested=True),
            storage=c["storage"],
        )


def test_cross_scope_denied_before_storage(context):
    c = context
    row = create(c)
    validate(c, row)

    class NoRead:
        def get_bytes(self, key):
            raise AssertionError("unauthorized storage read")

    for changes in [
        {"workspace_id": c["ordo"].id},
        {"organization_id": uuid4()},
        {"product_code": "ORDO"},
        {"geometry_id": uuid4()},
    ]:
        with pytest.raises(GeometryAccessError):
            get_geometry(
                c["db"], **(args(c) | {"geometry_id": row.id} | changes), at_date=date(2026, 1, 1), storage=NoRead()
            )


@pytest.mark.parametrize("damage", ["geometry", "metadata", "binding"])
def test_integrity_and_domain_invalidation(context, damage):
    c = context
    row = create(c)
    validate(c, row)
    if damage == "geometry":
        c["storage"]._path(row.storage_key).write_bytes(b"{}")
    elif damage == "metadata":
        row.source_version = "tampered"
    else:
        c["local"].jurisdiction_code = "changed"
        c["db"].flush()
    with pytest.raises(GeometryError):
        get_geometry(c["db"], **args(c), geometry_id=row.id, at_date=date(2026, 1, 1), storage=c["storage"])


def test_ordo_domain_retirement_blocks_geometry_but_allows_retirement(context):
    c = context
    row = create(c, "ORDO")
    validate(c, row, "ORDO")
    c["unit"].lifecycle_status = "retired"
    c["db"].flush()
    with pytest.raises(GeometryError, match="domain_not_validated"):
        get_geometry(c["db"], **args(c, "ORDO"), geometry_id=row.id, at_date=date(2026, 1, 1), storage=c["storage"])
    review_geometry(
        c["db"],
        **args(c, "ORDO"),
        geometry_id=row.id,
        payload=GeometryReview(revision=row.revision, state="RETIRED"),
        storage=c["storage"],
    )
    assert row.state == "RETIRED"


def test_geometry_period_must_fit_ordo_boundary_and_provenance(context):
    c = context
    c["unit"].valid_to = date(2026, 12, 31)
    c["db"].flush()
    with pytest.raises(GeometryError, match="validity"):
        create(c, "ORDO")
    p = request(
        organization_id=c["org"].id,
        workspace_id=c["ordo"].id,
        domain_id=c["unit"].id,
        domain_kind="spatial_unit",
        valid_to=date(2026, 12, 31),
        source_version="wrong",
    )
    with pytest.raises(GeometryError, match="provenance"):
        create_geometry(c["db"], user_id=c["user"].id, product_code="ORDO", payload=p, storage=c["storage"])


@pytest.mark.parametrize("revoke", ["membership", "entitlement"])
def test_revoked_authority_denied_before_geometry_storage(context, revoke):
    c = context
    row = create(c)
    validate(c, row)
    if revoke == "membership":
        c["member"].status = "suspended"
    else:
        entitlement = c["db"].scalar(
            select(OrganizationEntitlement).where(
                OrganizationEntitlement.organization_id == c["org"].id, OrganizationEntitlement.product_code == "SIMPA"
            )
        )
        entitlement.is_active = False
    c["db"].flush()

    class NoRead:
        def get_bytes(self, key):
            raise AssertionError("storage must not be read after authority revocation")

    with pytest.raises(GeometryAccessError):
        get_geometry(c["db"], **args(c), geometry_id=row.id, at_date=date(2026, 1, 1), storage=NoRead())
