from types import SimpleNamespace
from unittest.mock import Mock
import uuid

import pytest
from pydantic import ValidationError
from streamlit.testing.v1 import AppTest

from src.streamlit_app import data_ingestion_api as api
from src.streamlit_app.data_ingestion_workspace import binding_chain, field_mapping

IDS = [str(uuid.UUID(int=i)) for i in range(1,8)]
SCOPE = dict(organization_id=IDS[0], product_code='SIMPA', workspace_id=IDS[1])


def contracts():
    return dict(connector=[dict(id=IDS[2], version_no=1, lifecycle_state='ACTIVE')],
        mapping=[dict(id=IDS[3], version_no=1, lifecycle_state='ACTIVE', connector_contract_version_id=IDS[2],
                      field_mapping=[dict(disposition='MAP', field_key='unit')])],
        records=[dict(id=IDS[4], version_no=1, lifecycle_state='ACTIVE', connector_contract_version_id=IDS[2], schema_mapping_version_id=IDS[3])],
        operations=[dict(id=IDS[5], version_no=1, lifecycle_state='ACTIVE', connector_contract_version_id=IDS[2], schema_mapping_version_id=IDS[3], record_governance_policy_version_id=IDS[4])])


def test_active_chain_pins_all_bindings():
    assert all(binding_chain(contracts()).values())
    values = contracts()
    values['mapping'][0]['connector_contract_version_id'] = IDS[6]
    chain = binding_chain(values)
    assert chain['connector'] and not any(chain[x] for x in ['mapping', 'records', 'operations'])


@pytest.mark.parametrize('resource', api.RESOURCES)
def test_draft_is_not_active(resource):
    values = contracts()
    values[resource][0]['lifecycle_state'] = 'DRAFT'
    assert binding_chain(values)[resource] is None


def test_explicit_mapping():
    value = field_mapping([dict(source_field='unit', logical_type='STRING', required=True, nullable=False,
                               disposition='MAP', field_key='unit', missing_values='NA\nNULL')])
    assert value['source_schema'][0]['ordinal'] == 1
    assert value['source_schema'][0]['missing_values'] == ['NA','NULL']
    assert value['field_mapping'] == [dict(source_field='unit', disposition='MAP', field_key='unit')]


@pytest.mark.parametrize('rows', [[], [dict(source_field='')],
    [dict(source_field='a',disposition='MAP',field_key='')],
    [dict(source_field='a',disposition='IGNORE',field_key='x')],
    [dict(source_field='a',disposition='MAP',field_key='x'),dict(source_field='b',disposition='MAP',field_key='X')]])
def test_invalid_mapping_rejected(rows):
    with pytest.raises(ValueError):
        field_mapping(rows)


@pytest.mark.parametrize('resource', api.RESOURCES)
@pytest.mark.parametrize('product', ['SIMPA','ORDO'])
def test_scoped_list_activation(monkeypatch, resource, product):
    request = Mock(return_value=SimpleNamespace(status_code=200, json=lambda: {}))
    monkeypatch.setattr(api,'request',request)
    scope={**SCOPE,'product_code':product}
    api.list_contracts('synthetic',source_id=IDS[6],resource=resource,scope=scope)
    assert request.call_args.kwargs['params'] == scope
    api.activate_contract('synthetic',source_id=IDS[6],resource=resource,version_id=IDS[2],scope=scope)
    assert request.call_args.kwargs['json'] == scope
    assert request.call_args.args[1].endswith('/'+IDS[2]+'/activate')


def test_create_validates_before_request(monkeypatch):
    request=Mock()
    monkeypatch.setattr(api,'request',request)
    with pytest.raises(ValidationError):
        api.create_contract('synthetic',source_id=IDS[6],resource='records',scope=SCOPE,fields={})
    request.assert_not_called()


def test_scope_overrides_untrusted_fields(monkeypatch):
    request=Mock(return_value=SimpleNamespace(status_code=201,json=lambda:{}))
    monkeypatch.setattr(api,'request',request)
    api.create_contract('synthetic',source_id=IDS[6],resource='connector',scope=SCOPE,
                        fields=dict(connector_kind='inbound',transport='batch',product_code='ORDO',workspace_id=IDS[6]))
    assert request.call_args.kwargs['json']['workspace_id']==SCOPE['workspace_id']
    assert request.call_args.kwargs['json']['product_code']=='SIMPA'


