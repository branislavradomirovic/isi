"""Customer definitions bind to existing ORDO specification authority; no fitting."""

from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select

from src.domains.ordo.analytics_models import OrdoIndicatorMethodology, OrdoStatisticalModelContract
from src.domains.ordo.models import OrdoIndicatorDefinition
from src.domains.ordo import analytics_service as service
from src.domains.ordo.statistical_contracts import (
    OrdoStatisticalFeatureSpecV1,
    CROSS_SECTIONAL_FAMILIES,
    PANEL_FAMILIES,
    RESPONSE_FAMILIES,
)

Text = Annotated[str, Field(min_length=1, max_length=1000)]


class StatisticalDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    analysis_key: str = Field(min_length=1, max_length=140)
    purpose: str = Field(min_length=1, max_length=5000)
    target_indicator_code: str = Field(min_length=1, max_length=140)
    target_semantic: Literal["continuous", "count", "proportion_rate"]
    analysis_structure: Literal["cross_sectional", "panel"]
    model_family: Literal[
        "linear_regression",
        "robust_regression",
        "poisson_glm",
        "negative_binomial_glm",
        "fractional_logit",
        "beta_regression",
        "fixed_effects",
        "mixed_effects",
        "hierarchical",
    ]
    response_family: Literal["gaussian", "poisson", "negative_binomial", "fractional", "beta"]
    features: tuple[OrdoStatisticalFeatureSpecV1, ...] = Field(min_length=1, max_length=100)
    analysis_window_start: date
    analysis_window_end: date
    analysis_as_of: date
    assumptions: tuple[Text, ...] = Field(min_length=1, max_length=50)
    required_diagnostics: tuple[Text, ...] = Field(min_length=1, max_length=50)
    limitations: tuple[Text, ...] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def compatible(self):
        families = (
            CROSS_SECTIONAL_FAMILIES[self.target_semantic]
            if self.analysis_structure == "cross_sectional"
            else PANEL_FAMILIES
        )
        if self.model_family not in families or self.response_family not in RESPONSE_FAMILIES[self.target_semantic]:
            raise ValueError("statistical_semantics_incompatible")
        if not self.analysis_window_start <= self.analysis_window_end <= self.analysis_as_of:
            raise ValueError("statistical_window_invalid")
        if len({f.feature_key for f in self.features}) != len(self.features):
            raise ValueError("statistical_feature_keys_duplicate")
        return self


class StatisticalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    organization_id: UUID
    workspace_id: UUID
    analytics_run_id: UUID
    reviewed_methodology_id: UUID
    definition: StatisticalDefinition


class StatisticalTransition(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    organization_id: UUID
    workspace_id: UUID
    reviewed_status: Literal["draft", "proposed", "validated"]
    reviewed_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    validation_note: str = Field(default="", max_length=5000)
    validation_evidence_reference: str = Field(default="", max_length=500)
    retirement_note: str = Field(default="", max_length=5000)


def create(session, *, body, actor_id):
    if actor_id is None:
        raise service.OrdoAnalyticsError("contract_actor_required")
    definition = body.definition.model_dump()
    method = session.scalar(
        select(OrdoIndicatorMethodology)
        .join(OrdoIndicatorDefinition, OrdoIndicatorDefinition.id == OrdoIndicatorMethodology.indicator_id)
        .where(
            OrdoIndicatorDefinition.code == definition["target_indicator_code"].strip().casefold(),
            OrdoIndicatorDefinition.active.is_(True),
            OrdoIndicatorMethodology.status == "validated",
        )
        .order_by(OrdoIndicatorMethodology.version_no.desc())
        .with_for_update()
    )
    if method is None or method.id != body.reviewed_methodology_id:
        raise service.OrdoAnalyticsError("statistical_reviewed_methodology_changed")
    return service.create_statistical_model_contract(
        session,
        organization_id=body.organization_id,
        workspace_id=body.workspace_id,
        analytics_run_id=body.analytics_run_id,
        actor_id=actor_id,
        contract_value={
            **definition,
            "target_methodology_id": method.id,
            "target_methodology_version": method.version_no,
            "target_methodology_fingerprint": service._methodology_fingerprint(method),
            "non_causal": True,
            "automatic_policy_recommendation": False,
        },
    )


def get(session, *, organization_id, workspace_id, record_id, lock=False):
    query = select(OrdoStatisticalModelContract).where(
        OrdoStatisticalModelContract.id == record_id,
        OrdoStatisticalModelContract.organization_id == organization_id,
        OrdoStatisticalModelContract.workspace_id == workspace_id,
    )
    row = session.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise service.OrdoAnalyticsError("statistical_contract_not_accessible")
    return row


def transition(session, *, record_id, body, action, actor_id):
    row = get(
        session, organization_id=body.organization_id, workspace_id=body.workspace_id, record_id=record_id, lock=True
    )
    if row.status != body.reviewed_status or row.contract_fingerprint != body.reviewed_fingerprint:
        raise service.OrdoAnalyticsError("statistical_review_changed")
    kwargs = dict(contract_id=row.id, actor_id=actor_id)
    if action == "propose":
        return service.propose_statistical_model_contract(session, **kwargs)
    if action == "validate":
        return service.validate_statistical_model_contract(
            session,
            **kwargs,
            validation_note=body.validation_note,
            validation_evidence_reference=body.validation_evidence_reference,
        )
    if action == "retire":
        return service.retire_statistical_model_contract(session, **kwargs, retirement_note=body.retirement_note)
    raise service.OrdoAnalyticsError("statistical_transition_invalid")


def metadata(row):
    names = [
        "id",
        "organization_id",
        "workspace_id",
        "analytics_run_id",
        "target_methodology_id",
        "target_methodology_version",
        "methodology_fingerprint",
        "input_snapshot_sha256",
        "analysis_key",
        "version_no",
        "status",
        "schema_version",
        "contract_fingerprint",
        "created_by_membership_id",
        "proposed_by_membership_id",
        "proposed_at",
        "approved_by_membership_id",
        "approved_at",
        "validation_note",
        "validation_evidence_reference",
        "retired_by_membership_id",
        "retired_at",
        "retirement_note",
        "created_at",
    ]
    result = {name: getattr(row, name) for name in names}
    result.update(
        definition=row.contract_json,
        fitting="NOT_IMPLEMENTED",
        numerical_results="NOT_PRESENT",
        binding_verification="REQUIRED_ON_PROPOSE_VALIDATE",
    )
    return result
