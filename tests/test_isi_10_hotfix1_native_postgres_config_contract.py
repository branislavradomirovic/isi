from pathlib import Path


def test_isi10_native_postgres_uses_database_factory_contract():
    source = Path("tests/test_isi_10_native_postgres.py").read_text()
    assert "from src.core.database import build_engine" in source
    assert "engine = build_engine()" in source
    assert "from src.core.config import settings" not in source
    assert "create_engine(settings.database_url)" not in source


def test_isi10_native_postgres_preserves_catalog_assertions():
    source = Path("tests/test_isi_10_native_postgres.py").read_text()
    for token in (
        '"ordo_pillars"',
        '"ordo_dimensions"',
        '"ordo_source_types"',
        '"ordo_indicator_definitions"',
        "methodology_status='conceptual'",
    ):
        assert token in source
