"""Rebuild inspectable figures and reports from executed pipeline outputs."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from causal_target.config import FEATURES
from causal_target.statistics import balance
from causal_target.utils import json_write

PALETTE = ["#6d5efc", "#0d9488", "#e59b31", "#e25d77", "#3b82f6", "#8991a8", "#c15ed6"]


def style():
    sns.set_theme(style="whitegrid", palette=PALETTE, font_scale=1.05)
    plt.rcParams.update(
        {
            "figure.dpi": 140,
            "savefig.dpi": 180,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titleweight": "bold",
            "figure.facecolor": "white",
        }
    )


def savefig(folder: Path, name: str):
    folder.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(folder / f"{name}.png", bbox_inches="tight")
    plt.close()


def eda(frame, out: Path):
    style()
    metrics, figures = out / "metrics", out / "figures"
    metrics.mkdir(parents=True, exist_ok=True)
    describe = frame[FEATURES].describe(percentiles=[0.01, 0.25, 0.5, 0.75, 0.99]).T
    describe["dtype"] = [str(frame[f].dtype) for f in FEATURES]
    describe["missing"] = frame[FEATURES].isna().sum()
    describe["iqr_outliers"] = [
        int(
            (
                (
                    frame[f]
                    < describe.loc[f, "25%"]
                    - 1.5 * (describe.loc[f, "75%"] - describe.loc[f, "25%"])
                )
                | (
                    frame[f]
                    > describe.loc[f, "75%"]
                    + 1.5 * (describe.loc[f, "75%"] - describe.loc[f, "25%"])
                )
            ).sum()
        )
        for f in FEATURES
    ]
    describe.to_csv(metrics / "feature_summary.csv", index_label="feature")
    corr = frame[FEATURES + ["treatment", "conversion", "visit", "exposure"]].corr()
    corr.to_csv(metrics / "correlations.csv", index_label="feature")
    bal = balance(frame)
    bal.to_csv(metrics / "balance.csv", index=False)
    hist = []
    fig, axes = plt.subplots(3, 4, figsize=(14, 9))
    for f, ax in zip(FEATURES, axes.flat, strict=True):
        edges = np.linspace(float(frame[f].min()), float(frame[f].max()) + 1e-9, 41)
        for t in [0, 1]:
            counts, _ = np.histogram(frame.loc[frame.treatment == t, f], bins=edges)
            ax.stairs(
                counts / counts.sum(), edges, label="Control" if t == 0 else "Treatment", alpha=0.8
            )
            for i, count in enumerate(counts):
                hist.append(
                    {
                        "feature": f,
                        "treatment": t,
                        "left": edges[i],
                        "right": edges[i + 1],
                        "count": int(count),
                    }
                )
        ax.set_title(f)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("Anonymized feature distributions by assignment", y=1.02)
    savefig(figures, "feature_distributions")
    pd.DataFrame(hist).to_csv(metrics / "feature_histograms.csv", index=False)
    plt.figure(figsize=(11, 8))
    sns.heatmap(corr, center=0, cmap="vlag", vmin=-1, vmax=1)
    plt.title("Feature and outcome correlations · descriptive only")
    savefig(figures, "correlations")
    plt.figure(figsize=(8, 5))
    plt.barh(bal.feature, bal.smd, color=PALETTE[0])
    plt.axvline(0.1, linestyle="--", color=PALETTE[2])
    plt.axvline(-0.1, linestyle="--", color=PALETTE[2])
    plt.xlabel("Standardized mean difference (treatment − control)")
    plt.title("Pre-treatment covariate balance")
    savefig(figures, "treatment_balance")
    return {
        "max_abs_smd": float(bal.abs_smd.max()),
        "features_over_01_smd": bal.loc[bal.abs_smd > 0.1, "feature"].tolist(),
        "outliers_retained": int(describe.iqr_outliers.sum()),
        "feature_semantics": "Anonymized; no demographic or commercial meanings inferred",
    }


def model_figures(
    out: Path,
    prediction_curves: dict,
    uplift: pd.DataFrame,
    subgroups: pd.DataFrame,
    scores: pd.DataFrame,
    strategies: pd.DataFrame,
):
    style()
    figdir = out / "figures"
    for kind, xlabel, ylabel in [
        ("roc", "False positive rate", "True positive rate"),
        ("pr", "Recall", "Precision"),
        ("calibration", "Predicted probability", "Observed frequency"),
    ]:
        plt.figure(figsize=(8, 5))
        for name, curves in prediction_curves.items():
            plt.plot(curves[kind]["x"], curves[kind]["y"], label=name)
        if kind in {"roc", "calibration"}:
            max_x = max(max(v[kind]["x"]) for v in prediction_curves.values())
            plt.plot([0, max_x], [0, max_x], "--", color="#8991a8", linewidth=1)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(f"Held-out {kind.upper()} · calibrated models")
        plt.legend()
        savefig(figdir, kind)
    for name, column in [("uplift", "incremental_conversions"), ("qini", "qini_gain")]:
        plt.figure(figsize=(10, 6))
        for model, values in uplift.groupby("model", sort=False):
            plt.plot(values.fraction * 100, values[column], label=model)
        plt.axhline(0, color="#8991a8", linewidth=1)
        plt.xlabel("Targeted population (%)")
        plt.ylabel(
            "HT incremental conversions" if name == "uplift" else "Normalized gain above random"
        )
        plt.title(f"Held-out {name} curves · released benchmark")
        plt.legend(fontsize=9)
        savefig(figdir, name)
    plt.figure(figsize=(9, 5))
    plt.errorbar(
        subgroups.decile,
        subgroups.dr_effect,
        yerr=[subgroups.dr_effect - subgroups.ci_low, subgroups.ci_high - subgroups.dr_effect],
        fmt="o",
        capsize=4,
        label="Held-out DR estimate ±95% CI",
    )
    plt.plot(subgroups.decile, subgroups.mean_predicted_cate, label="Predicted CATE")
    plt.axhline(0, color="#8991a8", linewidth=1)
    plt.xlabel("Predicted-effect decile (10 = highest)")
    plt.ylabel("Conversion probability difference")
    plt.title("Effect heterogeneity with uncertainty")
    plt.legend()
    savefig(figdir, "subgroup_effects")
    plt.figure(figsize=(9, 5))
    plt.hist(scores.cate, bins=60, color=PALETTE[0], alpha=0.85)
    plt.axvline(0, color=PALETTE[3], linestyle="--")
    plt.title("Selected model · predicted treatment-effect distribution")
    plt.xlabel("Estimated CATE (probability difference)")
    plt.ylabel("Observations")
    savefig(figdir, "cate_distribution")
    plt.figure(figsize=(10, 5))
    feasible = strategies[strategies.feasible]
    plt.barh(feasible.strategy, feasible.incremental_profit, color=PALETTE[1])
    plt.xlabel("Model-based incremental profit ($, simulated assumptions)")
    plt.title("Budget-constrained strategy comparison")
    savefig(figdir, "strategy_comparison")


def explain(model, x, out: Path):
    """SHAP explains the uncalibrated predictive LightGBM log odds, not causation."""
    import shap

    style()
    sample = x[: min(800, len(x))]
    explanation = shap.TreeExplainer(model)(sample)
    values = explanation.values
    if values.ndim == 3:
        values = values[:, :, 1]
    importance = pd.DataFrame(
        {"feature": FEATURES, "mean_abs_shap": np.abs(values).mean(axis=0)}
    ).sort_values("mean_abs_shap", ascending=False)
    importance.to_csv(out / "metrics/shap_importance.csv", index=False)
    shap.summary_plot(values, sample, feature_names=FEATURES, show=False)
    plt.title("Predictive LightGBM SHAP · uncalibrated log odds")
    savefig(out / "figures", "shap_summary")
    plt.figure(figsize=(8, 5))
    plt.barh(importance.feature[::-1], importance.mean_abs_shap[::-1], color=PALETTE[0])
    plt.xlabel("Mean absolute SHAP value (log odds)")
    plt.title("Predictive feature importance · not causal evidence")
    savefig(out / "figures", "shap_importance")
    f = FEATURES.index(importance.iloc[0].feature)
    plt.figure(figsize=(8, 5))
    plt.scatter(sample[:, f], values[:, f], s=12, alpha=0.4, color=PALETTE[0])
    plt.xlabel(FEATURES[f])
    plt.ylabel("SHAP contribution (log odds)")
    plt.title("Predictive dependence · anonymized feature")
    savefig(out / "figures", "shap_dependence")


def markdown_table(frame: pd.DataFrame) -> str:
    def cell(v):
        if isinstance(v, (float, np.floating)):
            return f"{v:.6g}"
        return str(v)

    lines = [
        "| " + " | ".join(frame.columns) + " |",
        "| " + " | ".join(["---"] * len(frame.columns)) + " |",
    ]
    lines += [
        "| " + " | ".join(cell(v) for v in row) + " |"
        for row in frame.itertuples(index=False, name=None)
    ]
    return "\n".join(lines)


def reports(
    root: Path,
    summary: dict,
    predictive: pd.DataFrame,
    causal: pd.DataFrame,
    strategies: pd.DataFrame,
):
    out = root / "reports"
    exp = summary["experiment"]
    source = (
        "SYNTHETIC TEST FIXTURE"
        if summary["data"]["synthetic"]
        else "Criteo corrected v2.1 release, uniform sample"
    )
    common = (
        f"Executed at {summary['created_at']}. Source: **{source}**. "
        f"Analyzed {summary['data']['rows_retained']:,} rows; final test {summary['splits']['test']:,}. "
        "Original campaign effects are not identifiable from this privacy-sampled release. "
        "Figures are benchmark estimates; financial numbers are assumption-based simulations.\n\n"
    )
    texts = {
        "experimentation.md": "# Experimentation report\n\n"
        + common
        + markdown_table(
            pd.DataFrame([exp]).T.reset_index().rename(columns={"index": "Metric", 0: "Value"})
        )
        + "\n\nTreatment denotes assignment, not actual exposure. Newcombe-Wilson confidence intervals accompany the two-proportion Z and equivalent uncorrected chi-square tests. Bootstrap resamples within each arm. Power is prospective at a 0.1 percentage-point MDE, alpha 0.05, preserving the observed allocation ratio. Practical significance requires the entire interval to exceed the MDE. These are descriptive full-sample ITT statistics, separate from model-selection evidence.\n",
        "model-evaluation.md": "# Model evaluation report\n\n"
        + common
        + f"Selected predictive baseline: **{summary['selected_predictive']}**. Selected causal model: **{summary['selected_causal']}**.\n\n"
        + markdown_table(predictive.drop(columns="confusion_matrix", errors="ignore"))
        + "\n\n"
        + markdown_table(causal)
        + "\n\nPredictive selection uses validation average precision (log loss tie-break); thresholds maximize validation F1. Calibration uses a distinct partition. Causal selection maximizes the validation lower normal confidence bound on DR incremental conversion rate at the configured capacity. Test data never changes the selected model. AUUC and Qini integrate Horvitz–Thompson cumulative gain divided by test N over targeting fraction. Confidence intervals condition on the fitted model and propensity; they do not include training or selection uncertainty. Comparisons are exploratory, without multiplicity correction.\n",
        "executive_summary/report.md": "# Executive decision brief\n\n"
        + common
        + f"The released sample's control conversion rate is {exp['control_rate']:.3%}; treatment conversion is {exp['treatment_rate']:.3%}. "
        f"The ITT difference is {exp['ate']:.3%} (95% CI {exp['ci_low']:.3%} to {exp['ci_high']:.3%}).\n\n"
        + markdown_table(
            strategies[
                [
                    "strategy",
                    "feasible",
                    "targeted",
                    "incremental_conversions",
                    "spend",
                    "incremental_profit",
                    "roi",
                ]
            ]
        )
        + "\n\nUse this benchmark to demonstrate decision methodology, not to forecast Criteo revenue. A production rollout requires a new randomized holdout, measured contribution margins and treatment costs, consent/eligibility rules and a staged experiment. Prefer no intervention when estimated marginal profit is nonpositive; a positive point estimate alone does not establish reliable gain.\n",
        "eda.md": "# Exploratory analysis\n\n"
        + common
        + f"Quality checks: {json.dumps(summary['quality'], indent=2)}\n\n"
        + f"Balance and feature summary: {json.dumps(summary['eda'], indent=2)}\n\n"
        + "Feature values are anonymized projections: tails and matching rows are retained. No deduplication is justified without an original customer/time key. Observation IDs identify source positions, not real customers. Visit and exposure are excluded from predictors. See feature_summary.csv for dtypes, missingness, quantiles and IQR outlier counts; correlations.csv for descriptive relationships.\n",
    }
    for name, content in texts.items():
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    json_write(out / "metrics/summary.json", summary)
