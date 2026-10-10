from __future__ import annotations

from typing import Any

import streamlit as st

from src.domains.ordo.analytics_xai import build_forecast_xai, build_scenario_xai
from src.streamlit_app import data_api, ordo_analytics_api
from src.streamlit_app.xai_charts import MAX_ORIGINS, backtest_chart, forecast_chart, render_chart


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


def _render_time_series_workflow(
    *, token: str, organization_id: str, workspace_id: str,
    permissions: set[str], runs: list[dict],
) -> None:
    # Forecast execution form remains governed by backend scope and analysis.run authorization.
    st.markdown("### Time-series specifikacije i forecast izvršenje")
    st.caption(
        "Specifikacija se verzionira i ljudski odobrava odvojeno od forecast izvršenja. "
        "Backend autoritativno vezuje metodologiju i governed input."
    )
    specs = _safe(ordo_analytics_api.time_series_specs, token, organization_id, workspace_id) or []
    if specs:
        st.dataframe(
            [{
                "series_key": item.get("series_key"),
                "version": item.get("version_no"),
                "indicator": item.get("target_indicator_code"),
                "status": item.get("status"),
                "contract_fingerprint": item.get("contract_fingerprint"),
                "analytics_run_id": item.get("analytics_run_id"),
            } for item in specs],
            use_container_width=True,
            hide_index=True,
        )
        spec_by_id = {str(item["id"]): item for item in specs}
        review_id = st.selectbox(
            "Specifikacija za pregled",
            list(spec_by_id),
            format_func=lambda value: (
                f"{spec_by_id[value].get('series_key')} v{spec_by_id[value].get('version_no')} · "
                f"{spec_by_id[value].get('target_indicator_code')} · {spec_by_id[value].get('status')}"
            ),
            key="ordo_time_series_spec_review",
        )
        detail = _safe(
            ordo_analytics_api.time_series_spec_detail,
            token,
            time_series_spec_id=review_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
        ) or spec_by_id[review_id]
        st.json({
            "binding": {
                "analytics_run_id": detail.get("analytics_run_id"),
                "target_methodology_id": detail.get("target_methodology_id"),
                "target_methodology_version": detail.get("target_methodology_version"),
                "methodology_fingerprint": detail.get("methodology_fingerprint"),
                "input_snapshot_sha256": detail.get("input_snapshot_sha256"),
            },
            "contract": detail.get("contract_json"),
            "contract_fingerprint": detail.get("contract_fingerprint"),
            "locked_semantics": {
                "forecast_execution": detail.get("forecast_execution"),
                "automatic_model_selection": detail.get("automatic_model_selection"),
                "non_causal": detail.get("non_causal"),
            },
            "lifecycle": {
                "status": detail.get("status"),
                "proposed_by_membership_id": detail.get("proposed_by_membership_id"),
                "proposed_at": detail.get("proposed_at"),
                "approved_by_membership_id": detail.get("approved_by_membership_id"),
                "approved_at": detail.get("approved_at"),
                "validation_note": detail.get("validation_note"),
                "validation_evidence_reference": detail.get("validation_evidence_reference"),
                "retired_by_membership_id": detail.get("retired_by_membership_id"),
                "retired_at": detail.get("retired_at"),
                "retirement_note": detail.get("retirement_note"),
            },
        })
        if "indicator.manage" in permissions:
            status_value = detail.get("status")
            if status_value == "draft" and st.button(
                "Predloži specifikaciju", key=f"ordo_spec_propose_{review_id}"
            ):
                result = _safe(
                    ordo_analytics_api.propose_time_series_spec, token,
                    time_series_spec_id=review_id, organization_id=organization_id,
                    workspace_id=workspace_id,
                )
                if result is not None:
                    st.rerun()
            elif status_value == "proposed":
                validation_note = st.text_area(
                    "Napomena ljudske validacije", key=f"ordo_spec_validation_note_{review_id}"
                )
                validation_evidence = st.text_input(
                    "Referenca dokaza validacije", key=f"ordo_spec_validation_evidence_{review_id}"
                )
                if st.button("Validiraj specifikaciju", key=f"ordo_spec_validate_{review_id}"):
                    result = _safe(
                        ordo_analytics_api.validate_time_series_spec, token,
                        time_series_spec_id=review_id, organization_id=organization_id,
                        workspace_id=workspace_id, validation_note=validation_note,
                        validation_evidence_reference=validation_evidence,
                    )
                    if result is not None:
                        st.rerun()
            elif status_value == "validated":
                retirement_note = st.text_area(
                    "Napomena povlačenja", key=f"ordo_spec_retirement_note_{review_id}"
                )
                if st.button("Povuci specifikaciju", key=f"ordo_spec_retire_{review_id}"):
                    result = _safe(
                        ordo_analytics_api.retire_time_series_spec, token,
                        time_series_spec_id=review_id, organization_id=organization_id,
                        workspace_id=workspace_id, retirement_note=retirement_note,
                    )
                    if result is not None:
                        st.rerun()
    else:
        st.info("Nema time-series specifikacija u aktivnom ORDO workspace-u.")

    if "indicator.manage" in permissions:
        governed_runs = [row for row in runs if row.get("analytical_artifact_type") != "LEGACY_OBSERVATION"]
        with st.expander("Nova time-series specifikacija"):
            if not governed_runs:
                st.info("Prvo sačuvajte governed ORDO analitički snapshot.")
            else:
                run_id = st.selectbox(
                    "Governed analitički run",
                    [str(row["id"]) for row in governed_runs],
                    format_func=lambda value: f"Run {value[:8]}",
                    key="ordo_spec_run",
                )
                series_key = st.text_input("Ključ serije", key="ordo_spec_series_key")
                indicator_code = st.text_input("Kod ciljnog indikatora", key="ordo_spec_indicator")
                target_semantic = st.selectbox(
                    "Semantika cilja", ["continuous", "count", "proportion_rate"],
                    key="ordo_spec_target_semantic",
                )
                time_index_field = st.text_input("Polje vremenskog indeksa", key="ordo_spec_time_field")
                frequency = st.selectbox(
                    "Frekvencija", ["daily", "weekly", "monthly", "quarterly", "annual"],
                    key="ordo_spec_frequency",
                )
                series_fields = _lines(st.text_area(
                    "Polja identiteta serije · jedno po redu", key="ordo_spec_series_fields"
                ))
                start = st.date_input("Početak posmatranja", key="ordo_spec_start")
                end = st.date_input("Kraj posmatranja", key="ordo_spec_end")
                as_of = st.date_input("As-of datum", key="ordo_spec_as_of")
                minimum_history = st.number_input(
                    "Minimalan broj perioda", min_value=2, value=12, key="ordo_spec_min_history"
                )
                maximum_missing_ratio = st.number_input(
                    "Maksimalni missing ratio", min_value=0.0, max_value=1.0,
                    value=0.0, step=0.05, key="ordo_spec_missing_ratio",
                )
                missing_rule = st.selectbox(
                    "Eksplicitno pravilo za missing podatke",
                    ["fail", "exclude_periods", "explicit_gap"], key="ordo_spec_missing_rule",
                )
                outlier_policy = st.text_area("Outlier politika", key="ordo_spec_outlier")
                revision_policy = st.text_area("Revision politika", key="ordo_spec_revision")
                comparability_policy = st.text_area("Comparability politika", key="ordo_spec_comparability")
                transformation = st.selectbox(
                    "Transformacija", ["none", "log1p", "difference", "seasonal_difference"],
                    key="ordo_spec_transformation",
                )
                trend_requirement = st.selectbox(
                    "Trend zahtev", ["none", "allowed", "required"], key="ordo_spec_trend"
                )
                seasonality_period = st.number_input(
                    "Seasonality period · 0 znači nije primenljivo", min_value=0, value=0,
                    key="ordo_spec_seasonality",
                )
                families = st.multiselect(
                    "Dozvoljene kandidat porodice",
                    ["naive", "seasonal_naive", "ets", "sarima", "sarimax", "count_time_series"],
                    default=["naive"], key="ordo_spec_families",
                )
                horizon = st.number_input("Horizont", min_value=1, value=1, key="ordo_spec_horizon")
                horizon_unit = st.selectbox(
                    "Jedinica horizonta", ["days", "weeks", "months", "quarters", "years"],
                    key="ordo_spec_horizon_unit",
                )
                diagnostic_requirements = _lines(st.text_area(
                    "Dijagnostički zahtevi · jedan po redu", key="ordo_spec_diagnostics"
                ))
                limitations = _lines(st.text_area(
                    "Ograničenja · jedno po redu", key="ordo_spec_limitations"
                ))
                initial_train = st.number_input(
                    "Rolling-origin početni train periodi", min_value=2, value=8,
                    key="ordo_spec_initial_train",
                )
                step_size = st.number_input(
                    "Rolling-origin korak", min_value=1, value=1, key="ordo_spec_step"
                )
                minimum_origins = st.number_input(
                    "Minimalan broj origin-a", min_value=2, value=3, key="ordo_spec_origins"
                )
                required_metrics = st.multiselect(
                    "Obavezne backtest metrike",
                    ["MAE", "RMSE", "sMAPE", "MASE", "bias", "interval_coverage",
                     "interval_width_sharpness", "seasonal_baseline_comparison"],
                    default=["MAE", "RMSE"], key="ordo_spec_metrics",
                )
                if st.button("Kreiraj DRAFT specifikaciju", key="ordo_spec_create"):
                    spec_payload = {
                        "analytics_run_id": run_id, "series_key": series_key,
                        "target_indicator_code": indicator_code, "target_semantic": target_semantic,
                        "time_index_field": time_index_field, "frequency": frequency,
                        "series_key_fields": series_fields,
                        "observation_window_start": start.isoformat(),
                        "observation_window_end": end.isoformat(), "observation_as_of": as_of.isoformat(),
                        "minimum_history_periods": int(minimum_history),
                        "maximum_missing_ratio": float(maximum_missing_ratio),
                        "missing_data_rule": missing_rule, "outlier_policy": outlier_policy,
                        "revision_policy": revision_policy, "comparability_policy": comparability_policy,
                        "transformation": transformation, "trend_requirement": trend_requirement,
                        "seasonality_period": int(seasonality_period) or None,
                        "candidate_families": families, "horizon": int(horizon),
                        "horizon_unit": horizon_unit,
                        "diagnostic_requirements": diagnostic_requirements,
                        "limitations": limitations, "initial_train_periods": int(initial_train),
                        "step_size": int(step_size), "minimum_origins": int(minimum_origins),
                        "required_metrics": required_metrics,
                    }
                    result = _safe(
                        ordo_analytics_api.create_time_series_spec, token,
                        organization_id=organization_id, workspace_id=workspace_id, spec=spec_payload,
                    )
                    if result is not None:
                        st.rerun()

    validated_specs = [item for item in specs if item.get("status") == "validated"]
    if "analysis.run" in permissions:
        st.markdown("#### Pokreni forecast iz validirane specifikacije")
        if not validated_specs:
            st.info("Forecast zahteva postojeću VALIDATED specifikaciju.")
        else:
            validated_by_id = {str(item["id"]): item for item in validated_specs}
            selected_id = st.selectbox(
                "Validirana specifikacija",
                list(validated_by_id),
                format_func=lambda value: (
                    f"{validated_by_id[value].get('series_key')} "
                    f"v{validated_by_id[value].get('version_no')} · "
                    f"{validated_by_id[value].get('target_indicator_code')}"
                ),
                key="ordo_forecast_spec",
            )
            identities = _safe(
                ordo_analytics_api.time_series_identities, token,
                time_series_spec_id=selected_id, organization_id=organization_id,
                workspace_id=workspace_id,
            ) or []
            if not identities:
                st.info("Nema eligible identiteta serije u exact governed binding-u.")
            else:
                identity = st.selectbox(
                    "Otkriveni identitet serije", identities,
                    format_func=lambda value: ", ".join(f"{key}={item}" for key, item in value.items()),
                    key="ordo_forecast_identity",
                )
                contract = validated_by_id[selected_id].get("contract_json") or {}
                family = st.selectbox(
                    "Eksplicitno zahtevana porodica", contract.get("candidate_families") or [],
                    key="ordo_forecast_family",
                )
                interval_level = st.selectbox(
                    "Nivo intervala", [0.80, 0.90, 0.95], key="ordo_forecast_interval"
                )
                if st.button("Pokreni forecast", type="primary", key="ordo_forecast_execute"):
                    result = _safe(
                        ordo_analytics_api.execute_forecast, token,
                        organization_id=organization_id, workspace_id=workspace_id,
                        time_series_spec_id=selected_id, requested_family=family,
                        series_identity=identity, interval_level=interval_level,
                    )
                    if result is not None:
                        st.success(f"Forecast ishod je sačuvan: {result.get('result_status')}.")
                        st.rerun()


