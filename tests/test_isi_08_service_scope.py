from pathlib import Path


def test_service_scope_and_shared_data_provenance_contract():
    text = Path("src/domains/simpa/service.py").read_text()
    assert 'Workspace.product_code == "SIMPA"' in text
    assert 'DataSource.product_code == "SIMPA"' in text
    assert 'DataSourceVersion.product_code == "SIMPA"' in text
    assert "source_version_id" in text
    assert "provenance_note" in text
