import itertools

import numpy as np
import pytest

from causal_target.optimization import allocate, compare


def test_profit_optimizer_matches_exhaustive_feasible_search():
    tau = np.array([0.1, -0.2, 0.04, 0.3, 0.02])
    chosen, result = allocate(
        tau, np.ones(5) * 0.2, budget=3, cost=1, value=20, capacity_fraction=0.8
    )
    candidates = [
        np.dot(bits, tau * 20 - 1) for bits in itertools.product([0, 1], repeat=5) if sum(bits) <= 3
    ]
    assert result["incremental_profit"] == max(candidates)
    assert result["targeted"] == 2
    assert result["unspent_budget"] == 1
    assert not chosen[1]


@pytest.mark.parametrize(
    "tau,budget,expected", [([0.5, 0.2], 0, 0), ([-0.1, -0.2], 100, 0), ([], 100, 0)]
)
def test_optimizer_edges(tau, budget, expected):
    _, result = allocate(tau, np.zeros(len(tau)), budget, 1, 10)
    assert result["targeted"] == expected
    assert result["spend"] == 0
    assert result["roi"] is None


def test_treat_all_never_overspends():
    _, result = allocate([0.1] * 10, [0.2] * 10, 5, 1, 10, strategy="Treat everyone")
    assert not result["feasible"]
    assert result["spend"] == 0


def test_all_strategies_respect_budget_capacity():
    results = compare(
        [0.1] * 100, np.linspace(0, 1, 100), budget=2, cost=0.1, value=10, capacity_fraction=0.1
    )
    assert (results.targeted <= 10).all()
    assert (results.spend <= 2).all()


@pytest.mark.parametrize(
    "kwargs",
    [{"budget": -1}, {"cost": 0}, {"value": -1}, {"capacity_fraction": 2}, {"budget": np.nan}],
)
def test_invalid_economics(kwargs):
    args = dict(budget=10, cost=1, value=10, capacity_fraction=1)
    args.update(kwargs)
    with pytest.raises(ValueError):
        allocate([0.1], [0.3], **args)
