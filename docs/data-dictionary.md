# Data dictionary

Source: [Criteo Uplift Prediction Dataset](https://ailab.criteo.com/criteo-uplift-prediction-dataset/), corrected v2.1. The downloaded archive has 16 original columns and 13,979,592 rows. Some prose on the historical webpage refers to 11 features; the actual corrected file and field list contain **12**, f0–f11. The schema is checked against the file rather than inferred from that prose.

| Field | Stored type | Meaning | Model role |
| --- | --- | --- | --- |
| f0, f1, f2, f3, f4, f5 | float32 | Anonymized, randomly projected baseline features | Allowed predictors |
| f6, f7, f8, f9, f10, f11 | float32 | Anonymized, randomly projected baseline features | Allowed predictors |
| treatment | int8, binary | Randomized advertising eligibility/assignment indicator | Treatment; S-learner input only by design |
| conversion | int8, binary | Observed conversion outcome | Primary outcome; never a predictor |
| visit | int8, binary | Observed visit outcome | Descriptive only; excluded predictor |
| exposure | int8, binary | Actual advertising exposure after assignment | Post-treatment; excluded predictor |
| observation_id | int64 | Added zero-based position in corrected source file | Audit/export identifier only |

`exposure` is not an observed treatment effect, even though the historical field description uses that phrase. Conditioning on exposure would change the estimand and risk post-treatment selection bias. The primary analysis is intention-to-treat.

## Generated fields

| Field | Meaning and units |
| --- | --- |
| probability | Sigmoid-calibrated predicted conversion probability under the released assignment mixture |
| cate | Estimated conditional average treatment effect, probability difference |
| incremental_value | `cate × assumed contribution − assumed intervention cost`, currency per observation |
| recommended | Boolean from the current allocation constraints and chosen policy |
| cate_ci_low / cate_ci_high | Forest-based approximate CATE bounds only when supported by the selected learner |
| dr_increment_per_customer | Doubly robust gain over no treatment, divided by all evaluation rows |
| dr_incremental_conversions | DR gain per customer multiplied by evaluation cohort size |
| qini | Integral of normalized HT cumulative gain minus random diagonal |
| auuc | Integral of normalized HT cumulative gain over population fraction |
| psi | Population stability index using training/reference-defined bins |

The synthetic test generator adds `true_cate`, known by construction and never supplied to a learner. It is not present in Criteo data. Per-feature observed ranges, distributions, missing values, dtypes and outlier counts are in `reports/metrics/feature_summary.csv`.

Matching feature rows and matching full records are counted and retained. Neither equality establishes duplicate real users because no original identity/time key is released. Source-row IDs must remain unique. No demographic meanings are assigned to the projected features.
