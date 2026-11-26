# Model card — selected predictive and causal models

Version 1.0.0 · generated 2026-11-25T09:26:35.596160+00:00 · author Ashbin Karki.

## Intended use
Noncommercial portfolio research and demonstration of experimental targeting methodology. Inputs are twelve anonymous baseline projections. Outputs are purchase probability, estimated CATE, and scenario-specific allocation recommendations. IDs are source row positions, not contactable customers.

## Training and selection
The executed demo scanned **13,979,592** source rows, retained a uniform **500,000**-row sample, and reserved **100,000** observations for final evaluation. Validation selected **Random forest** for purchase prediction and **DR-learner** for causal ranking. Models use 300,000 training rows, with independent 50,000-row calibration and selection sets. The optional honest forest uses a uniform stratified 60,000-row training subset. Final test size is 100,000. The original design probability is unavailable: use training allocation fraction as a documented benchmark assumption. Random Forest uses sigmoid calibration; DR nuisance regressions use cross-fitting.

## Measured results
| model | roc_auc | pr_auc | log_loss | brier | f1 |
| --- | --- | --- | --- | --- | --- |
| Logistic regression | 0.955183 | 0.223549 | 0.0121778 | 0.00253971 | 0.301824 |
| Random forest | 0.964954 | 0.242422 | 0.014977 | 0.00261961 | 0.301115 |
| LightGBM | 0.965704 | 0.250833 | 0.0115455 | 0.00247153 | 0.322702 |

| model | qini | auuc | dr_incremental_conversions |
| --- | --- | --- | --- |
| S-learner | 0.000624091 | 0.00135148 | 117.17 |
| T-learner | 0.000523923 | 0.00125132 | 112.31 |
| X-learner | 0.000425487 | 0.00115288 | 88.7303 |
| DR-learner | 0.000656101 | 0.00138349 | 116.951 |
| Causal forest DML | 0.000627191 | 0.00135458 | 114.074 |
| Predictive targeting | 0.000672911 | 0.0014003 | 121.095 |
| Random targeting | 0.000233421 | 0.000960814 | 55.6344 |

At 30% targeting, the DR learner estimates **116.95 incremental conversions**, with a fixed-model normal 95% interval of **55.52 to 178.38**. The paired difference versus predictive targeting is **-4.14 conversions** (95% CI **-36.28 to +27.99**). This run does **not** establish superiority over the predictive baseline. LightGBM has the highest test average precision, but the preselected Random Forest is retained: test results do not retroactively change model selection.

## Uncertainty and failure modes
Rare outcomes, especially in control, cause noisy effect estimates. Policy/subgroup intervals are conditional on fitted models and a constant propensity; they exclude model selection, model-fitting and original privacy-sampling uncertainty. Forest intervals are stored for 1,000 held-out observations for inspection; they are approximate and do not reveal individual counterfactuals. The DR learner does not provide validated individual intervals. Poor calibration of nuisance regressions can increase finite-sample variance even under a correct propensity assumption. Matching anonymized rows may cross partitions because no valid deduplication identity exists.

## Exclusions and ethics
Exposure, visit, treatment and conversion cannot enter baseline features; treatment is appended only in the S learner by design. SHAP explains predictive LightGBM log odds, not causal feature effects. Protected attributes and real user context are unavailable, so no fairness guarantee is made. Do not use this release for real commercial targeting or decisions about financial/insurance/employment eligibility. Respect the data license and consent/eligibility requirements of any future experiment.

## Operations
Trusted-local joblib artifacts have SHA-256 manifests, package versions and data provenance. The app reads non-executable report tables. PSI/KS monitoring is implemented; no live monitoring service has been deployed. Retraining requires new representative experimental data and separate calibration/selection/test sets. Drift alerts alone must not trigger automatic campaign activation.
