from __future__ import annotations

from typing import Any

import streamlit as st

from src.domains.ordo.analytics_xai import build_forecast_xai, build_scenario_xai
from src.streamlit_app import data_api, ordo_analytics_api


def _scope(shell: dict[str, Any]) -> tuple[str, str] | None:
    workspace = shell.get("workspace")
    if not workspace or shell.get("product", {}).get("code") != "ORDO":
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


def _lines(value: str) -> list[str]:
    return [line.strip(" -\t") for line in value.splitlines() if line.strip(" -\t")]


def _eligible_artifacts(token: str, organization_id: str, workspace_id: str) -> list[dict]:
    items: list[dict] = []
    eligible_snapshot_ids: set[str] = set()
    datasets = _safe(data_api.list_analytical_datasets, token, organization_id=organization_id,
                     product_code="ORDO", workspace_id=workspace_id) or []
    for dataset in datasets:
        snapshots = _safe(data_api.list_analytical_snapshots, token, dataset_id=dataset["id"],
                          organization_id=organization_id, product_code="ORDO",
                          workspace_id=workspace_id) or []
        eligible = [row for row in snapshots if row.get("state") in {"VALIDATED", "FROZEN"}
                    and not row.get("invalidated")]
        eligible_snapshot_ids.update(row["id"] for row in eligible)
        items.extend({"type": "snapshot", "id": row["id"], "fingerprint": row["fingerprint"]}
                     for row in eligible)
    features = _safe(data_api.list_analytical_features, token, organization_id=organization_id,
                     product_code="ORDO", workspace_id=workspace_id) or []
    for feature in features:
        versions = _safe(data_api.list_analytical_feature_versions, token, feature_id=feature["id"],
                         organization_id=organization_id, product_code="ORDO",
                         workspace_id=workspace_id) or []
        items.extend({"type": "feature_version", "id": row["id"], "fingerprint": row["fingerprint"]}
                     for row in versions if row.get("state") in {"GOVERNED", "FROZEN"}
                     and not row.get("invalidated") and len(row.get("snapshot_inputs") or []) == 1
                     and row["snapshot_inputs"][0].get("snapshot_id") in eligible_snapshot_ids)
    return items


def _render_forecast_results(
    *, token: str, organization_id: str, workspace_id: str
) -> None:
    st.markdown("### Persistirani forecast rezultati")
    st.caption(
        "Read-only prikaz prihvacenih 24C rezultata. Ovaj ekran nema forecast execution formu "
        "niti time-series-spec authoring/discovery workflow."
    )
    items = _safe(ordo_analytics_api.forecasts, token, organization_id, workspace_id) or []
    if not items:
        st.info("Nema persistiranih forecast rezultata u aktivnom ORDO workspace-u.")
        return
    st.dataframe(
        [
            {
                "id": item.get("id"),
                "status": item.get("result_status"),
                "reason_code": item.get("reason_code") or "—",
                "requested_family": item.get("requested_family"),
                "executed_family": item.get("executed_family") or "—",
                "horizon": item.get("horizon"),
                "created_at": item.get("created_at"),
            }
            for item in items
        ],
        use_container_width=True,
        hide_index=True,
    )
    by_id = {str(item["id"]): item for item in items if item.get("id")}
    selected_id = st.selectbox(
        "Forecast rezultat za detaljan pregled",
        list(by_id),
        format_func=lambda value: (
            f"{value[:8]} · {by_id[value].get('result_status')} · "
            f"{by_id[value].get('requested_family')}"
        ),
        key="ordo_forecast_result_detail",
    )
    detail = _safe(
        ordo_analytics_api.forecast_detail,
        token,
        forecast_run_id=selected_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
    )
    if not detail:
        return
    xai = build_forecast_xai(detail)
    status = xai["result_status"]
    if status == "ESTIMATED":
        st.success("ESTIMATED · prikazane su samo persistirane tacke i intervali.")
    else:
        st.warning(
            f"{status or 'UNKNOWN'} · reason_code={xai['reason_code'] or '—'} · "
            f"{xai['reason_interpretation']}"
        )
    identity = xai["model_identity"]
    cols = st.columns(4)
    cols[0].metric("Status", status or "—")
    cols[1].metric("Requested family", identity.get("requested_family") or "—")
    cols[2].metric("Executed family", identity.get("executed_family") or "—")
    cols[3].metric("Horizon", xai["coverage"].get("horizon") or "—")
    st.caption(identity["interpretation"])

    if status == "ESTIMATED":
        points = xai["forecast_points"]
        if points:
            st.markdown("#### Forecast tacke i intervali")
            st.dataframe(points, use_container_width=True, hide_index=True)
        else:
            st.warning("Persistirani ESTIMATED rezultat nema tacke za prikaz; nije kreirana zamenska serija.")
    else:
        st.info("NOT_ESTIMATED nema point/interval vrednosti; UI ne prikazuje nule ili praznu zamensku seriju.")

    st.markdown("#### Interval i rolling-origin/backtest dokaz")
    st.write(xai["interval"])
    st.caption(xai["interval"]["interpretation"])
    st.write("**Observation/training window i rolling-origin plan**")
    st.json({"coverage": xai["coverage"], "rolling_origin_plan": xai["rolling_origin_plan"]})
    if status == "ESTIMATED":
        st.write("**Aggregate backtest metrics**")
        st.json(xai["aggregate_backtest_metrics"])
        st.write("**Metric availability**")
        st.json(xai["metric_availability"])
        with st.expander("Per-origin backtest evidence"):
            st.json(xai["backtest_records"])
    else:
        st.write("**Metric availability**")
        st.json(xai["metric_availability"])
    st.caption(xai["backtest_interpretation"])

    st.markdown("#### Dijagnostika i upozorenja")
    st.json({"diagnostics": xai["diagnostics"], "warnings": xai["warnings"]})
    st.caption(xai["diagnostics_interpretation"])
    st.markdown("#### Provenance i metodoloske granice")
    st.json(xai["provenance"])
    st.write(xai["safety"]["interpretation"])
    st.write("**Eksplicitno nepodrzano**")
    st.json(xai["unsupported"])


