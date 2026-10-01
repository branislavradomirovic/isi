"""Versioned fixed catalogue. Changing fixture semantics requires a new version."""
from tools.performance.contracts import Budget, BudgetClass, BudgetState, Workload, fingerprint

_DEFINITIONS = (
    ("api.health.read.v1", "Health", "api", "IN_PROCESS"),
    ("api.authenticated.context.v1", "Authenticated context", "api", "ISOLATED_SQLITE"),
    ("api.authenticated.navigation.v1", "Authenticated navigation", "api", "ISOLATED_SQLITE"),
    ("api.readiness.synthetic.v1", "Synthetic readiness", "api", "IN_PROCESS"),
    ("data.ingestion.synthetic.v1", "Synthetic ingestion", "data", "ISOLATED_SQLITE"),
    ("simpa.analytics.synthetic.v1", "SIMPA aggregate statistics", "simpa", "IN_PROCESS"),
    ("ordo.forecast.synthetic.v1", "ORDO explicit forecast", "ordo", "IN_PROCESS"),
    ("report.render.synthetic.v1", "Persisted report rendering", "report", "ISOLATED_SQLITE"),
    ("ai.stub.synthetic.v1", "Development AI stub", "ai", "ISOLATED_SQLITE"),
    ("ai.circuit.synthetic.v1", "AI circuit and fallback", "ai", "ISOLATED_SQLITE"),
)


def catalogue() -> tuple[Workload, ...]:
    budgets = (
        Budget(metric="correctness_failures", budget_class=BudgetClass.CORRECTNESS,
               state=BudgetState.HARD_GATE, threshold=0),
        Budget(metric="resilience_failures", budget_class=BudgetClass.RESILIENCE,
               state=BudgetState.HARD_GATE, threshold=0),
        *(Budget(metric=metric, budget_class=BudgetClass.LATENCY_THROUGHPUT,
                 state=BudgetState.UNCALIBRATED) for metric in
          ("p50_seconds", "p95_seconds", "p99_seconds", "throughput")),
        Budget(metric="resource", budget_class=BudgetClass.RESOURCE,
               state=BudgetState.UNAVAILABLE, unavailable_reason="not_portable"),
    )
    # Fingerprint the actual fixture/scenario implementation as well as its version.
    # No machine identity or absolute path enters the digest.
    from pathlib import Path
    import hashlib
    fixture_digest = hashlib.sha256(Path(__file__).with_name("scenarios.py").read_bytes()).hexdigest()
    return tuple(Workload(
        workload_id=identity, title=title, category=category, execution_mode=mode,
        fixture_sha256=fingerprint({"version": "synthetic-v1", "workload": identity,
                                    "implementation": fixture_digest}),
        correctness_gates=("exact_result", "scope_isolation", "bounded_failure", "deterministic_result"),
        budgets=budgets,
    ) for identity, title, category, mode in _DEFINITIONS)
