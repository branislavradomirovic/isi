"""Existing source/version inspection and bounded ingestion recovery UI."""
from __future__ import annotations

from typing import Any
from pathlib import Path

import streamlit as st

from src.streamlit_app import data_api
from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired

ERRORS = (AuthenticationRequired, AccessDenied, ApiUnavailable)


def _table(item: dict, fields: dict[str, str]) -> None:
    st.dataframe([{label: item.get(key, "—") for key, label in fields.items()}],
                 hide_index=True, use_container_width=True)


def _version_upload(token: str, params: dict, source: dict, key: str) -> None:
    with st.form(key + "_upload"):
        uploaded = st.file_uploader("Datoteka nove verzije", type=["csv", "json", "xlsx", "pdf", "docx", "txt"])
        confirmed = st.checkbox(f"Potvrđujem novu verziju izvora: {source['name']}")
        submitted = st.form_submit_button("Dodaj novu verziju")
    if submitted:
        if uploaded is None or not confirmed:
            st.error("Izaberite datoteku i potvrdite izvor nove verzije.")
            return
        try:
            result = data_api.create_source_version(token, **params, filename=uploaded.name,
                content_type=uploaded.type or "application/octet-stream", payload=uploaded.getvalue())
            st.success(f"Verzija {result['version']['version_no']} je registrovana. Osvežite prikaz za status obrade.")
        except ERRORS as exc:
            st.error(str(exc))
            st.warning("Operacija je možda registrovana pre prekida obrade. Osvežite istoriju verzija pre ponovnog slanja.")


def _retry(token: str, params: dict, run: dict, key: str) -> None:
    with st.form(key + "_retry"):
        confirmed = st.checkbox("Potvrđujem ponavljanje izabrane neuspele obrade")
        submitted = st.form_submit_button("Ponovi neuspelu obradu")
    if not submitted:
        return
    if not confirmed:
        st.error("Potvrdite ponavljanje neuspele obrade.")
        return
    try:
        fresh = data_api.get_ingestion_run(token, **params)
        if fresh.get("status") != "FAILED":
            st.warning("Status se promenio. Ponavljanje nije poslato; osvežite prikaz.")
            return
        result = data_api.retry_ingestion_run(token, **params)
        st.success(f"Zahtev za ponavljanje je registrovan: {result['status']}. Osvežite prikaz.")
    except ERRORS as exc:
        st.error(str(exc))
        st.warning("Osvežite status pre ponavljanja; zahtev je možda već registrovan.")


