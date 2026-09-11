from __future__ import annotations

import hashlib
import uuid
from datetime import timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.core.config import Settings
from src.core.database import Base
from src.platform import models as platform_models  # noqa: F401
from src.platform.auth.models import MfaChallenge, MfaFactor
from src.platform.auth.security import hash_mfa_challenge_verifier
from src.platform.auth.service import (
    AuthError,
    MfaChallengeVerificationResult,
    create_mfa_factor,
    issue_mfa_challenge,
    provision_user,
    revoke_mfa_challenge,
    revoke_mfa_factor,
    utcnow,
    verify_mfa_challenge,
)


@pytest.fixture()
def db():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _user(db: Session, label: str = "primary"):
    return provision_user(
        db,
        email=f"{label}-{uuid.uuid4().hex}@example.invalid",
        display_name=f"{label.title()} User",
        password="Synthetic-test-password-2026",
        email_verified=True,
    )


def _assert_code(expected: str, operation) -> None:
    with pytest.raises(AuthError) as raised:
        operation()
    assert raised.value.code == expected


def test_low_entropy_verifier_uses_keyed_domain_separated_digest():
    challenge_id = uuid.uuid4()
    verifier = "synthetic-low-entropy-value"
    first_settings = Settings(security_identifier_pepper="a" * 48)
    second_settings = Settings(security_identifier_pepper="b" * 48)

    first = hash_mfa_challenge_verifier(challenge_id, verifier, first_settings)
    assert len(first) == 64
    assert verifier not in first
    assert first != hashlib.sha256(verifier.encode("utf-8")).hexdigest()
    assert first != hash_mfa_challenge_verifier(challenge_id, verifier, second_settings)
    assert first != hash_mfa_challenge_verifier(uuid.uuid4(), verifier, first_settings)
    with pytest.raises(ValueError):
        hash_mfa_challenge_verifier(
            challenge_id,
            verifier,
            Settings(isi_env="production", security_identifier_pepper=""),
        )


def test_enrollment_challenge_activates_factor_and_rejects_replay(db):
    user = _user(db)
    factor = create_mfa_factor(db, user, method="synthetic.test", display_name="Test factor")
    verifier = "synthetic-enrollment-verifier"
    wrong_verifier = "synthetic-wrong-verifier"
    issued = issue_mfa_challenge(
        db,
        user_id=user.id,
        factor_id=factor.id,
        purpose="enrollment",
        verifier=verifier,
    )
    db.commit()

    stored = db.get(MfaChallenge, issued.challenge_id)
    assert stored is not None
    assert stored.verifier_digest != verifier
    assert verifier not in repr(stored)
    denied = verify_mfa_challenge(
        db,
        user_id=user.id,
        challenge_id=issued.challenge_id,
        verifier=wrong_verifier,
    )
    assert denied == MfaChallengeVerificationResult(
        challenge_id=issued.challenge_id,
        succeeded=False,
        error_code="invalid_mfa_verifier",
    )
    assert verifier not in repr(denied)
    assert wrong_verifier not in repr(denied)
    assert stored.verifier_digest not in repr(denied)
    assert not hasattr(denied, "verifier")
    assert not hasattr(denied, "verifier_digest")
    db.commit()
    with Session(db.get_bind()) as fresh_db:
        assert fresh_db.get(MfaChallenge, issued.challenge_id).attempt_count == 1

    succeeded = verify_mfa_challenge(
        db,
        user_id=user.id,
        challenge_id=issued.challenge_id,
        verifier=verifier,
    )
    assert succeeded == MfaChallengeVerificationResult(
        challenge_id=issued.challenge_id,
        succeeded=True,
    )
    db.commit()
    assert db.get(MfaChallenge, issued.challenge_id).consumed_at is not None
    assert factor.status == "active"
    assert factor.verified_at is not None
    _assert_code(
        "mfa_challenge_already_consumed",
        lambda: verify_mfa_challenge(
            db,
            user_id=user.id,
            challenge_id=issued.challenge_id,
            verifier=verifier,
        ),
    )


def test_attempt_limit_fails_closed_and_is_persisted(db):
    user = _user(db)
    factor = create_mfa_factor(db, user, method="synthetic.test")
    issued = issue_mfa_challenge(
        db,
        user_id=user.id,
        factor_id=factor.id,
        purpose="enrollment",
        verifier="synthetic-expected-verifier",
        max_attempts=2,
    )
    db.commit()

    first_denial = verify_mfa_challenge(
        db, user_id=user.id, challenge_id=issued.challenge_id, verifier="synthetic-wrong-one"
    )
    assert first_denial.succeeded is False
    assert first_denial.error_code == "invalid_mfa_verifier"
    db.commit()
    exhausted = verify_mfa_challenge(
        db, user_id=user.id, challenge_id=issued.challenge_id, verifier="synthetic-wrong-two"
    )
    assert exhausted.succeeded is False
    assert exhausted.error_code == "mfa_challenge_attempts_exhausted"
    db.commit()
    with Session(db.get_bind()) as fresh_db:
        challenge = fresh_db.get(MfaChallenge, issued.challenge_id)
        assert challenge.attempt_count == challenge.max_attempts == 2
    _assert_code(
        "mfa_challenge_attempts_exhausted",
        lambda: verify_mfa_challenge(
            db, user_id=user.id, challenge_id=issued.challenge_id, verifier="synthetic-expected-verifier"
        ),
    )
    assert factor.status == "pending"


