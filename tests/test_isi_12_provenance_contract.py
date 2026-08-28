from pathlib import Path


def test_report_source_manifest_is_tenant_workspace_product_bound():
    text = Path("src/platform/reporting/service.py").read_text()
    for token in (
        "report_source_cross_tenant",
        "report_source_cross_workspace",
        "report_source_cross_product",
        "report_source_checksum_invalid",
    ):
        assert token in text


def test_domain_adapters_emit_only_their_own_product_scope():
    simpa = Path("src/domains/simpa/reporting_adapter.py").read_text()
    ordo = Path("src/domains/ordo/reporting_adapter.py").read_text()
    assert '"product_code": "SIMPA"' in simpa
    assert '"product_code": "ORDO"' not in simpa
    assert '"product_code": "ORDO"' in ordo
    assert '"product_code": "SIMPA"' not in ordo
    assert "src.domains.ordo" not in simpa
    assert "src.domains.simpa" not in ordo
