# CausalTarget AI — execution status

Author: Ashbin Karki. Started 2026-11-25.

## Objective
Deliver a reproducible Criteo uplift analysis, tested optimization engine, eight-page Streamlit application, and portfolio documentation. Real-data results must come from executed pipelines. Financial outputs are simulations.

## Implementation plan
1. Inspect hardware, official data release/license and package compatibility.
2. Configure uv, modular Python package, resource-bounded quick/demo/full profiles.
3. Download corrected Criteo release, validate archive, sample reproducibly, persist Parquet/DuckDB.
4. Implement EDA, experimentation, prediction, S/T/X/DR learners, optional causal forest, held-out evaluation and optimization.
5. Execute real-data demo pipeline; generate reports, plots, model artifacts, explanations and monitoring.
6. Build and verify eight interactive dashboard pages, controls and downloads.
7. Complete tests, CI, Docker, architecture/model cards, career and portfolio materials.
8. Review secrets/licensing, commit and publish only through available authorized access; verify any remote outcome.

## Verified
- Workspace contains only an empty Git repository, with no remote.
- Python 3.13.5, Node and Git are available; uv, Docker and gh are not on PATH.
- 20 logical CPUs and approximately 693 GB free disk. Memory inventory via CIM is restricted; alternative inspection pending.
- Official Criteo source identifies a corrected 13,979,592-row release and CC BY-NC-SA 4.0 terms. Original release has a documented advertiser leakage issue and will not be used.

## Executed and verified
- Installed uv 0.13.10 and workspace-local Python 3.12.16; `uv.lock` resolves 110 packages including EconML 0.16.0.
- 24.82 GB total RAM; about 4.1 GB was free. Four threads and a 60,000-row forest training cap used.
- Legacy Criteo Azure host fails DNS. Downloaded the corrected release from Criteo's own Hugging Face account, pinned revision 82811785048bb633de2d55c02bab4e57066e6423.
- Verified SHA-256 2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc and full gzip CRC. Scanned 13,979,592 records and uniformly retained 500,000.
- Ran quick synthetic pipeline and real demo pipeline. Real partitions: 300,000 train, 50,000 calibration, 50,000 selection, 100,000 test.
- Trained Logistic Regression, Random Forest, LightGBM, S/T/X/DR learners and Causal Forest DML. Validation selected Random Forest and DR-learner.
- First test pass: 45 unit/integration tests plus 2 Streamlit AppTests. All eight pages render; zero-budget control updates correctly.
- Local server health responds HTTP 200. Browser checked navigation, simulator and actual CSV export: 100,000 scored records, 8,408 recommended at default assumptions.
- Captured real desktop and mobile screenshots under docs/screenshots.

## Latest verification
- Full local suite: 48 passed; 88% statement coverage. Ruff lint/format and portable bundle consistency pass.
- Paired comparison added: DR versus predictive targeting = -4.14 conversions, 95% normal CI [-36.28, +27.99]; superiority not established.
- Random baseline is now identical across evaluation and financial tables.
- Completed README, technical architecture/ADRs, data dictionary, mathematical methodology, model card, deployment/troubleshooting, portfolio metadata/case study and career package with 45 interview Q&As.
- Docker/Compose and GitHub Actions configured. No Docker executable or GPU tooling is present on this host.
- Separate minimal dashboard dependency lock contains 36 packages; a clean runtime environment is being smoke-tested.
- Local Git foundation and implementation milestone commits created with GitHub no-reply identity. Branch: codex/causal-target-ai.

## In progress
Final publication commit, GitHub repository/PR creation, remote CI inspection, and deployment access check. No remote publication or public deployment claimed yet.

## Important measured finding
At 30% targeting, DR-learner estimates 116.95 held-out incremental conversions versus predictive targeting's 121.10. Do not claim causal superiority. Default profit optimization selects 8,408 observations and simulates $5,964.68 incremental profit from $420.40 spend, using assumed $50 contribution and $0.05 treatment cost; these are not realized revenue/savings.

## Decisions
- Streamlit/Plotly for the complete analytics app; no separate frontend/backend needed.
- Use only pre-treatment f0–f11 features. Exclude exposure and visit from conversion predictors.
- Report intention-to-treat benchmark effects, with privacy sampling and unknown original design probabilities documented.
- MIT for original code; third-party dataset and adapted data retain separate attribution/noncommercial/share-alike terms.

## Continuation
Read this file, inspect Git status and `reports/metrics/`, then resume the first unverified phase. Do not overwrite unrelated changes or fabricate missing evidence.
