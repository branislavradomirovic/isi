from pathlib import Path


def test_product_package_boundaries_remain_empty():
    for product in ("simpa", "ordo"):
        init_path = Path("src") / "domains" / product / "__init__.py"
        assert init_path.is_file(), init_path
        assert init_path.read_text().strip() == "", f"{init_path} must remain an empty domain boundary marker"


def test_simpa_catalog_is_imported_from_concrete_module():
    from src.domains.simpa.catalog import DIMENSION_CATALOG, INDICATOR_CATALOG, SOURCE_TYPE_CATALOG

    assert len(DIMENSION_CATALOG) == 9
    assert len(SOURCE_TYPE_CATALOG) == 9
    assert len(INDICATOR_CATALOG) == 15
