from __future__ import annotations

from typing import Any

import streamlit as st

from src.streamlit_app import data_api, simpa_analytics_api
from src.domains.simpa.statistical_xai import build_statistical_xai
from src.streamlit_app.xai_charts import coefficient_chart, render_chart


def _scope(shell: dict[str, Any]) -> tuple[str, str] | None:
    workspace = shell.get("workspace")
    if not workspace or shell.get("product", {}).get("code") != "SIMPA":
        return None
    return str(shell["organization"]["id"]), str(workspace["id"])


def _safe(call, *args, **kwargs):
    try:
        return call(*args, **kwargs)
    except Exception as exc:
        st.error(str(exc))
        return None


def _pct(value: float | int | None) -> str:
    return f"{float(value or 0) * 100:.0f}%"


def _eligible_artifacts(token: str, organization_id: str, workspace_id: str) -> list[dict]:
    items: list[dict] = []
    eligible_snapshot_ids: set[str] = set()
    datasets = (
        _safe(
            data_api.list_analytical_datasets,
            token,
            organization_id=organization_id,
            product_code="SIMPA",
            workspace_id=workspace_id,
        )
        or []
    )
    for dataset in datasets:
        snapshots = (
            _safe(
                data_api.list_analytical_snapshots,
                token,
                dataset_id=dataset["id"],
                organization_id=organization_id,
                product_code="SIMPA",
                workspace_id=workspace_id,
            )
            or []
        )
        eligible = [
            row for row in snapshots if row.get("state") in {"VALIDATED", "FROZEN"} and not row.get("invalidated")
        ]
        eligible_snapshot_ids.update(row["id"] for row in eligible)
        items.extend({"type": "snapshot", "id": row["id"], "fingerprint": row["fingerprint"]} for row in eligible)
    features = (
        _safe(
            data_api.list_analytical_features,
            token,
            organization_id=organization_id,
            product_code="SIMPA",
            workspace_id=workspace_id,
        )
        or []
    )
    for feature in features:
        versions = (
            _safe(
                data_api.list_analytical_feature_versions,
                token,
                feature_id=feature["id"],
                organization_id=organization_id,
                product_code="SIMPA",
                workspace_id=workspace_id,
            )
            or []
        )
        items.extend(
            {"type": "feature_version", "id": row["id"], "fingerprint": row["fingerprint"]}
            for row in versions
            if row.get("state") in {"GOVERNED", "FROZEN"}
            and not row.get("invalidated")
            and len(row.get("snapshot_inputs") or []) == 1
            and row["snapshot_inputs"][0].get("snapshot_id") in eligible_snapshot_ids
        )
    return items


