"""simpa analytics and ai

Revision ID: 20260828_0008
Revises: 20260828_0007
Create Date: 2026-08-28
"""
from __future__ import annotations

import hashlib
import json
import uuid

from alembic import op
import sqlalchemy as sa

revision = "20260828_0008"
down_revision = "20260828_0007"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)
NS = uuid.UUID("de9158f0-6b5b-4f85-88bb-a08097d48d09")


def uid(kind: str, key: str) -> uuid.UUID:
    return uuid.uuid5(NS, f"{kind}:{key}")


def upgrade() -> None:
    op.create_table(
        "simpa_indicator_methodologies",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("indicator_id", UUID, sa.ForeignKey("simpa_indicator_definitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("computation_type", sa.String(40), nullable=False, server_default="direct_observation"),
        sa.Column("computation_spec", sa.JSON(), nullable=False),
        sa.Column("source_requirements", sa.JSON(), nullable=False),
        sa.Column("methodology_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("validation_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("approved_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", TS, nullable=True),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("indicator_id", "version_no", name="uq_simpa_indicator_methodology_version"),
        sa.CheckConstraint("status IN ('draft','validated','retired')", name="ck_simpa_indicator_methodology_status"),
        sa.CheckConstraint("computation_type IN ('direct_observation')", name="ck_simpa_indicator_methodology_computation"),
    )
    op.create_index("ix_simpa_indicator_methodologies_indicator_id", "simpa_indicator_methodologies", ["indicator_id"])

    op.create_table(
        "simpa_analytics_runs",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("monitoring_cycle_id", UUID, sa.ForeignKey("simpa_monitoring_cycles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="completed"),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("evidence_quality_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("validated_observation_ratio", sa.Float(), nullable=False, server_default="0"),
        sa.Column("provenance_coverage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("indicator_coverage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("status IN ('completed','failed')", name="ck_simpa_analytics_run_status"),
        sa.CheckConstraint("evidence_quality_score >= 0 AND evidence_quality_score <= 1", name="ck_simpa_analytics_run_quality_score"),
        sa.CheckConstraint("validated_observation_ratio >= 0 AND validated_observation_ratio <= 1", name="ck_simpa_analytics_run_validated_ratio"),
        sa.CheckConstraint("provenance_coverage >= 0 AND provenance_coverage <= 1", name="ck_simpa_analytics_run_provenance"),
        sa.CheckConstraint("indicator_coverage >= 0 AND indicator_coverage <= 1", name="ck_simpa_analytics_run_indicator_coverage"),
    )
    op.create_index("ix_simpa_analytics_runs_organization_id", "simpa_analytics_runs", ["organization_id"])
    op.create_index("ix_simpa_analytics_runs_workspace_id", "simpa_analytics_runs", ["workspace_id"])
    op.create_index("ix_simpa_analytics_runs_monitoring_cycle_id", "simpa_analytics_runs", ["monitoring_cycle_id"])

    op.create_table(
        "simpa_indicator_results",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analytics_run_id", UUID, sa.ForeignKey("simpa_analytics_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("indicator_id", UUID, sa.ForeignKey("simpa_indicator_definitions.id"), nullable=False),
        sa.Column("methodology_id", UUID, sa.ForeignKey("simpa_indicator_methodologies.id"), nullable=False),
        sa.Column("value_numeric", sa.Float(), nullable=True),
        sa.Column("value_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("unit", sa.String(80), nullable=False, server_default=""),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source_observation_ids", sa.JSON(), nullable=False),
        sa.Column("computation_trace", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="computed"),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("status IN ('computed','reviewed','rejected')", name="ck_simpa_indicator_result_status"),
        sa.CheckConstraint("quality_score >= 0 AND quality_score <= 1", name="ck_simpa_indicator_result_quality"),
    )
    for col in ("organization_id", "workspace_id", "analytics_run_id", "indicator_id", "methodology_id"):
        op.create_index(f"ix_simpa_indicator_results_{col}", "simpa_indicator_results", [col])

    op.create_table(
        "simpa_ai_syntheses",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analytics_run_id", UUID, sa.ForeignKey("simpa_analytics_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ai_job_id", UUID, sa.ForeignKey("core_ai_jobs.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("source_snapshot_sha256", sa.String(64), nullable=False),
        sa.Column("review_status", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("reviewer_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("reviewed_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", TS, nullable=True),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("review_status IN ('pending','accepted','rejected')", name="ck_simpa_ai_synthesis_review"),
    )
    for col in ("organization_id", "workspace_id", "analytics_run_id", "ai_job_id"):
        op.create_index(f"ix_simpa_ai_syntheses_{col}", "simpa_ai_syntheses", [col])

    prompt_id = uid("prompt", "simpa.monitoring.synthesis")
    version_id = uid("prompt-version", "simpa.monitoring.synthesis:1")
    schema = {
        "type": "object",
        "required": ["executive_summary", "evidence_quality", "attention_points", "limitations", "human_review_required"],
        "properties": {
            "executive_summary": {"type": "string"},
            "evidence_quality": {"type": "string"},
            "attention_points": {"type": "array"},
            "limitations": {"type": "array"},
            "human_review_required": {"type": "boolean"},
        },
    }
    system_template = (
        "You are the SIMPA evidence-synthesis component inside the ISI platform. "
        "Use only the supplied monitoring snapshot. Do not diagnose people, determine eligibility, assign benefits, "
        "make institutional decisions, invent missing facts, or infer social-risk levels from evidence-quality metrics. "
        "Explicitly state limitations when evidence is absent, draft, weak, incomplete or lacks provenance. "
        "Return only JSON conforming to the requested schema. human_review_required must be true."
    )
    user_template = "SIMPA monitoring evidence snapshot: {input}"
    checksum = hashlib.sha256((system_template + "\n" + user_template + "\n" + json.dumps(schema, sort_keys=True)).encode("utf-8")).hexdigest()
    prompts = sa.table("core_ai_prompts", sa.column("id", UUID), sa.column("prompt_key", sa.String), sa.column("product_scope", sa.String), sa.column("title", sa.String), sa.column("purpose", sa.String), sa.column("is_active", sa.Boolean))
    versions = sa.table("core_ai_prompt_versions", sa.column("id", UUID), sa.column("prompt_id", UUID), sa.column("version_no", sa.Integer), sa.column("system_template", sa.Text), sa.column("user_template", sa.Text), sa.column("output_schema", sa.JSON), sa.column("checksum", sa.String), sa.column("status", sa.String))
    op.bulk_insert(prompts, [{"id": prompt_id, "prompt_key": "simpa.monitoring.synthesis", "product_scope": "SIMPA", "title": "SIMPA monitoring evidence synthesis", "purpose": "Evidence-bounded decision support requiring human review", "is_active": True}])

    # Alembic offline SQL rendering cannot literalize Python dicts for JSON columns.
    # Bind the serialized schema as text and cast explicitly to JSON so this seed
    # is valid in both offline (--sql) and online PostgreSQL migration modes.
    op.execute(
        sa.text(
            """
            INSERT INTO core_ai_prompt_versions
                (id, prompt_id, version_no, system_template, user_template, output_schema, checksum, status)
            VALUES
                (:id, :prompt_id, 1, :system_template, :user_template, CAST(:output_schema AS JSON), :checksum, 'active')
            """
        ).bindparams(
            sa.bindparam("id", value=version_id, type_=UUID),
            sa.bindparam("prompt_id", value=prompt_id, type_=UUID),
            sa.bindparam("system_template", value=system_template, type_=sa.Text()),
            sa.bindparam("user_template", value=user_template, type_=sa.Text()),
            sa.bindparam("output_schema", value=json.dumps(schema, sort_keys=True), type_=sa.Text()),
            sa.bindparam("checksum", value=checksum, type_=sa.String()),
        )
    )


def downgrade() -> None:
    op.execute("DELETE FROM core_ai_prompt_versions WHERE prompt_id IN (SELECT id FROM core_ai_prompts WHERE prompt_key='simpa.monitoring.synthesis')")
    op.execute("DELETE FROM core_ai_prompts WHERE prompt_key='simpa.monitoring.synthesis'")
    for col in ("ai_job_id", "analytics_run_id", "workspace_id", "organization_id"):
        op.drop_index(f"ix_simpa_ai_syntheses_{col}", table_name="simpa_ai_syntheses")
    op.drop_table("simpa_ai_syntheses")
    for col in ("methodology_id", "indicator_id", "analytics_run_id", "workspace_id", "organization_id"):
        op.drop_index(f"ix_simpa_indicator_results_{col}", table_name="simpa_indicator_results")
    op.drop_table("simpa_indicator_results")
    op.drop_index("ix_simpa_analytics_runs_monitoring_cycle_id", table_name="simpa_analytics_runs")
    op.drop_index("ix_simpa_analytics_runs_workspace_id", table_name="simpa_analytics_runs")
    op.drop_index("ix_simpa_analytics_runs_organization_id", table_name="simpa_analytics_runs")
    op.drop_table("simpa_analytics_runs")
    op.drop_index("ix_simpa_indicator_methodologies_indicator_id", table_name="simpa_indicator_methodologies")
    op.drop_table("simpa_indicator_methodologies")
