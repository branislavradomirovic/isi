from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field


ProductCode = Literal["SIMPA", "ORDO"]
SourceKind = Literal["analytics_run", "scenario_assessment"]
ExportFormat = Literal["json", "markdown", "html"]


class ReportingScope(BaseModel):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: ProductCode


class ReportGenerateRequest(ReportingScope):
    title: str = Field(min_length=3, max_length=500)
    report_type: str = Field(min_length=3, max_length=80)
    source_kind: SourceKind
    source_id: uuid.UUID


class ReportVersionGenerateRequest(ReportingScope):
    source_kind: SourceKind
    source_id: uuid.UUID


class ReportLifecycleRequest(ReportingScope):
    pass


class ReportReviewRequest(ReportingScope):
    decision: Literal["approved", "rejected"]
    note: str = Field(default="", max_length=4000)


class ReportExportRequest(ReportingScope):
    format: ExportFormat
