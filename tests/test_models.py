from dataclasses import replace

import numpy as np
import pytest

from causal_target.causal import train_causal
from causal_target.config import Config
from causal_target.data import partition, synthetic
from causal_target.predictive import features, train_predictive


def test_prediction_preprocessing_is_fit_on_train_only(sample):
    parts = partition(sample, 42)
    cfg = Config(trees=20, optuna_trials=0)
    models, _ = train_predictive(parts, cfg)
    scaler = models["Logistic regression"].base.steps[1][1]
    np.testing.assert_allclose(scaler.mean_, features(parts["train"]).mean(axis=0))
    for model in models.values():
        p = model.predict_proba(features(parts["test"]))
        assert len(p) == len(parts["test"])
        assert ((p >= 0) & (p <= 1)).all()


def test_meta_learners_recover_known_effect_ranking():
    frame = synthetic(16000, 5)
    parts = partition(frame, 42)
    cfg = Config(trees=100, optuna_trials=0, threads=2)
    models, nuisance, diagnostics = train_causal(parts["train"], cfg)
    xt = features(parts["test"])
    positive = parts["test"].true_cate.to_numpy() > 0
    for name, model in models.items():
        tau = model.predict(xt)
        assert np.isfinite(tau).all(), name
        assert tau[positive].mean() > tau[~positive].mean() + 0.04, name
    assert diagnostics["crossfit_folds"] == 3
    assert len(nuisance.outcomes(xt)[0]) == len(xt)


def test_config_validation():
    for kwargs in [
        {"budget": -1},
        {"sample_rows": 5},
        {"threads": 0},
        {"crossfit_folds": 1},
        {"assignment_probability": 1},
    ]:
        with pytest.raises(ValueError):
            replace(Config(), **kwargs)
    for kwargs in [{"budget": np.nan}, {"trees": 1.2}, {"seed": -1}]:
        with pytest.raises(ValueError):
            replace(Config(), **kwargs)
