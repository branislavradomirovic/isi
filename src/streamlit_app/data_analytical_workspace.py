"""Governed analytical registry/contract/snapshot/feature authoring UI."""
from pathlib import Path

import pandas as pd
import streamlit as st

from src.streamlit_app import data_api
from src.streamlit_app import data_analytical_api as api
from src.streamlit_app.data_ingestion_workspace import _write, TYPES, ERRORS

SNAPSHOT_NEXT = dict(DRAFT='VALIDATED', VALIDATED='FROZEN', FROZEN='RETIRED')
FEATURE_NEXT = dict(DRAFT='GOVERNED', GOVERNED='FROZEN', FROZEN='RETIRED')


def eligible_snapshots(snapshots):
    return [item for item in snapshots if item.get('state') in {'VALIDATED', 'FROZEN'}
            and not item.get('invalidated') and item.get('lineage_mode') == 'GOVERNED_OUTPUT_V1'
            and item.get('dataset_contract_version_id')]


def _method_fields(prefix=''):
    reference = st.text_input(prefix + 'Referenca metodologije', max_chars=500)
    version = st.text_input(prefix + 'Verzija metodologije', max_chars=120)
    return dict(methodology_reference=reference.strip(), methodology_version=version.strip())


def _registry(token, scope, kind, key):
    title = 'skupa podataka' if kind == 'dataset' else 'feature-a'
    with st.form(key):
        code = st.text_input('Jedinstvena oznaka', max_chars=120)
        name = st.text_input('Naziv', max_chars=240)
        description = st.text_area('Opis', max_chars=1000)
        method = _method_fields()
        confirmed = st.checkbox('Potvrđujem registraciju ' + title + ' i referencu metodologije')
        submitted = st.form_submit_button('Registruj analitički skup' if kind == 'dataset' else 'Registruj feature')
    if submitted:
        _write(lambda: api.create_registry(token, kind=kind, scope=scope,
               fields=dict(code=code.strip(), name=name.strip(), description=description, **method)), confirmed=confirmed)


def _contract(token, scope, dataset, contracts, key):
    with st.form(key):
        grid = st.data_editor(pd.DataFrame(columns=['field_key', 'logical_type', 'required', 'semantic_role']),
            hide_index=True, width='stretch', num_rows='dynamic', column_config={
                'field_key': st.column_config.TextColumn('Ključ polja', required=True),
                'logical_type': st.column_config.SelectboxColumn('Tip', options=TYPES, required=True),
                'required': st.column_config.CheckboxColumn('Obavezno', default=False),
                'semantic_role': st.column_config.SelectboxColumn('Uloga', options=['KEY','DIMENSION','MEASURE','ATTRIBUTE'], required=True)})
        mode = st.selectbox('Vremenski ugovor', ['STATIC','POINT_IN_TIME','PERIOD'])
        temporal = st.text_area('Vremenski ključevi po jedan u redu; redosled početak/kraj za PERIOD')
        granularity = st.text_area('Ključevi granularnosti po jedan u redu; obavezna KEY polja')
        st.caption('PRESERVE_MISSING: nema imputacije. STATIC nema vremenske ključeve; POINT_IN_TIME jedan, PERIOD dva obavezna DATE/DATETIME polja.')
        confirmed = st.checkbox('Potvrđujem analitički ugovor polja i vremenske semantike')
        submitted = st.form_submit_button('Registruj analitički ugovor')
    if submitted:
        rows = [{name:(None if pd.isna(value) else value) for name,value in row.items()} for row in grid.to_dict('records')]
        for row in rows:
            row['required'] = row.get('required') is True
        _write(lambda: api.create_dataset_contract(token, scope=scope, dataset_id=str(dataset['id']), fields=dict(
            field_contract=rows, temporal_mode=mode, temporal_key_fields=[x.strip() for x in temporal.splitlines() if x.strip()],
            granularity_key_fields=[x.strip() for x in granularity.splitlines() if x.strip()])), confirmed=confirmed)
    drafts = [item for item in contracts if item['lifecycle_state'] == 'DRAFT']
    if drafts:
        with st.form(key + '_activate'):
            selected = st.selectbox('Nacrt analitičkog ugovora', drafts, format_func=lambda x:f"v{x['version_no']} · {x['id']}")
            confirmed = st.checkbox('Potvrđujem aktiviranje izabranog analitičkog ugovora')
            submitted = st.form_submit_button('Aktiviraj analitički ugovor')
        if submitted:
            _write(lambda: api.activate_dataset_contract(token, scope=scope, dataset_id=str(dataset['id']), contract_id=str(selected['id'])), confirmed=confirmed)


