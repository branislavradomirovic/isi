"""Existing analytical mutations validated against canonical request schemas."""
from urllib.parse import quote

from src.platform.data.schemas import (
    AnalyticalDatasetCreate, AnalyticalFeatureCreate, AnalyticalDatasetContractVersionCreate,
    AnalyticalDatasetContractActivationRequest, AnalyticalSnapshotCreate,
    AnalyticalFeatureVersionCreate, AnalyticalTransitionRequest, FeatureTransitionRequest,
)
from src.streamlit_app.api_client import request
from src.streamlit_app.data_api import _checked


def _id(value):
    return quote(str(value), safe='')


def _write(token, path, schema, scope, fields):
    payload = schema.model_validate({**fields, **scope}).model_dump(mode='json')
    return _checked(request('POST', '/api/v1/data/' + path, token=token, json=payload),
                    unavailable='Operacija je možda registrovana. Osvežite listu pre ponavljanja.')


def create_registry(token, *, kind, scope, fields):
    schema = {'dataset': AnalyticalDatasetCreate, 'feature': AnalyticalFeatureCreate}[kind]
    return _write(token, {'dataset': 'analytical-datasets', 'feature': 'analytical-features'}[kind], schema, scope, fields)


def list_dataset_contracts(token, *, dataset_id, scope):
    return _checked(request('GET', f'/api/v1/data/analytical-datasets/{_id(dataset_id)}/contract-versions',
                            token=token, params=scope), unavailable='Nije moguće učitati analitičke ugovore.')


def create_dataset_contract(token, *, dataset_id, scope, fields):
    return _write(token, f'analytical-datasets/{_id(dataset_id)}/contract-versions', AnalyticalDatasetContractVersionCreate, scope, fields)


def activate_dataset_contract(token, *, dataset_id, contract_id, scope):
    return _write(token, f'analytical-datasets/{_id(dataset_id)}/contract-versions/{_id(contract_id)}/activate', AnalyticalDatasetContractActivationRequest, scope, {})


def create_snapshot(token, *, dataset_id, scope, fields):
    return _write(token, f'analytical-datasets/{_id(dataset_id)}/snapshots', AnalyticalSnapshotCreate, scope, fields)


def create_feature_version(token, *, feature_id, scope, fields):
    return _write(token, f'analytical-features/{_id(feature_id)}/versions', AnalyticalFeatureVersionCreate, scope, fields)


def transition(token, *, kind, artifact_id, scope, revision, target_state):
    resource, schema = {'snapshot': ('analytical-snapshots', AnalyticalTransitionRequest),
                        'feature': ('analytical-feature-versions', FeatureTransitionRequest)}[kind]
    return _write(token, f'{resource}/{_id(artifact_id)}/transition', schema, scope,
                  dict(expected_revision=revision, target_state=target_state))