def test_expired_revoked_and_cross_user_challenges_are_rejected(db):
    owner = _user(db, "owner")
    other = _user(db, "other")
    factor = create_mfa_factor(db, owner, method="synthetic.test")
    now = utcnow()
    expired = issue_mfa_challenge(
        db,
        user_id=owner.id,
        factor_id=factor.id,
        purpose="enrollment",
        verifier="synthetic-expired-verifier",
        now=now - timedelta(minutes=2),
        ttl_seconds=60,
    )
    db.commit()
    _assert_code(
        "mfa_challenge_expired",
        lambda: verify_mfa_challenge(
            db,
            user_id=owner.id,
            challenge_id=expired.challenge_id,
            verifier="synthetic-expired-verifier",
            now=now,
        ),
    )
    _assert_code(
        "invalid_mfa_challenge",
        lambda: verify_mfa_challenge(
            db,
            user_id=other.id,
            challenge_id=expired.challenge_id,
            verifier="synthetic-expired-verifier",
            now=now,
        ),
    )

    replacement = issue_mfa_challenge(
        db,
        user_id=owner.id,
        factor_id=factor.id,
        purpose="enrollment",
        verifier="synthetic-revoked-verifier",
        now=now,
    )
    revoke_mfa_challenge(db, user_id=owner.id, challenge_id=replacement.challenge_id, now=now)
    db.commit()
    _assert_code(
        "mfa_challenge_revoked",
        lambda: verify_mfa_challenge(
            db,
            user_id=owner.id,
            challenge_id=replacement.challenge_id,
            verifier="synthetic-revoked-verifier",
            now=now,
        ),
    )


def test_factor_revocation_invalidates_open_challenges(db):
    user = _user(db)
    factor = create_mfa_factor(db, user, method="synthetic.test")
    issued = issue_mfa_challenge(
        db,
        user_id=user.id,
        factor_id=factor.id,
        purpose="enrollment",
        verifier="synthetic-factor-revocation-verifier",
    )
    revoked = revoke_mfa_factor(db, user_id=user.id, factor_id=factor.id)
    db.commit()
    assert revoked.status == "revoked"
    assert revoked.revoked_at is not None
    assert db.get(MfaChallenge, issued.challenge_id).revoked_at is not None
    _assert_code(
        "mfa_challenge_revoked",
        lambda: verify_mfa_challenge(
            db,
            user_id=user.id,
            challenge_id=issued.challenge_id,
            verifier="synthetic-factor-revocation-verifier",
        ),
    )


def test_authentication_challenge_requires_active_factor(db):
    user = _user(db)
    factor = create_mfa_factor(db, user, method="synthetic.test")
    _assert_code(
        "mfa_factor_not_ready",
        lambda: issue_mfa_challenge(
            db,
            user_id=user.id,
            factor_id=factor.id,
            purpose="authentication",
            verifier="synthetic-authentication-verifier",
        ),
    )
    enrollment = issue_mfa_challenge(
        db,
        user_id=user.id,
        factor_id=factor.id,
        purpose="enrollment",
        verifier="synthetic-enrollment-verifier",
    )
    verify_mfa_challenge(
        db,
        user_id=user.id,
        challenge_id=enrollment.challenge_id,
        verifier="synthetic-enrollment-verifier",
    )
    authentication = issue_mfa_challenge(
        db,
        user_id=user.id,
        factor_id=factor.id,
        purpose="authentication",
        verifier="synthetic-authentication-verifier",
    )
    db.commit()
    result = verify_mfa_challenge(
        db,
        user_id=user.id,
        challenge_id=authentication.challenge_id,
        verifier="synthetic-authentication-verifier",
    )
    assert result.succeeded is True
    assert db.get(MfaChallenge, authentication.challenge_id).consumed_at is not None


def test_inactive_user_cannot_issue_or_consume_challenges(db):
    user = _user(db)
    factor = create_mfa_factor(db, user, method="synthetic.test")
    issued = issue_mfa_challenge(
        db,
        user_id=user.id,
        factor_id=factor.id,
        purpose="enrollment",
        verifier="synthetic-inactive-user-verifier",
    )
    user.is_active = False
    db.commit()
    denied = verify_mfa_challenge(
        db,
        user_id=user.id,
        challenge_id=issued.challenge_id,
        verifier="synthetic-inactive-user-verifier",
    )
    assert denied.succeeded is False
    assert denied.error_code == "mfa_factor_not_ready"
    db.commit()
    with Session(db.get_bind()) as fresh_db:
        assert fresh_db.get(MfaChallenge, issued.challenge_id).revoked_at is not None
    _assert_code(
        "mfa_factor_not_ready",
        lambda: issue_mfa_challenge(
            db,
            user_id=user.id,
            factor_id=factor.id,
            purpose="enrollment",
            verifier="synthetic-second-inactive-user-verifier",
        ),
    )


def test_persistence_constraints_reject_out_of_policy_attempt_limit(db):
    user = _user(db)
    factor = create_mfa_factor(db, user, method="synthetic.test")
    db.add(
        MfaChallenge(
            user_id=user.id,
            factor_id=factor.id,
            purpose="enrollment",
            verifier_digest="a" * 64,
            issued_at=utcnow(),
            expires_at=utcnow() + timedelta(minutes=5),
            attempt_count=0,
            max_attempts=11,
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()


def test_exact_migration_revision_and_model_registration():
    migration = Path("migrations/versions/20260910_0014_enterprise_security.py").read_text(encoding="utf-8")
    assert 'revision = "20260910_0014"' in migration
    assert 'down_revision = "20260828_0013"' in migration
    assert {"core_mfa_factors", "core_mfa_challenges"} <= set(Base.metadata.tables)
    assert select(MfaFactor) is not None