def render_source_inspection(*, token: str, shell: dict[str, Any], sources: list[dict]) -> None:
    permissions = set(shell['product'].get('permission_codes', []))
    if 'data.read' not in permissions or not shell.get('workspace'):
        return
    st.markdown('### Verzije, kvalitet i obrada izvora')
    with st.expander('Uputstvo: verzije, kvalitet i obrada'):
        st.markdown((Path(__file__).resolve().parents[2] / 'docs/help/ISI-DATA-WORKFLOWS-GUIDE.md').read_text())
    if not sources:
        st.info('Prvo učitajte izvor podataka. Ovde se zatim prikazuju njegove verzije i rezultati obrade.')
        return
    scope = dict(organization_id=str(shell['organization']['id']),
                 product_code=str(shell['product']['code']), workspace_id=str(shell['workspace']['id']))
    scope_key = '_'.join(scope.values())
    source = st.selectbox('Izvor za pregled', sources, format_func=lambda value: value['name'],
                          key=scope_key + '_source_inspection')
    params = {**scope, 'source_id': str(source['id'])}
    key = scope_key + '_' + str(source['id'])
    if st.button('Osveži verzije i obradu', key=key + '_refresh'):
        st.rerun()
    try:
        detail = data_api.get_source_detail(token, **params)
        runs = data_api.list_ingestion_runs(token, **params)
    except ERRORS as exc:
        st.error(str(exc))
        return
    versions = detail.get('versions', [])
    if versions:
        version = st.selectbox('Verzija izvora', versions,
            format_func=lambda item: f"v{item['version_no']} · {item['original_filename']} · {item['ingest_status']}",
            key=key + '_version')
        _table(version, {'id': 'ID verzije', 'version_no': 'Verzija', 'ingest_status': 'Status',
            'content_state': 'Stanje sadržaja', 'detected_format': 'Format', 'size_bytes': 'Bajtovi',
            'row_count': 'Redovi', 'column_count': 'Kolone', 'sha256': 'SHA-256 sadržaja',
            'schema_fingerprint': 'Otisak strukture', 'created_at': 'Registrovano'})
        st.markdown('**Provere kvaliteta izabrane verzije**')
        quality = version.get('quality', [])
        if quality:
            st.dataframe([{label: check.get(field, '—') for field, label in {
                'check_code': 'Provera', 'status': 'Status', 'message': 'Poruka',
                'metric_name': 'Metrika', 'metric_value': 'Vrednost'}.items()} for check in quality],
                hide_index=True, use_container_width=True)
        else:
            st.caption('Za ovu verziju još nema rezultata provere kvaliteta.')
    else:
        st.caption('Za izvor još nema registrovanih verzija.')
    if 'data.upload' in permissions:
        with st.expander('Nova verzija postojećeg izvora'):
            _version_upload(token, params, source, key)
    st.markdown('**Kontrolisane obrade izvora**')
    from src.streamlit_app.data_ingestion_workspace import render_governed_ingestion
    with st.expander('Priprema ugovora i kontrolisano učitavanje'):
        render_governed_ingestion(token=token, shell=shell, source_id=str(source['id']))
    from src.streamlit_app.data_governance_workspace import render_source_governance
    with st.expander('Governance izvora i karantin'):
        render_source_governance(token=token, shell=shell, source_id=str(source['id']))
    from src.streamlit_app.data_operations_workspace import render_ingestion_operations
    with st.expander('Operativni oporavak obrade'):
        render_ingestion_operations(token=token, shell=shell, source_id=str(source['id']), runs=runs)
    if not runs:
        st.caption('Nema kontrolisanih obrada. Osnovno učitavanje verzije samo po sebi ne kreira governed output.')
        return
    chosen = st.selectbox('Obrada za pregled', runs,
        format_func=lambda item: f"#{item['run_no']} · {item['status']} · {item['id']}", key=key + '_run')
    run_params = {**params, 'run_id': str(chosen['id'])}
    run_key = key + '_' + str(chosen['id'])
    try:
        run = data_api.get_ingestion_run(token, **run_params)
        _table(run, {'id': 'ID obrade', 'status': 'Status', 'execution_mode': 'Režim',
            'source_version_id': 'Verzija izvora', 'attempts': 'Pokušaji', 'error_code': 'Šifra greške',
            'error_message': 'Poruka', 'payload_sha256': 'Otisak sadržaja', 'request_fingerprint': 'Otisak zahteva',
            'connector_contract_version_id': 'Ugovor konektora', 'schema_mapping_version_id': 'Mapiranje',
            'operational_policy_version_id': 'Operativna politika'})
        if st.button('Status inspekcije', key=run_key + '_job'):
            job = data_api.get_inspection_job(token, job_id=str(run['inspection_job_id']), **scope)
            _table(job, {'status': 'Status', 'progress': 'Napredak (%)', 'attempts': 'Pokušaji',
                        'error_code': 'Šifra greške', 'error_message': 'Poruka'})
        if st.button('Prikaži ocenu obrade', key=run_key + '_evaluation'):
            evaluation = data_api.get_run_evaluation(token, **run_params)
            _table(evaluation, {'decision': 'Odluka', 'freshness_status': 'Svežina', 'quality_status': 'Kvalitet',
                'evidence_fingerprint': 'Otisak dokaza', 'evaluated_at': 'Ocenjeno'})
        if st.button('Prikaži kontrolisani izlaz', key=run_key + '_output'):
            output = data_api.get_run_governed_output(token, **run_params)
            _table(output, {'id': 'ID izlaza', 'evaluation_id': 'Ocena', 'record_count': 'Zapisi',
                'current_record_count': 'Aktuelni', 'duplicate_record_count': 'Duplikati',
                'quarantined_record_count': 'Karantin', 'superseded_record_count': 'Zamenjeni',
                'output_fingerprint': 'Otisak izlaza'})
        if run['status'] == 'FAILED' and 'data.upload' in permissions:
            _retry(token, run_params, run, run_key)
    except ERRORS as exc:
        st.error(str(exc))
        st.caption('Ocena ili kontrolisani izlaz mogu biti nedostupni dok obrada nije završena i prihvaćena.')
    st.info('Uspešna inspekcija ne znači validiranu metodologiju ili odobrenje za AI. Dalji rad koristi eksplicitno kontrolisani izlaz i analitički ugovor.')