def _load_outputs(token, scope):
    outputs, unavailable = [], 0
    for source in data_api.list_data_sources(token, **scope):
        for run in data_api.list_ingestion_runs(token, source_id=str(source['id']), **scope):
            if run['status'] != 'SUCCEEDED':
                continue
            try:
                output = data_api.get_run_governed_output(token, source_id=str(source['id']), run_id=str(run['id']), **scope)
            except data_api.AccessDenied:
                unavailable += 1
                continue
            outputs.append({**output, 'source_name': source['name']})
    return outputs, unavailable


def _snapshot(token, scope, dataset, contracts, key):
    active = next((x for x in contracts if x['lifecycle_state'] == 'ACTIVE'), None)
    if not active:
        st.info('Prvo registrujte i aktivirajte analitički ugovor za ovaj skup.')
        return
    key += '_' + str(active['id'])
    if st.button('Učitaj dostupne kontrolisane izlaze', key=key + '_load'):
        st.session_state.pop(key + '_outputs', None)
        try:
            outputs, unavailable = _load_outputs(token, scope)
            st.session_state[key + '_outputs'] = outputs
            if unavailable:
                st.warning(f'{unavailable} obrada nema dostupan kontrolisani izlaz. Uspešna inspekcija sama nije odobren analitički ulaz.')
        except ERRORS as exc:
            st.error(str(exc))
    outputs = st.session_state.get(key + '_outputs', [])
    if not outputs:
        st.caption('Učitajte dostupne izlaze. Samo registrovani kontrolisani izlazi mogu biti odabrani; backend ponovo proverava kvalitet i governance.')
        return
    with st.form(key):
        selected = st.multiselect('Kontrolisani izlazi snapshot-a', outputs,
            format_func=lambda x:f"{x['source_name']} · {x['id']} · {x['output_fingerprint']}")
        method = _method_fields()
        build = st.text_input('Referenca izrade snapshot-a', max_chars=500)
        confirmed = st.checkbox('Potvrđujem izabrane izlaze, aktivni ugovor i metodologiju snapshot-a')
        submitted = st.form_submit_button('Kreiraj snapshot')
    if submitted:
        _write(lambda: api.create_snapshot(token, scope=scope, dataset_id=str(dataset['id']), fields=dict(
            dataset_contract_version_id=str(active['id']), governed_output_ids=[str(x['id']) for x in selected],
            build_reference=build.strip(), **method)), confirmed=confirmed)


def _transition(token, scope, kind, items, key):
    next_states = SNAPSHOT_NEXT if kind == 'snapshot' else FEATURE_NEXT
    candidates = [item for item in items if item['state'] in next_states and not item.get('invalidated')
                  and (item.get('lineage_mode') == 'GOVERNED_OUTPUT_V1' if kind == 'snapshot' else
                       bool(item.get('snapshot_inputs')) and all(
                           edge.get('snapshot_lineage_mode') == 'GOVERNED_OUTPUT_V1' and edge.get('dataset_contract_version_id')
                           for edge in item['snapshot_inputs']))]
    if not candidates:
        st.caption('Nema artefakta podobnog za sledeći korak životnog ciklusa. Istorijski raw-source snapshot-i se ne promovišu.')
        return
    chosen = st.selectbox('Artefakt za promenu stanja', candidates,
        format_func=lambda x:f"{x['id']} · {x['state']} · rev{x['revision']}", key=key + '_selection')
    target = next_states[chosen['state']]
    with st.form(key + '_' + str(chosen['id']) + '_' + str(chosen['revision'])):
        st.caption(f"Trenutno {chosen['state']} → {target}; revizija {chosen['revision']}; otisak {chosen.get('fingerprint','—')}.")
        confirmed = st.checkbox('Potvrđujem ljudski pregled i prikazanu promenu stanja')
        submitted = st.form_submit_button('Promeni stanje na ' + target)
    if submitted:
        _write(lambda: api.transition(token, scope=scope, kind=kind, artifact_id=str(chosen['id']),
            revision=chosen['revision'], target_state=target), confirmed=confirmed)
        st.caption('Ako je revizija zastarela ili izvor povučen, backend odbija promenu. Osvežite registre i ponovo pregledajte dokaze.')


