from __future__ import annotations

import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import inspect

from src.core.database import build_engine, build_session_factory
from src.platform.auth.service import (
    AuthError,
    create_mfa_factor,
    issue_mfa_challenge,
    provision_user,
    verify_mfa_challenge,
)


pytestmark = pytest.mark.skipif(
    os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1",
    reason="native PostgreSQL acceptance only",
)


def test_native_postgres_mfa_tables_constraints_and_atomic_consume():
    engine = build_engine()
    inspector = inspect(engine)
    assert {"core_mfa_factors", "core_mfa_challenges"} <= set(inspector.get_table_names())
    challenge_constraints = {item["name"] for item in inspector.get_check_constraints("core_mfa_challenges")}
    assert {
        "ck_core_mfa_challenges_attempts_bounded",
        "ck_core_mfa_challenges_max_attempts",
        "ck_core_mfa_challenges_terminal_state",
    } <= challenge_constraints

    factory = build_session_factory(engine)
    verifier = "synthetic-concurrent-verifier"
    with factory() as db:
        user = provision_user(
            db,
            email=f"isi20-{uuid.uuid4().hex}@example.invalid",
            display_name="ISI-20 Native PostgreSQL",
            password="Native-Postgres-password-2026",
            email_verified=True,
        )
        factor = create_mfa_factor(db, user, method="synthetic.test")
        issued = issue_mfa_challenge(
            db,
            user_id=user.id,
            factor_id=factor.id,
            purpose="enrollment",
            verifier=verifier,
        )
        user_id = user.id
        challenge_id = issued.challenge_id
        db.commit()

    barrier = Barrier(2)

    def consume_once() -> str:
        with factory() as db:
            barrier.wait()
            try:
                result = verify_mfa_challenge(
                    db,
                    user_id=user_id,
                    challenge_id=challenge_id,
                    verifier=verifier,
                )
                assert result.succeeded is True
                db.commit()
                return "consumed"
            except AuthError as exc:
                db.rollback()
                return exc.code

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _index: consume_once(), range(2)))

    assert sorted(outcomes) == ["consumed", "mfa_challenge_already_consumed"]

    with factory() as db:
        from src.platform.identity.models import User

        persisted_user = db.get(User, user_id)
        assert persisted_user is not None
        db.delete(persisted_user)
        db.commit()
