"""Held-out predictive metrics and explicitly normalized causal policy estimators."""

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from causal_target.statistics import mean_interval


def binary_inputs(y, t, propensity):
    y, t = np.asarray(y, dtype=float), np.asarray(t, dtype=float)
    if y.ndim != 1 or t.ndim != 1 or len(y) == 0 or len(y) != len(t):
        raise ValueError("Empty or mismatched outcomes and assignments")
    if not np.isin(y, [0, 1]).all() or not np.isin(t, [0, 1]).all():
        raise ValueError("Outcomes and assignments must be binary")
    if not 0 < propensity < 1:
        raise ValueError("Propensity must be strictly between zero and one")
    return y, t


def ipw_scores(y, t, propensity):
    y, t = binary_inputs(y, t, propensity)
    return t * y / propensity - (1 - t) * y / (1 - propensity)


def dr_scores(y, t, mu0, mu1, propensity):
    y, t = binary_inputs(y, t, propensity)
    mu0, mu1 = np.asarray(mu0), np.asarray(mu1)
    if mu0.shape != y.shape or mu1.shape != y.shape or not np.isfinite([mu0, mu1]).all():
        raise ValueError("Invalid nuisance predictions")
    return mu1 - mu0 + t * (y - mu1) / propensity - (1 - t) * (y - mu0) / (1 - propensity)


def policy_value(y, t, mu0, mu1, propensity, policy):
    y, t = binary_inputs(y, t, propensity)
    mu0, mu1 = np.asarray(mu0, dtype=float), np.asarray(mu1, dtype=float)
    if mu0.shape != y.shape or mu1.shape != y.shape or not np.isfinite([mu0, mu1]).all():
        raise ValueError("Invalid nuisance predictions")
    policy = np.asarray(policy, dtype=float)
    if policy.shape != y.shape or not np.isin(policy, [0, 1]).all():
        raise ValueError("Policy must be a binary vector matching the cohort")
    a0 = mu0 + (1 - t) * (y - mu0) / (1 - propensity)
    a1 = mu1 + t * (y - mu1) / propensity
    return mean_interval(policy * a1 + (1 - policy) * a0)


def top_policy(score, fraction):
    score = np.asarray(score, dtype=float)
    if score.ndim != 1 or not np.isfinite(score).all() or not 0 <= fraction <= 1:
        raise ValueError("Invalid policy score or targeting fraction")
    policy = np.zeros(len(score), dtype=int)
    # Stable tie breaking on source order, never on treatment or outcome.
    policy[np.argsort(-score, kind="stable")[: int(np.floor(len(score) * fraction))]] = 1
    return policy


def paired_policy_difference(candidate, baseline, pseudo_effect, reps=500, seed=42):
    """Paired DR gain difference, preserving covariance between two fixed policies."""
    candidate, baseline, pseudo_effect = map(np.asarray, [candidate, baseline, pseudo_effect])
    if candidate.shape != baseline.shape or candidate.shape != pseudo_effect.shape:
        raise ValueError("Paired policy vectors must align")
    difference = (candidate - baseline) * pseudo_effect
    estimate, lo, hi = mean_interval(difference)
    blo, bhi = bootstrap_mean(difference, reps, seed)
    return {
        "difference_per_customer": estimate,
        "ci_low": lo,
        "ci_high": hi,
        "bootstrap_ci_low": blo,
        "bootstrap_ci_high": bhi,
        "difference_conversions": estimate * len(difference),
        "conversions_ci_low": lo * len(difference),
        "conversions_ci_high": hi * len(difference),
    }


def bootstrap_mean(values, reps, seed=42):
    values = np.asarray(values, dtype=float)
    if len(values) < 2 or reps < 1:
        raise ValueError("Bootstrap requires at least two observations and one replicate")
    rng = np.random.default_rng(seed)
    means = np.empty(reps)
    for i in range(reps):
        means[i] = values[rng.integers(0, len(values), len(values))].mean()
    return tuple(np.quantile(means, [0.025, 0.975]))


