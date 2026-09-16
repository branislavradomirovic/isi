import uuid
import pytest
from types import SimpleNamespace
from src.domains.ordo.service import OrdoDomainError, _require_lifecycle_transition, _stamp_lifecycle, _require_sha256


def test_reference_lifecycle_is_strict_and_human_governed() -> None:
    for current, target in [("draft", "proposed"), ("proposed", "validated"), ("validated", "retired")]:
        _require_lifecycle_transition(current, target)
    for current, target in [("draft", "validated"), ("proposed", "retired"), ("retired", "validated")]:
        with pytest.raises(OrdoDomainError):
            _require_lifecycle_transition(current, target)
    row = SimpleNamespace(lifecycle_status="draft", lifecycle_note="", proposed_by_membership_id=None, proposed_at=None, validated_by_membership_id=None, validated_at=None, retired_by_membership_id=None, retired_at=None)
    with pytest.raises(OrdoDomainError):
        _stamp_lifecycle(row, target="proposed", actor_id=None, note="")
    actor = uuid.uuid4()
    _stamp_lifecycle(row, target="proposed", actor_id=actor, note="review")
    assert row.proposed_by_membership_id == actor


def test_sha256_contract_is_exact_lower_hex() -> None:
    assert _require_sha256("A" * 64, "x") == "a" * 64
    with pytest.raises(OrdoDomainError):
        _require_sha256("not-a-sha", "x")
