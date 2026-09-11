from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.core.database import Base
from src.platform import models as platform_models  # noqa: F401
from src.platform.auth.service import (
    AuthError,
    create_mfa_factor,
    issue_mfa_challenge,
    provision_user,
    verify_mfa_challenge,
)
from src.platform.security.models import SecurityEvent
from src.platform.security.service import record_security_event


@pytest.fixture()
def db():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.mark.parametrize(
    "metadata",
    [
        {"outer": {"PaSsWoRdHint": "redacted"}},
        {"outer": [{"sessionTOKEN": "redacted"}]},
        {"outer": ["Bearer abc.def.ghi"]},
        {"outer": {"header": "Cookie: session=abc"}},
        {"outer": "isi_sess_obviousSensitiveValue123"},
        {"outer": {"header": "token=obvious-sensitive-value"}},
    ],
)
def test_recursive_metadata_rejects_sensitive_nested_keys_and_values(db, metadata):
    with pytest.raises(ValueError):
        record_security_event(db, event_type="test.security", outcome="rejected", metadata=metadata)
    assert db.scalar(select(SecurityEvent.id)) is None


def test_metadata_is_depth_cardinality_string_key_and_total_size_bounded(db):
    invalid = [
        {"a": {"b": {"c": {"d": {"e": {"f": True}}}}}},
        {"items": list(range(51))},
        {"k" * 81: "value"},
        {"value": "x" * 1001},
        {"items": ["x" * 200 for _ in range(50)]},
        {"object": uuid.uuid4()},
        {"number": float("nan")},
    ]
    for metadata in invalid:
        with pytest.raises(ValueError):
            record_security_event(db, event_type="test.security", outcome="rejected", metadata=metadata)
        db.rollback()
    assert db.scalar(select(SecurityEvent.id)) is None


def test_safe_nested_metadata_is_preserved_without_partial_persistence(db):
    metadata = {"operation": {"allowed": True, "attempt": 2, "reason": None, "scopes": ["SIMPA", "workspace"]}}
    event = record_security_event(db, event_type="test.security", outcome="success", metadata=metadata)
    db.commit()
    assert event.event_metadata == metadata


def test_mfa_challenge_outcomes_are_audited_without_verifiers(db):
    user = provision_user(
        db,
        email="mfa-events@example.invalid",
        display_name="MFA Events",
        password="Synthetic-mfa-event-password-2026",
        email_verified=True,
    )
    factor = create_mfa_factor(db, user, method="synthetic.test")
    expected = "synthetic-private-verifier"
    wrong = "synthetic-wrong-verifier"
    issued = issue_mfa_challenge(
        db,
        user_id=user.id,
        factor_id=factor.id,
        purpose="enrollment",
        verifier=expected,
    )
    assert not verify_mfa_challenge(
        db, user_id=user.id, challenge_id=issued.challenge_id, verifier=wrong
    ).succeeded
    assert verify_mfa_challenge(
        db, user_id=user.id, challenge_id=issued.challenge_id, verifier=expected
    ).succeeded
    with pytest.raises(AuthError):
        verify_mfa_challenge(db, user_id=user.id, challenge_id=issued.challenge_id, verifier=expected)
    db.commit()
    events = db.scalars(select(SecurityEvent).where(SecurityEvent.event_type == "auth.mfa.challenge")).all()
    assert {event.outcome for event in events} >= {"failure", "success", "replay"}
    serialized = repr([event.event_metadata for event in events])
    assert expected not in serialized and wrong not in serialized