def _render_scenario_assessments(assessments: list[dict]) -> None:
    if not assessments:
        return
    st.markdown("#### Sacuvane scenario procene")
    for item in assessments:
        xai = build_scenario_xai(item)
        with st.expander(
            f"{str(item.get('id') or '')[:8]} · impact={xai['impact'] or '—'} · "
            f"forecast_performed={xai['forecast_performed']}"
        ):
            st.warning(xai["scenario_interpretation"])
            st.write(
                f"**Impact:** {xai['impact'] or '—'}  \n"
                f"**Reason:** {xai['impact_estimation_reason_code'] or '—'}  \n"
                f"**Forecast performed:** {xai['forecast_performed']}"
            )
            st.write(xai["forecast_boundary"])
            st.write(xai["reason_interpretation"])
            if xai["impact_estimate_numeric"] is None:
                st.info("Numericki impact nije persistiran i nije zamenjen nulom.")
            else:
                st.metric(
                    "Persistirani impact",
                    f"{xai['impact_estimate_numeric']} {xai['impact_estimate_unit'] or ''}",
                )
            st.json({"provenance": xai["provenance"], "limitations": xai["limitations"]})
            st.write("**Eksplicitno nepodrzano**")
            st.json(xai["unsupported"])


def render_ordo_analytics(*, token: str, shell: dict[str, Any]) -> None:
    scope = _scope(shell)
    st.markdown('<div class="isi-eyebrow">ORDO · Analitika + AI</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">Inteligencija odlučivanja bez lažne predikcije</h1>', unsafe_allow_html=True)
    st.caption(
        "ISI-11 povezuje razvojni cilj, kvalitet dokaza, validirane indikatorske metodologije, scenarije i lokalnu AI sintezu. "
        "Scenario procena je evidence-readiness pregled, ne prognoza efekata."
    )
    if scope is None:
        st.info("ORDO workspace nije izabran.")
        return
    organization_id, workspace_id = scope
    permissions = set(shell.get("product", {}).get("permission_codes", []))
    runs = _safe(ordo_analytics_api.runs, token, organization_id, workspace_id) or []

    artifacts = _eligible_artifacts(token, organization_id, workspace_id)
    selected_artifact = None
    snapshot = None
    if not artifacts:
        st.info("Nema validiranog governed analytical snapshot-a ili eligible feature verzije za analitiku.")
    else:
        selected_artifact = st.selectbox(
            "Governed analytical artefakt", artifacts,
            format_func=lambda row: f"{row['type']} · {row['id']} · {row['fingerprint']}",
        )
        snapshot = _safe(
            ordo_analytics_api.summary, token, organization_id, workspace_id,
            analytical_artifact_type=selected_artifact["type"],
            analytical_artifact_id=selected_artifact["id"],
        )
    if snapshot:
        cols = st.columns(5)
        cards = [
            ("Opservacije", snapshot.get("observation_count", 0)),
            ("Validirane", _pct(snapshot.get("validated_observation_ratio"))),
            ("Provenance", _pct(snapshot.get("provenance_coverage"))),
            ("Dimenzije", _pct(snapshot.get("dimension_coverage"))),
            ("Stubovi", _pct(snapshot.get("pillar_coverage"))),
        ]
        for col, (label, value) in zip(cols, cards):
            col.metric(label, value)
        st.progress(
            float(snapshot.get("evidence_quality_score", 0.0)),
            text=f"Kvalitet dokaza: {snapshot.get('evidence_quality_band', 'no_evidence')} · {_pct(snapshot.get('evidence_quality_score'))}",
        )
        st.caption(snapshot.get("semantic_notice", "Ovo nije destination-performance score."))

        st.markdown("### Pokrivenost razvoja")
        st.write("**Pokrivene dimenzije:**", ", ".join(snapshot.get("observed_dimensions") or []) or "—")
        st.write("**Dimenzije bez dokaza:**", ", ".join(snapshot.get("missing_dimensions") or []) or "—")

    st.markdown("### Metodološki status")
    if snapshot:
        method_cols = st.columns(3)
        method_cols[0].metric("Aktivni indikatori", snapshot.get("active_indicator_count", 0))
        method_cols[1].metric("Konceptualni", snapshot.get("conceptual_indicator_count", 0))
        method_cols[2].metric("Sa validiranom metodologijom", snapshot.get("validated_methodology_indicator_count", 0))
    methods = _safe(ordo_analytics_api.methodologies, token, organization_id, workspace_id) or []
    if methods:
        st.dataframe(methods, use_container_width=True, hide_index=True)
    else:
        st.info("Nema validiranih metodologija. ISI-11 ne izmišlja formule niti automatski validira konceptualne ORDO indikatore.")

    st.markdown("### Analitički snapshot")
    if snapshot and selected_artifact is not None and "analysis.run" in permissions and st.button("Sačuvaj trenutni ORDO snapshot", type="primary", use_container_width=True):
        result = _safe(ordo_analytics_api.create_run, token, organization_id=organization_id, workspace_id=workspace_id, analytical_artifact_type=selected_artifact["type"], analytical_artifact_id=selected_artifact["id"])
        if result is not None:
            st.success("ORDO snapshot je sačuvan.")
            st.rerun()
    if runs:
        compact = [
            {
                "id": item["id"],
                "artefakt": item.get("analytical_artifact_type"),
                "artifact_id": item.get("analytical_snapshot_id") or item.get("analytical_feature_version_id"),
                "fingerprint": item.get("analytical_artifact_fingerprint"),
                "kvalitet_dokaza": item["evidence_quality_score"],
                "provenance": item["provenance_coverage"],
                "indikatori": item["indicator_coverage"],
                "dimenzije": item["dimension_coverage"],
                "stubovi": item["pillar_coverage"],
                "kreirano": item["created_at"],
            }
            for item in runs
        ]
        st.dataframe(compact, use_container_width=True, hide_index=True)
    else:
        st.info("Još nema sačuvanih ORDO analitičkih snapshot-a.")
    eligible_artifacts = {
        (("ANALYTICAL_SNAPSHOT" if item["type"] == "snapshot" else "ANALYTICAL_FEATURE_VERSION"), item["id"])
        for item in artifacts
    }
    governed_runs = [
        item for item in runs
        if (
            item.get("analytical_artifact_type"),
            item.get("analytical_snapshot_id") or item.get("analytical_feature_version_id"),
        ) in eligible_artifacts
    ]

    _render_forecast_results(
        token=token,
        organization_id=organization_id,
        workspace_id=workspace_id,
    )

    st.markdown("### Razvojni ciljevi i scenariji")
    st.caption("Scenario je korisnički definisan razvojni pravac. Sistem ne predstavlja pretpostavke kao činjenice niti računa predviđene efekte bez validiranog modela.")
    goals = _safe(ordo_analytics_api.goals, token, organization_id, workspace_id) or []
    scenarios = _safe(ordo_analytics_api.scenarios, token, organization_id, workspace_id) or []

    if "analysis.run" in permissions:
        with st.expander("Novi razvojni cilj"):
            goal_code = st.text_input("Kod cilja", key="ordo_goal_code")
            goal_title = st.text_input("Naziv cilja", key="ordo_goal_title")
            goal_description = st.text_area("Opis", key="ordo_goal_desc")
            focus_area = st.selectbox(
                "Fokus",
                ["destination_development", "competitiveness", "sustainability", "inclusion", "employment", "quality_of_life", "custom"],
                key="ordo_goal_focus",
            )
            if st.button("Sačuvaj razvojni cilj", use_container_width=True, key="ordo_goal_save"):
                result = _safe(
                    ordo_analytics_api.create_goal,
                    token,
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    code=goal_code,
                    title=goal_title,
                    description=goal_description,
                    focus_area=focus_area,
                )
                if result is not None:
                    st.success("Razvojni cilj je sačuvan.")
                    st.rerun()

        if goals:
            with st.expander("Novi scenario"):
                goal_map = {item["id"]: item["title"] for item in goals}
                goal_id = st.selectbox("Razvojni cilj", list(goal_map), format_func=lambda value: goal_map[value], key="ordo_scenario_goal")
                scenario_name = st.text_input("Naziv scenarija", key="ordo_scenario_name")
                scenario_description = st.text_area("Opis scenarija", key="ordo_scenario_desc")
                assumptions_text = st.text_area("Pretpostavke · jedna po redu", key="ordo_scenario_assumptions")
                measures_text = st.text_area("Predložene mere · jedna po redu", key="ordo_scenario_measures")
                if st.button("Sačuvaj scenario", use_container_width=True, key="ordo_scenario_save"):
                    result = _safe(
                        ordo_analytics_api.create_scenario,
                        token,
                        organization_id=organization_id,
                        workspace_id=workspace_id,
                        goal_id=goal_id,
                        name=scenario_name,
                        description=scenario_description,
                        assumptions=_lines(assumptions_text),
                        measures=_lines(measures_text),
                    )
                    if result is not None:
                        st.success("Scenario je sačuvan kao draft.")
                        st.rerun()

    if goals:
        st.dataframe(goals, use_container_width=True, hide_index=True)
    if scenarios:
        st.dataframe(scenarios, use_container_width=True, hide_index=True)

    assessments = _safe(ordo_analytics_api.assessments, token, organization_id, workspace_id) or []
    if scenarios and governed_runs and "analysis.run" in permissions:
        st.markdown("#### Evidence-only procena scenarija")
        scenario_map = {item["id"]: item["name"] for item in scenarios}
        run_ids = [item["id"] for item in governed_runs]
        scenario_id = st.selectbox("Scenario", list(scenario_map), format_func=lambda value: scenario_map[value], key="ordo_assessment_scenario")
        run_id = st.selectbox("Analitički snapshot", run_ids, format_func=lambda value: f"Snapshot {value[:8]}", key="ordo_assessment_run")
        if st.button("Kreiraj evidence-only procenu", use_container_width=True, key="ordo_assessment_create"):
            result = _safe(
                ordo_analytics_api.create_assessment,
                token,
                organization_id=organization_id,
                workspace_id=workspace_id,
                scenario_id=scenario_id,
                analytics_run_id=run_id,
            )
            if result is not None:
                st.success("Procena je sačuvana bez prediktivnog izračunavanja.")
                st.rerun()
    _render_scenario_assessments(assessments)

    st.markdown("### Lokalna ORDO AI podrška")
    st.warning(
        "AI ne donosi razvojnu odluku i ne prognozira efekte bez validiranog modela. ORDO AI profil je local-only i svaki rezultat zahteva human review."
    )
    st.caption(
        "Trenutni lokalni QA model: qwen2.5:7b-instruct preko shared ISI Ollama gateway-a. ORDO koristi sopstveni prompt i policy profil; finalni produkcioni model biće zaključan kasnije."
    )
    if governed_runs and "analysis.run" in permissions:
        run_ids = [item["id"] for item in governed_runs]
        selected_run = st.selectbox("Snapshot za AI sintezu", run_ids, format_func=lambda value: f"Snapshot {value[:8]}", key="ordo_ai_run")
        mode = st.radio("Vrsta sinteze", ["monitoring", "scenario_review"], horizontal=True, key="ordo_ai_mode")
        selected_scenario = None
        if mode == "scenario_review":
            if not scenarios:
                st.info("Za scenario review prvo kreiraj razvojni cilj i scenario.")
            else:
                scenario_map = {item["id"]: item["name"] for item in scenarios}
                selected_scenario = st.selectbox("Scenario za AI pregled", list(scenario_map), format_func=lambda value: scenario_map[value], key="ordo_ai_scenario")
        disabled = mode == "scenario_review" and not selected_scenario
        if st.button("Pokreni lokalnu ORDO AI sintezu", use_container_width=True, disabled=disabled):
            result = _safe(
                ordo_analytics_api.create_synthesis,
                token,
                organization_id=organization_id,
                workspace_id=workspace_id,
                analytics_run_id=selected_run,
                synthesis_type=mode,
                scenario_id=selected_scenario,
            )
            if result is not None:
                st.success("ORDO AI posao je poslat kroz shared gateway. Rezultat ostaje na human review-u.")
                st.rerun()

    syntheses = _safe(ordo_analytics_api.syntheses, token, organization_id, workspace_id) or []
    if not syntheses:
        st.info("Nema ORDO AI sinteza u aktivnom workspace-u.")
        return

    for item in syntheses:
        job = item.get("job", {})
        with st.expander(f"{item.get('synthesis_type')} · {item['id'][:8]} · {job.get('status', 'unknown')} · review: {item.get('review_status')}"):
            st.caption(
                f"provider={job.get('provider_name') or '-'} · model={job.get('model_name') or '-'} · policy={job.get('effective_provider_policy')} · prompt={job.get('prompt_key')} v{job.get('prompt_version')}"
            )
            st.caption(
                f"source_snapshot_sha256={item.get('source_snapshot_sha256') or '-'} · "
                f"structured_output_state={'present' if job.get('structured_output') else 'unavailable'} · "
                f"human_review_status={job.get('human_review_status') or item.get('review_status') or '-'}"
            )
            structured = job.get("structured_output")
            if structured:
                st.markdown("**Sažetak**")
                st.write(structured.get("executive_summary", ""))
                st.markdown("**Osnova u dokazima**")
                st.write(structured.get("evidence_basis", ""))
                for title, key in (
                    ("Razvojne mogućnosti za razmatranje", "development_opportunities"),
                    ("Trade-off pitanja", "tradeoffs"),
                    ("Ograničenja i nepoznanice", "limitations"),
                    ("Sledeći podaci / pitanja", "next_evidence_needed"),
                ):
                    values = structured.get(key) or []
                    if values:
                        st.markdown(f"**{title}**")
                        for value in values:
                            st.write(f"- {value}")
                st.caption(f"forecast_performed={structured.get('forecast_performed')} · human_review_required={structured.get('human_review_required')}")
            elif job.get("error_message"):
                st.error(job.get("error_message"))
            else:
                st.caption("AI rezultat još nije dostupan.")

            if item.get("review_status") == "pending" and job.get("status") in {"review_required", "succeeded"} and "analysis.run" in permissions:
                note = st.text_area("Napomena review-a", key=f"ordo_review_note_{item['id']}")
                accept, reject = st.columns(2)
                if accept.button("Prihvati kao pregledano", key=f"ordo_accept_{item['id']}", use_container_width=True):
                    result = _safe(
                        ordo_analytics_api.review_synthesis,
                        token,
                        synthesis_id=item["id"],
                        organization_id=organization_id,
                        workspace_id=workspace_id,
                        decision="accepted",
                        reviewer_note=note,
                    )
                    if result is not None:
                        st.rerun()
                if reject.button("Odbaci", key=f"ordo_reject_{item['id']}", use_container_width=True):
                    result = _safe(
                        ordo_analytics_api.review_synthesis,
                        token,
                        synthesis_id=item["id"],
                        organization_id=organization_id,
                        workspace_id=workspace_id,
                        decision="rejected",
                        reviewer_note=note,
                    )
                    if result is not None:
                        st.rerun()
