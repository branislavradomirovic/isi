from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import src.platform.models  # noqa: F401
from src.core.database import Base
from src.domains.ordo.analytics_models import OrdoIndicatorMethodology
from src.domains.ordo.analytics_service import (
    OrdoAnalyticsError,
    create_methodology,
    propose_methodology,
    retire_methodology,
    validate_methodology,
)
from src.domains.ordo.models import OrdoDimension, OrdoIndicatorDefinition, OrdoPillar
from src.platform.identity.models import Membership, Organization, User


@pytest.fixture
def methodology_case():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        marker = uuid.uuid4().hex
        user = User(email=f"{marker}@example.test", display_name="Reviewer")
        organization = Organization(slug=f"org-{marker}", name="Organization")
        db.add_all([user, organization]); db.flush()
        actor = Membership(user_id=user.id, organization_id=organization.id)
        dimension = OrdoDimension(code=f"D-{marker}", name_sr="Dimension")
        pillar = OrdoPillar(code=f"P-{marker}", name_sr="Pillar")
        db.add_all([actor, dimension, pillar]); db.flush()
        indicator = OrdoIndicatorDefinition(
            code=f"I-{marker}", name_sr="Indicator", dimension_code=dimension.code,
            pillar_code=pillar.code, unit_hint="count", methodology_status="conceptual",
        )
        db.add(indicator); db.flush()
        yield db, actor, indicator


def test_draft_cannot_skip_proposal_and_actor_is_required(methodology_case):
    db, actor, indicator = methodology_case
    row = create_methodology(
        db, indicator_code=indicator.code, computation_type="direct_observation",
        methodology_note="Human-authored method.", source_requirements={}, actor_id=actor.id,
    )
    with pytest.raises(OrdoAnalyticsError, match="methodology_not_proposed"):
        validate_methodology(db, methodology_id=row.id, validation_note="Reviewed evidence.", actor_id=actor.id)
    with pytest.raises(OrdoAnalyticsError, match="methodology_actor_required"):
        propose_methodology(db, methodology_id=row.id, actor_id=None)
    propose_methodology(db, methodology_id=row.id, actor_id=actor.id)
    assert row.status == "proposed" and row.proposed_by_membership_id == actor.id and row.proposed_at


def test_validate_supersedes_truthfully_and_explicit_retire_updates_summary(methodology_case):
    db, actor, indicator = methodology_case
    historical = OrdoIndicatorMethodology(
        indicator_id=indicator.id, version_no=1, status="validated",
        computation_type="direct_observation", computation_spec={}, source_requirements={},
        methodology_note="Historical", validation_note="Historical approval",
    )
    db.add(historical); db.flush()
    assert historical.proposed_at is None and historical.proposed_by_membership_id is None
    candidate = create_methodology(
        db, indicator_code=indicator.code, computation_type="direct_observation",
        methodology_note="Replacement.", source_requirements={}, actor_id=actor.id,
    )
    propose_methodology(db, methodology_id=candidate.id, actor_id=actor.id)
    validate_methodology(db, methodology_id=candidate.id, validation_note="Human validation.", actor_id=actor.id)
    assert historical.status == "retired" and historical.retired_by_membership_id == actor.id
    assert "Superseded" in historical.retirement_note
    assert candidate.status == "validated" and indicator.methodology_status == "validated"
    retire_methodology(db, methodology_id=candidate.id, retirement_note="Explicit withdrawal.", actor_id=actor.id)
    assert candidate.status == "retired" and indicator.methodology_status == "retired"
    with pytest.raises(OrdoAnalyticsError, match="methodology_not_validated"):
        retire_methodology(db, methodology_id=candidate.id, retirement_note="Again.", actor_id=actor.id)
