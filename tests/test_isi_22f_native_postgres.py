from __future__ import annotations

import os

import pytest
from sqlalchemy import inspect, text

from src.core.database import build_engine


pytestmark = pytest.mark.skipif(os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1",
                                reason="native PostgreSQL acceptance only")


def test_native_postgres_0025_constraints_fks_and_partial_uniqueness():
    engine = build_engine()
    inspector = inspect(engine)
    assert {"core_analytical_dataset_contract_versions",
            "core_analytical_snapshot_governed_outputs",
            "core_analytical_snapshot_record_inputs"} <= set(inspector.get_table_names())
    with engine.connect() as connection:
        active_index = connection.execute(text("""
            SELECT i.indisunique, i.indisvalid, pg_get_expr(i.indpred, i.indrelid)
            FROM pg_index AS i
            JOIN pg_class AS c ON c.oid = i.indexrelid
            WHERE c.relname = 'uq_analytical_contract_active_dataset'
        """)).one()
    assert active_index[0] is True and active_index[1] is True
    assert "ACTIVE" in active_index[2]
    active = next(item for item in inspector.get_indexes("core_analytical_dataset_contract_versions")
                  if item["name"] == "uq_analytical_contract_active_dataset")
    assert active["unique"] is True
    assert active["column_names"] == ["dataset_id"]
    assert "ACTIVE" in str(active.get("dialect_options", {}).get("postgresql_where", ""))
    output_fks = {fk["referred_table"] for fk in inspector.get_foreign_keys(
        "core_analytical_snapshot_governed_outputs")}
    record_fks = {fk["referred_table"] for fk in inspector.get_foreign_keys(
        "core_analytical_snapshot_record_inputs")}
    assert {"core_data_governed_ingestion_outputs", "core_data_ingestion_evaluations",
            "core_data_ingestion_runs"} <= output_fks
    assert {"core_data_governed_ingestion_outputs", "core_data_normalized_records",
            "core_analytical_dataset_snapshots"} <= record_fks