def _render_forecast_results(
    *, token: str, organization_id: str, workspace_id: str,
    permissions: set[str], runs: list[dict],
) -> None:
    _render_time_series_workflow(
        token=token, organization_id=organization_id, workspace_id=workspace_id,
        permissions=permissions, runs=runs,
    )
    st.markdown("### Persistirani forecast rezultati")
    st.caption(
        "Pregled sačuvanih ESTIMATED/NOT_ESTIMATED ishoda, backtest dokaza, intervala i provenance-a."
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

    render_chart(st, forecast_chart(detail))
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
        origins = xai["backtest_records"]
        if origins:
            if len(origins) > MAX_ORIGINS:
                st.warning(f"Izbor grafikona ograničen je na prvih {MAX_ORIGINS} porekla; puni dokaz ostaje ispod.")
            position = st.selectbox(
                "Backtest poreklo / origin", list(range(min(len(origins), MAX_ORIGINS))),
                format_func=lambda i: f"Zapis {i + 1} · origin_index={origins[i].get('origin_index', '—')}",
                key=f"ordo_xai_origin_{selected_id}",
            )
            chart = backtest_chart(detail, position)
            render_chart(st, chart)
            if chart.rows:
                st.dataframe(list(chart.rows), use_container_width=True, hide_index=True)
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
        "ORDO povezuje razvojni cilj, kvalitet dokaza, validirane indikatorske metodologije, scenarije i lokalnu AI sintezu. "
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
        st.info("Nema validiranih metodologija. ORDO ne izmišlja formule niti automatski validira konceptualne indikatore.")

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
        permissions=permissions,
        runs=runs,
    )

    scenarios = _render_scenario_workflow(token, organization_id, workspace_id, permissions, governed_runs)

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


