# Statistical and causal methodology

## Estimand and identification

Let T be assignment, Y conversion, X baseline features, and Y(1), Y(0) potential outcomes. The target is τ(x)=E[Y(1)−Y(0)|X=x] **within the released benchmark distribution**. We observe only one potential outcome per row.

Identification requires consistency, no interference, positivity 0<e(x)<1 and exchangeability Y(t) ⟂ T | X in the analyzed release. The source pools incrementality experiments; the corrected version addresses advertiser-related leakage in the first release. Privacy-oriented nonuniform subsampling prevents recovery of original campaign lift. We therefore do not equate benchmark effects to original-population causal effects.

The original per-trial assignment probabilities and advertiser identifiers are absent. The default constant e is the assignment fraction estimated on training rows only. `assignment_probability` can instead supply a documented known design probability. No arbitrary propensity clipping hides poor overlap: the supported benchmark pipeline rejects allocation fractions outside [0.05,0.95]. SMD and assignment-prediction AUC are diagnostics; neither proves identification.

## Data partitions and leakage controls

Uniform sampling occurs independently of treatment/outcome. A seeded split then creates 60% train, 10% calibration, 10% selection and 20% final test, stratified on (T,Y). Calibration and selection are distinct. Only f0–f11 can enter baseline predictors. Exposure and visit are post-assignment variables/outcomes; conditioning on them could introduce bias. Source row ID and synthetic true CATE are excluded.

## Experimentation

The ITT estimate is mean(Y|T=1)−mean(Y|T=0). Report two-sided Z and equivalent uncorrected chi-square tests, Newcombe–Wilson difference intervals and a within-arm nonparametric bootstrap. For Bernoulli outcomes, drawing binomial counts from observed arm rates is exactly the within-arm bootstrap distribution of arm means. Newcombe intervals remain nondegenerate in zero-event cases where an ordinary bootstrap collapses.

Relative lift divides the absolute difference by the control rate and is undefined when that rate is zero. Cohen's h is 2 asin(sqrt(p1))−2 asin(sqrt(p0)). Prospective power/sample size use alpha 0.05, an explicitly stated 0.001 absolute MDE, the observed allocation ratio and 80% target power. This is not post-hoc observed power. Practical significance requires the entire primary interval to exceed the stated MDE; financial significance is a separate question.

## Learners

- **S:** train m(x,t) and subtract m(x,1)−m(x,0). Shrinkage can suppress treatment interactions.
- **T:** fit m1 and m0 separately and subtract. An imbalanced control arm may yield a noisy m0.
- **X:** create imputed effects D1=Y−m0(X) and D0=m1(X)−Y using out-of-fold nuisance estimates, regress each by arm, and combine e(X)τ0(X)+(1−e(X))τ1(X).
- **DR:** fit a regression to cross-fitted pseudo-outcomes Γ=m1−m0+T(Y−m1)/e−(1−T)(Y−m0)/(1−e). This reduces first-stage overfitting and uses the randomization assumption explicitly.
- **Causal Forest DML:** honest forest using cross-fitted residualized treatment/outcome moments, discrete outcome/treatment and a constant propensity estimator. Demo training is capped for resources.

The DR final regression is bounded to the feasible [−1,1] range for a binary outcome. This does not prove calibration or individual causal accuracy. The X-learner is similarly bounded. No observed individual ground truth exists in Criteo; synthetic known-CATE tests check implementation behavior only.

## Policy evaluation

For a fixed policy π(x)∈{0,1}, incremental value over never treating is E[π(X)τ(X)]. The IPW estimator averages π[T Y/e−(1−T)Y/(1−e)]. The DR estimator averages πΓ using nuisance predictions trained independently of final test outcomes.

Absolute DR policy value uses a0=m0+(1−T)(Y−m0)/(1−e) and a1=m1+T(Y−m1)/e, averaging (1−π)a0+πa1. Subtracting the no-treatment value gives mean(πΓ), which is verified in tests. These are conversion probabilities, not dollars.

For ranked rows, the uplift curve at k/N is the cumulative HT effect sum divided by total N. It begins at zero and ends at the full-cohort HT ATE. AUUC is its trapezoid integral over [0,1]. Qini subtracts the area under the diagonal from zero to the endpoint. Display curves use 101 points; scalar metrics integrate every ordered row. Stable tie-breaking uses fixed input order, never outcome or treatment.

Normal intervals use the empirical variance of policy contributions; nonparametric bootstrap resamples rows while keeping the fitted policy contributions fixed. Pairwise comparisons bootstrap **paired differences** (πA−πB)Γ, retaining policy covariance. The random policy is seeded and identical across the evaluation and financial tables. These intervals do not retrain models or reselect thresholds; they are fixed-model uncertainty, not end-to-end uncertainty. Quantile and half-test comparisons are exploratory. No multiplicity correction is claimed.

## Financial optimization

With assumed contribution v, equal cost c, budget B and maximum count K, maximize Σ ai(v τi−c) subject to c Σai≤B, Σai≤K, ai∈{0,1}. Sort descending by τi (or equivalently vτi−c for nonnegative v), retain strictly positive marginal profits, and choose up to min(floor(B/c),K). An exchange argument proves optimality: replacing a chosen lower-value item with an unchosen higher-value item preserves feasibility and cannot reduce profit.

This formulation ignores uncertainty penalties, varying costs and interference. The simulator exposes budget, c, v, capacity and an effect-scale stress assumption. Model-implied profit and separately estimated held-out DR policy outcomes are kept distinct. Neither is realized business revenue.

## Explanations and monitoring

Tree SHAP is applied to the uncalibrated predictive LightGBM log-odds model on a bounded test-feature sample. It does not explain a causal mechanism, and its features remain anonymous. CATE distributions, held-out DR score-decile intervals and optional forest intervals provide effect diagnostics. PSI and KS compare reference/current baseline distributions; they cannot establish causal-effect stability or fairness.

## Sources

- [Criteo dataset and erratum](https://ailab.criteo.com/criteo-uplift-prediction-dataset/)
- [EconML DR learning](https://www.pywhy.org/EconML/spec/estimation/dr.html)
- [EconML CausalForestDML](https://www.pywhy.org/EconML/_autosummary/econml.dml.CausalForestDML.html)
- [scikit-learn probability calibration](https://scikit-learn.org/stable/modules/calibration.html)
- [LightGBM Python API](https://lightgbm.readthedocs.io/en/stable/Python-API.html)

APIs are locked in uv.lock; online stable documentation may describe newer versions than the selected compatibility set.
