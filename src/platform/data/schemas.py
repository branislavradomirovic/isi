from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UploadCreateRequest(BaseModel):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    source_name: str = Field(min_length=1, max_length=300)
    filename: str = Field(min_length=1, max_length=500)
    content_type: str = Field(default="application/octet-stream", max_length=200)
    content_base64: str = Field(min_length=1)


class VersionCreateRequest(BaseModel):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str
    filename: str = Field(min_length=1, max_length=500)
    content_type: str = Field(default="application/octet-stream", max_length=200)
    content_base64: str = Field(min_length=1)


class ScopeQuery(BaseModel):
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    product_code: str


class QualityResultResponse(BaseModel):
    check_code: str
    status: str
    message: str
    metric_name: str = ""
    metric_value: str = ""


class VersionResponse(BaseModel):
    id: uuid.UUID
    version_no: int
    original_filename: str
    extension: str
    content_type: str
    size_bytes: int
    sha256: str
    ingest_status: str
    detected_format: str
    row_count: int | None
    column_count: int | None
    sheet_count: int | None
    schema_fingerprint: str
    created_at: datetime
    quality: list[QualityResultResponse] = Field(default_factory=list)


class SourceSummaryResponse(BaseModel):
    id: uuid.UUID
    name: str
    source_kind: str
    product_code: str
    workspace_id: uuid.UUID
    status: str
    created_at: datetime
    latest_version: VersionResponse | None = None


class SourceDetailResponse(SourceSummaryResponse):
    versions: list[VersionResponse]


class IngestionJobResponse(BaseModel):
    id: uuid.UUID
    version_id: uuid.UUID
    job_type: str
    status: str
    backend: str
    progress: int
    attempts: int
    error_code: str
    error_message: str
    queued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class UploadResponse(BaseModel):
    source: SourceSummaryResponse
    version: VersionResponse
    job: IngestionJobResponse
    storage_reused: bool