def _feature_version(token, scope, feature, snapshots, key):
    eligible = eligible_snapshots(snapshots)
    if not eligible:
        st.info('Verzija feature-a zahteva validiran ili zamrznut kontrolisani snapshot sa neprekinutom provenijencijom.')
        return
    with st.form(key):
        selected = st.multiselect('Ulazni snapshot-i feature-a', eligible,
            format_func=lambda x:f"{x['id']} · v{x['version_no']} · {x['state']} · {x['fingerprint']}")
        method = _method_fields()
        confirmed = st.checkbox('Potvrđujem ulazne snapshot-e i metodologiju feature verzije')
        submitted = st.form_submit_button('Kreiraj verziju feature-a')
    if submitted:
        _write(lambda: api.create_feature_version(token, scope=scope, feature_id=str(feature['id']),
            fields=dict(snapshot_ids=[str(x['id']) for x in selected], **method)), confirmed=confirmed)


def render_analytical_authoring(*, token, shell, datasets, features, snapshots, feature_versions):
    permissions = set(shell['product'].get('permission_codes', []))
    if 'data.read' not in permissions or 'data.governance.manage' not in permissions or not shell.get('workspace'):
        return
    scope = dict(organization_id=str(shell['organization']['id']), product_code=shell['product']['code'], workspace_id=str(shell['workspace']['id']))
    key = '_'.join(scope.values()) + '_analytical_authoring'
    with st.expander('Uputstvo: analitički skupovi i feature verzije'):
        st.markdown((Path(__file__).resolve().parents[2]/'docs/help/ISI-ANALYTICAL-AUTHORING-GUIDE.md').read_text())
    if st.button('Osveži analitičke registre',key=key+'_refresh'):
        for state_key in list(st.session_state):
            if state_key.startswith(key) and state_key.endswith('_outputs'):
                del st.session_state[state_key]
        st.rerun()
    with st.expander('Registracija analitičkog skupa'):
        _registry(token,scope,'dataset',key+'_dataset')
    if datasets:
        dataset = st.selectbox('Skup za ugovor i snapshot', datasets, format_func=lambda x:x['name'], key=key+'_dataset_select')
        dataset_key = key + '_' + str(dataset['id'])
        try:
            contracts = api.list_dataset_contracts(token,dataset_id=str(dataset['id']),scope=scope)
        except ERRORS as exc:
            st.error(str(exc))
            return
        with st.expander('Ugovor polja i aktiviranje'):
            st.dataframe([{field:item.get(field,'—') for field in ['id','version_no','lifecycle_state','temporal_mode','fingerprint']} for item in contracts], hide_index=True, width='stretch')
            _contract(token,scope,dataset,contracts,dataset_key+'_contract')
        with st.expander('Snapshot iz kontrolisanih izlaza'):
            _snapshot(token,scope,dataset,contracts,dataset_key+'_snapshot')
    with st.expander('Životni ciklus snapshot-a'):
        _transition(token,scope,'snapshot',snapshots,key+'_snapshot_transition')
    with st.expander('Registracija feature-a'):
        _registry(token,scope,'feature',key+'_feature')
    if features:
        feature = st.selectbox('Feature za verziju',features,format_func=lambda x:x['name'],key=key+'_feature_select')
        with st.expander('Verzija feature-a iz kontrolisanih snapshot-a'):
            _feature_version(token,scope,feature,snapshots,key+'_'+str(feature['id'])+'_version')
    with st.expander('Životni ciklus feature verzije'):
        _transition(token,scope,'feature',feature_versions,key+'_feature_transition')
    st.info('Registracija i promena stanja ne izmišljaju formulu niti predstavljaju automatsku institucionalnu potvrdu. Koristite odobrenu metodologiju i proverite lineage/quality.')
