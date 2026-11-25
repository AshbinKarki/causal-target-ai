# Working on CausalTarget AI

Read PROJECT_STATUS.md before changing the project. Preserve provenance and never replace real benchmark metrics with synthetic outputs. Run Ruff and Pytest after changes; use the quick synthetic pipeline for integration checks and the demo Criteo pipeline for portfolio results.

Only f0–f11 are baseline predictors. Treatment is randomized assignment, exposure is post-treatment and visit is an outcome. Keep train, calibration/selection and final test observations separate. Select models on validation only. Financial inputs are assumptions, not observed Criteo business data.

Do not commit raw records, model pickle files, credentials or tracking databases. All data-derived public artifacts must retain the Criteo attribution and separate data license. Update PROJECT_STATUS.md with executed commands, measured results and verification limits.
