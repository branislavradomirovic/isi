"""Typed customer forms for existing upload-backed governed ingestion."""
from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
from pydantic import ValidationError
import streamlit as st

from src.streamlit_app import data_ingestion_api as api
from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired

ERRORS = (AccessDenied, ApiUnavailable, AuthenticationRequired)
TYPES = ['STRING', 'INTEGER', 'NUMBER', 'BOOLEAN', 'DATE', 'DATETIME', 'JSON']


def binding_chain(contracts: dict[str, list[dict]]) -> dict[str, dict | None]:
    """Pin active matching chain; an orphaned active policy is never selectable."""
    connector = next((x for x in contracts['connector'] if x['lifecycle_state'] == 'ACTIVE'), None)
    mapping = next((x for x in contracts['mapping'] if x['lifecycle_state'] == 'ACTIVE'
                    and connector and str(x['connector_contract_version_id']) == str(connector['id'])), None)
    records = next((x for x in contracts['records'] if x['lifecycle_state'] == 'ACTIVE' and connector and mapping
                    and str(x['connector_contract_version_id']) == str(connector['id'])
                    and str(x['schema_mapping_version_id']) == str(mapping['id'])), None)
    operations = next((x for x in contracts['operations'] if x['lifecycle_state'] == 'ACTIVE' and connector and mapping and records
                    and str(x['connector_contract_version_id']) == str(connector['id'])
                    and str(x['schema_mapping_version_id']) == str(mapping['id'])
                    and str(x['record_governance_policy_version_id']) == str(records['id'])), None)
    return dict(connector=connector, mapping=mapping, records=records, operations=operations)


def field_mapping(rows: list[dict]) -> dict:
    """Explicit grid semantics; no guessing fields, types, units or missing values."""
    fields, mapping = [], []
    seen, keys = set(), set()
    for ordinal, raw_row in enumerate(rows, 1):
        row = {key: (None if pd.isna(value) else value) for key, value in raw_row.items()}
        source = str(row.get('source_field') or '').strip()
        key = str(row.get('field_key') or '').strip()
        disposition = row.get('disposition')
        if not source or source in seen:
            raise ValueError('Unesite jedinstvena imena izvornih kolona.')
        seen.add(source)
        if disposition == 'MAP':
            if not key or key.casefold() in keys:
                raise ValueError('Mapirane kolone zahtevaju jedinstvene ciljne ključeve.')
            keys.add(key.casefold())
        elif disposition != 'IGNORE' or key:
            raise ValueError('Za IGNORE ostavite ciljni ključ prazan.')
        fields.append(dict(ordinal=ordinal, source_field=source, logical_type=row.get('logical_type'),
                           required=row.get('required') is True, nullable=row.get('nullable') is True,
                           missing_values=str(row.get('missing_values') or '').splitlines()))
        mapping.append(dict(source_field=source, disposition=disposition, field_key=key if disposition == 'MAP' else None))
    if not fields:
        raise ValueError('Dodajte najmanje jednu kolonu.')
    return dict(source_schema=fields, field_mapping=mapping)


def _write(callback, *, confirmed: bool):
    if not confirmed:
        st.error('Označite potvrdu pre slanja.')
        return
    try:
        result = callback()
        st.success(f"Registrovano: {result.get('id', (result.get('run') or {}).get('id', '—'))}. Osvežite pregled.")
    except ValidationError:
        st.error('Proverite obavezna polja, formate identifikatora, tipove i međusobni odnos pragova. Zahtev nije poslat.')
    except ValueError as exc:
        st.error(str(exc))
    except ERRORS as exc:
        st.error(str(exc))
        st.warning('Osvežite stanje pre ponovnog slanja; promena je mogla biti registrovana.')


def _activation(token, params, resource, versions, key):
    drafts = [item for item in versions if item['lifecycle_state'] == 'DRAFT']
    if not drafts:
        st.caption('Nema nacrta za aktiviranje.')
        return
    with st.form(key + '_activate'):
        selected = st.selectbox('Nacrt za aktiviranje', drafts,
            format_func=lambda item: f"v{item['version_no']} · {item['id']}")
        confirmed = st.checkbox('Potvrđujem aktiviranje izabranog nacrta i njegovih vezanih ugovora')
        submitted = st.form_submit_button('Aktiviraj nacrt')
    if submitted:
        _write(lambda: api.activate_contract(token, **params, resource=resource, version_id=str(selected['id'])), confirmed=confirmed)


def _connector(token, params, key):
    st.caption('Ulazne datoteke · batch transport. Ovaj profil ne preuzima podatke sa mreže i ne čuva tajne.')
    with st.form(key):
        confirmed = st.checkbox('Potvrđujem registraciju ugovora ulaznih datoteka')
        submitted = st.form_submit_button('Registruj ugovor konektora')
    if submitted:
        _write(lambda: api.create_contract(token, **params, resource='connector', fields=dict(
            connector_kind='inbound', transport='batch', configuration={}, credential_reference='', capabilities=[])),
            confirmed=confirmed)


