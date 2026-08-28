from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa

revision = "20260828_0007"
down_revision = "20260828_0006"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)
NS = uuid.UUID("7f5a3d8c-30e4-4f11-9fbf-f99a5c7f7808")


def uid(kind: str, code: str) -> uuid.UUID:
    return uuid.uuid5(NS, f"{kind}:{code}")


DIMENSIONS = [
    ("SOCIAL_NEEDS", "Socijalne potrebe stanovništva", 10),
    ("POVERTY", "Siromaštvo i materijalna ugroženost", 20),
    ("FAMILY_CHILDREN_YOUTH", "Porodica, deca i mladi", 30),
    ("VIOLENCE_CRISIS", "Nasilje i krizne situacije", 40),
    ("OLDER_DISABLED", "Starije osobe i osobe sa invaliditetom", 50),
    ("SERVICE_ACCESS", "Dostupnost socijalnih usluga", 60),
    ("SYSTEM_CAPACITY", "Kapaciteti lokalnog sistema", 70),
    ("INTERSECTORAL_COOPERATION", "Međusektorska saradnja", 80),
    ("OUTCOMES_EFFECTS", "Rezultati i efekti usluga", 90),
]
SOURCE_TYPES = [
    ("LOCAL_GOVERNMENT", "Jedinica lokalne samouprave"),
    ("SOCIAL_WORK_CENTER", "Centar za socijalni rad"),
    ("SOCIAL_SERVICE_PROVIDER", "Pružalac usluga socijalne zaštite"),
    ("EDUCATION", "Obrazovanje"),
    ("HEALTH", "Zdravstvo"),
    ("EMPLOYMENT", "Zapošljavanje"),
    ("HOUSING", "Stanovanje"),
    ("CIVIL_SOCIETY", "Civilno društvo"),
    ("DEMOGRAPHY", "Demografija i statistika"),
]
INDICATORS = [
    ("new_client_entry_rate", "Stopa ulaska novih korisnika u sistem socijalne zaštite", "SOCIAL_NEEDS", "rate"),
    ("average_support_duration", "Prosečno trajanje korišćenja pojedinih prava i usluga", "SOCIAL_NEEDS", "duration"),
    ("repeat_intervention_rate", "Učestalost ponovljenih intervencija", "OUTCOMES_EFFECTS", "rate"),
    ("long_term_assistance_dependency_risk", "Rizik od dugotrajne zavisnosti od socijalne pomoći", "POVERTY", "risk_index"),
    ("territorial_social_risk_concentration", "Teritorijalna koncentracija socijalnih rizika", "SOCIAL_NEEDS", "index"),
    ("family_vulnerability_index", "Indeks porodične ranjivosti", "FAMILY_CHILDREN_YOUTH", "index"),
    ("child_wellbeing_risk_index", "Indeks dečje dobrobiti i ugroženosti", "FAMILY_CHILDREN_YOUTH", "index"),
    ("older_people_social_inclusion_index", "Indeks socijalne uključenosti starijih osoba", "OLDER_DISABLED", "index"),
    ("social_service_access_index", "Indeks dostupnosti socijalnih usluga", "SERVICE_ACCESS", "index"),
    ("preventive_crisis_intervention_ratio", "Odnos preventivnih i kriznih intervencija", "OUTCOMES_EFFECTS", "ratio"),
    ("local_social_service_coverage", "Obuhvat stanovništva lokalnim uslugama socijalne zaštite", "SERVICE_ACCESS", "rate"),
    ("community_service_development_index", "Indeks razvijenosti usluga u zajednici", "SERVICE_ACCESS", "index"),
    ("intersectoral_cooperation_index", "Indeks međusektorske saradnje", "INTERSECTORAL_COOPERATION", "index"),
    ("vulnerable_group_social_inclusion_index", "Indeks socijalne inkluzije posebno osetljivih grupa", "OUTCOMES_EFFECTS", "index"),
    ("investment_social_effect_ratio", "Odnos ulaganja lokalne samouprave i ostvarenih društvenih efekata", "SYSTEM_CAPACITY", "ratio"),
]


