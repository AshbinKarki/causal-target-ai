"""S/T/X learners, cross-fitted DR learner and optional honest Causal Forest DML."""

import logging
from dataclasses import dataclass

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.model_selection import StratifiedKFold, train_test_split

from causal_target.config import Config
from causal_target.predictive import classifier, features, regressor

LOG = logging.getLogger(__name__)


class ConstantPropensity(ClassifierMixin, BaseEstimator):
    """Cloneable constant design-probability estimator for randomized designs."""

    def __init__(self, probability=0.85):
        self.probability = probability

    def fit(self, X, y):
        self.classes_ = np.array([0, 1])
        self.n_features_in_ = X.shape[1]
        return self

    def predict_proba(self, X):
        return np.tile([1 - self.probability, self.probability], (len(X), 1))

    def predict(self, X):
        return np.full(len(X), int(self.probability >= 0.5))


@dataclass
class SLearner:
    model: object

    def predict(self, x):
        p1 = self.model.predict_proba(np.column_stack([x, np.ones(len(x))]))[:, 1]
        p0 = self.model.predict_proba(np.column_stack([x, np.zeros(len(x))]))[:, 1]
        return p1 - p0


@dataclass
class TLearner:
    control: object
    treated: object

    def outcomes(self, x):
        return self.control.predict_proba(x)[:, 1], self.treated.predict_proba(x)[:, 1]

    def predict(self, x):
        p0, p1 = self.outcomes(x)
        return p1 - p0


@dataclass
class XLearner:
    control_effect: object
    treated_effect: object
    propensity: float

    def predict(self, x):
        # X-learner weighting: e(x)*tau0(x) + (1-e(x))*tau1(x).
        return np.clip(
            self.propensity * self.control_effect.predict(x)
            + (1 - self.propensity) * self.treated_effect.predict(x),
            -1,
            1,
        )


@dataclass
class DRLearner:
    model: object

    def predict(self, x):
        return np.clip(self.model.predict(x), -1, 1)


@dataclass
class ForestLearner:
    model: object

    def predict(self, x):
        return np.asarray(self.model.effect(x)).ravel()

    def interval(self, x):
        lo, hi = self.model.effect_interval(x, alpha=0.05)
        return np.asarray(lo).ravel(), np.asarray(hi).ravel()


def fit_t(x, y, t, cfg):
    models = [classifier(cfg).fit(x[t == arm], y[t == arm]) for arm in [0, 1]]
    return TLearner(*models)


def train_causal(train, cfg: Config):
    from causal_target.evaluation import dr_scores

    x, y, t = features(train), train.conversion.to_numpy(), train.treatment.to_numpy()
    e = cfg.assignment_probability if cfg.assignment_probability is not None else float(t.mean())
    if not 0.05 <= e <= 0.95:
        raise ValueError("Inadequate arm overlap for supported benchmark analysis")
    LOG.info("Training S/T/X learners and cross-fitted nuisance estimates")
    s = SLearner(classifier(cfg).fit(np.column_stack([x, t]), y))
    nuisance = fit_t(x, y, t, cfg)
    folds = StratifiedKFold(cfg.crossfit_folds, shuffle=True, random_state=cfg.seed)
    m0, m1 = np.zeros(len(x)), np.zeros(len(x))
    for fit, holdout in folds.split(x, 2 * t + y):
        local = fit_t(x[fit], y[fit], t[fit], cfg)
        m0[holdout], m1[holdout] = local.outcomes(x[holdout])
    x_model = XLearner(
        regressor(cfg).fit(x[t == 0], m1[t == 0] - y[t == 0]),
        regressor(cfg).fit(x[t == 1], y[t == 1] - m0[t == 1]),
        e,
    )
    dr = DRLearner(regressor(cfg).fit(x, dr_scores(y, t, m0, m1, e)))
    models = {"S-learner": s, "T-learner": nuisance, "X-learner": x_model, "DR-learner": dr}
    diagnostics = {
        "propensity": e,
        "propensity_source": "configured design probability"
        if cfg.assignment_probability is not None
        else "training assignment fraction; original trial probability unavailable",
        "crossfit_folds": cfg.crossfit_folds,
        "forest_requested": cfg.causal_forest,
        "forest_rows": 0,
        "forest_status": "disabled by profile",
    }
    if cfg.causal_forest:
        try:
            from econml.dml import CausalForestDML
        except ImportError:
            diagnostics["forest_status"] = "econml optional extra not installed"
            LOG.warning(diagnostics["forest_status"])
        else:
            idx = np.arange(len(x))
            if len(idx) > cfg.forest_rows:
                idx, _ = train_test_split(
                    idx, train_size=cfg.forest_rows, stratify=2 * t + y, random_state=cfg.seed
                )
            LOG.info("Training Causal Forest DML on %s training rows", len(idx))
            forest = CausalForestDML(
                model_y=classifier(cfg),
                model_t=ConstantPropensity(e),
                discrete_treatment=True,
                discrete_outcome=True,
                n_estimators=100,
                min_samples_leaf=100,
                max_depth=10,
                cv=3,
                n_jobs=cfg.threads,
                random_state=cfg.seed,
                honest=True,
                inference=True,
            )
            forest.fit(y[idx], t[idx], X=x[idx])
            models["Causal forest DML"] = ForestLearner(forest)
            diagnostics.update(forest_status="trained", forest_rows=len(idx))
    return models, nuisance, diagnostics
