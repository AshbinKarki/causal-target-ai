"""Deterministic train/evaluate/report orchestration with local MLflow tracking."""

import importlib.metadata
import json
import logging
import time
from pathlib import Path

import joblib
import mlflow
import numpy as np
import pandas as pd
import psutil

from causal_target import __version__
from causal_target.causal import train_causal
from causal_target.config import Config
from causal_target.data import download, ingest, partition, synthetic, validate, warehouse
from causal_target.evaluation import (
    causal_metrics,
    dr_scores,
    paired_policy_difference,
    predictive_curves,
    predictive_metrics,
    subgroup_effects,
    top_policy,
)
from causal_target.monitoring import drift
from causal_target.optimization import allocate, compare, sensitivity
from causal_target.predictive import classifier, features, train_predictive
from causal_target.reporting import eda, explain, model_figures, reports
from causal_target.statistics import experiment, mean_interval
from causal_target.utils import json_write, now, sha256

LOG = logging.getLogger(__name__)


def run(root: Path, cfg: Config, source="criteo", output: Path | None = None):
    started = time.perf_counter()
    root = root.resolve()
    output = (output or root).resolve()
    metrics, artifacts = output / "reports/metrics", output / "artifacts"
    metrics.mkdir(parents=True, exist_ok=True)
    artifacts.mkdir(parents=True, exist_ok=True)
    if cfg.profile == "full" and psutil.virtual_memory().available < 12 * 1024**3:
        raise MemoryError(
            "Full training requires at least 12 GiB available RAM; use the demo profile"
        )
    if source == "synthetic":
        frame = synthetic(cfg.sample_rows or 20000, cfg.seed)
        provenance = {
            "synthetic": True,
            "source": "Known-effect synthetic testing fixture",
            "rows_retained": len(frame),
            "source_rows_scanned": len(frame),
            "seed": cfg.seed,
        }
    elif source == "criteo":
        path = ingest(root, cfg, download(root))
        frame = pd.read_parquet(path)
        provenance = json.loads(path.with_name("manifest.json").read_text())
    else:
        raise ValueError("source must be criteo or synthetic")
    quality = validate(frame)
    LOG.info("Validated %s rows; splitting data", len(frame))
    parts = partition(frame, cfg.seed)
    eda_summary = eda(frame, output / "reports")
    ab = experiment(frame, cfg.seed, cfg.bootstrap_reps)
    predictive, trials = train_predictive(parts, cfg)
    pd.DataFrame(trials).to_csv(metrics / "optuna_trials.csv", index=False)
    xv, xt = features(parts["selection"]), features(parts["test"])
    yv, yt = parts["selection"].conversion.to_numpy(), parts["test"].conversion.to_numpy()
    tv, tt = parts["selection"].treatment.to_numpy(), parts["test"].treatment.to_numpy()
    val_predictions = [
        predictive_metrics(name, yv, model.predict_proba(xv), model.threshold)
        for name, model in predictive.items()
    ]
    pred_best = sorted(val_predictions, key=lambda m: (-m["pr_auc"], m["log_loss"]))[0]["model"]
    test_predictions = [
        predictive_metrics(name, yt, model.predict_proba(xt), model.threshold)
        for name, model in predictive.items()
    ]
    curve_predictions = {
        name: predictive_curves(yt, model.predict_proba(xt)) for name, model in predictive.items()
    }
    json_write(metrics / "predictive_curves.json", curve_predictions)
    pd.DataFrame(val_predictions).to_csv(metrics / "predictive_validation.csv", index=False)
    pred_table = pd.DataFrame(test_predictions)
    pred_table.to_csv(metrics / "predictive_test.csv", index=False)
    causal, nuisance, diagnostics = train_causal(parts["train"], cfg)
    e = diagnostics["propensity"]
    v0, v1 = nuisance.outcomes(xv)
    m0, m1 = nuisance.outcomes(xt)
    val_scores = {name: model.predict(xv) for name, model in causal.items()}
    test_scores = {name: model.predict(xt) for name, model in causal.items()}
    val_scores.update(
        {
            "Predictive targeting": predictive[pred_best].predict_proba(xv),
            "Random targeting": np.random.default_rng(cfg.seed).random(len(xv)),
        }
    )
    test_scores.update(
        {
            "Predictive targeting": predictive[pred_best].predict_proba(xt),
            "Random targeting": np.random.default_rng(cfg.seed).random(len(xt)),
        }
    )
    val_metrics, test_metrics, curves = [], [], []
    for name in val_scores:
        LOG.info("Evaluating held-out policies: %s", name)
        val, _ = causal_metrics(
            name,
            val_scores[name],
            yv,
            tv,
            v0,
            v1,
            e,
            cfg.capacity_fraction,
            min(cfg.bootstrap_reps, 150),
            cfg.seed,
        )
        val_metrics.append(val)
        test, curve = causal_metrics(
            name,
            test_scores[name],
            yt,
            tt,
            m0,
            m1,
            e,
            cfg.capacity_fraction,
            cfg.bootstrap_reps,
            cfg.seed,
        )
        test_metrics.append(test)
        curves.append(curve)
    causal_best = max(
        (m for m in val_metrics if m["model"] in causal), key=lambda m: m["dr_ci_low"]
    )["model"]
    causal_table = pd.DataFrame(test_metrics)
    pd.DataFrame(val_metrics).to_csv(metrics / "causal_validation.csv", index=False)
    causal_table.to_csv(metrics / "causal_test.csv", index=False)
    uplift = pd.concat(curves, ignore_index=True)
    uplift.to_csv(metrics / "uplift_curves.csv", index=False)
    cate, probability = test_scores[causal_best], test_scores["Predictive targeting"]
    scores = pd.DataFrame(
        {
            "observation_id": parts["test"].observation_id.to_numpy(),
            "probability": probability,
            "cate": cate,
        }
    )
    if hasattr(causal[causal_best], "interval"):
        scores["cate_ci_low"], scores["cate_ci_high"] = causal[causal_best].interval(xt)
    if "Causal forest DML" in causal:
        interval_x = xt[: min(len(xt), 1000)]
        forest_lo, forest_hi = causal["Causal forest DML"].interval(interval_x)
        pd.DataFrame(
            {
                "observation_id": scores.observation_id.iloc[: len(interval_x)],
                "forest_cate": test_scores["Causal forest DML"][: len(interval_x)],
                "ci_low": forest_lo,
                "ci_high": forest_hi,
            }
        ).to_csv(metrics / "forest_intervals.csv", index=False)
    scores.to_parquet(metrics / "targeting.parquet", index=False, compression="zstd")
    sql_scores = scores.assign(treatment=tt, conversion=yt)
    warehouse(output, frame, sql_scores)
    groups = subgroup_effects(cate, yt, tt, m0, m1, e)
    groups.to_csv(metrics / "subgroups.csv", index=False)
    economics = dict(
        budget=cfg.budget,
        cost=cfg.intervention_cost,
        value=cfg.conversion_value,
        capacity_fraction=cfg.capacity_fraction,
    )
    strategies = compare(cate, probability, **economics)
    pseudo = dr_scores(yt, tt, m0, m1, e)
    candidate_policy = top_policy(cate, cfg.capacity_fraction)
    paired = []
    for baseline in ["Predictive targeting", "Random targeting"]:
        paired.append(
            {
                "candidate": causal_best,
                "baseline": baseline,
                **paired_policy_difference(
                    candidate_policy,
                    top_policy(test_scores[baseline], cfg.capacity_fraction),
                    pseudo,
                    cfg.bootstrap_reps,
                    cfg.seed,
                ),
            }
        )
    pd.DataFrame(paired).to_csv(metrics / "paired_policy_comparisons.csv", index=False)
    for i, row in strategies.iterrows():
        chosen, _ = allocate(cate, probability, strategy=row.strategy, **economics)
        observed, low, high = mean_interval(chosen * pseudo)
        strategies.loc[i, "heldout_dr_conversions"] = observed * len(yt)
        strategies.loc[i, "heldout_dr_conversions_ci_low"] = low * len(yt)
        strategies.loc[i, "heldout_dr_conversions_ci_high"] = high * len(yt)
        strategies.loc[i, "heldout_dr_profit"] = (
            observed * len(yt) * cfg.conversion_value - row.spend
        )
    strategies.to_csv(metrics / "strategies.csv", index=False)
    sensitivity(cate, probability, **economics).to_csv(metrics / "sensitivity.csv", index=False)
    drift(parts["train"], parts["test"]).to_csv(metrics / "drift.csv", index=False)
    # Assignment predictability is a diagnostic; no claim that it proves randomization.
    assignment = classifier(cfg).fit(features(parts["train"]), parts["train"].treatment)
    from sklearn.metrics import roc_auc_score

    diagnostics["assignment_test_auc"] = roc_auc_score(tt, assignment.predict_proba(xt)[:, 1])
    # Half-test stability describes sampling variability, without selecting a model.
    stability = []
    for name, ranking in test_scores.items():
        for half in [0, 1]:
            idx = np.arange(half, len(yt), 2)
            metric, _ = causal_metrics(
                name,
                ranking[idx],
                yt[idx],
                tt[idx],
                m0[idx],
                m1[idx],
                e,
                cfg.capacity_fraction,
                50,
                cfg.seed,
            )
            stability.append({"half": half, **metric})
    pd.DataFrame(stability).to_csv(metrics / "stability.csv", index=False)
    explain(predictive["LightGBM"].base, xt, output / "reports")
    model_figures(output / "reports", curve_predictions, uplift, groups, scores, strategies)
    versions = {
        name: importlib.metadata.version(name)
        for name in ["numpy", "pandas", "scikit-learn", "lightgbm", "streamlit", "mlflow-skinny"]
    }
    summary = {
        "created_at": now(),
        "project_version": __version__,
        "config": cfg.to_dict(),
        "data": provenance,
        "quality": quality,
        "eda": eda_summary,
        "experiment": ab,
        "splits": {k: len(v) for k, v in parts.items()},
        "selected_predictive": pred_best,
        "selected_causal": causal_best,
        "causal_diagnostics": diagnostics,
        "paired_policy_comparisons": paired,
        "package_versions": versions,
        "elapsed_seconds": time.perf_counter() - started,
        "hardware": {
            "logical_cpus": psutil.cpu_count(),
            "total_ram_gb": psutil.virtual_memory().total / 1e9,
            "threads_used": cfg.threads,
        },
        "uncertainty": "Fixed-model held-out sampling intervals; original design and training uncertainty excluded",
    }
    bundle = {
        "predictive": predictive,
        "causal": causal,
        "selected_predictive": pred_best,
        "selected_causal": causal_best,
        "config": cfg.to_dict(),
        "version": __version__,
    }
    model_path = artifacts / "models.joblib"
    joblib.dump(bundle, model_path, compress=3)
    json_write(
        artifacts / "model_manifest.json",
        {
            "sha256": sha256(model_path),
            "created_at": now(),
            "versions": versions,
            "source": provenance,
            "trusted_local_only": True,
        },
    )
    reports(output, summary, pred_table, causal_table, strategies)
    mlflow.set_tracking_uri("sqlite:///" + (output / "mlflow.db").as_posix())
    mlflow.set_experiment("CausalTarget AI")
    with mlflow.start_run(run_name=f"{source}-{cfg.profile}") as active:
        mlflow.log_params({**cfg.to_dict(), "source": source, "selected_causal": causal_best})
        for name, table in [("predictive", test_predictions), ("causal", test_metrics)]:
            for metric in table:
                prefix = metric["model"].replace(" ", "_")
                mlflow.log_metrics(
                    {
                        f"{name}.{prefix}.{k}": float(v)
                        for k, v in metric.items()
                        if isinstance(v, (float, int)) and np.isfinite(v)
                    }
                )
        mlflow.log_artifacts(str(metrics), artifact_path="evaluation")
        mlflow.log_artifact(str(artifacts / "model_manifest.json"), artifact_path="models")
        summary["mlflow_run_id"] = active.info.run_id
    json_write(metrics / "summary.json", summary)
    LOG.info(
        "Pipeline complete: %s rows, selected %s, %.1f seconds",
        len(frame),
        causal_best,
        summary["elapsed_seconds"],
    )
    return summary