def render_simpa_analytics(*, token: str, shell: dict[str, Any]) -> None:
    scope = _scope(shell)
    st.markdown('<div class="isi-eyebrow">SIMPA · Analitika + AI</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">Monitoring zasnovan na dokazima</h1>', unsafe_allow_html=True)
    st.caption(
        "ISI-09 meri kvalitet i pokrivenost dokaza, primenjuje samo eksplicitno validirane metodologije i koristi AI isključivo kao lokalni decision-support uz human review."
    )
    if scope is None:
        st.info("SIMPA workspace nije izabran.")
        return
    organization_id, workspace_id = scope
    permissions = set(shell.get("product", {}).get("permission_codes", []))
    runs = _safe(simpa_analytics_api.runs, token, organization_id, workspace_id) or []

    artifacts = _eligible_artifacts(token, organization_id, workspace_id)
    selected_artifact = None
    snapshot = None
    if not artifacts:
        st.info("Nema validiranog governed analytical snapshot-a ili eligible feature verzije za analitiku.")
    else:
        selected_artifact = st.selectbox(
            "Governed analytical artefakt",
            artifacts,
            format_func=lambda row: f"{row['type']} · {row['id']} · {row['fingerprint']}",
        )
        snapshot = _safe(
            simpa_analytics_api.summary,
            token,
            organization_id,
            workspace_id,
            analytical_artifact_type=selected_artifact["type"],
            analytical_artifact_id=selected_artifact["id"],
        )
    if snapshot:
        cols = st.columns(4)
        cards = [
            ("Opservacije", snapshot.get("observation_count", 0)),
            ("Validirane", _pct(snapshot.get("validated_observation_ratio"))),
            ("Provenance", _pct(snapshot.get("provenance_coverage"))),
            ("Pokrivenost indikatora", _pct(snapshot.get("indicator_coverage"))),
        ]
        for col, (label, value) in zip(cols, cards):
            col.metric(label, value)
        st.progress(
            float(snapshot.get("evidence_quality_score", 0.0)),
            text=f"Kvalitet dokaza: {snapshot.get('evidence_quality_band', 'no_evidence')} · {_pct(snapshot.get('evidence_quality_score'))}",
        )
        st.caption(snapshot.get("semantic_notice", "Ovo nije skor socijalnog rizika."))

    st.markdown("### Metodološki status")
    st.caption("DRAFT = authored/test work, not institutionally validated.")
    st.caption("PROPOSED = controlled testing only, not validated or approved.")
    st.caption("VALIDATED = human-approved after the required deterministic reference gate.")
    st.caption("RETIRED = historical and reproducible, not eligible for new production calculations.")
    st.caption(
        "Reference-check state and fingerprints below are deterministic methodology evidence; they do not bypass governed production data."
    )
    st.caption("PASSED reference suite nije institucionalno odobrenje; PROPOSED ostaje različit od VALIDATED.")
    if snapshot:
        m1, m2, m3 = st.columns(3)
        m1.metric("Aktivni indikatori", snapshot.get("active_indicator_count", 0))
        m2.metric("Konceptualni", snapshot.get("conceptual_indicator_count", 0))
        m3.metric("Sa validiranom metodologijom", snapshot.get("validated_methodology_indicator_count", 0))
    methods = _safe(simpa_analytics_api.methodologies, token, organization_id, workspace_id) or []
    if methods:
        lifecycle = [
            {
                "indicator": item.get("indicator_code"),
                "version": item.get("version_no"),
                "lifecycle": item.get("status"),
                "computation": item.get("computation_type"),
                "reference_evidence_mode": item.get("reference_evidence_mode"),
                "contract_fingerprint": item.get("contract_fingerprint"),
                "reference_check": item.get("reference_check_status"),
                "reference_fingerprint": item.get("reference_check_fingerprint"),
                "proposed_at": item.get("proposed_at"),
                "approved_at": item.get("approved_at"),
                "retired_at": item.get("retired_at"),
            }
            for item in methods
        ]
        st.dataframe(lifecycle, use_container_width=True, hide_index=True)
        suite_rows = []
        case_rows = []
        for method in methods:
            suites = (
                _safe(
                    simpa_analytics_api.reference_suites,
                    token,
                    method["id"],
                    organization_id,
                    workspace_id,
                )
                or []
            )
            for suite in suites:
                suite_rows.append(
                    {
                        "indicator": method.get("indicator_code"),
                        "methodology_version": method.get("version_no"),
                        "suite_version": suite.get("version_no"),
                        "status": suite.get("status"),
                        "reference_dataset": suite.get("reference_dataset"),
                        "reference_dataset_version": suite.get("reference_dataset_version"),
                        "suite_fingerprint": suite.get("suite_fingerprint"),
                        "result_fingerprint": suite.get("result_fingerprint"),
                        "case_count": suite.get("case_count"),
                        "created_by": suite.get("created_by_membership_id"),
                        "executed_by": suite.get("executed_by_membership_id"),
                        "executed_at": suite.get("executed_at"),
                    }
                )
                case_rows.extend(
                    {
                        "suite_version": suite.get("version_no"),
                        "case_key": case.get("case_key"),
                        "case_index": case.get("case_index"),
                        "status": case.get("status"),
                        "case_fingerprint": case.get("case_fingerprint"),
                        "result_fingerprint": case.get("result_fingerprint"),
                    }
                    for case in suite.get("cases") or []
                )
        if suite_rows:
            st.markdown("#### Versionirani referentni suite-ovi")
            st.dataframe(suite_rows, use_container_width=True, hide_index=True)
            st.markdown("#### Referentni slučajevi")
            st.dataframe(case_rows, use_container_width=True, hide_index=True)
    else:
        st.info(
            "Nema draft, proposed, validated ili retired metodologija u analytics registru. SIMPA ne izmišlja formule niti automatski validira konceptualne indikatore."
        )
    st.caption("Detaljno tumacenje lifecycle-a, reference evidence-a, statistike, ogranicenja i recovery koraka nalazi se u SIMPA Help sekciji.")

    st.markdown("### Monitoring snapshot-i")
    if snapshot and selected_artifact is not None and "analysis.run" in permissions:
        if st.button("Sačuvaj trenutni monitoring snapshot", type="primary", use_container_width=True):
            result = _safe(
                simpa_analytics_api.create_run,
                token,
                organization_id=organization_id,
                workspace_id=workspace_id,
                analytical_artifact_type=selected_artifact["type"],
                analytical_artifact_id=selected_artifact["id"],
            )
            if result is not None:
                st.success("Monitoring snapshot je sačuvan.")
                st.rerun()
    if runs:
        compact = [
            {
                "id": item["id"],
                "artefakt": item.get("analytical_artifact_type"),
                "artifact_id": item.get("analytical_snapshot_id") or item.get("analytical_feature_version_id"),
                "fingerprint": item.get("analytical_artifact_fingerprint"),
                "kvalitet_dokaza": item["evidence_quality_score"],
                "validirane_opservacije": item["validated_observation_ratio"],
                "provenance": item["provenance_coverage"],
                "pokrivenost_indikatora": item["indicator_coverage"],
                "kreirano": item["created_at"],
            }
            for item in runs
        ]
        st.dataframe(compact, use_container_width=True, hide_index=True)
    else:
        st.info("Još nema sačuvanih analitičkih snapshot-a.")

    st.markdown("### Statistički metodološki ugovori i rezultati")
    st.caption("Statistički izlazi slede dokaze i indikatore, a prikazuju se pre AI interpretacije.")
    st.caption("PROPOSED = samo kontrolisano testiranje; VALIDATED = ljudski odobrena metodologija, ne champion niti automatska potvrda performansi.")
    st.warning("Statistical association or feature contribution does not by itself establish causal effect.")
    contracts = (
        _safe(simpa_analytics_api.statistical_model_contracts, token, organization_id, workspace_id) or []
    )
    statistical_results = (
        _safe(simpa_analytics_api.statistical_model_results, token, organization_id, workspace_id) or []
    )
    if contracts:
        contract_rows = []
        for item in contracts:
            specification = item.get("contract") or {}
            contract_rows.append(
                {
                    "analysis_key": item.get("analysis_key"),
                    "target_indicator": item.get("target_indicator_code"),
                    "target_methodology_version": item.get("target_methodology_version"),
                    "target_methodology_fingerprint": item.get("target_methodology_contract_fingerprint"),
                    "lifecycle": item.get("status"),
                    "target_semantic": item.get("target_semantic"),
                    "model_family": item.get("model_family"),
                    "features": ", ".join(specification.get("feature_fields") or []),
                    "confidence_level": specification.get("confidence_level"),
                    "covariance_type": specification.get("covariance_type"),
                    "contract_fingerprint": item.get("contract_fingerprint"),
                    "validation_evidence_reference": item.get("validation_evidence_reference"),
                }
            )
        st.dataframe(contract_rows, use_container_width=True, hide_index=True)
    else:
        st.info("Nema statističkih metodoloških ugovora.")

    executable_contracts = [item for item in contracts if item.get("status") in {"proposed", "validated"}]
    if executable_contracts and runs and "analysis.run" in permissions:
        selected_contract = st.selectbox(
            "Statistički ugovor za izvršenje",
            executable_contracts,
            format_func=lambda item: (
                f"{item.get('analysis_key')} · {item.get('target_indicator_code')} · "
                f"{item.get('status')} · v{item.get('version_no')}"
            ),
        )
        selected_statistical_run = st.selectbox(
            "Governed monitoring snapshot za statističko izvršenje",
            runs,
            format_func=lambda item: f"Snapshot {item['id'][:8]} · {item.get('analytical_artifact_type')}",
            key="simpa_statistical_run",
        )
        proposed = selected_contract.get("status") == "proposed"
        controlled_testing_ack = False
        if proposed:
            controlled_testing_ack = st.checkbox(
                "Potvrđujem da je ovo eksplicitno kontrolisano testiranje PROPOSED ugovora.",
                key="simpa_statistical_controlled_testing_ack",
            )
        if st.button(
            "Izvrši deterministički statistički model",
            use_container_width=True,
            disabled=proposed and not controlled_testing_ack,
        ):
            created = _safe(
                simpa_analytics_api.run_statistical_model,
                token,
                organization_id=organization_id,
                workspace_id=workspace_id,
                analytics_run_id=selected_statistical_run["id"],
                statistical_model_contract_id=selected_contract["id"],
                controlled_testing_ack=controlled_testing_ack,
            )
            if created is not None:
                st.success("Deterministički statistički rezultat je sačuvan kao nepromenljiv dokaz.")
                st.rerun()

    if statistical_results:
        for item in statistical_results:
            xai = build_statistical_xai(item)
            detail = item.get("result_detail") or {}
            identity = xai["model_identity"]
            with st.expander(
                f"Rezultat {item['id'][:8]} · contract v{item.get('statistical_contract_version_no')} · "
                f"production_eligible={item.get('production_eligible')}"
            ):
                st.markdown("**Model / cilj / uncertainty contract**")
                st.json(identity)
                st.caption(xai["coefficient_interpretation"])
                render_chart(st, coefficient_chart(item))
                st.dataframe(xai["coefficients"], use_container_width=True, hide_index=True)
                st.caption(xai["p_value_interpretation"])
                st.caption(xai["missing_data_interpretation"])
                st.markdown("**Fit / error metrics**")
                st.json(xai["metrics"])
                st.caption(xai["metrics_interpretation"])
                st.markdown("**Diagnostics**")
                st.json(xai["diagnostics"])
                st.caption(xai["diagnostics_interpretation"])
                st.markdown("**Calibration / error summary**")
                st.json(xai["calibration"])
                st.caption(xai["calibration_interpretation"])
                st.markdown("**Reproducibility / provenance**")
                st.json(xai["provenance"])
                st.caption(f"result_fingerprint={item.get('result_fingerprint') or '-'}")
                st.caption(xai["production_eligibility"]["interpretation"])
                st.markdown("**Unsupported / unavailable XAI states**")
                st.json(xai["unsupported"])
                st.warning(xai["non_causal_notice"])
                st.caption(f"Limitations: {xai['limitations']}")
                if not detail.get("coefficients"):
                    st.info("Stored result nema coefficient rows za prikaz.")
    else:
        st.info("Jos nema nepromenljivih statistickih rezultata u aktivnom workspace-u.")

    st.markdown("### Lokalna AI podržana sinteza")
    st.warning(
        "AI izlaz nije institucionalni zakljucak. Za osetljive SIMPA podatke provider je prinudno local-only, a rezultat zahteva human review."
    )
    st.caption(
        "23D prikazuje source/model/policy/prompt/failure/review provenance, ali ne menja shared AI champion/evaluation/promotion/fallback contract koji pripada ISI-25."
    )
    eligible_artifacts = {
        (("ANALYTICAL_SNAPSHOT" if item["type"] == "snapshot" else "ANALYTICAL_FEATURE_VERSION"), item["id"])
        for item in artifacts
    }
    governed_runs = [
        item
        for item in runs
        if (
            item.get("analytical_artifact_type"),
            item.get("analytical_snapshot_id") or item.get("analytical_feature_version_id"),
        )
        in eligible_artifacts
    ]
    if governed_runs and "analysis.run" in permissions:
        run_ids = [item["id"] for item in governed_runs]
        selected_run = st.selectbox(
            "Monitoring snapshot za sintezu", run_ids, format_func=lambda value: f"Snapshot {value[:8]}"
        )
        if st.button("Pokreni lokalnu SIMPA AI sintezu", use_container_width=True):
            result = _safe(
                simpa_analytics_api.create_synthesis,
                token,
                organization_id=organization_id,
                workspace_id=workspace_id,
                analytics_run_id=selected_run,
                sensitivity="sensitive",
            )
            if result is not None:
                st.success("AI sinteza je izvršena kroz shared gateway. Rezultat ostaje na human review-u.")
                st.rerun()

    syntheses = _safe(simpa_analytics_api.syntheses, token, organization_id, workspace_id) or []
    if not syntheses:
        st.info("Nema AI sinteza u aktivnom workspace-u.")
        return
    for item in syntheses:
        job = item.get("job", {})
        with st.expander(
            f"Sinteza {item['id'][:8]} · {job.get('status', 'unknown')} · review: {item.get('review_status')}"
        ):
            st.caption(
                f"provider={job.get('provider_name') or '-'} · model={job.get('model_name') or '-'} · policy={job.get('effective_provider_policy')} · prompt={job.get('prompt_key')} v{job.get('prompt_version')}"
            )
            st.caption(f"source_snapshot_sha256={item.get('source_snapshot_sha256') or '-'} · request_sha256={job.get('request_sha256') or '-'}")
            structured = job.get("structured_output")
            structured_output_state = "present" if structured else ("failed" if job.get("error_code") else "unavailable")
            st.caption(f"structured_output_state={structured_output_state} · job_status={job.get('status')} · human_review_status={job.get('human_review_status')} · review={item.get('review_status')}")
            if structured:
                st.markdown("**Sažetak**")
                st.write(structured.get("executive_summary", ""))
                st.markdown("**Kvalitet dokaza**")
                st.write(structured.get("evidence_quality", ""))
                points = structured.get("attention_points") or []
                if points:
                    st.markdown("**Tačke za stručnu pažnju**")
                    for point in points:
                        st.write(f"- {point}")
                limitations = structured.get("limitations") or []
                if limitations:
                    st.markdown("**Ograničenja**")
                    for limitation in limitations:
                        st.write(f"- {limitation}")
            elif job.get("error_message"):
                st.error(job.get("error_message"))
            else:
                st.caption("AI rezultat još nije dostupan.")
            if (
                item.get("review_status") == "pending"
                and job.get("status") in {"review_required", "succeeded"}
                and "analysis.run" in permissions
            ):
                note = st.text_area("Napomena review-a", key=f"simpa_review_note_{item['id']}")
                left, right = st.columns(2)
                if left.button("Prihvati kao pregledano", key=f"simpa_accept_{item['id']}", use_container_width=True):
                    result = _safe(
                        simpa_analytics_api.review_synthesis,
                        token,
                        synthesis_id=item["id"],
                        organization_id=organization_id,
                        workspace_id=workspace_id,
                        decision="accepted",
                        reviewer_note=note,
                    )
                    if result is not None:
                        st.rerun()
                if right.button("Odbaci", key=f"simpa_reject_{item['id']}", use_container_width=True):
                    result = _safe(
                        simpa_analytics_api.review_synthesis,
                        token,
                        synthesis_id=item["id"],
                        organization_id=organization_id,
                        workspace_id=workspace_id,
                        decision="rejected",
                        reviewer_note=note,
                    )
                    if result is not None:
                        st.rerun()


def render_ordo_analytics_placeholder() -> None:
    st.markdown('<div class="isi-eyebrow">ORDO · Analitika</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">ORDO analytics foundation</h1>', unsafe_allow_html=True)
    st.info(
        "ORDO domain analytics dolazi u ISI-11. SIMPA analytics modeli, metodologije i AI sinteze se ne koriste kao ORDO analitika."
    )
