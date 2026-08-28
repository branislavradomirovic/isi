from __future__ import annotations

import os

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(
    os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1",
    reason="native PostgreSQL acceptance only",
)


def test_native_postgres_has_reporting_tables_and_expected_constraints():
    from src.core.database import build_session_factory

    factory = build_session_factory()
    with factory() as session:
        names = {
            row[0]
            for row in session.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'core_report%'")
            )
        }
        assert {"core_reports", "core_report_versions", "core_report_reviews", "core_report_exports"}.issubset(names)
        version_status = session.execute(
            text("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname='ck_core_report_versions_status'")
        ).scalar_one()
        assert "published" in version_status and "superseded" in version_status
        export_format = session.execute(
            text("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname='ck_core_report_exports_format'")
        ).scalar_one()
        assert "markdown" in export_format and "html" in export_format and "json" in export_format
