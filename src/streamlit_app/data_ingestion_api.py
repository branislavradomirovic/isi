"""Fixed governed-ingestion resources, validated existing mutation contracts."""
from __future__ import annotations

from urllib.parse import quote

from src.platform.data.schemas import (
    ConnectorContractVersionCreate, ConnectorContractActivationRequest,
    SourceSchemaMappingVersionCreate, RecordGovernancePolicyVersionCreate,
    IngestionOperationalPolicyVersionCreate, IngestionRunCreate,
)
from src.streamlit_app.api_client import request
from src.streamlit_app.data_api import _checked

RESOURCES = {
    'connector': ('connector-contracts', ConnectorContractVersionCreate),
    'mapping': ('schema-mappings', SourceSchemaMappingVersionCreate),
    'records': ('record-policies', RecordGovernancePolicyVersionCreate),
    'operations': ('ingestion-operational-policy-versions', IngestionOperationalPolicyVersionCreate),
}


def _path(source_id: str, resource: str) -> str:
    route, _ = RESOURCES[resource]
    return f"/api/v1/data/sources/{quote(source_id, safe='')}/{route}"


def list_contracts(token: str, *, source_id: str, resource: str, scope: dict):
    return _checked(request('GET', _path(source_id, resource), token=token, params=scope),
                    unavailable='Nije moguće učitati ugovore izvora.')


def create_contract(token: str, *, source_id: str, resource: str, scope: dict, fields: dict):
    _, schema = RESOURCES[resource]
    payload = schema.model_validate({**fields, **scope}).model_dump(mode='json')
    suffix = '' if resource == 'operations' else '/versions'
    return _checked(request('POST', _path(source_id, resource) + suffix, token=token, json=payload),
                    unavailable='Ugovor možda već postoji. Osvežite listu pre ponavljanja.')


def activate_contract(token: str, *, source_id: str, resource: str, version_id: str, scope: dict):
    payload = ConnectorContractActivationRequest.model_validate(scope).model_dump(mode='json')
    return _checked(request('POST', _path(source_id, resource) + f"/{quote(version_id, safe='')}/activate",
                            token=token, json=payload), unavailable='Osvežite listu za potvrdu aktiviranja.')


def create_governed_run(token: str, *, source_id: str, scope: dict, fields: dict):
    payload = IngestionRunCreate.model_validate({**fields, **scope}).model_dump(mode='json')
    return _checked(request('POST', f"/api/v1/data/sources/{quote(source_id, safe='')}/ingestion-runs",
                            token=token, json=payload),
                    unavailable='Obrada je možda registrovana. Osvežite status pre ponavljanja.')
