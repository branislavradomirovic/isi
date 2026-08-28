import os
import pytest

pytestmark = pytest.mark.skipif(os.environ.get("ISI_NATIVE_POSTGRES_TEST") != "1", reason="native PostgreSQL acceptance only")


def test_native_postgres_has_isi09_tables_and_prompt():
    from sqlalchemy import text
    from src.core.database import build_session_factory
    factory = build_session_factory()
    with factory() as session:
        names = {row[0] for row in session.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'simpa_%'"))}
        for table in ("simpa_indicator_methodologies", "simpa_analytics_runs", "simpa_indicator_results", "simpa_ai_syntheses"):
            assert table in names
        count = session.execute(text("SELECT count(*) FROM core_ai_prompts WHERE prompt_key='simpa.monitoring.synthesis' AND product_scope='SIMPA' AND is_active=true")).scalar_one()
        assert count == 1
        validated = session.execute(text("SELECT count(*) FROM simpa_indicator_methodologies WHERE status='validated'")).scalar_one()
        assert validated == 0
