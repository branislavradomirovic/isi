from __future__ import annotations
import os
import pytest
from sqlalchemy import text
from src.core.database import build_engine

pytestmark = pytest.mark.skipif(os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1", reason="native PostgreSQL acceptance only")

def test_native_postgres_ordo_catalog_and_tables():
    engine = build_engine()
    with engine.connect() as conn:
        tables = {r[0] for r in conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'ordo_%'"))}
        for name in {"ordo_pillars", "ordo_dimensions", "ordo_source_types", "ordo_indicator_definitions", "ordo_destination_profiles", "ordo_assets", "ordo_stakeholders", "ordo_monitoring_cycles", "ordo_data_mappings", "ordo_indicator_observations"}: assert name in tables
        assert conn.execute(text("SELECT count(*) FROM ordo_pillars")).scalar_one() == 5
        assert conn.execute(text("SELECT count(*) FROM ordo_dimensions")).scalar_one() == 9
        assert conn.execute(text("SELECT count(*) FROM ordo_source_types")).scalar_one() == 12
        assert conn.execute(text("SELECT count(*) FROM ordo_indicator_definitions WHERE methodology_status='conceptual'")).scalar_one() == 15