def upgrade() -> None:
    op.create_table(
        "simpa_dimensions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("code", sa.String(80), nullable=False, unique=True),
        sa.Column("name_sr", sa.String(260), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "simpa_source_types",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("code", sa.String(80), nullable=False, unique=True),
        sa.Column("name_sr", sa.String(260), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "simpa_indicator_definitions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("code", sa.String(140), nullable=False),
        sa.Column("name_sr", sa.String(400), nullable=False),
        sa.Column("dimension_code", sa.String(80), sa.ForeignKey("simpa_dimensions.code"), nullable=False),
        sa.Column("unit_hint", sa.String(80), nullable=False, server_default=""),
        sa.Column("methodology_status", sa.String(24), nullable=False, server_default="conceptual"),
        sa.Column("methodology_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("code", name="uq_simpa_indicator_definitions_code"),
        sa.CheckConstraint("methodology_status IN ('conceptual', 'validated', 'retired')", name="ck_simpa_indicator_methodology_status"),
    )
    op.create_index("ix_simpa_indicator_definitions_dimension_code", "simpa_indicator_definitions", ["dimension_code"])

    op.create_table(
        "simpa_local_system_profiles",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("jurisdiction_name", sa.String(300), nullable=False),
        sa.Column("jurisdiction_code", sa.String(80), nullable=False, server_default=""),
        sa.Column("reference_year", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("workspace_id", name="uq_simpa_local_system_profiles_workspace"),
    )
    op.create_index("ix_simpa_local_system_profiles_organization_id", "simpa_local_system_profiles", ["organization_id"])
    op.create_index("ix_simpa_local_system_profiles_workspace_id", "simpa_local_system_profiles", ["workspace_id"])

    op.create_table(
        "simpa_local_actors",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_type", sa.String(40), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("external_code", sa.String(120), nullable=False, server_default=""),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("workspace_id", "name", name="uq_simpa_local_actors_workspace_name"),
        sa.CheckConstraint("actor_type IN ('local_government','social_work_center','social_service_provider','education','health','employment','housing','civil_society','other')", name="ck_simpa_local_actors_type"),
    )
    op.create_index("ix_simpa_local_actors_organization_id", "simpa_local_actors", ["organization_id"])
    op.create_index("ix_simpa_local_actors_workspace_id", "simpa_local_actors", ["workspace_id"])

    op.create_table(
        "simpa_monitoring_cycles",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="planned"),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("workspace_id", "code", name="uq_simpa_monitoring_cycles_workspace_code"),
        sa.CheckConstraint("status IN ('planned','open','closed')", name="ck_simpa_monitoring_cycles_status"),
        sa.CheckConstraint("period_end >= period_start", name="ck_simpa_monitoring_cycles_period"),
    )
    op.create_index("ix_simpa_monitoring_cycles_organization_id", "simpa_monitoring_cycles", ["organization_id"])
    op.create_index("ix_simpa_monitoring_cycles_workspace_id", "simpa_monitoring_cycles", ["workspace_id"])

    op.create_table(
        "simpa_data_mappings",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("data_source_id", UUID, sa.ForeignKey("core_data_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type_code", sa.String(80), sa.ForeignKey("simpa_source_types.code"), nullable=False),
        sa.Column("mapping_schema", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("workspace_id", "data_source_id", name="uq_simpa_data_mappings_workspace_source"),
        sa.CheckConstraint("status IN ('draft','validated','retired')", name="ck_simpa_data_mappings_status"),
    )
    op.create_index("ix_simpa_data_mappings_organization_id", "simpa_data_mappings", ["organization_id"])
    op.create_index("ix_simpa_data_mappings_workspace_id", "simpa_data_mappings", ["workspace_id"])
    op.create_index("ix_simpa_data_mappings_data_source_id", "simpa_data_mappings", ["data_source_id"])
    op.create_index("ix_simpa_data_mappings_source_type_code", "simpa_data_mappings", ["source_type_code"])

    op.create_table(
        "simpa_indicator_observations",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("indicator_id", UUID, sa.ForeignKey("simpa_indicator_definitions.id"), nullable=False),
        sa.Column("monitoring_cycle_id", UUID, sa.ForeignKey("simpa_monitoring_cycles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_version_id", UUID, sa.ForeignKey("core_data_source_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("geography_code", sa.String(120), nullable=False, server_default=""),
        sa.Column("geography_label", sa.String(300), nullable=False, server_default=""),
        sa.Column("population_group", sa.String(220), nullable=False, server_default=""),
        sa.Column("value_numeric", sa.Float(), nullable=True),
        sa.Column("value_text", sa.String(500), nullable=False, server_default=""),
        sa.Column("quality_status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("provenance_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("quality_status IN ('draft','validated','rejected')", name="ck_simpa_indicator_observations_quality"),
        sa.CheckConstraint("value_numeric IS NOT NULL OR value_text <> ''", name="ck_simpa_indicator_observations_value"),
        sa.CheckConstraint("period_end IS NULL OR period_start IS NULL OR period_end >= period_start", name="ck_simpa_indicator_observations_period"),
    )
    for col in ("organization_id", "workspace_id", "indicator_id", "monitoring_cycle_id", "source_version_id"):
        op.create_index(f"ix_simpa_indicator_observations_{col}", "simpa_indicator_observations", [col])

    dim_table = sa.table("simpa_dimensions", sa.column("id", UUID), sa.column("code", sa.String), sa.column("name_sr", sa.String), sa.column("sort_order", sa.Integer), sa.column("active", sa.Boolean))
    op.bulk_insert(dim_table, [{"id": uid("dimension", code), "code": code, "name_sr": name, "sort_order": order, "active": True} for code, name, order in DIMENSIONS])
    source_table = sa.table("simpa_source_types", sa.column("id", UUID), sa.column("code", sa.String), sa.column("name_sr", sa.String), sa.column("active", sa.Boolean))
    op.bulk_insert(source_table, [{"id": uid("source", code), "code": code, "name_sr": name, "active": True} for code, name in SOURCE_TYPES])
    indicator_table = sa.table("simpa_indicator_definitions", sa.column("id", UUID), sa.column("code", sa.String), sa.column("name_sr", sa.String), sa.column("dimension_code", sa.String), sa.column("unit_hint", sa.String), sa.column("methodology_status", sa.String), sa.column("methodology_note", sa.Text), sa.column("active", sa.Boolean))
    op.bulk_insert(indicator_table, [{"id": uid("indicator", code), "code": code, "name_sr": name, "dimension_code": dim, "unit_hint": unit, "methodology_status": "conceptual", "methodology_note": "ISI-08 registry only; formula and validation are intentionally deferred to SIMPA analytics methodology.", "active": True} for code, name, dim, unit in INDICATORS])


def downgrade() -> None:
    for col in ("source_version_id", "monitoring_cycle_id", "indicator_id", "workspace_id", "organization_id"):
        op.drop_index(f"ix_simpa_indicator_observations_{col}", table_name="simpa_indicator_observations")
    op.drop_table("simpa_indicator_observations")
    op.drop_index("ix_simpa_data_mappings_source_type_code", table_name="simpa_data_mappings")
    op.drop_index("ix_simpa_data_mappings_data_source_id", table_name="simpa_data_mappings")
    op.drop_index("ix_simpa_data_mappings_workspace_id", table_name="simpa_data_mappings")
    op.drop_index("ix_simpa_data_mappings_organization_id", table_name="simpa_data_mappings")
    op.drop_table("simpa_data_mappings")
    op.drop_index("ix_simpa_monitoring_cycles_workspace_id", table_name="simpa_monitoring_cycles")
    op.drop_index("ix_simpa_monitoring_cycles_organization_id", table_name="simpa_monitoring_cycles")
    op.drop_table("simpa_monitoring_cycles")
    op.drop_index("ix_simpa_local_actors_workspace_id", table_name="simpa_local_actors")
    op.drop_index("ix_simpa_local_actors_organization_id", table_name="simpa_local_actors")
    op.drop_table("simpa_local_actors")
    op.drop_index("ix_simpa_local_system_profiles_workspace_id", table_name="simpa_local_system_profiles")
    op.drop_index("ix_simpa_local_system_profiles_organization_id", table_name="simpa_local_system_profiles")
    op.drop_table("simpa_local_system_profiles")
    op.drop_index("ix_simpa_indicator_definitions_dimension_code", table_name="simpa_indicator_definitions")
    op.drop_table("simpa_indicator_definitions")
    op.drop_table("simpa_source_types")
    op.drop_table("simpa_dimensions")
