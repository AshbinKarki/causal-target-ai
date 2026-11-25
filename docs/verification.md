# Verification evidence

Local verification date: 2026-11-25. These statements distinguish execution from configuration.

## Data and modeling

- Official Criteo-owned pinned v2.1 archive downloaded: 311,422,618 bytes.
- Publisher SHA-256 and gzip CRC verified; all 13,979,592 source rows scanned and schema-validated.
- Uniform 500,000-row sample retained. Final partitions: 300,000 training, 50,000 calibration, 50,000 selection, 100,000 test.
- Three predictive models and five causal learners trained and evaluated. Causal Forest DML used 60,000 training rows.
- Real demo pipeline completed, including SQL, EDA, reports, SHAP, optimization, monitoring and MLflow run logging.
- Synthetic known-effect smoke pipeline also completed in a separate output directory; not used as real-data performance evidence.

## Automated checks

- **48 tests passed** in the complete local Pytest run, with **88% package statement coverage**.
- Ruff lint and formatting checks passed for source, app, tests and scripts.
- The real-data portable report-bundle consistency check passed.
- Offline configured secret-pattern scan found no matches in publishable files. This is a focused pattern scan, not a guarantee that all possible secrets or sensitive content have been detected.
- Git whitespace checks passed before publication.

The seven emitted warnings concern upstream deprecations in Matplotlib/Seaborn/SHAP, scikit-learn/SciPy and SQLAlchemy/MLflow. They did not cause failing tests; versions are locked for reproducibility.

## Application checks

- Streamlit AppTest rendered all eight navigation views without exceptions.
- AppTest checked zero-budget recalculation: zero targeting and zero budget utilization.
- A separate clean dashboard environment was installed from the 36-package hashed runtime lock, independently of the training environment.
- Actual server health endpoint returned HTTP 200.
- Browser QA checked desktop layout at 1440×1000 and mobile layout at 390×844, sidebar navigation, budget editing and recalculation.
- Actual browser scenario export produced a CSV with 100,000 rows and 8,408 recommended observations under default assumptions; the saved CSV was parsed to confirm schema and count.
- Real screenshots are in docs/screenshots. They are captures of the running app, not design mockups.

## Explicit limits

- Docker is not installed on this host. Local Docker build/container execution is not verified. A remote CI container job is configured; its eventual status must be recorded after it runs.
- Full 13.98-million-row **model training** was not executed. Scanning the archive does not mean all rows trained the models.
- No live production monitoring stream or real marketing campaign was deployed.
- A public hosting URL is not claimed until a hosting service reports a successful deployment and the app is checked.
- Notebook files are generated review artifacts with executable inspection cells; they were not executed in a notebook kernel. Their narrative results and linked figures come from the executed Python pipeline.
- Figures and calculations are benchmark evidence, not actual Criteo financial results.

See PROJECT_STATUS.md for remote publication and CI updates, and reports/metrics/summary.json for the exact executed run metadata.