def _render_scenario_workflow(token, organization_id, workspace_id, permissions, governed_runs):
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

    if "analysis.run" in permissions:
        if scenarios:
            with st.expander("Status scenarija"):
                chosen = st.selectbox("Scenario za promenu statusa", scenarios,
                    format_func=lambda row: f"{row['name']} · {row['status']}", key="ordo_scenario_status_item")
                with st.form("ordo_scenario_status_form"):
                    status_value = st.selectbox("Novi status", ["draft", "review_ready", "accepted", "rejected"])
                    st.caption("Prihvaćen scenario beleži stručni izbor; ne potvrđuje metodologiju, prognozu ili efekat mera.")
                    confirmed = st.checkbox("Potvrđujem promenu statusa izabranog scenarija")
                    if st.form_submit_button("Sačuvaj status scenarija"):
                        if not confirmed:
                            st.error("Potvrdite promenu statusa pre čuvanja.")
                        elif _safe(ordo_analytics_api.scenario_status, token, scenario_id=chosen["id"],
                                organization_id=organization_id, workspace_id=workspace_id, status=status_value) is not None:
                            st.success("Status scenarija je sačuvan.")
                            st.rerun()
        if assessments:
            with st.expander("Stručni pregled procene"):
                chosen = st.selectbox("Procena za pregled", assessments,
                    format_func=lambda row: f"{row['id'][:8]} · {row.get('status', 'unknown')}", key="ordo_assessment_review_item")
                with st.form("ordo_assessment_review_form"):
                    decision = st.selectbox("Odluka o pregledu", ["reviewed", "rejected"])
                    note = st.text_area("Obrazloženje stručnog pregleda", max_chars=5000)
                    st.caption("Pregled potvrđuje vaš stav o dokazima; ne pretvara scenario u prognozu. Izvor se ponovo proverava pri čuvanju.")
                    confirmed = st.checkbox("Pregledao/la sam izvore, ograničenja i izabranu procenu")
                    if st.form_submit_button("Sačuvaj stručni pregled"):
                        if not confirmed or not note.strip():
                            st.error("Unesite obrazloženje i potvrdite pregled izvora.")
                        elif _safe(ordo_analytics_api.review_assessment, token, assessment_id=chosen["id"],
                                organization_id=organization_id, workspace_id=workspace_id, decision=decision, reviewer_note=note.strip()) is not None:
                            st.success("Stručni pregled je sačuvan.")
                            st.rerun()
    return scenarios


