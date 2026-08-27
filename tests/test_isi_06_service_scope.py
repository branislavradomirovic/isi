import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.core.database import Base
from src.platform.access.models import Product
from src.platform.data.models import DataSource
from src.platform.data.service import DataPlatformError, get_scoped_source, list_sources, validate_scope
from src.platform.identity.models import Organization
from src.platform.workspaces.models import Workspace


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_source_lookup_never_crosses_workspace_or_product():
    session = _session()
    simpa = Product(code="SIMPA", name="SIMPA", is_active=True)
    ordo = Product(code="ORDO", name="ORDO", is_active=True)
    org = Organization(slug="org", name="Org", status="active")
    session.add_all([simpa, ordo, org])
    session.flush()
    ws_simpa = Workspace(organization_id=org.id, product_code="SIMPA", slug="simpa", name="SIMPA", status="active")
    ws_ordo = Workspace(organization_id=org.id, product_code="ORDO", slug="ordo", name="ORDO", status="active")
    session.add_all([ws_simpa, ws_ordo])
    session.flush()
    source = DataSource(
        organization_id=org.id,
        workspace_id=ws_simpa.id,
        product_code="SIMPA",
        name="SIMPA izvor",
        source_kind="dataset",
        status="active",
    )
    session.add(source)
    session.commit()

    assert len(list_sources(session, organization_id=org.id, workspace_id=ws_simpa.id, product_code="SIMPA")) == 1
    assert len(list_sources(session, organization_id=org.id, workspace_id=ws_ordo.id, product_code="ORDO")) == 0
    with pytest.raises(DataPlatformError, match="source_not_accessible"):
        get_scoped_source(
            session,
            source_id=source.id,
            organization_id=org.id,
            workspace_id=ws_ordo.id,
            product_code="ORDO",
        )
