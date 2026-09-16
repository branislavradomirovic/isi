from datetime import date
import pytest
from pydantic import ValidationError
from src.domains.ordo.models import OrdoReferenceEvidence
from src.domains.ordo.schemas import ReferenceEvidenceCreateRequest


def test_reference_evidence_model_contract() -> None:
    cols = OrdoReferenceEvidence.__table__.columns
    for name in ["evidence_key", "source_identity", "source_version", "external_identity", "artifact_sha256", "content_sha256", "valid_from", "valid_to", "lifecycle_status", "provenance_lineage", "proposed_by_membership_id", "validated_by_membership_id", "retired_by_membership_id"]:
        assert name in cols
    constraints = " ".join(str(c.sqltext) for c in OrdoReferenceEvidence.__table__.constraints if hasattr(c, "sqltext"))
    assert "draft" in constraints and "proposed" in constraints and "validated" in constraints and "retired" in constraints


def test_reference_validity_rejects_reversed_window() -> None:
    with pytest.raises(ValidationError):
        ReferenceEvidenceCreateRequest(organization_id="00000000-0000-0000-0000-000000000001", workspace_id="00000000-0000-0000-0000-000000000002", evidence_key="x", valid_from=date(2026, 2, 2), valid_to=date(2026, 1, 1))