def render_ordo_scenarios(*, token: str, shell: dict[str, Any]) -> None:
    st.markdown('<div class="isi-eyebrow">ORDO · Planiranje</div>', unsafe_allow_html=True)
    st.title("Razvojni ciljevi i scenariji")
    if shell.get("product", {}).get("code") != "ORDO":
        st.info("Scenariji su dostupni u ORDO radnom prostoru.")
        return
    scope = _scope(shell)
    if scope is None:
        st.info("Izaberite ORDO radni prostor da biste pregledali ciljeve i scenarije.")
        return
    permissions = set(shell["product"].get("permission_codes", []))
    if "analysis.read" not in permissions:
        st.info("Pregled scenarija zahteva dozvolu analysis.read; obratite se administratoru.")
        return
    organization_id, workspace_id = scope
    st.info("Cilj → pretpostavke i mere → pregled dokaza → stručna procena. Efekat ostaje NOT_ESTIMATED bez odobrenog modela uticaja.")
    with st.expander("Uputstvo za scenarije"):
        st.write("1. Pregledajte ili napravite razvojni cilj. 2. Unesite scenario, pretpostavke i predložene mere. 3. U Analitici sačuvajte analitički snimak iz validiranog izvora. 4. Povežite scenario sa snimkom kroz procenu zasnovanu na dokazima. 5. Pregledajte izvor, ograničenja i status procene. Pisanje zahteva analysis.run; scenario nije prognoza ni procena uzročnog efekta.")
    artifacts = _eligible_artifacts(token, organization_id, workspace_id)
    eligible = {(("ANALYTICAL_SNAPSHOT" if row["type"] == "snapshot" else "ANALYTICAL_FEATURE_VERSION"), row["id"]) for row in artifacts}
    runs = _safe(ordo_analytics_api.runs, token, organization_id, workspace_id) or []
    governed_runs = [row for row in runs if (row.get("analytical_artifact_type"), row.get("analytical_snapshot_id") or row.get("analytical_feature_version_id")) in eligible]
    if not governed_runs:
        st.info("Za novu procenu prvo pripremite validiran analitički izvor u Podacima i sačuvajte njegov snimak u Analitici. Ciljeve i scenarije možete pregledati nezavisno od toga.")
    _render_scenario_workflow(token, organization_id, workspace_id, permissions, governed_runs)
