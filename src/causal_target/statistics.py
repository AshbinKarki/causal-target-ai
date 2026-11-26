"""Intention-to-treat statistics with explicit uncertainty and design limits."""

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, norm
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import (
    confint_proportions_2indep,
    proportion_effectsize,
    proportions_ztest,
)

from causal_target.config import FEATURES


def experiment(frame: pd.DataFrame, seed=42, reps=500, practical_lift=0.001) -> dict:
    groups = [frame.loc[frame.treatment == t, "conversion"].to_numpy() for t in [0, 1]]
    if any(len(g) == 0 for g in groups):
        raise ValueError("Both experiment arms need observations")
    n0, n1 = (len(g) for g in groups)
    s0, s1 = (int(g.sum()) for g in groups)
    p0, p1 = s0 / n0, s1 / n1
    delta = p1 - p0
    rng = np.random.default_rng(seed)
    # For Bernoulli outcomes, binomial resampling is exactly the within-arm bootstrap.
    draws = rng.binomial(n1, p1, reps) / n1 - rng.binomial(n0, p0, reps) / n0
    if s0 + s1 == 0 or s0 + s1 == n0 + n1:
        z, pvalue, chi_p = 0.0, 1.0, 1.0
    else:
        z, pvalue = proportions_ztest([s1, s0], [n1, n0])
        chi_p = chi2_contingency([[s1, n1 - s1], [s0, n0 - s0]], correction=False)[1]
    ci = confint_proportions_2indep(s1, n1, s0, n0, method="newcomb")
    effect = proportion_effectsize(p1, p0)
    # Prospective power at a stated minimum detectable effect; not post-hoc observed power.
    planning_p0 = float(np.clip(p0, 1e-5, 1 - practical_lift - 1e-5))
    planning_effect = abs(proportion_effectsize(planning_p0 + practical_lift, planning_p0))
    power_model = NormalIndPower()
    ratio = n1 / n0
    needed0 = power_model.solve_power(
        effect_size=planning_effect, power=0.8, alpha=0.05, ratio=ratio
    )
    return {
        "control_n": n0,
        "treatment_n": n1,
        "control_events": s0,
        "treatment_events": s1,
        "control_rate": p0,
        "treatment_rate": p1,
        "ate": delta,
        "relative_lift": delta / p0 if p0 else None,
        "ci_low": ci[0],
        "ci_high": ci[1],
        "bootstrap_ci_low": float(np.quantile(draws, 0.025)),
        "bootstrap_ci_high": float(np.quantile(draws, 0.975)),
        "z_statistic": z,
        "p_value": pvalue,
        "chi_square_p_value": chi_p,
        "cohen_h": effect,
        "significant_005": bool(pvalue < 0.05),
        "practical_lift_threshold": practical_lift,
        "practically_positive": bool(ci[0] > practical_lift),
        "planned_power_at_mde": power_model.power(
            planning_effect, nobs1=n0, alpha=0.05, ratio=ratio
        ),
        "required_total_n_80pct_power": int(np.ceil(needed0 * (1 + ratio))),
        "analysis": "Intention-to-treat difference within released benchmark sample",
        "interval": "95% Newcombe-Wilson; within-arm bootstrap also reported",
    }


def balance(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for f in FEATURES:
        control, treated = [frame.loc[frame.treatment == t, f] for t in [0, 1]]
        pooled = np.sqrt((control.var() + treated.var()) / 2)
        smd = (treated.mean() - control.mean()) / pooled if pooled else 0.0
        rows.append(
            {
                "feature": f,
                "control_mean": control.mean(),
                "treatment_mean": treated.mean(),
                "smd": smd,
                "abs_smd": abs(smd),
            }
        )
    return pd.DataFrame(rows)


def mean_interval(values: np.ndarray, alpha=0.05) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    if len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("At least two finite values required")
    mean = float(values.mean())
    half = norm.ppf(1 - alpha / 2) * values.std(ddof=1) / np.sqrt(len(values))
    return mean, mean - half, mean + half
