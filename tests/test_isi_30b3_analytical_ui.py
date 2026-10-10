from types import SimpleNamespace
from unittest.mock import Mock
import uuid

import pytest
from pydantic import ValidationError
from streamlit.testing.v1 import AppTest

from src.streamlit_app import data_analytical_api as api
from src.streamlit_app.data_analytical_workspace import eligible_snapshots

IDS=[str(uuid.UUID(int=i)) for i in range(1,9)]
SCOPE=dict(organization_id=IDS[0], product_code='SIMPA', workspace_id=IDS[1])
SNAP=dict(id=IDS[4], state='VALIDATED', revision=1, version_no=1, fingerprint='synthetic',
          lineage_mode='GOVERNED_OUTPUT_V1', dataset_contract_version_id=IDS[3], invalidated=False)


@pytest.mark.parametrize('state,invalidated,lineage,contract,allowed', [
    ('VALIDATED',False,'GOVERNED_OUTPUT_V1',IDS[3],True), ('FROZEN',False,'GOVERNED_OUTPUT_V1',IDS[3],True),
    ('DRAFT',False,'GOVERNED_OUTPUT_V1',IDS[3],False), ('VALIDATED',True,'GOVERNED_OUTPUT_V1',IDS[3],False),
    ('VALIDATED',False,'LEGACY_SOURCE_VERSION',None,False), ('VALIDATED',False,'GOVERNED_OUTPUT_V1',None,False)])
def test_snapshot_input_filter(state, invalidated, lineage, contract, allowed):
    rows=eligible_snapshots([{**SNAP,'state':state,'invalidated':invalidated,'lineage_mode':lineage,'dataset_contract_version_id':contract}])
    assert bool(rows)==allowed


@pytest.mark.parametrize('kind',['dataset','feature'])
@pytest.mark.parametrize('product',['SIMPA','ORDO'])
def test_typed_registry_scope(monkeypatch,kind,product):
    request=Mock(return_value=SimpleNamespace(status_code=201,json=lambda:{}))
    monkeypatch.setattr(api,'request',request)
    scope={**SCOPE,'product_code':product}
    api.create_registry('synthetic',kind=kind,scope=scope,fields=dict(code='sample',name='Sintetički',methodology_reference='synthetic-method',methodology_version='1',product_code='ORDO',workspace_id=IDS[7]))
    assert request.call_args.kwargs['json']['workspace_id']==SCOPE['workspace_id']
    assert request.call_args.kwargs['json']['product_code']==product


def test_invalid_contract_no_request(monkeypatch):
    request=Mock()
    monkeypatch.setattr(api,'request',request)
    with pytest.raises(ValidationError):
        api.create_dataset_contract('synthetic',dataset_id=IDS[2],scope=SCOPE,fields=dict(field_contract=[],temporal_mode='STATIC',granularity_key_fields=[]))
    request.assert_not_called()


def test_snapshot_payload_cannot_use_raw_source(monkeypatch):
    request=Mock()
    monkeypatch.setattr(api,'request',request)
    with pytest.raises(ValidationError):
        api.create_snapshot('synthetic',dataset_id=IDS[2],scope=SCOPE,fields=dict(source_version_ids=[IDS[6]],methodology_reference='s',methodology_version='1',build_reference='b'))
    request.assert_not_called()


def test_snapshot_pinned_contract_output(monkeypatch):
    request=Mock(return_value=SimpleNamespace(status_code=201,json=lambda:{}))
    monkeypatch.setattr(api,'request',request)
    fields=dict(dataset_contract_version_id=IDS[3],governed_output_ids=[IDS[6]],methodology_reference='s',methodology_version='1',build_reference='b')
    api.create_snapshot('synthetic',dataset_id=IDS[2],scope=SCOPE,fields=fields)
    assert request.call_args.kwargs['json']=={**fields,**SCOPE}


@pytest.mark.parametrize('kind,state', [('snapshot','VALIDATED'),('feature','GOVERNED')])
def test_revision_pinned_transition(monkeypatch,kind,state):
    request=Mock(return_value=SimpleNamespace(status_code=200,json=lambda:{}))
    monkeypatch.setattr(api,'request',request)
    api.transition('synthetic',kind=kind,artifact_id=IDS[4],scope=SCOPE,revision=3,target_state=state)
    assert request.call_args.kwargs['json']=={**SCOPE,'expected_revision':3,'target_state':state}


