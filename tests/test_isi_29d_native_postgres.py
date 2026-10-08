"""Isolated loopback PostgreSQL migration lane; owned disposable schema only."""

import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

pytestmark = pytest.mark.skipif(
    not (os.environ.get("ISI_29D_NATIVE_DATABASE_URL") or os.environ.get("ISI_RUN_NATIVE_DB_TESTS") == "1"),
    reason="requires isolated 29D PostgreSQL lane"
)


def test_upgrade_downgrade_reupgrade_and_scope_foreign_keys():
    url = make_url(os.environ.get("ISI_29D_NATIVE_DATABASE_URL") or os.environ["DATABASE_URL"])
    assert url.get_backend_name() == "postgresql" and url.database in {"isi29d_synthetic", "isi_ci"}
    assert url.host in {"localhost", "127.0.0.1"}
    engine = create_engine(url)
    schema = "isi29d_" + uuid4().hex
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA " + schema))
    scoped = url.set(query=dict(url.query) | {"options": "-csearch_path=" + schema})
    native = create_engine(scoped)
    env = dict(os.environ)
    env["DATABASE_URL"] = scoped.render_as_string(hide_password=False).replace("%3D", "=")
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")

    def migrate(revision, action="upgrade"):
        p = subprocess.run(
            [sys.executable, "-m", "alembic", action, revision],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        assert p.returncode == 0, "isolated migration failed; do not print database URL"

    try:
        migrate("20261007_0035")
        previous = set(inspect(native).get_table_names())
        migrate("20261008_0036")
        assert set(inspect(native).get_table_names()) == previous | {"simpa_attribution_artifacts"}
        constraints = inspect(native).get_foreign_keys("simpa_attribution_artifacts")
        assert {x["referred_table"] for x in constraints} == {
            "core_organizations",
            "core_workspaces",
            "core_memberships",
            "simpa_statistical_model_results",
        }
        assert len(inspect(native).get_unique_constraints("simpa_attribution_artifacts")) == 1
        with native.begin() as conn:
            with pytest.raises(IntegrityError):
                with conn.begin_nested():
                    conn.execute(
                        text(
                            "INSERT INTO simpa_attribution_artifacts (id,organization_id,workspace_id,statistical_result_id,result_fingerprint,schema_version,artifact,fingerprint,created_by_membership_id) VALUES (:id,:org,:workspace,:result,:hash,'SIMPA-LINEAR-SHAP-v1','{}',:hash,:actor)"
                        ),
                        {
                            "id": uuid4(),
                            "org": uuid4(),
                            "workspace": uuid4(),
                            "result": uuid4(),
                            "hash": "a" * 64,
                            "actor": uuid4(),
                        },
                    )
        migrate("20261007_0035", "downgrade")
        assert set(inspect(native).get_table_names()) == previous
        migrate("20261008_0036")
        assert set(inspect(native).get_table_names()) == previous | {"simpa_attribution_artifacts"}
        with native.connect() as conn:
            assert conn.scalar(text("SELECT count(*) FROM simpa_attribution_artifacts")) == 0
    finally:
        native.dispose()
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA " + schema + " CASCADE"))
        engine.dispose()
