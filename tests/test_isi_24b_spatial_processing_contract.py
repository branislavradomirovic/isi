from pathlib import Path

import pytest
from pydantic import ValidationError

from src.domains.ordo.analytics_models import OrdoSpatialAggregationRun
from src.domains.ordo.spatial_processing import OrdoSpatialAggregationContractV1


def _contract(**changes):
    value = {
        "aggregation_rule": "sum",
        "required_source_fields": ["indicator_code", "quality_status", "spatial_unit_key", "spatial_unit_type", "boundary_version", "crs", "value_numeric"],
        "validated_quality_required": True, "missing_numeric_rule": "exclude_and_count",
        "weighted": False, "spatial_join_performed": False, "non_causal": True,
        "automatic_policy_recommendation": False,
    }
    value.update(changes)
    return value


def test_spatial_contract_locks_descriptive_identity_semantics():
    contract = OrdoSpatialAggregationContractV1.model_validate(_contract())
    assert contract.schema_version == "ORDO-SPATIAL-AGGREGATION-v1"
    assert not contract.weighted and not contract.spatial_join_performed
    assert contract.non_causal and not contract.automatic_policy_recommendation
    for change in ({"weighted": True}, {"spatial_join_performed": True}, {"aggregation_rule": "weighted_mean"}):
        with pytest.raises(ValidationError):
            OrdoSpatialAggregationContractV1.model_validate(_contract(**change))


def test_spatial_run_persistence_and_service_fail_closed_markers():
    columns = OrdoSpatialAggregationRun.__table__.columns
    for name in ("methodology_fingerprint", "boundary_version", "crs", "spatial_unit_type", "input_snapshot_sha256", "dropped_missing_numeric_count", "run_fingerprint", "forecast_performed"):
        assert name in columns
    service = Path("src/domains/ordo/analytics_service.py").read_text()
    for marker in ("spatial_identity_mismatch", "spatial_record_quality_not_validated", "spatial_unit_not_validated", "revalidate_analytics_run"):
        assert marker in service
    for forbidden in ("geopandas", "shapely", "geoalchemy", "st_distance", "st_intersects"):
        assert forbidden not in service.lower()