def ui_script():
    import streamlit as st
    from src.streamlit_app.data_analytical_workspace import render_analytical_authoring
    render_analytical_authoring(token='synthetic',shell=st.session_state['shell'],datasets=st.session_state['datasets'],features=st.session_state['features'],snapshots=st.session_state['snapshots'],feature_versions=st.session_state['feature_versions'])


def app(monkeypatch, permissions=('data.read','data.governance.manage'),snapshots=None):
    monkeypatch.setattr(api,'list_dataset_contracts',Mock(return_value=[]))
    monkeypatch.setattr(api,'create_registry',Mock(return_value=dict(id=IDS[2])))
    monkeypatch.setattr(api,'transition',Mock(return_value=dict(id=IDS[4])))
    at=AppTest.from_function(ui_script)
    at.session_state['shell']=dict(organization=dict(id=IDS[0]),product=dict(code='SIMPA',permission_codes=permissions),workspace=dict(id=IDS[1]))
    at.session_state['datasets']=[dict(id=IDS[2],name='Sintetički skup')]
    at.session_state['features']=[dict(id=IDS[5],name='Sintetički feature')]
    at.session_state['feature_versions']=[]
    at.session_state['snapshots']=[SNAP] if snapshots is None else snapshots
    at.run()
    assert not at.exception
    return at


def test_readonly_no_authoring(monkeypatch):
    at=app(monkeypatch,permissions=('data.read',))
    api.list_dataset_contracts.assert_not_called()
    assert not at.button and not at.checkbox


def test_registry_requires_confirmation(monkeypatch):
    at=app(monkeypatch)
    next(x for x in at.button if x.label=='Registruj analitički skup').click().run()
    api.create_registry.assert_not_called()
    assert at.error


def test_no_active_contract_no_snapshot_creation(monkeypatch):
    at=app(monkeypatch)
    assert not any(x.label=='Kreiraj snapshot' for x in at.button)
    assert any('aktivirajte analitički ugovor' in x.value for x in at.info)


def test_legacy_snapshot_not_promotable(monkeypatch):
    at=app(monkeypatch,snapshots=[{**SNAP,'lineage_mode':'LEGACY_SOURCE_VERSION'}])
    assert not any('Promeni stanje' in x.label for x in at.button)
    api.transition.assert_not_called()


def test_transition_confirmation_and_revision(monkeypatch):
    at=app(monkeypatch)
    next(x for x in at.button if x.label=='Promeni stanje na FROZEN').click().run()
    api.transition.assert_not_called()
    next(x for x in at.checkbox if x.label=='Potvrđujem ljudski pregled i prikazanu promenu stanja').check()
    next(x for x in at.button if x.label=='Promeni stanje na FROZEN').click().run()
    api.transition.assert_called_once_with('synthetic',scope=SCOPE,kind='snapshot',artifact_id=SNAP['id'],revision=1,target_state='FROZEN')


def test_revision_change_clears_confirmation(monkeypatch):
    at=app(monkeypatch)
    next(x for x in at.checkbox if x.label=='Potvrđujem ljudski pregled i prikazanu promenu stanja').check().run()
    at.session_state['snapshots']=[{**SNAP,'revision':2}]
    at.run()
    assert not next(x for x in at.checkbox if x.label=='Potvrđujem ljudski pregled i prikazanu promenu stanja').value


def test_legacy_feature_cannot_be_promoted(monkeypatch):
    at=app(monkeypatch,snapshots=[])
    at.session_state['feature_versions']=[dict(id=IDS[7],state='DRAFT',revision=1,invalidated=False,snapshot_inputs=[dict(snapshot_lineage_mode='LEGACY_SOURCE_VERSION',dataset_contract_version_id=None)])]
    at.run()
    assert not any('Promeni stanje' in x.label for x in at.button)
    api.transition.assert_not_called()


def test_feature_version_payload_pins_snapshot_inputs(monkeypatch):
    request=Mock(return_value=SimpleNamespace(status_code=201,json=lambda:{}))
    monkeypatch.setattr(api,'request',request)
    fields=dict(snapshot_ids=[IDS[4]],methodology_reference='synthetic',methodology_version='1')
    api.create_feature_version('synthetic',feature_id=IDS[5],scope=SCOPE,fields=fields)
    assert request.call_args.kwargs['json']=={**fields,**SCOPE}
