from __future__ import annotations

import os

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(
    os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1",
    reason="native PostgreSQL acceptance only",
)


def test_native_postgres_has_isi11_tables_prompt_policy_and_no_validated_methodology_seed():
    from src.core.database import build_session_factory

    factory = build_session_factory()
    with factory() as session:
        names = {
            row[0]
            for row in session.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'ordo_%'")
            )
        }
        for table in (
            "ordo_indicator_methodologies",
            "ordo_analytics_runs",
            "ordo_indicator_results",
            "ordo_development_goals",
            "ordo_scenarios",
            "ordo_scenario_assessments",
            "ordo_ai_syntheses",
        ):
            assert table in names
        prompt_count = session.execute(
            text("SELECT count(*) FROM core_ai_prompts WHERE prompt_key='ordo.decision_support.synthesis' AND product_scope='ORDO' AND is_active=true")
        ).scalar_one()
        assert prompt_count == 1
        policy = session.execute(
            text("SELECT provider_policy, allow_external, require_human_review FROM core_ai_policy_profiles WHERE policy_key='ordo-decision-support-local' AND product_scope='ORDO'")
        ).one()
        assert policy[0] == "local_only"
        assert policy[1] is False
        assert policy[2] is True
        validated = session.execute(text("SELECT count(*) FROM ordo_indicator_methodologies WHERE status='validated'")).scalar_one()
        assert validated == 0
