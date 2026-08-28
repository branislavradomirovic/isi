from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_shared_data_mapping_is_restricted_to_ordo_scope():
    text = (ROOT / "src/domains/ordo/service.py").read_text()
    assert 'DataSource.organization_id == organization_id' in text
    assert 'DataSource.workspace_id == workspace_id' in text
    assert 'DataSource.product_code == "ORDO"' in text
    assert 'DataSourceVersion.id == source_version_id' in text
