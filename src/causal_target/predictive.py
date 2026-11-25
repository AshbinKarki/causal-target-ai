"""Train-only preprocessing, separate probability calibration and model selection."""

import logging
from dataclasses import dataclass

import numpy as np
import optuna
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.frozen import FrozenEstimator
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_curve
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from causal_target.config import FEATURES, Config

LOG = logging.getLogger(__name__)


def classifier(cfg: Config, **params):
    return LGBMClassifier(
        n_estimators=cfg.trees,
        learning_rate=0.04,
        num_leaves=15,
        min_child_samples=100,
        reg_lambda=5.0,
        verbosity=-1,
        n_jobs=cfg.threads,
        random_state=cfg.seed,
        deterministic=True,
        force_col_wise=True,
        **params,
    )


def regressor(cfg: Config):
    return LGBMRegressor(
        n_estimators=cfg.trees,
        learning_rate=0.03,
        num_leaves=10,
        min_child_samples=250,
        reg_lambda=10.0,
        verbosity=-1,
        n_jobs=cfg.threads,
        random_state=cfg.seed,
        deterministic=True,
        force_col_wise=True,
    )


def features(frame):
    """Explicit allowlist prevents accidental exposure, visit or outcome leakage."""
    return frame.loc[:, FEATURES].to_numpy(dtype=np.float64)


@dataclass
class PredictionModel:
    name: str
    base: object
    calibrated: object
    threshold: float

    def predict_proba(self, x):
        return self.calibrated.predict_proba(x)[:, 1]


def train_predictive(parts, cfg: Config):
    x, y = features(parts["train"]), parts["train"].conversion.to_numpy()
    xc, yc = features(parts["calibration"]), parts["calibration"].conversion.to_numpy()
    xv, yv = features(parts["selection"]), parts["selection"].conversion.to_numpy()
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    best_params = {}
    trials = []
    if cfg.optuna_trials:

        def objective(trial):
            model = classifier(cfg)
            model.set_params(
                num_leaves=trial.suggest_int("num_leaves", 7, 31),
                min_child_samples=trial.suggest_int("min_child_samples", 60, 300),
                reg_lambda=trial.suggest_float("reg_lambda", 1, 20, log=True),
            )
            model.fit(x, y)
            return average_precision_score(yv, model.predict_proba(xv)[:, 1])

        study = optuna.create_study(
            direction="maximize", sampler=optuna.samplers.TPESampler(seed=cfg.seed)
        )
        study.optimize(objective, n_trials=cfg.optuna_trials)
        best_params = study.best_params
        trials = [{"trial": t.number, "validation_ap": t.value, **t.params} for t in study.trials]
    boosted = classifier(cfg).set_params(**best_params)
    candidates = {
        "Logistic regression": make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            LogisticRegression(max_iter=500, random_state=cfg.seed),
        ),
        "Random forest": RandomForestClassifier(
            n_estimators=cfg.trees,
            max_depth=12,
            min_samples_leaf=50,
            max_samples=0.7,
            n_jobs=cfg.threads,
            random_state=cfg.seed,
        ),
        "LightGBM": boosted,
    }
    fitted = {}
    for name, base in candidates.items():
        LOG.info("Training predictive model: %s", name)
        base.fit(x, y)
        calibrated = CalibratedClassifierCV(FrozenEstimator(base), method="sigmoid")
        calibrated.fit(xc, yc)
        p = calibrated.predict_proba(xv)[:, 1]
        precision, recall, thresholds = precision_recall_curve(yv, p)
        f1 = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-15)
        threshold = float(thresholds[np.argmax(f1)])
        fitted[name] = PredictionModel(name, base, calibrated, threshold)
    return fitted, trials
