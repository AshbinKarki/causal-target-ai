import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

from app.components.data import load_bundle
from causal_target.config import Config
from causal_target.inference import predict
from causal_target.monitoring import drift
from causal_target.pipeline import run


def test_complete_synthetic_pipeline_and_batch_inference(tmp_path):
    root = Path(__file__).resolve().parents[1]
    cfg = Config(sample_rows=4000, trees=20, optuna_trials=0, bootstrap_reps=30, threads=2)
    result = run(root, cfg, source="synthetic", output=tmp_path)
    assert result["data"]["synthetic"] is True
    bundle = load_bundle(tmp_path / "reports")
    assert len(bundle["targeting"]) == 800
    assert bundle["summary"]["mlflow_run_id"]
    from causal_target.data import synthetic

    batch = synthetic(30, 3)
    path = tmp_path / "batch.csv"
    batch.to_csv(path, index=False)
    predictions = predict(path, tmp_path / "artifacts/models.joblib", tmp_path / "predictions.csv")
    assert len(predictions) == 30
    loaded = joblib.load(tmp_path / "artifacts/models.joblib")
    assert loaded["selected_causal"] == result["selected_causal"]
    assert json.loads((tmp_path / "reports/metrics/summary.json").read_text())["data"]["synthetic"]


def test_missing_model_and_dashboard_errors(tmp_path):
    with pytest.raises(FileNotFoundError, match="Model artifact missing"):
        predict(tmp_path / "input.csv", tmp_path / "missing.joblib", tmp_path / "out.csv")
    with pytest.raises(FileNotFoundError, match="Missing pipeline outputs"):
        load_bundle(tmp_path)


def test_drift_detects_shift_and_preserves_reference_bins(sample):
    shifted = sample.copy()
    shifted["f0"] += 4
    results = drift(sample, shifted).set_index("feature")
    assert results.loc["f0", "psi_alert"]
    assert results.loc["f1", "psi"] == pytest.approx(0)
    assert np.isfinite(results.psi).all()
    with pytest.raises(ValueError):
        drift(pd.DataFrame(), sample)
