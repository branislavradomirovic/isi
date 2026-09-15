"""Add versioned SIMPA reference-calculation suites and cases.

Revision ID: 20260915_0028
Revises: 20260914_0027
Create Date: 2026-09-15
"""

from alembic import op
import sqlalchemy as sa


revision = "20260915_0028"
down_revision = "20260914_0027"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.add_column(
        "simpa_indicator_methodologies",
        sa.Column(
            "reference_evidence_mode",
            sa.String(24),
            nullable=False,
            server_default="legacy_unknown",
        ),
    )
    op.execute(
        "UPDATE simpa_indicator_methodologies "
        "SET reference_evidence_mode = CASE "
        "WHEN reference_check_status = 'legacy_unknown' THEN 'legacy_unknown' "
        "ELSE 'legacy_inline' END"
    )
    op.alter_column(
        "simpa_indicator_methodologies",
        "reference_evidence_mode",
        server_default="suite_v1",
    )
    op.create_check_constraint(
        "ck_simpa_methodology_reference_evidence_mode",
        "simpa_indicator_methodologies",
        "reference_evidence_mode IN ('legacy_unknown','legacy_inline','suite_v1')",
    )

    op.create_table(
        "simpa_methodology_reference_suites",
        sa.Column("id", UUID, nullable=False),
        sa.Column("methodology_id", UUID, nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column(
            "schema_version",
            sa.String(40),
            nullable=False,
            server_default="SIMPA-REFERENCE-SUITE-v1",
        ),
        sa.Column("methodology_contract_fingerprint", sa.String(64), nullable=False),
        sa.Column("reference_dataset", sa.Text(), nullable=False),
        sa.Column("reference_dataset_version", sa.String(255), nullable=False),
        sa.Column("suite_fingerprint", sa.String(64), nullable=False),
        sa.Column("case_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="not_run"),
        sa.Column("result_fingerprint", sa.String(64), nullable=False, server_default=""),
        sa.Column("result_detail", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_by_membership_id", UUID, nullable=True),
        sa.Column("executed_by_membership_id", UUID, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.Column("executed_at", TS, nullable=True),
        sa.CheckConstraint("version_no >= 1", name="ck_simpa_reference_suite_version"),
        sa.CheckConstraint("case_count >= 1", name="ck_simpa_reference_suite_case_count"),
        sa.CheckConstraint(
            "schema_version = 'SIMPA-REFERENCE-SUITE-v1'",
            name="ck_simpa_reference_suite_schema_version",
        ),
        sa.CheckConstraint(
            "length(methodology_contract_fingerprint) = 64",
            name="ck_simpa_reference_suite_contract_fingerprint",
        ),
        sa.CheckConstraint("length(reference_dataset) > 0", name="ck_simpa_reference_suite_dataset"),
        sa.CheckConstraint(
            "length(reference_dataset_version) > 0",
            name="ck_simpa_reference_suite_dataset_version",
        ),
        sa.CheckConstraint("length(suite_fingerprint) = 64", name="ck_simpa_reference_suite_fingerprint"),
        sa.CheckConstraint("status IN ('not_run','passed','failed')", name="ck_simpa_reference_suite_status"),
        sa.CheckConstraint(
            "(status = 'not_run' AND result_fingerprint = '' AND length(CAST(result_detail AS TEXT)) = 2 AND executed_by_membership_id IS NULL AND executed_at IS NULL) OR "
            "(status IN ('passed','failed') AND length(result_fingerprint) = 64 AND length(CAST(result_detail AS TEXT)) > 2 AND executed_at IS NOT NULL)",
            name="ck_simpa_reference_suite_terminal",
        ),
        sa.ForeignKeyConstraint(
            ["methodology_id"],
            ["simpa_indicator_methodologies.id"],
            name="fk_simpa_reference_suite_methodology",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_membership_id"],
            ["core_memberships.id"],
            name="fk_simpa_reference_suite_creator",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["executed_by_membership_id"],
            ["core_memberships.id"],
            name="fk_simpa_reference_suite_executor",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_simpa_methodology_reference_suites"),
        sa.UniqueConstraint("methodology_id", "version_no", name="uq_simpa_reference_suite_version"),
        sa.UniqueConstraint("methodology_id", "suite_fingerprint", name="uq_simpa_reference_suite_fingerprint"),
    )
    op.create_index(
        "ix_simpa_reference_suite_methodology_status",
        "simpa_methodology_reference_suites",
        ["methodology_id", "status"],
    )

    op.create_table(
        "simpa_methodology_reference_cases",
        sa.Column("id", UUID, nullable=False),
        sa.Column("suite_id", UUID, nullable=False),
        sa.Column("case_key", sa.String(255), nullable=False),
        sa.Column("case_index", sa.Integer(), nullable=False),
        sa.Column("reference_record", sa.JSON(), nullable=False),
        sa.Column("expected_result", sa.JSON(), nullable=False),
        sa.Column("case_fingerprint", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="not_run"),
        sa.Column("result_fingerprint", sa.String(64), nullable=False, server_default=""),
        sa.Column("result_detail", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("length(case_key) > 0", name="ck_simpa_reference_case_key"),
        sa.CheckConstraint("case_index >= 0", name="ck_simpa_reference_case_index"),
        sa.CheckConstraint("length(case_fingerprint) = 64", name="ck_simpa_reference_case_fingerprint"),
        sa.CheckConstraint("status IN ('not_run','passed','failed')", name="ck_simpa_reference_case_status"),
        sa.CheckConstraint(
            "(status = 'not_run' AND result_fingerprint = '' AND length(CAST(result_detail AS TEXT)) = 2) OR "
            "(status IN ('passed','failed') AND length(result_fingerprint) = 64 AND length(CAST(result_detail AS TEXT)) > 2)",
            name="ck_simpa_reference_case_terminal",
        ),
        sa.ForeignKeyConstraint(
            ["suite_id"],
            ["simpa_methodology_reference_suites.id"],
            name="fk_simpa_reference_case_suite",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_simpa_methodology_reference_cases"),
        sa.UniqueConstraint("suite_id", "case_key", name="uq_simpa_reference_case_key"),
        sa.UniqueConstraint("suite_id", "case_index", name="uq_simpa_reference_case_index"),
    )
    op.create_index(
        "ix_simpa_reference_case_suite",
        "simpa_methodology_reference_cases",
        ["suite_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_simpa_reference_case_suite", table_name="simpa_methodology_reference_cases")
    op.drop_table("simpa_methodology_reference_cases")
    op.drop_index(
        "ix_simpa_reference_suite_methodology_status",
        table_name="simpa_methodology_reference_suites",
    )
    op.drop_table("simpa_methodology_reference_suites")
    op.drop_constraint(
        "ck_simpa_methodology_reference_evidence_mode",
        "simpa_indicator_methodologies",
        type_="check",
    )
    op.drop_column("simpa_indicator_methodologies", "reference_evidence_mode")