def ui_script():
    import streamlit as st
    from src.streamlit_app.data_ingestion_workspace import render_governed_ingestion
    render_governed_ingestion(token='synthetic',shell=st.session_state['shell'],source_id=st.session_state['source_id'])


def app(monkeypatch, permissions=('data.read','data.governance.manage','data.upload'), values=None):
    values = contracts() if values is None else values
    monkeypatch.setattr(api,'list_contracts',Mock(side_effect=lambda *a,resource,**k:values[resource]))
    monkeypatch.setattr(api,'create_contract',Mock(return_value=dict(id=IDS[6])))
    monkeypatch.setattr(api,'activate_contract',Mock(return_value=dict(id=IDS[6])))
    monkeypatch.setattr(api,'create_governed_run',Mock(return_value=dict(run=dict(id=IDS[6]))))
    at=AppTest.from_function(ui_script)
    at.session_state['shell']=dict(organization=dict(id=IDS[0]),product=dict(code='SIMPA',permission_codes=permissions),workspace=dict(id=IDS[1]))
    at.session_state['source_id']=IDS[6]
    at.run()
    assert not at.exception
    return at


def test_readonly_has_no_mutations(monkeypatch):
    at=app(monkeypatch,permissions=('data.read',))
    assert not at.checkbox and not at.text_input
    assert len(at.button)==1


def test_no_permission_calls_nothing(monkeypatch):
    at=app(monkeypatch,permissions=())
    api.list_contracts.assert_not_called()
    assert not at.button


def test_missing_chain_has_prerequisites(monkeypatch):
    at=app(monkeypatch,values={x:[] for x in api.RESOURCES})
    assert len(at.info)==4
    assert not at.number_input


def test_connector_requires_explicit_confirmation(monkeypatch):
    at=app(monkeypatch)
    next(x for x in at.button if x.label=='Registruj ugovor konektora').click().run()
    api.create_contract.assert_not_called()
    assert any('Označite potvrdu' in x.value for x in at.error)


def test_confirmed_connector_payload(monkeypatch):
    at=app(monkeypatch)
    next(x for x in at.checkbox if x.label=='Potvrđujem registraciju ugovora ulaznih datoteka').check()
    next(x for x in at.button if x.label=='Registruj ugovor konektora').click().run()
    api.create_contract.assert_called_once_with('synthetic',source_id=IDS[6],scope=SCOPE,resource='connector',fields=dict(connector_kind='inbound',transport='batch',configuration={},credential_reference='',capabilities=[]))


def test_thresholds_have_no_institutional_defaults(monkeypatch):
    at=app(monkeypatch)
    assert len(at.number_input)==5
    assert all(x.value is None for x in at.number_input)


def test_no_file_cannot_start_ingestion(monkeypatch):
    at=app(monkeypatch)
    next(x for x in at.button if x.label=='Pokreni kontrolisanu obradu').click().run()
    api.create_governed_run.assert_not_called()
    assert any('Izaberite datoteku' in x.value for x in at.error)


def test_api_unavailability_controlled(monkeypatch):
    from src.streamlit_app.api_client import ApiUnavailable
    at=app(monkeypatch)
    api.list_contracts.side_effect=ApiUnavailable('Servis nedostupan')
    at.run()
    assert not at.exception and at.error[0].value=='Servis nedostupan'


def test_empty_grid_cells_do_not_become_true_or_nan():
    result=field_mapping([dict(source_field='a', logical_type='STRING', required=float('nan'), nullable=float('nan'), disposition='IGNORE', field_key=float('nan'), missing_values=float('nan'))])
    assert result['source_schema'][0]['required'] is False
    assert result['source_schema'][0]['nullable'] is False
    assert result['source_schema'][0]['missing_values']==[]
    assert result['field_mapping'][0]['field_key'] is None


def test_upstream_contract_change_clears_downstream_draft(monkeypatch):
    values=contracts()
    at=app(monkeypatch,values=values)
    at.number_input[0].set_value(60).run()
    assert at.number_input[0].value==60
    values['records'][0]['id']=IDS[6]
    at.run()
    assert not at.exception
    assert at.number_input[0].value is None
    assert any('Kontrolisano učitavanje zahteva aktivan' in x.value for x in at.info)
    assert not any(x.label=='Pokreni kontrolisanu obradu' for x in at.button)
