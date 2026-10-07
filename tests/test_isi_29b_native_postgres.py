"""Native migration/persistence proof in an owned temporary schema; no live/server DB."""

import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from test_isi_29b_spatial_registry import setup_db, create, validate, args
from src.platform.data.storage import LocalFilesystemStorage
from src.platform.spatial.service import get_geometry
from datetime import date

NATIVE = os.environ.get("ISI_RUN_NATIVE_DB_TESTS") == "1" or bool(os.environ.get("ISI_29B_NATIVE_DATABASE_URL"))
pytestmark = pytest.mark.skipif(not NATIVE, reason="requires isolated native PostgreSQL lane")


def test_native_migration_upgrade_downgrade_and_scoped_persistence(tmp_path):
    url = make_url(os.environ.get("ISI_29B_NATIVE_DATABASE_URL") or os.environ["DATABASE_URL"])
    assert url.get_backend_name() == "postgresql" and url.database in {"isi29b_synthetic", "isi_ci"}
    assert url.host in {"127.0.0.1", "localhost"}, "native fixture must stay on loopback"
    schema = "isi29b_" + uuid4().hex
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("CREATE SCHEMA " + schema))
    scoped_url = url.set(query=dict(url.query) | {"options": "-csearch_path=" + schema})
    native = create_engine(scoped_url)
    env = dict(os.environ)
    env["DATABASE_URL"] = scoped_url.render_as_string(hide_password=False).replace("%3D", "=")
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")

    def migrate(target, action="upgrade"):
        completed = subprocess.run(
            [sys.executable, "-m", "alembic", action, target],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        assert completed.returncode == 0, "isolated migration failed; do not expose database URL"

    try:
        migrate("20260918_0034")
        previous = set(inspect(native).get_table_names())
        migrate("20261007_0035")
        assert set(inspect(native).get_table_names()) == previous | {"core_spatial_geometry_versions"}
        with sessionmaker(bind=native, expire_on_commit=False)() as db:
            c = setup_db(db)
            c["db"] = db
            c["storage"] = LocalFilesystemStorage(tmp_path)
            row = create(c)
            validate(c, row)
            assert (
                get_geometry(db, **args(c), geometry_id=row.id, at_date=date(2026, 1, 1), storage=c["storage"])[
                    "geometry"
                ]["type"]
                == "Polygon"
            )
        from sqlalchemy.exc import IntegrityError
        from sqlalchemy.orm.exc import StaleDataError
        from src.platform.spatial.models import SpatialGeometryVersion

        with native.begin() as conn:
            with pytest.raises(IntegrityError):
                with conn.begin_nested():
                    conn.execute(text("UPDATE core_spatial_geometry_versions SET domain_kind='asset'"))
        factory = sessionmaker(bind=native, expire_on_commit=False)
        with factory() as first, factory() as second:
            a = first.get(SpatialGeometryVersion, row.id)
            b = second.get(SpatialGeometryVersion, row.id)
            a.state = "RETIRED"
            first.commit()
            b.state = "RETIRED"
            with pytest.raises(StaleDataError):
                second.commit()
        migrate("20260918_0034", "downgrade")
        assert set(inspect(native).get_table_names()) == previous
        with native.connect() as conn:
            assert conn.scalar(text("SELECT count(*) FROM core_organizations")) == 1
        migrate("20261007_0035")
        with native.connect() as conn:
            assert conn.scalar(text("SELECT count(*) FROM core_spatial_geometry_versions")) == 0
            assert conn.scalar(text("SELECT count(*) FROM core_organizations")) == 1
    finally:
        native.dispose()
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA " + schema + " CASCADE"))
        engine.dispose()
