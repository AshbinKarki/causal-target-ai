"""Batch inference on trusted local artifacts with explicit input contracts."""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from causal_target.config import FEATURES
from causal_target.predictive import features
from causal_target.utils import sha256


def predict(input_path: Path, model_path: Path, output_path: Path):
    if not model_path.exists():
        raise FileNotFoundError("Model artifact missing; run the training pipeline first")
    manifest_path = model_path.with_name("model_manifest.json")
    if not manifest_path.exists() or json.loads(manifest_path.read_text())["sha256"] != sha256(
        model_path
    ):
        raise ValueError("Model integrity manifest missing or checksum mismatch")
    frame = (
        pd.read_parquet(input_path) if input_path.suffix == ".parquet" else pd.read_csv(input_path)
    )
    if frame.empty or set(FEATURES) - set(frame):
        raise ValueError("Batch must contain rows and every baseline feature")
    x = features(frame)
    if not np.isfinite(x).all():
        raise ValueError("Batch contains missing or nonfinite baseline features")
    # A checksum is integrity protection, not a safe unpickler. Never load untrusted joblib.
    bundle = joblib.load(model_path)
    result = pd.DataFrame(
        {
            "observation_id": frame.get("observation_id", pd.Series(np.arange(len(frame)))),
            "probability": bundle["predictive"][bundle["selected_predictive"]].predict_proba(x),
            "cate": bundle["causal"][bundle["selected_causal"]].predict(x),
        }
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    return result
