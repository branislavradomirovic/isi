import os
import pytest
from sqlalchemy import inspect, text
from src.core.database import build_engine


@pytest.mark.skipif(os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1", reason="native PostgreSQL acceptance only")
def test_native_postgres_has_simpa_domain_tables_and_seed_catalog():
    engine = build_engine()
    names = set(inspect(engine).get_table_names())
    assert {
        "simpa_dimensions", "simpa_source_types", "simpa_indicator_definitions",
        "simpa_local_system_profiles", "simpa_local_actors", "simpa_monitoring_cycles",
        "simpa_data_mappings", "simpa_indicator_observations",
    } <= names
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM simpa_dimensions WHERE active=true")).scalar() == 9
        assert connection.execute(text("SELECT count(*) FROM simpa_source_types WHERE active=true")).scalar() == 9
        assert connection.execute(text("SELECT count(*) FROM simpa_indicator_definitions WHERE active=true")).scalar() == 15
        assert connection.execute(text("SELECT count(*) FROM simpa_indicator_definitions WHERE methodology_status='conceptual'")).scalar() == 15
