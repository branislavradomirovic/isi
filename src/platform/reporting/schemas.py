from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


ProductCode = Literal["SIMPA", "ORDO"]
SourceKind = Literal["analytics_run", "scenario_assessment", "extraction_request"]
ExportFormat = Literal["json", "markdown", "html"]


class ReportingScope(BaseModel):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: ProductCode


class EvidenceLink(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim_id: str = Field(pattern="^c[0-9]{1,4}$")
    result_id: uuid.UUID | None = None
    note: str = Field(min_length=3, max_length=2000)
    attested: Literal[True]

    @field_validator("attested", mode="before")
    @classmethod
    def explicit_attestation(cls, value):
        if value is not True:
            raise ValueError("Explicit human attestation required")
        return value

    @field_validator("note")
    @classmethod
    def nonblank_note(cls, value):
        if len(value.strip()) < 3:
            raise ValueError("Link explanation required")
        return value.strip()


class ReportGenerateRequest(ReportingScope):
    title: str = Field(min_length=3, max_length=500)
    report_type: str = Field(min_length=3, max_length=80)
    source_kind: SourceKind
    source_id: uuid.UUID
    evidence_link: EvidenceLink | None = None


class ReportVersionGenerateRequest(ReportingScope):
    source_kind: SourceKind
    source_id: uuid.UUID
    evidence_link: EvidenceLink | None = None


class ReportLifecycleRequest(ReportingScope):
    reviewed_status: Literal["draft", "in_review", "approved", "rejected", "published", "superseded"] | None = None
    reviewed_content_sha256: str | None = Field(default=None, pattern="^[a-f0-9]{64}$")
    reviewed_source_manifest_sha256: str | None = Field(default=None, pattern="^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def reviewed_evidence_requires_status(self):
        if (self.reviewed_content_sha256 or self.reviewed_source_manifest_sha256) and self.reviewed_status is None:
            raise ValueError("Reviewed status required with evidence hashes")
        return self


class ReportReviewRequest(ReportLifecycleRequest):
    decision: Literal["approved", "rejected"]
    note: str = Field(default="", max_length=4000)


class ReportExportRequest(ReportingScope):
    format: ExportFormat
