from pathlib import Path

from src.platform.data.models import DataAuditEvent, DataQualityResult, DataSource, DataSourceVersion, IngestionJob


def test_shared_data_tables_are_explicit_and_tenant_scoped():
    assert DataSource.__tablename__ == "core_data_sources"
    assert DataSourceVersion.__tablename__ == "core_data_source_versions"
    assert IngestionJob.__tablename__ == "core_ingestion_jobs"
    assert DataQualityResult.__tablename__ == "core_data_quality_results"
    assert DataAuditEvent.__tablename__ == "core_data_audit_events"
    source_columns = set(DataSource.__table__.columns.keys())
    assert {"organization_id", "workspace_id", "product_code"} <= source_columns
    version_columns = set(DataSourceVersion.__table__.columns.keys())
    assert {"sha256", "storage_key", "version_no", "organization_id", "workspace_id", "product_code"} <= version_columns


def test_platform_model_registry_registers_shared_data_models():
    text = Path("src/platform/models.py").read_text()
    assert "src.platform.data.models" in text
