# Model evaluation report

Executed at 2026-11-25T09:26:35.596160+00:00. Source: **Criteo corrected v2.1 release, uniform sample**. Analyzed 500,000 rows; final test 100,000. Original campaign effects are not identifiable from this privacy-sampled release. Figures are benchmark estimates; financial numbers are assumption-based simulations.

Selected predictive baseline: **Random forest**. Selected causal model: **DR-learner**.

| model | roc_auc | pr_auc | log_loss | brier | precision | recall | f1 | threshold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Logistic regression | 0.955183 | 0.223549 | 0.0121778 | 0.00253971 | 0.291667 | 0.312715 | 0.301824 | 0.112422 |
| Random forest | 0.964954 | 0.242422 | 0.014977 | 0.00261961 | 0.327935 | 0.278351 | 0.301115 | 0.0374728 |
| LightGBM | 0.965704 | 0.250833 | 0.0115455 | 0.00247153 | 0.355372 | 0.295533 | 0.322702 | 0.178154 |

| auuc | qini | model | targeted_fraction | dr_increment_per_customer | dr_ci_low | dr_ci_high | bootstrap_ci_low | bootstrap_ci_high | dr_incremental_conversions | ipw_increment_per_customer | dr_policy_value | dr_policy_value_ci_low | dr_policy_value_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.00135148 | 0.000624091 | S-learner | 0.3 | 0.0011717 | 0.000480626 | 0.00186278 | 0.000441752 | 0.00184248 | 117.17 | 0.00143939 | 0.00302425 | 0.0026356 | 0.0034129 |
| 0.00125132 | 0.000523923 | T-learner | 0.3 | 0.0011231 | 0.000490297 | 0.0017559 | 0.000456824 | 0.00177755 | 112.31 | 0.00131903 | 0.00297564 | 0.00253254 | 0.00341875 |
| 0.00115288 | 0.000425487 | X-learner | 0.3 | 0.000887303 | 0.000221509 | 0.0015531 | 0.000211296 | 0.00151088 | 88.7303 | 0.00114182 | 0.00273985 | 0.00234958 | 0.00313012 |
| 0.00138349 | 0.000656101 | DR-learner | 0.3 | 0.00116951 | 0.000555166 | 0.00178385 | 0.000580886 | 0.00177521 | 116.951 | 0.0013389 | 0.00302205 | 0.00255991 | 0.00348419 |
| 0.00135458 | 0.000627191 | Causal forest DML | 0.3 | 0.00114074 | 0.00045054 | 0.00183094 | 0.000426381 | 0.00182938 | 114.074 | 0.00140412 | 0.00299328 | 0.00260749 | 0.00337908 |
| 0.0014003 | 0.000672911 | Predictive targeting | 0.3 | 0.00121095 | 0.000518431 | 0.00190347 | 0.000508416 | 0.00189231 | 121.095 | 0.00147466 | 0.0030635 | 0.00267366 | 0.00345334 |
| 0.000960814 | 0.000233421 | Random targeting | 0.3 | 0.000556344 | 0.00023004 | 0.000882649 | 0.000245718 | 0.000874938 | 55.6344 | 0.000594295 | 0.00240889 | 0.00181529 | 0.00300248 |

Predictive selection uses validation average precision (log loss tie-break); thresholds maximize validation F1. Calibration uses a distinct partition. Causal selection maximizes the validation lower normal confidence bound on DR incremental conversion rate at the configured capacity. Test data never changes the selected model. AUUC and Qini integrate Horvitz–Thompson cumulative gain divided by test N over targeting fraction. Confidence intervals condition on the fitted model and propensity; they do not include training or selection uncertainty. Comparisons are exploratory, without multiplicity correction.
