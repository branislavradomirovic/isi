import copy
import itertools
import math
import pytest
from test_isi_23c_statistical_engine import _contract, FIELDS
from src.domains.simpa.statistical_models import run_statistical_model, result_fingerprint
from src.domains.simpa.statistical_attribution import explain, AttributionError, MAX_RECORDS


def case():
    contract = _contract(feature_fields=["z", "x"])
    records = [
        {"value_numeric": y, "x": x, "z": z}
        for x, z, y in [
            (0, 0, 1.2),
            (1, 1, 3.8),
            (2, 1, 5.5),
            (3, 4, 8.1),
            (4, 3, 10.3),
            (5, 5, 12.2),
            (6, 4, 15.1),
            (7, 8, 17.3),
        ]
    ]
    return contract, records, run_statistical_model(contract, records, FIELDS)


def test_closed_form_matches_independent_shapley_coalition_enumeration_and_additivity(monkeypatch):
    c, records, detail = case()
    monkeypatch.setattr("src.domains.simpa.statistical_models._fit_ols", lambda *a: pytest.fail("must not refit"))
    a = explain(c, detail, records, FIELDS, unit="synthetic units")
    features = a["features"]
    beta = [r["estimate"] for r in detail["coefficients"]]
    background = [[r[f] for f in features] for r in records]

    def game(sample, subset):
        return math.fsum(
            beta[0] + math.fsum(beta[j + 1] * (sample[j] if j in subset else bg[j]) for j in range(len(features)))
            for bg in background
        ) / len(background)

    for index, sample in enumerate(a["samples"]):
        for j in range(len(features)):
            others = set(range(len(features))) - {j}
            phi = 0
            for size in range(len(features)):
                for subset in itertools.combinations(others, size):
                    weight = (
                        math.factorial(size) * math.factorial(len(features) - size - 1) / math.factorial(len(features))
                    )
                    phi += weight * (game(sample["values"], set(subset) | {j}) - game(sample["values"], set(subset)))
            assert a["matrix"][index][j] == pytest.approx(phi, abs=1e-8)
        assert a["baseline"] + sum(a["matrix"][index]) == pytest.approx(sample["prediction"], abs=1e-8)
    assert a["features"] == ["x", "z"] and a["samples"][0]["values"] == [0, 0]
    assert a["in_sample_only"] and a["non_causal"] and "correlations" in a["limitations"]
    assert result_fingerprint(a) == result_fingerprint(explain(c, detail, records, FIELDS, unit="synthetic units"))


def test_missing_complete_case_and_background_are_exact_not_future_sampled():
    c, r, _ = case()
    r += [{"value_numeric": None, "x": 100, "z": 100}, {"value_numeric": 4, "x": None, "z": 2}]
    d = run_statistical_model(c, r, FIELDS)
    a = explain(c, d, r, FIELDS, unit="count")
    assert a["background_count"] == 8 and a["selected_count"] == 10 and a["dropped_missing_count"] == 2
    assert a["background_means"] == [3.5, 3.25]
    r[-1]["x"] = 200
    with pytest.raises(AttributionError):
        explain(c, d, r, FIELDS, unit="count")


@pytest.mark.parametrize(
    "kind", ["family", "order", "metric", "coefficient", "count", "noncausal", "finite", "unit", "capacity"]
)
def test_rejects_unfaithful_contract_or_numerical_payload(kind):
    c, r, d = case()
    d = copy.deepcopy(d)
    unit = "units"
    if kind == "family":
        d["model_family"] = "binomial_logit"
    elif kind == "order":
        d["coefficients"].reverse()
    elif kind == "metric":
        d["metrics"]["rmse"] += 1
    elif kind == "coefficient":
        d["coefficients"][1]["estimate"] += 1
    elif kind == "count":
        d["sample_size"] += 1
    elif kind == "noncausal":
        d["non_causal"] = False
    elif kind == "finite":
        d["coefficients"][0]["estimate"] = float("nan")
    elif kind == "unit":
        unit = ""
    elif kind == "capacity":
        r = r * (MAX_RECORDS // len(r) + 1)
    with pytest.raises(AttributionError):
        explain(c, d, r, FIELDS, unit=unit)


def test_background_change_changes_fingerprint_and_zero_contribution_is_zero():
    c, r, d = case()
    a = explain(c, d, r, FIELDS, unit="units")
    assert a["matrix"][0][0] < 0
    means = a["background_means"]
    r[0]["x"] = means[0]
    r[0]["z"] = means[1]
    d = run_statistical_model(c, r, FIELDS)
    b = explain(c, d, r, FIELDS, unit="units")
    assert a["background_fingerprint"] != b["background_fingerprint"]
