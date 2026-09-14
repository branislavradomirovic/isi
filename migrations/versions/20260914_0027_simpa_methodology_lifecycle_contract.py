"""Add the SIMPA methodology lifecycle and production contract authority.

Revision ID: 20260914_0027
Revises: 20260914_0026
Create Date: 2026-09-14
"""

from alembic import op
import sqlalchemy as sa


revision = "20260914_0027"
down_revision = "20260914_0026"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.drop_constraint(
        "ck_simpa_indicator_methodology_status",
        "simpa_indicator_definitions",
        type_="check",
    )
    op.create_check_constraint(
        "ck_simpa_indicator_methodology_status",
        "simpa_indicator_definitions",
        "methodology_status IN ('conceptual','draft','proposed','validated','retired')",
    )

    op.drop_constraint(
        "ck_simpa_indicator_methodology_status",
        "simpa_indicator_methodologies",
        type_="check",
    )
    op.create_check_constraint(
        "ck_simpa_indicator_methodology_status",
        "simpa_indicator_methodologies",
        "status IN ('draft','proposed','validated','retired')",
    )
    op.add_column(
        "simpa_indicator_methodologies",
        sa.Column("contract_fingerprint", sa.String(64), nullable=False, server_default=""),
    )
    op.add_column(
        "simpa_indicator_methodologies",
        sa.Column("proposed_by_membership_id", UUID, nullable=True),
    )
    op.add_column(
        "simpa_indicator_methodologies",
        sa.Column("proposed_at", TS, nullable=True),
    )
    op.add_column(
        "simpa_indicator_methodologies",
        sa.Column("reference_check_status", sa.String(24), nullable=False, server_default="legacy_unknown"),
    )
    op.add_column(
        "simpa_indicator_methodologies",
        sa.Column("reference_check_fingerprint", sa.String(64), nullable=False, server_default=""),
    )
    op.add_column(
        "simpa_indicator_methodologies",
        sa.Column("reference_check_detail", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )
    op.add_column(
        "simpa_indicator_methodologies",
        sa.Column("retired_by_membership_id", UUID, nullable=True),
    )
    op.add_column(
        "simpa_indicator_methodologies",
        sa.Column("retired_at", TS, nullable=True),
    )
    op.add_column(
        "simpa_indicator_methodologies",
        sa.Column("retirement_note", sa.Text(), nullable=False, server_default=""),
    )
    op.create_foreign_key(
        "fk_simpa_methodology_proposer",
        "simpa_indicator_methodologies",
        "core_memberships",
        ["proposed_by_membership_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_simpa_methodology_retirer",
        "simpa_indicator_methodologies",
        "core_memberships",
        ["retired_by_membership_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_check_constraint(
        "ck_simpa_methodology_contract_fingerprint",
        "simpa_indicator_methodologies",
        "contract_fingerprint = '' OR length(contract_fingerprint) = 64",
    )
    op.create_check_constraint(
        "ck_simpa_methodology_reference_status",
        "simpa_indicator_methodologies",
        "reference_check_status IN ('not_run','passed','failed','legacy_unknown')",
    )
    op.create_check_constraint(
        "ck_simpa_methodology_reference_fingerprint",
        "simpa_indicator_methodologies",
        "(reference_check_status IN ('not_run','legacy_unknown') AND reference_check_fingerprint = '') OR "
        "(reference_check_status IN ('passed','failed') AND length(reference_check_fingerprint) = 64)",
    )


def downgrade() -> None:
    # PROPOSED did not exist before 0027. Map it back to DRAFT so the historical
    # constraint can be restored without deleting methodology history.
    op.execute("UPDATE simpa_indicator_methodologies SET status='draft' WHERE status='proposed'")
    op.execute(
        "UPDATE simpa_indicator_definitions SET methodology_status='conceptual' "
        "WHERE methodology_status IN ('draft','proposed')"
    )
    for name in (
        "ck_simpa_methodology_reference_fingerprint",
        "ck_simpa_methodology_reference_status",
        "ck_simpa_methodology_contract_fingerprint",
    ):
        op.drop_constraint(name, "simpa_indicator_methodologies", type_="check")
    for name in ("fk_simpa_methodology_retirer", "fk_simpa_methodology_proposer"):
        op.drop_constraint(name, "simpa_indicator_methodologies", type_="foreignkey")
    for column in (
        "retirement_note",
        "retired_at",
        "retired_by_membership_id",
        "reference_check_detail",
        "reference_check_fingerprint",
        "reference_check_status",
        "proposed_at",
        "proposed_by_membership_id",
        "contract_fingerprint",
    ):
        op.drop_column("simpa_indicator_methodologies", column)
    op.drop_constraint(
        "ck_simpa_indicator_methodology_status",
        "simpa_indicator_methodologies",
        type_="check",
    )
    op.create_check_constraint(
        "ck_simpa_indicator_methodology_status",
        "simpa_indicator_methodologies",
        "status IN ('draft','validated','retired')",
    )
    op.drop_constraint(
        "ck_simpa_indicator_methodology_status",
        "simpa_indicator_definitions",
        type_="check",
    )
    op.create_check_constraint(
        "ck_simpa_indicator_methodology_status",
        "simpa_indicator_definitions",
        "methodology_status IN ('conceptual','validated','retired')",
    )