def uplift_curve(score, y, t, propensity, points=101):
    """HT cumulative incremental outcomes / total N; zero origin.

    AUUC integrates normalized cumulative gain over targeted population fraction.
    Qini integrates gain minus the straight line joining (0,0) and (1,ATE_HT).
    These definitions deliberately avoid ambiguous library-specific scales.
    """
    score = np.asarray(score)
    effect = ipw_scores(y, t, propensity)
    if score.shape != effect.shape or not np.isfinite(score).all():
        raise ValueError("Invalid ranking scores")
    order = np.argsort(-score, kind="stable")
    cumulative = np.r_[0.0, np.cumsum(effect[order]) / len(effect)]
    idx = np.unique(np.linspace(0, len(effect), min(points, len(effect) + 1)).astype(int))
    fraction = idx / len(effect)
    # Metrics use every point, not the downsampled display curve.
    full_fraction = np.arange(len(effect) + 1) / len(effect)
    area = np.trapezoid(cumulative, full_fraction)
    qini = area - cumulative[-1] / 2
    table = pd.DataFrame(
        {
            "fraction": fraction,
            "gain_per_customer": cumulative[idx],
            "incremental_conversions": cumulative[idx] * len(effect),
            "random_gain": fraction * cumulative[-1],
            "qini_gain": cumulative[idx] - fraction * cumulative[-1],
        }
    )
    return table, {"auuc": float(area), "qini": float(qini)}


def causal_metrics(name, score, y, t, mu0, mu1, propensity, fraction=0.3, reps=150, seed=42):
    curve, metrics = uplift_curve(score, y, t, propensity)
    policy = top_policy(score, fraction)
    contribution = policy * dr_scores(y, t, mu0, mu1, propensity)
    mean, lo, hi = mean_interval(contribution)
    boot_lo, boot_hi = bootstrap_mean(contribution, reps, seed)
    value, value_lo, value_hi = policy_value(y, t, mu0, mu1, propensity, policy)
    metrics.update(
        model=name,
        targeted_fraction=float(policy.mean()),
        dr_increment_per_customer=mean,
        dr_ci_low=lo,
        dr_ci_high=hi,
        bootstrap_ci_low=boot_lo,
        bootstrap_ci_high=boot_hi,
        dr_incremental_conversions=mean * len(y),
        ipw_increment_per_customer=float(np.mean(policy * ipw_scores(y, t, propensity))),
        dr_policy_value=value,
        dr_policy_value_ci_low=value_lo,
        dr_policy_value_ci_high=value_hi,
    )
    curve["model"] = name
    return metrics, curve


def predictive_metrics(name, y, p, threshold):
    y, p = np.asarray(y), np.asarray(p)
    labels = p >= threshold
    two_classes = len(np.unique(y)) == 2
    return {
        "model": name,
        "roc_auc": roc_auc_score(y, p) if two_classes else None,
        "pr_auc": average_precision_score(y, p) if y.sum() else 0.0,
        "log_loss": log_loss(y, p, labels=[0, 1]),
        "brier": brier_score_loss(y, p),
        "precision": precision_score(y, labels, zero_division=0),
        "recall": recall_score(y, labels, zero_division=0),
        "f1": f1_score(y, labels, zero_division=0),
        "threshold": threshold,
        "confusion_matrix": confusion_matrix(y, labels, labels=[0, 1]).tolist(),
    }


def predictive_curves(y, p):
    fpr, tpr, _ = roc_curve(y, p)
    precision, recall, _ = precision_recall_curve(y, p)
    actual, predicted = calibration_curve(y, p, n_bins=10, strategy="quantile")

    def compress(a, b):
        idx = np.unique(np.linspace(0, len(a) - 1, min(len(a), 250)).astype(int))
        return {"x": a[idx].tolist(), "y": b[idx].tolist()}

    return {
        "roc": compress(fpr, tpr),
        "pr": compress(recall, precision),
        "calibration": {"x": predicted.tolist(), "y": actual.tolist()},
    }


def subgroup_effects(scores, y, t, mu0, mu1, propensity):
    quantile = pd.qcut(pd.Series(scores).rank(method="first"), 10, labels=False)
    pseudo = dr_scores(y, t, mu0, mu1, propensity)
    rows = []
    for group in sorted(quantile.unique()):
        mask = quantile.to_numpy() == group
        effect, lo, hi = mean_interval(pseudo[mask])
        rows.append(
            {
                "decile": int(group + 1),
                "n": int(mask.sum()),
                "dr_effect": effect,
                "ci_low": lo,
                "ci_high": hi,
                "mean_predicted_cate": float(np.mean(scores[mask])),
            }
        )
    return pd.DataFrame(rows)
