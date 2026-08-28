"""ordo analytics and ai

Revision ID: 20260828_0010
Revises: 20260828_0009
Create Date: 2026-08-28
"""
from __future__ import annotations

import hashlib
import json
import uuid

from alembic import op
import sqlalchemy as sa

revision = "20260828_0010"
down_revision = "20260828_0009"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)
NS = uuid.UUID("b6aa3f9f-4130-44b4-a772-7f174a6b2cd8")


def uid(kind: str, key: str) -> uuid.UUID:
    return uuid.uuid5(NS, f"{kind}:{key}")


def upgrade() -> None:
    op.create_table(
        "ordo_indicator_methodologies",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("indicator_id", UUID, sa.ForeignKey("ordo_indicator_definitions.id", ondelete="CASCADE"), nullable=False),
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
        sa.UniqueConstraint("indicator_id", "version_no", name="uq_ordo_indicator_methodology_version"),
        sa.CheckConstraint("status IN ('draft','validated','retired')", name="ck_ordo_indicator_methodology_status"),
        sa.CheckConstraint("computation_type IN ('direct_observation')", name="ck_ordo_indicator_methodology_computation"),
    )
    op.create_index("ix_ordo_indicator_methodologies_indicator_id", "ordo_indicator_methodologies", ["indicator_id"])

    op.create_table(
        "ordo_analytics_runs",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("monitoring_cycle_id", UUID, sa.ForeignKey("ordo_monitoring_cycles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="completed"),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("evidence_quality_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("validated_observation_ratio", sa.Float(), nullable=False, server_default="0"),
        sa.Column("provenance_coverage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("indicator_coverage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("dimension_coverage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("pillar_coverage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("status IN ('completed','failed')", name="ck_ordo_analytics_run_status"),
        sa.CheckConstraint("evidence_quality_score >= 0 AND evidence_quality_score <= 1", name="ck_ordo_analytics_run_quality_score"),
        sa.CheckConstraint("validated_observation_ratio >= 0 AND validated_observation_ratio <= 1", name="ck_ordo_analytics_run_validated_ratio"),
        sa.CheckConstraint("provenance_coverage >= 0 AND provenance_coverage <= 1", name="ck_ordo_analytics_run_provenance"),
        sa.CheckConstraint("indicator_coverage >= 0 AND indicator_coverage <= 1", name="ck_ordo_analytics_run_indicator_coverage"),
        sa.CheckConstraint("dimension_coverage >= 0 AND dimension_coverage <= 1", name="ck_ordo_analytics_run_dimension_coverage"),
        sa.CheckConstraint("pillar_coverage >= 0 AND pillar_coverage <= 1", name="ck_ordo_analytics_run_pillar_coverage"),
    )
    for col in ("organization_id", "workspace_id", "monitoring_cycle_id"):
        op.create_index(f"ix_ordo_analytics_runs_{col}", "ordo_analytics_runs", [col])

    op.create_table(
        "ordo_indicator_results",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analytics_run_id", UUID, sa.ForeignKey("ordo_analytics_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("indicator_id", UUID, sa.ForeignKey("ordo_indicator_definitions.id"), nullable=False),
        sa.Column("methodology_id", UUID, sa.ForeignKey("ordo_indicator_methodologies.id"), nullable=False),
        sa.Column("value_numeric", sa.Float(), nullable=True),
        sa.Column("value_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("unit", sa.String(80), nullable=False, server_default=""),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source_observation_ids", sa.JSON(), nullable=False),
        sa.Column("computation_trace", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="computed"),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("status IN ('computed','reviewed','rejected')", name="ck_ordo_indicator_result_status"),
        sa.CheckConstraint("quality_score >= 0 AND quality_score <= 1", name="ck_ordo_indicator_result_quality"),
    )
    for col in ("organization_id", "workspace_id", "analytics_run_id", "indicator_id", "methodology_id"):
        op.create_index(f"ix_ordo_indicator_results_{col}", "ordo_indicator_results", [col])

    op.create_table(
        "ordo_development_goals",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("title", sa.String(400), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("focus_area", sa.String(40), nullable=False, server_default="destination_development"),
        sa.Column("target_horizon", sa.Date(), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("workspace_id", "code", name="uq_ordo_development_goals_workspace_code"),
        sa.CheckConstraint("status IN ('draft','active','closed')", name="ck_ordo_development_goal_status"),
        sa.CheckConstraint("focus_area IN ('competitiveness','sustainability','inclusion','employment','quality_of_life','destination_development','custom')", name="ck_ordo_development_goal_focus"),
    )
    op.create_index("ix_ordo_development_goals_organization_id", "ordo_development_goals", ["organization_id"])
    op.create_index("ix_ordo_development_goals_workspace_id", "ordo_development_goals", ["workspace_id"])

    op.create_table(
        "ordo_scenarios",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("goal_id", UUID, sa.ForeignKey("ordo_development_goals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("assumptions", sa.JSON(), nullable=False),
        sa.Column("measures", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("workspace_id", "goal_id", "name", name="uq_ordo_scenarios_workspace_goal_name"),
        sa.CheckConstraint("status IN ('draft','review_ready','accepted','rejected')", name="ck_ordo_scenario_status"),
    )
    for col in ("organization_id", "workspace_id", "goal_id"):
        op.create_index(f"ix_ordo_scenarios_{col}", "ordo_scenarios", [col])

    op.create_table(
        "ordo_scenario_assessments",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scenario_id", UUID, sa.ForeignKey("ordo_scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analytics_run_id", UUID, sa.ForeignKey("ordo_analytics_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_snapshot", sa.JSON(), nullable=False),
        sa.Column("assessment", sa.JSON(), nullable=False),
        sa.Column("forecast_performed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(24), nullable=False, server_default="evidence_only"),
        sa.Column("reviewer_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("reviewed_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", TS, nullable=True),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("status IN ('evidence_only','reviewed','rejected')", name="ck_ordo_scenario_assessment_status"),
        sa.CheckConstraint("forecast_performed = false", name="ck_ordo_scenario_assessment_no_forecast"),
    )
    for col in ("organization_id", "workspace_id", "scenario_id", "analytics_run_id"):
        op.create_index(f"ix_ordo_scenario_assessments_{col}", "ordo_scenario_assessments", [col])

    op.create_table(
        "ordo_ai_syntheses",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analytics_run_id", UUID, sa.ForeignKey("ordo_analytics_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scenario_id", UUID, sa.ForeignKey("ordo_scenarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ai_job_id", UUID, sa.ForeignKey("core_ai_jobs.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("synthesis_type", sa.String(32), nullable=False, server_default="monitoring"),
        sa.Column("source_snapshot_sha256", sa.String(64), nullable=False),
        sa.Column("review_status", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("reviewer_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("reviewed_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", TS, nullable=True),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("synthesis_type IN ('monitoring','scenario_review')", name="ck_ordo_ai_synthesis_type"),
        sa.CheckConstraint("review_status IN ('pending','accepted','rejected')", name="ck_ordo_ai_synthesis_review"),
    )
    for col in ("organization_id", "workspace_id", "analytics_run_id", "scenario_id", "ai_job_id"):
        op.create_index(f"ix_ordo_ai_syntheses_{col}", "ordo_ai_syntheses", [col])

    policy_id = uid("policy", "ordo-decision-support-local")
    policies = sa.table(
        "core_ai_policy_profiles",
        sa.column("id", UUID),
        sa.column("policy_key", sa.String),
        sa.column("product_scope", sa.String),
        sa.column("sensitivity", sa.String),
        sa.column("provider_policy", sa.String),
        sa.column("allow_external", sa.Boolean),
        sa.column("require_human_review", sa.Boolean),
        sa.column("max_attempts", sa.Integer),
        sa.column("enabled", sa.Boolean),
    )
    op.bulk_insert(policies, [{
        "id": policy_id,
        "policy_key": "ordo-decision-support-local",
        "product_scope": "ORDO",
        "sensitivity": "internal",
        "provider_policy": "local_only",
        "allow_external": False,
        "require_human_review": True,
        "max_attempts": 2,
        "enabled": True,
    }])

    prompt_id = uid("prompt", "ordo.decision_support.synthesis")
    version_id = uid("prompt-version", "ordo.decision_support.synthesis:1")
    schema = {
        "type": "object",
        "required": [
            "executive_summary",
            "evidence_basis",
            "development_opportunities",
            "tradeoffs",
            "limitations",
            "next_evidence_needed",
            "forecast_performed",
            "human_review_required",
        ],
        "properties": {
            "executive_summary": {"type": "string"},
            "evidence_basis": {"type": "string"},
            "development_opportunities": {"type": "array", "items": {"type": "string"}},
            "tradeoffs": {"type": "array", "items": {"type": "string"}},
            "limitations": {"type": "array", "items": {"type": "string"}},
            "next_evidence_needed": {"type": "array", "items": {"type": "string"}},
            "forecast_performed": {"type": "boolean", "enum": [False]},
            "human_review_required": {"type": "boolean", "enum": [True]},
        },
    }
    system_template = (
        "You are the ORDO decision-support synthesis component inside the ISI platform. "
        "Use only supplied evidence and explicitly user-authored scenario assumptions. Distinguish evidence from assumptions. "
        "Do not invent facts, rank destinations, calculate unvalidated indicator formulas, predict visitor numbers, employment, investment, "
        "sustainability, inclusion or quality-of-life effects without a validated model, and do not make the development decision. "
        "Describe opportunities as questions or options for expert consideration, not guaranteed outcomes. "
        "Always state evidence limitations. forecast_performed must be false and human_review_required must be true. "
        "Return only JSON conforming to the requested schema."
    )
    user_template = "ORDO evidence and scenario context: {input}"
    checksum = hashlib.sha256((system_template + "\n" + user_template + "\n" + json.dumps(schema, sort_keys=True)).encode("utf-8")).hexdigest()
    prompts = sa.table(
        "core_ai_prompts",
        sa.column("id", UUID),
        sa.column("prompt_key", sa.String),
        sa.column("product_scope", sa.String),
        sa.column("title", sa.String),
        sa.column("purpose", sa.String),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(prompts, [{
        "id": prompt_id,
        "prompt_key": "ordo.decision_support.synthesis",
        "product_scope": "ORDO",
        "title": "ORDO evidence-bounded decision-support synthesis",
        "purpose": "Destination development synthesis and scenario review requiring human judgment",
        "is_active": True,
    }])

    # Keep JSON prompt-version seeding valid in Alembic offline (--sql) mode.
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
    op.execute("DELETE FROM core_ai_prompt_versions WHERE prompt_id IN (SELECT id FROM core_ai_prompts WHERE prompt_key='ordo.decision_support.synthesis')")
    op.execute("DELETE FROM core_ai_prompts WHERE prompt_key='ordo.decision_support.synthesis'")
    op.execute("DELETE FROM core_ai_policy_profiles WHERE policy_key='ordo-decision-support-local'")

    for col in ("ai_job_id", "scenario_id", "analytics_run_id", "workspace_id", "organization_id"):
        op.drop_index(f"ix_ordo_ai_syntheses_{col}", table_name="ordo_ai_syntheses")
    op.drop_table("ordo_ai_syntheses")

    for col in ("analytics_run_id", "scenario_id", "workspace_id", "organization_id"):
        op.drop_index(f"ix_ordo_scenario_assessments_{col}", table_name="ordo_scenario_assessments")
    op.drop_table("ordo_scenario_assessments")

    for col in ("goal_id", "workspace_id", "organization_id"):
        op.drop_index(f"ix_ordo_scenarios_{col}", table_name="ordo_scenarios")
    op.drop_table("ordo_scenarios")

    op.drop_index("ix_ordo_development_goals_workspace_id", table_name="ordo_development_goals")
    op.drop_index("ix_ordo_development_goals_organization_id", table_name="ordo_development_goals")
    op.drop_table("ordo_development_goals")

    for col in ("methodology_id", "indicator_id", "analytics_run_id", "workspace_id", "organization_id"):
        op.drop_index(f"ix_ordo_indicator_results_{col}", table_name="ordo_indicator_results")
    op.drop_table("ordo_indicator_results")

    for col in ("monitoring_cycle_id", "workspace_id", "organization_id"):
        op.drop_index(f"ix_ordo_analytics_runs_{col}", table_name="ordo_analytics_runs")
    op.drop_table("ordo_analytics_runs")

    op.drop_index("ix_ordo_indicator_methodologies_indicator_id", table_name="ordo_indicator_methodologies")
    op.drop_table("ordo_indicator_methodologies")
