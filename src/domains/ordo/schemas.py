from __future__ import annotations

import uuid
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ScopeQuery(BaseModel):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID


class DestinationProfileUpsertRequest(ScopeQuery):
    destination_name: str = Field(min_length=1, max_length=300)
    destination_code: str = Field(default="", max_length=80)
    destination_type: str = Field(default="", max_length=80)
    reference_year: int | None = Field(default=None, ge=1900, le=2200)
    notes: str = Field(default="", max_length=4000)


class AssetCreateRequest(ScopeQuery):
    asset_type: Literal["natural_resource", "cultural_heritage", "attraction", "experience", "infrastructure", "mobility", "accommodation", "gastronomy", "event", "knowledge", "entrepreneurship", "community", "other"]
    name: str = Field(min_length=1, max_length=300)
    external_code: str = Field(default="", max_length=120)
    location_label: str = Field(default="", max_length=300)
    description: str = Field(default="", max_length=4000)


class StakeholderCreateRequest(ScopeQuery):
    stakeholder_type: Literal["local_government", "tourism_organization", "heritage_institution", "protected_area_manager", "business", "entrepreneur", "education_research", "infrastructure_operator", "civil_society", "community", "other"]
    name: str = Field(min_length=1, max_length=300)
    external_code: str = Field(default="", max_length=120)


class CycleCreateRequest(ScopeQuery):
    code: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=300)
    period_start: date
    period_end: date
    status: Literal["planned", "open", "closed"] = "planned"

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_end < self.period_start:
            raise ValueError("period_end_before_start")
        return self


class MappingCreateRequest(ScopeQuery):
    data_source_id: uuid.UUID
    source_type_code: str = Field(min_length=1, max_length=80)
    mapping_schema: dict[str, Any] = Field(default_factory=dict)
    status: Literal["draft", "validated", "retired"] = "draft"
    notes: str = Field(default="", max_length=4000)


class ObservationCreateRequest(ScopeQuery):
    indicator_code: str = Field(min_length=1, max_length=140)
    monitoring_cycle_id: uuid.UUID | None = None
    source_version_id: uuid.UUID | None = None
    period_start: date | None = None
    period_end: date | None = None
    geography_code: str = Field(default="", max_length=120)
    geography_label: str = Field(default="", max_length=300)
    value_numeric: float | None = None
    value_text: str = Field(default="", max_length=500)
    quality_status: Literal["draft", "validated", "rejected"] = "draft"
    provenance_note: str = Field(default="", max_length=5000)

    @model_validator(mode="after")
    def validate_observation(self):
        if self.value_numeric is None and not self.value_text.strip():
            raise ValueError("observation_value_required")
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValueError("period_end_before_start")
        return self

class ReferenceEvidenceCreateRequest(ScopeQuery):
    evidence_key: str = Field(min_length=1, max_length=160)
    indicator_id: uuid.UUID | None = None
    source_version_id: uuid.UUID | None = None
    source_identity: str = Field(default="", max_length=300)
    source_version: str = Field(default="", max_length=160)
    external_identity: str = Field(default="", max_length=300)
    artifact_sha256: str = Field(default="", max_length=64)
    content_sha256: str = Field(default="", max_length=64)
    valid_from: date | None = None
    valid_to: date | None = None
    provenance_lineage: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_validity(self):
        if self.valid_from and self.valid_to and self.valid_to < self.valid_from:
            raise ValueError("valid_to_before_valid_from")
        return self


class ReferenceEvidenceLifecycleTransitionRequest(ScopeQuery):
    target_status: Literal["proposed", "validated", "retired"]
    note: str = Field(default="", max_length=5000)


class SpatialUnitCreateRequest(ScopeQuery):
    spatial_unit_key: str = Field(min_length=1, max_length=160)
    spatial_unit_type: Literal["national", "macro_region", "region", "local_government", "custom"]
    name: str = Field(min_length=1, max_length=300)
    boundary_source: str = Field(default="", max_length=300)
    boundary_version: str = Field(default="", max_length=160)
    geometry_id: str = Field(default="", max_length=300)
    crs: str = Field(default="", max_length=80)
    artifact_sha256: str = Field(default="", max_length=64)
    valid_from: date | None = None
    valid_to: date | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_validity(self):
        if self.valid_from and self.valid_to and self.valid_to < self.valid_from:
            raise ValueError("valid_to_before_valid_from")
        return self


class SpatialUnitLifecycleTransitionRequest(ScopeQuery):
    target_status: Literal["proposed", "validated", "retired"]
    note: str = Field(default="", max_length=5000)
