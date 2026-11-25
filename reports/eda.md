# Exploratory analysis

Executed at 2026-11-25T09:26:35.596160+00:00. Source: **Criteo corrected v2.1 release, uniform sample**. Analyzed 500,000 rows; final test 100,000. Original campaign effects are not identifiable from this privacy-sampled release. Figures are benchmark estimates; financial numbers are assumption-based simulations.

Quality checks: {
  "rows": 500000,
  "columns": 17,
  "missing": {
    "observation_id": 0,
    "f0": 0,
    "f1": 0,
    "f2": 0,
    "f3": 0,
    "f4": 0,
    "f5": 0,
    "f6": 0,
    "f7": 0,
    "f8": 0,
    "f9": 0,
    "f10": 0,
    "f11": 0,
    "treatment": 0,
    "conversion": 0,
    "visit": 0,
    "exposure": 0
  },
  "matching_feature_rows": 3973,
  "matching_complete_rows": 2878,
  "conversion_events": 1456,
  "treatment_share": 0.850536,
  "exposed_controls": 0,
  "conversion_without_visit": 0
}

Balance and feature summary: {
  "max_abs_smd": 0.04679442569613457,
  "features_over_01_smd": [],
  "outliers_retained": 341594,
  "feature_semantics": "Anonymized; no demographic or commercial meanings inferred"
}

Feature values are anonymized projections: tails and matching rows are retained. No deduplication is justified without an original customer/time key. Observation IDs identify source positions, not real customers. Visit and exposure are excluded from predictors. See feature_summary.csv for dtypes, missingness, quantiles and IQR outlier counts; correlations.csv for descriptive relationships.
