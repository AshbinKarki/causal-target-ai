"""Exact budget allocation for equal intervention costs and additive value."""

import numpy as np
import pandas as pd

STRATEGIES = [
    "No intervention",
    "Random targeting",
    "Treat everyone",
    "Predictive targeting",
    "Uplift targeting",
    "Profit optimized",
]


def allocate(
    cate,
    probability,
    budget,
    cost,
    value,
    capacity_fraction=1.0,
    strategy="Profit optimized",
    seed=42,
):
    """Sorting solves this uniform-cost binary knapsack exactly.

    Treat-everyone is marked infeasible unless the whole cohort meets both
    constraints; it never silently overspends. Costs and values are assumptions.
    """
    cate, probability = np.asarray(cate, dtype=float), np.asarray(probability, dtype=float)
    scalars = [budget, cost, value, capacity_fraction]
    if (
        cate.ndim != 1
        or cate.shape != probability.shape
        or not np.isfinite(cate).all()
        or not np.isfinite(probability).all()
        or not np.isfinite(scalars).all()
    ):
        raise ValueError("Inputs must be matching finite vectors and finite financial assumptions")
    if budget < 0 or cost <= 0 or value < 0 or not 0 <= capacity_fraction <= 1:
        raise ValueError("Invalid budget, cost, contribution value or capacity")
    if strategy not in STRATEGIES:
        raise ValueError("Unknown targeting strategy")
    n = len(cate)
    k = min(n, int(np.floor((budget + 1e-10) / cost)), int(np.floor(n * capacity_fraction)))
    feasible = strategy != "Treat everyone" or k >= n
    chosen = np.zeros(n, dtype=bool)
    if strategy != "No intervention" and feasible:
        if strategy == "Random targeting":
            order = np.argsort(-np.random.default_rng(seed).random(n), kind="stable")
        elif strategy == "Predictive targeting":
            order = np.argsort(-probability, kind="stable")
        else:
            order = np.argsort(-cate, kind="stable")
        if strategy == "Profit optimized":
            order = order[cate[order] * value - cost > 0]
        chosen[order[:k]] = True
    count = int(chosen.sum())
    conversions = float(cate[chosen].sum())
    spend = count * cost
    revenue = conversions * value
    profit = revenue - spend
    return chosen, {
        "strategy": strategy,
        "feasible": feasible,
        "targeted": count,
        "incremental_conversions": conversions,
        "spend": spend,
        "incremental_contribution": revenue,
        "incremental_profit": profit,
        "roi": profit / spend if spend else None,
        "cost_per_incremental_conversion": spend / conversions if conversions > 0 else None,
        "budget_utilization": spend / budget if budget else 0.0,
        "unspent_budget": budget - spend,
        "financial_basis": "Assumed contribution value and intervention cost; model-based simulation",
    }


def compare(cate, probability, **kwargs):
    return pd.DataFrame([allocate(cate, probability, strategy=s, **kwargs)[1] for s in STRATEGIES])


def sensitivity(cate, probability, budget, cost, value, capacity_fraction=1.0):
    rows = []
    for budget_scale in [0.25, 0.5, 1.0, 2.0]:
        for cost_scale in [0.5, 1.0, 2.0]:
            for value_scale in [0.5, 1.0, 2.0]:
                for effect_scale in [0.5, 1.0]:
                    for capacity in sorted({min(capacity_fraction, 0.1), capacity_fraction, 1.0}):
                        _, metrics = allocate(
                            np.asarray(cate) * effect_scale,
                            probability,
                            budget * budget_scale,
                            cost * cost_scale,
                            value * value_scale,
                            capacity,
                        )
                        rows.append(
                            {
                                "budget": budget * budget_scale,
                                "cost": cost * cost_scale,
                                "value": value * value_scale,
                                "effect_scale": effect_scale,
                                "capacity": capacity,
                                **metrics,
                            }
                        )
    return pd.DataFrame(rows)
