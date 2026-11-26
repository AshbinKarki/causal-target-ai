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
- A separate clean dashboard environment was installed from the 36-package hashed runtime lock, independently of the training environment; all eight pages passed AppTest in that environment too.
- Actual server health endpoint returned HTTP 200.
- Browser QA checked desktop layout at 1440×1000 and mobile layout at 390×844, sidebar navigation, budget editing and recalculation.
- Actual browser scenario export produced a CSV with 100,000 rows and 8,408 recommended observations under default assumptions; the saved CSV was parsed to confirm schema and count.
- Real screenshots are in docs/screenshots. They are captures of the running app, not design mockups.

## Explicit limits

- Docker is not installed on this host. Local Docker execution was not performed; remote Docker build and container health verification passed as recorded below.
- Full 13.98-million-row **model training** was not executed. Scanning the archive does not mean all rows trained the models.
- No live production monitoring stream or real marketing campaign was deployed.
- The hosted app is a portfolio demonstration of precomputed benchmark results; it is not an operational marketing system.
- Notebook files are generated review artifacts with executable inspection cells; they were not executed in a notebook kernel. Their narrative results and linked figures come from the executed Python pipeline.
- Figures and calculations are benchmark evidence, not actual Criteo financial results.

See PROJECT_STATUS.md for remote publication and CI updates, and reports/metrics/summary.json for the exact executed run metadata.

## Remote publication and Linux verification

- Public repository: [AshbinKarki/causal-target-ai](https://github.com/AshbinKarki/causal-target-ai).
- Complete implementation is on `main`; [PR #1](https://github.com/AshbinKarki/causal-target-ai/pull/1) was merged at `a7a581f48660446953c93625f379f8d1cd77893e`. The remote main tree was verified to contain all 128 project files.
- Verified revision: `8ec108b43f0f5d8e8bb451589e267631c2479e13`.
- [GitHub Actions run 45691060867](https://github.com/AshbinKarki/causal-target-ai/actions/runs/45691060867): both `test` and `container` jobs passed.
- Ubuntu / Python 3.12.16: **48 tests passed, 88% coverage**, Ruff lint/format passed, focused secret-pattern scan passed, real-data report-bundle check passed.
- Docker image built successfully and its running container returned a successful health response.
- The initial Linux run exposed a test import-path difference between `pytest` and `python -m pytest`; explicit project/source paths fixed it, followed by successful local and Linux reruns.
- After the account owner completed sign-in and terms acceptance, Streamlit Community Cloud deployed the app at [causal-target-ai.streamlit.app](https://causal-target-ai.streamlit.app/). Python 3.12.16 and the minimal runtime lock were confirmed in build logs.
- Hosted browser checks: all eight navigation pages rendered; zero-budget recalculation showed zero utilization and no spending; restoring default assumptions showed 8,408 targets. A real recommendation download was parsed: 100,000 rows, 8,408 recommended, five expected columns.
- The Share dialog showed public sharing enabled. A real hosted screenshot is saved as `docs/screenshots/live-dashboard.jpg`.