def _mapping(token, params, key, chain):
    connector = chain['connector']
    if not connector:
        st.info('Prvo aktivirajte ugovor konektora.')
        return
    with st.form(key):
        kind = st.selectbox('Oblik podataka', ['TABULAR', 'RECORD'])
        st.caption('Redosled kolona je redosled šeme. Nedostajuće tokene navedite po jedan u redu; prazan spisak ne izmišlja zamene.')
        grid = st.data_editor(pd.DataFrame(columns=['source_field', 'logical_type', 'required', 'nullable',
            'disposition', 'field_key', 'missing_values']), num_rows='dynamic', width='stretch', hide_index=True,
            column_config={
                'source_field': st.column_config.TextColumn('Izvorna kolona', required=True),
                'logical_type': st.column_config.SelectboxColumn('Tip', options=TYPES, required=True),
                'required': st.column_config.CheckboxColumn('Obavezna', default=False),
                'nullable': st.column_config.CheckboxColumn('Dozvoljeno prazno', default=False),
                'disposition': st.column_config.SelectboxColumn('Radnja', options=['MAP', 'IGNORE'], required=True),
                'field_key': st.column_config.TextColumn('Ciljni ključ'),
                'missing_values': st.column_config.TextColumn('Tokeni praznih vrednosti')})
        unexpected = st.selectbox('Neočekivane kolone', ['REJECT', 'IGNORE'])
        confirmed = st.checkbox('Potvrđujem šemu i mapiranje bez izmišljanja vrednosti')
        submitted = st.form_submit_button('Registruj mapiranje')
    if submitted:
        _write(lambda: api.create_contract(token, **params, resource='mapping', fields=dict(
            connector_contract_version_id=str(connector['id']), schema_kind=kind,
            unexpected_field_policy=unexpected, **field_mapping(grid.to_dict('records')))), confirmed=confirmed)


def _records(token, params, key, chain):
    connector, mapping = chain['connector'], chain['mapping']
    if not mapping:
        st.info('Prvo aktivirajte mapiranje vezano za aktivni konektor.')
        return
    fields = [x['field_key'] for x in mapping['field_mapping'] if x['disposition'] == 'MAP']
    with st.form(key):
        identity = st.multiselect('Ključevi identiteta zapisa', fields)
        st.caption('Nedostajući identitet i konflikti idu u karantin; identični duplikati se povezuju sa postojećim zapisom.')
        confirmed = st.checkbox('Potvrđujem identitet i pravila zapisa')
        submitted = st.form_submit_button('Registruj politiku zapisa')
    if submitted:
        _write(lambda: api.create_contract(token, **params, resource='records', fields=dict(
            connector_contract_version_id=str(connector['id']), schema_mapping_version_id=str(mapping['id']),
            identity_field_keys=identity)), confirmed=confirmed)


def _operations(token, params, key, chain):
    if not chain['records']:
        st.info('Prvo aktivirajte politiku zapisa za aktivno mapiranje.')
        return
    with st.form(key):
        st.caption('Unesite pragove odobrene operativne politike. Sistem nema institucionalne podrazumevane pragove.')
        warning = st.number_input('Upozorenje starosti (sekunde)', min_value=0, value=None)
        reject = st.number_input('Odbijanje starosti (sekunde)', min_value=0, value=None)
        missing_freshness = st.selectbox('Bez dokaza svežine', ['WARN', 'REJECT'])
        warning_ratio = st.number_input('Upozorenje udela karantina (0–1)', min_value=0.0, max_value=1.0, value=None)
        reject_ratio = st.number_input('Odbijanje udela karantina (0–1)', min_value=0.0, max_value=1.0, value=None)
        checks = st.text_area('Obavezne šifre provera, po jedna u redu')
        missing_checks = st.selectbox('Nedostajuće obavezne provere', ['WARN', 'REJECT'])
        backfill = st.checkbox('Politika dozvoljava backfill')
        replay = st.checkbox('Politika dozvoljava replay')
        attempts = st.number_input('Maksimalni broj retry pokušaja', min_value=1, value=None)
        terminal = st.text_area('Terminalne šifre grešaka, po jedna u redu')
        dead_letter = st.checkbox('Odbijena ocena prelazi u dead-letter')
        confirmed = st.checkbox('Potvrđujem odobrene operativne pragove i pravila')
        submitted = st.form_submit_button('Registruj operativnu politiku')
    if submitted:
        _write(lambda: api.create_contract(token, **params, resource='operations', fields=dict(
            connector_contract_version_id=str(chain['connector']['id']), schema_mapping_version_id=str(chain['mapping']['id']),
            record_governance_policy_version_id=str(chain['records']['id']),
            freshness_contract=dict(warning_after_seconds=warning, reject_after_seconds=reject, missing_evidence_action=missing_freshness),
            quality_contract=dict(required_check_codes=[x.strip() for x in checks.splitlines() if x.strip()],
                warning_quarantine_ratio=warning_ratio, reject_quarantine_ratio=reject_ratio, missing_required_check_action=missing_checks),
            backfill_contract=dict(backfill_allowed=backfill, replay_allowed=replay),
            dead_letter_contract=dict(max_retry_attempts=attempts, terminal_error_codes=[x.strip() for x in terminal.splitlines() if x.strip()],
                rejected_evaluation_to_dead_letter=dead_letter))), confirmed=confirmed)


