"""Add ORDO governed forecast runtime and scenario impact semantics.

Revision ID: 20260916_0032
Revises: 20260916_0031
Create Date: 2026-09-16
"""

from alembic import op
import sqlalchemy as sa


revision = "20260916_0032"
down_revision = "20260916_0031"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "ordo_forecast_runs",
        sa.Column("id", UUID, nullable=False),
        sa.Column("organization_id", UUID, nullable=False),
        sa.Column("workspace_id", UUID, nullable=False),
        sa.Column("analytics_run_id", UUID, nullable=False),
        sa.Column("time_series_spec_id", UUID, nullable=False),
        sa.Column("time_series_spec_version", sa.Integer(), nullable=False),
        sa.Column("time_series_spec_fingerprint", sa.String(64), nullable=False),
        sa.Column("target_indicator_id", UUID, nullable=False),
        sa.Column("target_methodology_id", UUID, nullable=False),
        sa.Column("target_methodology_version", sa.Integer(), nullable=False),
        sa.Column("methodology_fingerprint", sa.String(64), nullable=False),
        sa.Column("input_snapshot_sha256", sa.String(64), nullable=False),
        sa.Column("schema_version", sa.String(64), nullable=False, server_default="ORDO-FORECAST-RUN-v1"),
        sa.Column("series_identity", sa.JSON(), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("requested_family", sa.String(32), nullable=False),
        sa.Column("executed_family", sa.String(32), nullable=True),
        sa.Column("engine_key", sa.String(80), nullable=False),
        sa.Column("engine_version", sa.String(32), nullable=False),
        sa.Column("interval_method", sa.String(80), nullable=False),
        sa.Column("interval_level", sa.Float(), nullable=False),
        sa.Column("result_status", sa.String(24), nullable=False),
        sa.Column("reason_code", sa.String(80), nullable=False, server_default=""),
        sa.Column("observation_window", sa.JSON(), nullable=False),
        sa.Column("training_window", sa.JSON(), nullable=False),
        sa.Column("horizon", sa.Integer(), nullable=False),
        sa.Column("rolling_origin_plan", sa.JSON(), nullable=False),
        sa.Column("backtest_records", sa.JSON(), nullable=False),
        sa.Column("aggregate_backtest_metrics", sa.JSON(), nullable=False),
        sa.Column("metric_availability", sa.JSON(), nullable=False),
        sa.Column("diagnostics", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("forecast_points", sa.JSON(), nullable=False),
        sa.Column("result_fingerprint", sa.String(64), nullable=False),
        sa.Column("non_causal", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("automatic_model_selection", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("automatic_policy_recommendation", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by_membership_id", UUID, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_ordo_forecast_runs"),
        sa.CheckConstraint("schema_version = 'ORDO-FORECAST-RUN-v1'", name="ck_ordo_forecast_run_schema"),
        sa.CheckConstraint("result_status IN ('ESTIMATED','NOT_ESTIMATED')", name="ck_ordo_forecast_run_status"),
        sa.CheckConstraint("requested_family IN ('naive','seasonal_naive','ets','sarima','sarimax','count_time_series')", name="ck_ordo_forecast_run_requested_family"),
        sa.CheckConstraint("executed_family IS NULL OR executed_family IN ('naive','seasonal_naive')", name="ck_ordo_forecast_run_executed_family"),
        sa.CheckConstraint("interval_level IN (0.80,0.90,0.95)", name="ck_ordo_forecast_run_interval_level"),
        sa.CheckConstraint("horizon >= 1", name="ck_ordo_forecast_run_horizon"),
        sa.CheckConstraint("length(time_series_spec_fingerprint) = 64 AND length(methodology_fingerprint) = 64 AND length(input_snapshot_sha256) = 64 AND length(request_fingerprint) = 64 AND length(result_fingerprint) = 64", name="ck_ordo_forecast_run_fingerprints"),
        sa.CheckConstraint("non_causal = true AND automatic_model_selection = false AND automatic_policy_recommendation = false", name="ck_ordo_forecast_run_locked_semantics"),
        sa.CheckConstraint("(result_status = 'ESTIMATED' AND executed_family IS NOT NULL AND reason_code = '' AND json_array_length(forecast_points) = horizon AND json_array_length(backtest_records) > 0) OR (result_status = 'NOT_ESTIMATED' AND executed_family IS NULL AND length(reason_code) > 0 AND json_array_length(forecast_points) = 0 AND json_array_length(backtest_records) = 0)", name="ck_ordo_forecast_run_result_state"),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["core_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analytics_run_id"], ["ordo_analytics_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["time_series_spec_id"], ["ordo_time_series_specs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["target_indicator_id"], ["ordo_indicator_definitions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["target_methodology_id"], ["ordo_indicator_methodologies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_ordo_forecast_run_scope_created", "ordo_forecast_runs", ["organization_id", "workspace_id", "created_at"])
    op.create_index("ix_ordo_forecast_run_request_fingerprint", "ordo_forecast_runs", ["request_fingerprint"])

    with op.batch_alter_table("ordo_scenario_assessments") as batch:
        batch.add_column(sa.Column("impact_estimation_status", sa.String(32), nullable=False, server_default="LEGACY_NOT_EVALUATED"))
        batch.add_column(sa.Column("impact_estimation_reason_code", sa.String(80), nullable=False, server_default=""))
        batch.add_column(sa.Column("impact_estimate_numeric", sa.Float(), nullable=True))
        batch.add_column(sa.Column("impact_estimate_unit", sa.String(80), nullable=False, server_default=""))
        batch.add_column(sa.Column("impact_model_reference", sa.String(400), nullable=False, server_default=""))
        # The accepted ck_ordo_scenario_assessment_no_forecast constraint is intentionally preserved.
        batch.create_check_constraint("ck_ordo_scenario_assessment_impact_status", "impact_estimation_status IN ('LEGACY_NOT_EVALUATED','NOT_ESTIMATED','ESTIMATED')")
        batch.create_check_constraint("ck_ordo_scenario_assessment_not_estimated_impact", "impact_estimation_status != 'NOT_ESTIMATED' OR (impact_estimation_reason_code = 'NO_APPROVED_RESPONSE_MODEL' AND impact_estimate_numeric IS NULL AND impact_model_reference = '')")
    op.execute(
        "UPDATE ordo_scenario_assessments SET impact_estimation_status = 'LEGACY_NOT_EVALUATED', "
        "impact_estimation_reason_code = '', impact_estimate_numeric = NULL, impact_estimate_unit = '', "
        "impact_model_reference = ''"
    )
    op.alter_column(
        "ordo_scenario_assessments", "impact_estimation_status",
        existing_type=sa.String(32), server_default="NOT_ESTIMATED",
    )
    op.alter_column(
        "ordo_scenario_assessments", "impact_estimation_reason_code",
        existing_type=sa.String(80), server_default="NO_APPROVED_RESPONSE_MODEL",
    )


def downgrade() -> None:
    with op.batch_alter_table("ordo_scenario_assessments") as batch:
        batch.drop_constraint("ck_ordo_scenario_assessment_not_estimated_impact", type_="check")
        batch.drop_constraint("ck_ordo_scenario_assessment_impact_status", type_="check")
        batch.drop_column("impact_model_reference")
        batch.drop_column("impact_estimate_unit")
        batch.drop_column("impact_estimate_numeric")
        batch.drop_column("impact_estimation_reason_code")
        batch.drop_column("impact_estimation_status")
    op.drop_index("ix_ordo_forecast_run_request_fingerprint", table_name="ordo_forecast_runs")
    op.drop_index("ix_ordo_forecast_run_scope_created", table_name="ordo_forecast_runs")
    op.drop_table("ordo_forecast_runs")
