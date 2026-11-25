"""Read precomputed reports without loading executable model files."""

import json
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def report_root() -> Path:
    return Path(os.environ.get("CAUSAL_TARGET_REPORTS", ROOT / "reports"))


def load_bundle(folder: Path) -> dict:
    required = [
        "summary.json",
        "predictive_test.csv",
        "causal_test.csv",
        "targeting.parquet",
        "uplift_curves.csv",
        "strategies.csv",
        "subgroups.csv",
        "predictive_curves.json",
        "feature_summary.csv",
        "feature_histograms.csv",
        "correlations.csv",
        "balance.csv",
        "shap_importance.csv",
        "drift.csv",
        "stability.csv",
        "causal_validation.csv",
    ]
    missing = [name for name in required if not (folder / "metrics" / name).exists()]
    if missing:
        raise FileNotFoundError("Missing pipeline outputs: " + ", ".join(missing))
    bundle = {}
    for name in required:
        path = folder / "metrics" / name
        if path.suffix == ".json":
            value = json.loads(path.read_text(encoding="utf-8"))
        elif path.suffix == ".parquet":
            value = pd.read_parquet(path)
        else:
            value = pd.read_csv(path)
        bundle[path.stem] = value
    if bundle["targeting"].empty:
        raise ValueError("Scored cohort is empty; regenerate pipeline outputs")
    return bundle