def _binding_key(key: str, chain: dict, resources: tuple[str, ...]) -> str:
    return key + '_' + '_'.join(str((chain[name] or {}).get('id', 'missing')) for name in resources)


def _ingest(token, params, key, chain):
    if not all(chain.values()):
        st.info('Kontrolisano učitavanje zahteva aktivan usaglašen konektor, mapiranje, politiku zapisa i operativnu politiku.')
        return
    st.caption('Izabrana datoteka se obrađuje kroz prikazani aktivni lanac ugovora. Za oporavak istog zahteva koristite isti idempotency ključ i isti sadržaj.')
    with st.form(key):
        uploaded = st.file_uploader('Datoteka kontrolisane obrade', type=['csv', 'json', 'xlsx'], max_upload_size=16)
        idempotency = st.text_input('Idempotency ključ', max_chars=200)
        cursor = st.text_input('Novi kursor (opciono)', max_chars=1000)
        confirmed = st.checkbox('Potvrđujem učitavanje u aktivni lanac ugovora')
        submitted = st.form_submit_button('Pokreni kontrolisanu obradu')
    if submitted:
        if uploaded is None:
            st.error('Izaberite datoteku.')
            return
        _write(lambda: api.create_governed_run(token, **params, fields=dict(
            connector_contract_version_id=str(chain['connector']['id']), schema_mapping_version_id=str(chain['mapping']['id']),
            idempotency_key=idempotency, filename=uploaded.name, content_type=uploaded.type or 'application/octet-stream',
            content_base64=base64.b64encode(uploaded.getvalue()).decode('ascii'), cursor_after=cursor)), confirmed=confirmed)


def render_governed_ingestion(*, token: str, shell: dict, source_id: str):
    permissions = set(shell['product'].get('permission_codes', []))
    if 'data.read' not in permissions or not shell.get('workspace'):
        return
    scope = dict(organization_id=str(shell['organization']['id']), product_code=shell['product']['code'], workspace_id=str(shell['workspace']['id']))
    params = dict(source_id=source_id, scope=scope)
    key = '_'.join(scope.values()) + '_' + source_id + '_contracts'
    st.markdown('### Ugovori i kontrolisano učitavanje')
    with st.expander('Uputstvo: kontrolisano učitavanje'):
        st.markdown((Path(__file__).resolve().parents[2] / 'docs/help/ISI-GOVERNED-INGESTION-GUIDE.md').read_text())
    try:
        contracts = {resource: api.list_contracts(token, **params, resource=resource) for resource in api.RESOURCES}
    except ERRORS as exc:
        st.error(str(exc))
        return
    chain = binding_chain(contracts)
    st.dataframe([dict(Ugovor=resource, ID=item['id'] if item else 'Nedostaje aktivna vezana verzija') for resource, item in chain.items()], hide_index=True, width='stretch')
    if st.button('Osveži ugovore', key=key + '_refresh'):
        st.rerun()
    renderers = {'connector': _connector, 'mapping': _mapping, 'records': _records, 'operations': _operations}
    labels = dict(connector='1. Konektor', mapping='2. Mapiranje kolona', records='3. Identitet i politika zapisa', operations='4. Operativna politika')
    for resource, renderer in renderers.items():
        with st.expander(labels[resource]):
            st.dataframe([{k: item.get(k, '—') for k in ['id', 'version_no', 'lifecycle_state', 'fingerprint']} for item in contracts[resource]], width='stretch', hide_index=True)
            if 'data.governance.manage' in permissions:
                if resource == 'connector':
                    renderer(token, params, key + '_' + resource)
                else:
                    upstream = {'mapping': ('connector',), 'records': ('connector', 'mapping'),
                                'operations': ('connector', 'mapping', 'records')}[resource]
                    renderer(token, params, _binding_key(key + '_' + resource, chain, upstream), chain)
                _activation(token, params, resource, contracts[resource], key + '_' + resource)
    if 'data.upload' in permissions:
        with st.expander('5. Učitavanje kroz aktivne ugovore'):
            _ingest(token, params, _binding_key(key + '_ingest', chain, tuple(api.RESOURCES)), chain)
