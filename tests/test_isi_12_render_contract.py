import importlib.util
from pathlib import Path


def _module():
    path = Path("src/platform/reporting/render.py")
    spec = importlib.util.spec_from_file_location("isi12_render", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_renderers_are_deterministic_and_do_not_claim_pdf_support():
    module = _module()
    metadata = {"title": "QA", "product_code": "SIMPA", "report_type": "monitoring_summary", "version_no": 1, "status": "published", "content_sha256": "a" * 64}
    content = {"sections": [{"key": "e", "title": "Evidence", "metrics": {"coverage": 0.5}}]}
    manifest = [{"kind": "simpa_analytics_run", "id": "1", "product_code": "SIMPA", "checksum": "b" * 64}]
    assert module.render_json(metadata=metadata, content=content, source_manifest=manifest) == module.render_json(metadata=metadata, content=content, source_manifest=manifest)
    assert "# QA" in module.render_markdown(metadata=metadata, content=content, source_manifest=manifest)
    assert "<!doctype html>" in module.render_html(metadata=metadata, content=content, source_manifest=manifest)
    assert set(module.MIME_TYPES) == {"json", "markdown", "html"}
