"""Enforce governed analytical consumption by domain runs.

Revision ID: 20260914_0026
Revises: 20260913_0025
Create Date: 2026-09-14
"""

from alembic import op
import sqlalchemy as sa


revision = "20260914_0026"
down_revision = "20260913_0025"
branch_labels = None
depends_on = None

UUID = sa.Uuid()


def _upgrade_run_table(table: str, prefix: str) -> None:
    op.add_column(table, sa.Column("analytical_artifact_type", sa.String(40), nullable=False, server_default="LEGACY_OBSERVATION"))
    op.add_column(table, sa.Column("analytical_snapshot_id", UUID, nullable=True))
    op.add_column(table, sa.Column("analytical_feature_version_id", UUID, nullable=True))
    op.add_column(table, sa.Column("analytical_artifact_fingerprint", sa.String(64), nullable=False, server_default=""))
    op.add_column(table, sa.Column("dataset_contract_version_id", UUID, nullable=True))
    op.add_column(table, sa.Column("dataset_contract_fingerprint", sa.String(64), nullable=False, server_default=""))
    op.add_column(table, sa.Column("analytical_quality_state", sa.String(32), nullable=False, server_default="LEGACY_UNKNOWN"))
    op.create_foreign_key(f"fk_{prefix}_run_snapshot", table, "core_analytical_dataset_snapshots", ["analytical_snapshot_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key(f"fk_{prefix}_run_feature", table, "core_analytical_feature_versions", ["analytical_feature_version_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key(f"fk_{prefix}_run_contract", table, "core_analytical_dataset_contract_versions", ["dataset_contract_version_id"], ["id"], ondelete="RESTRICT")
    op.create_check_constraint(
        f"ck_{prefix}_run_artifact_type",
        table,
        "analytical_artifact_type IN ('LEGACY_OBSERVATION','ANALYTICAL_SNAPSHOT','ANALYTICAL_FEATURE_VERSION')",
    )
    op.create_check_constraint(
        f"ck_{prefix}_run_artifact_binding",
        table,
        "(analytical_artifact_type = 'LEGACY_OBSERVATION' AND analytical_snapshot_id IS NULL AND analytical_feature_version_id IS NULL) OR "
        "(analytical_artifact_type = 'ANALYTICAL_SNAPSHOT' AND analytical_snapshot_id IS NOT NULL AND analytical_feature_version_id IS NULL) OR "
        "(analytical_artifact_type = 'ANALYTICAL_FEATURE_VERSION' AND analytical_snapshot_id IS NULL AND analytical_feature_version_id IS NOT NULL)",
    )
    op.create_check_constraint(
        f"ck_{prefix}_run_governed_identity",
        table,
        "analytical_artifact_type = 'LEGACY_OBSERVATION' OR "
        "(dataset_contract_version_id IS NOT NULL AND length(analytical_artifact_fingerprint) = 64 AND "
        "length(dataset_contract_fingerprint) = 64 AND analytical_quality_state IN ('ACCEPTED_CLEAN','ACCEPTED_WITH_WARNING'))",
    )
    op.create_index(f"ix_{prefix}_run_analytical_snapshot", table, ["analytical_snapshot_id"])
    op.create_index(f"ix_{prefix}_run_analytical_feature", table, ["analytical_feature_version_id"])
    op.create_index(f"ix_{prefix}_run_dataset_contract", table, ["dataset_contract_version_id"])


def upgrade() -> None:
    _upgrade_run_table("simpa_analytics_runs", "simpa")
    _upgrade_run_table("ordo_analytics_runs", "ordo")


def _downgrade_run_table(table: str, prefix: str) -> None:
    for suffix in ("dataset_contract", "analytical_feature", "analytical_snapshot"):
        op.drop_index(f"ix_{prefix}_run_{suffix}", table_name=table)
    for suffix in ("governed_identity", "artifact_binding", "artifact_type"):
        op.drop_constraint(f"ck_{prefix}_run_{suffix}", table, type_="check")
    for suffix in ("contract", "feature", "snapshot"):
        op.drop_constraint(f"fk_{prefix}_run_{suffix}", table, type_="foreignkey")
    for column in (
        "analytical_quality_state",
        "dataset_contract_fingerprint",
        "dataset_contract_version_id",
        "analytical_artifact_fingerprint",
        "analytical_feature_version_id",
        "analytical_snapshot_id",
        "analytical_artifact_type",
    ):
        op.drop_column(table, column)


def downgrade() -> None:
    _downgrade_run_table("ordo_analytics_runs", "ordo")
    _downgrade_run_table("simpa_analytics_runs", "simpa")
