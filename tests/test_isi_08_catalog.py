from src.domains.simpa.catalog import DIMENSION_CATALOG, SOURCE_TYPE_CATALOG, INDICATOR_CATALOG


def test_simpa_catalog_is_source_derived_conceptual_foundation():
    assert len(DIMENSION_CATALOG) == 9
    assert len(SOURCE_TYPE_CATALOG) == 9
    assert len(INDICATOR_CATALOG) == 15
    assert len({x["code"] for x in DIMENSION_CATALOG}) == 9
    assert len({x["code"] for x in SOURCE_TYPE_CATALOG}) == 9
    assert len({x["code"] for x in INDICATOR_CATALOG}) == 15
    assert {x["dimension_code"] for x in INDICATOR_CATALOG} <= {x["code"] for x in DIMENSION_CATALOG}


def test_catalog_does_not_reintroduce_retired_cosmos_brand():
    text = repr((DIMENSION_CATALOG, SOURCE_TYPE_CATALOG, INDICATOR_CATALOG)).upper()
    assert "COSMOS" not in text
