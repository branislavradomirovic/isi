from src.domains.ordo.catalog import PILLAR_CATALOG, DIMENSION_CATALOG, SOURCE_TYPE_CATALOG, INDICATOR_CATALOG

def test_ordo_catalog_shape():
    assert len(PILLAR_CATALOG) == 5
    assert len(DIMENSION_CATALOG) == 9
    assert len(SOURCE_TYPE_CATALOG) == 12
    assert len(INDICATOR_CATALOG) == 15
    assert len({x["code"] for x in INDICATOR_CATALOG}) == 15
    assert {x["pillar_code"] for x in INDICATOR_CATALOG} <= {x["code"] for x in PILLAR_CATALOG}
    assert {x["dimension_code"] for x in INDICATOR_CATALOG} <= {x["code"] for x in DIMENSION_CATALOG}
