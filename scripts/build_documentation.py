"""Generate portfolio documentation directly from verified experiment artifacts."""

import json
from pathlib import Path

import nbformat as nbf
import pandas as pd

from causal_target.reporting import markdown_table

ROOT = Path(__file__).resolve().parents[1]


def write(path, text):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text.strip() + "\n", encoding="utf-8")


def main():
    metrics = ROOT / "reports/metrics"
    s = json.loads((metrics / "summary.json").read_text())
    if s["data"]["synthetic"]:
        raise ValueError("Portfolio documentation requires an executed real-data run")
    pred = pd.read_csv(metrics / "predictive_test.csv")
    causal = pd.read_csv(metrics / "causal_test.csv")
    strategies = pd.read_csv(metrics / "strategies.csv")
    paired = pd.read_csv(metrics / "paired_policy_comparisons.csv")
    exp = s["experiment"]
    rf = pred.set_index("model").loc[s["selected_predictive"]]
    dr = causal.set_index("model").loc[s["selected_causal"]]
    profit = strategies.set_index("strategy").loc["Profit optimized"]
    paired_predictive = paired.set_index("baseline").loc["Predictive targeting"]
    metadata_path = ROOT / "docs/project-metadata.json"
    old = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
    metadata = {
        "slug": "causal-target-ai",
        "title": "CausalTarget AI",
        "subtitle": "Causal AI for Intelligent Customer Targeting and Business Decision Optimization",
        "author": "Ashbin Karki",
        "category": "Data Science / Causal Inference",
        "summary": "An experimental marketing decision platform connecting calibrated prediction, uplift modeling and budget optimization.",
        "repository_url": old.get("repository_url"),
        "live_url": old.get("live_url"),
        "thumbnail": "docs/assets/project-thumbnail.svg",
        "screenshots": [
            "docs/screenshots/executive-dashboard.jpg",
            "docs/screenshots/budget-simulator.jpg",
            "docs/screenshots/causal-analysis.jpg",
        ],
        "stack": [
            "Python",
            "uv",
            "Polars",
            "DuckDB",
            "scikit-learn",
            "LightGBM",
            "EconML",
            "MLflow",
            "Streamlit",
            "Plotly",
            "Docker",
            "GitHub Actions",
        ],
        "verified_metrics": {
            "source_rows_scanned": s["data"]["source_rows_scanned"],
            "rows_analyzed": s["data"]["rows_retained"],
            "heldout_rows": s["splits"]["test"],
            "selected_predictive_roc_auc": rf.roc_auc,
            "selected_predictive_average_precision": rf.pr_auc,
            "selected_causal_qini": dr.qini,
            "heldout_incremental_conversions_at_30pct": dr.dr_incremental_conversions,
        },
        "simulation": {
            "budget": s["config"]["budget"],
            "cost_per_treatment": s["config"]["intervention_cost"],
            "contribution_per_conversion": s["config"]["conversion_value"],
            "targeted": int(profit.targeted),
            "spend": profit.spend,
            "model_based_incremental_profit": profit.incremental_profit,
            "not_realized_company_revenue": True,
        },
        "limitations": [
            "Privacy-sampled benchmark does not identify original campaign lift",
            "No significant paired advantage over predictive targeting",
            "No actual financial outcomes",
            "No public deployment verified",
        ],
        "code_license": "MIT",
        "data_license": "CC-BY-NC-SA-4.0",
        "results_generated_at": s["created_at"],
    }
    write("docs/project-metadata.json", json.dumps(metadata, indent=2))
    ptable = markdown_table(pred[["model", "roc_auc", "pr_auc", "log_loss", "brier", "f1"]])
    ctable = markdown_table(causal[["model", "qini", "auuc", "dr_incremental_conversions"]])
    btable = markdown_table(
        strategies[
            [
                "strategy",
                "feasible",
                "targeted",
                "spend",
                "incremental_profit",
                "heldout_dr_conversions",
            ]
        ]
    )
    facts = (
        f"The executed demo scanned **{s['data']['source_rows_scanned']:,}** source rows, retained a uniform **{s['data']['rows_retained']:,}**-row sample, "
        f"and reserved **{s['splits']['test']:,}** observations for final evaluation. "
        f"Validation selected **{s['selected_predictive']}** for purchase prediction and **{s['selected_causal']}** for causal ranking."
    )
    interpretation = (
        f"At 30% targeting, the DR learner estimates **{dr.dr_incremental_conversions:.2f} incremental conversions**, "
        f"with a fixed-model normal 95% interval of **{dr.dr_ci_low * s['splits']['test']:.2f} to {dr.dr_ci_high * s['splits']['test']:.2f}**. "
        f"The paired difference versus predictive targeting is **{paired_predictive.difference_conversions:+.2f} conversions** "
        f"(95% CI **{paired_predictive.conversions_ci_low:+.2f} to {paired_predictive.conversions_ci_high:+.2f}**). "
        "This run does **not** establish superiority over the predictive baseline. LightGBM has the highest test average precision, "
        "but the preselected Random Forest is retained: test results do not retroactively change model selection."
    )
    arch = """```mermaid
flowchart LR
    A[Criteo v2.1 official mirror] --> B[SHA-256 + gzip CRC + schema]
    B --> C[Uniform stream sample]
    C --> D[Parquet + DuckDB SQL]
    D --> E[60% training]
    D --> F[10% calibration]
    D --> G[10% selection]
    D --> H[20% final test]
    E --> I[Prediction + causal learners]
    F --> I
    I --> J[Validation model choice]
    G --> J
    J --> K[Held-out IPW / DR evaluation]
    H --> K
    K --> L[Versioned reports + model artifacts]
    L --> M[Budget optimizer + Streamlit]
```"""
    readme = f"""<p align="center"><img src="docs/assets/logo.svg" width="370" alt="CausalTarget AI" /></p>

# CausalTarget AI

### Causal AI for Intelligent Customer Targeting and Business Decision Optimization

![Python](https://img.shields.io/badge/Python-3.12-3776AB) ![Streamlit](https://img.shields.io/badge/App-Streamlit-FF4B4B) ![Code license](https://img.shields.io/badge/Code-MIT-7463ed) ![Data license](https://img.shields.io/badge/Data-CC_BY--NC--SA_4.0-16a994)

**Spend on customers whose behavior can change.** CausalTarget AI combines an experimental-data pipeline, calibrated purchase prediction, five causal learners, statistically explicit policy evaluation and a budget simulator in an eight-page analytics application.

This is a reproducible, production-oriented **portfolio benchmark**, not a deployed company marketing system. All numeric results below come from executed Criteo experiments. Financial figures are simulations with configurable assumptions.

![Working executive dashboard](docs/screenshots/executive-dashboard.jpg)

## Measured result, including the inconvenient part

{facts}

{interpretation}

The control conversion rate is **{exp["control_rate"]:.3%}**, treatment conversion **{exp["treatment_rate"]:.3%}**, and released-sample intention-to-treat difference **{exp["ate"] * 100:.3f} percentage points** (95% Newcombe interval {exp["ci_low"] * 100:.3f}–{exp["ci_high"] * 100:.3f} pp). The original campaign's effect cannot be recovered from the privacy-sampled release.

## Business problem

A likely buyer may buy without an advertisement. Ranking customers only by purchase probability can allocate spend to conversions that would happen anyway. The project asks a different question: which eligible observations have positive expected incremental contribution from intervention, under a budget and capacity limit?

Objectives are to measure treatment lift, compare targeting policies on held-out randomized assignments, expose uncertainty, and translate CATE into an auditable financial scenario. No actual Criteo revenue, cost or margin data is available.

## Application

1. **Executive overview:** experiment KPIs, selected model, uplift and simulated strategy comparison.
2. **Data explorer:** assignment filters, feature-range filters over aggregated bins, missingness, correlations and quality diagnostics.
3. **A/B experimentation:** assignment conversion, Z/chi-square tests, Newcombe/bootstrapped intervals, balance and prospective power.
4. **Predictive models:** ROC/PR/calibration, confusion matrices, validation-selected thresholds and predictive SHAP.
5. **Causal AI & uplift:** S/T/X/DR/forest comparisons, AUUC/Qini, paired policy comparisons and subgroup uncertainty.
6. **Budget simulator:** live budget/cost/value/capacity/effect assumptions, six strategies, sensitivity and CSV export.
7. **Customer recommendations:** anonymous source IDs, probabilities, CATE, value, filtering, sorting and export.
8. **Methodology & docs:** assumptions, provenance, reports and drift diagnostics.

![Budget simulator](docs/screenshots/budget-simulator.jpg)

## Quick start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) using its official instructions. Python 3.12 is selected by `.python-version`; uv can install it automatically. From the repository root:

```bash
uv sync --frozen --extra forest
uv run streamlit run app/main.py
```

The committed, compact real-data report bundle makes the app usable **without downloading data or retraining**. Visit the localhost URL printed by Streamlit. No credentials are needed. Streamlit's Settings menu supports theme selection; the checked-in default is light.

Windows PowerShell also supports:

```powershell
.\\scripts\\run.ps1 -Task setup
.\\scripts\\run.ps1 -Task app
```

In the original development workspace, a local uv executable is available at `.tools\\bin\\uv.exe`; the PowerShell helper detects it. This bootstrap directory is excluded from Git.

## Reproduce the experiment

```bash
uv run causal-target download
uv run causal-target process --profile demo
uv run causal-target run --profile demo
uv run causal-target evaluate
uv run python scripts/build_documentation.py
```

`run` includes ingestion, validation, SQL, EDA, training, evaluation, optimization, reports, figures, model serialization and MLflow logging. `train` is an alias for this auditable end-to-end run. `evaluate` displays the saved untouched-test results; it does not retrain or retune on test outcomes.

| Profile | Retained data | Purpose | Forest training cap |
| --- | ---: | --- | ---: |
| Quick | 20,000 | Synthetic smoke tests; real quick samples may lack rare control events | Disabled |
| Demo | 500,000 | Executed portfolio benchmark | 60,000 training rows |
| Full | All 13,979,592 | Larger workstation experiments; not executed here | 250,000 training rows |

```bash
uv run causal-target run --profile quick --source synthetic
uv run causal-target run --profile full
```

Synthetic runs write to `reports/runs/synthetic/` so they cannot replace the real portfolio bundle. Full training requires at least 12 GiB **available** memory (a safety floor, not a peak-memory guarantee); allow substantially more for large copies/forests. Demo uses four worker threads. No GPU is required. The verified model/report computation took about {s["elapsed_seconds"]:.0f} seconds on this host, excluding initial environment installation and the first archive scan; it is not a portable performance guarantee.

## Data and integrity

- Corrected **Criteo v2.1**, 12 anonymized baseline features plus treatment, conversion, visit and exposure.
- Official source: [Criteo AI Lab](https://ailab.criteo.com/criteo-uplift-prediction-dataset/); actual download: [Criteo's Hugging Face repository](https://huggingface.co/datasets/criteo/criteo-uplift).
- The old Azure host no longer resolved during execution. The ingestion pipeline uses pinned revision `82811785048bb633de2d55c02bab4e57066e6423`.
- Archive SHA-256: `{s["data"]["archive_sha256"]}`. Verified against the publisher's hash, gzip CRC, schema and expected source row count.
- Uniform IID-priority reservoir sampling scans every row and never stratifies the sampling step on outcomes. The 60/10/10/20 modeling split is stratified on assignment and outcome.
- {s["quality"]["conversion_events"]:,} observed conversions in the demo; no missing feature/label values. {s["quality"]["matching_feature_rows"]:,} matching feature rows retained because anonymized equality does not prove duplicate identity.
- Data and derived artifacts: **CC BY-NC-SA 4.0**, separate from MIT code. Raw observations and binary model files are ignored. See [data terms](DATA_LICENSE.md) and [data dictionary](docs/data-dictionary.md).

## Architecture and stack

{arch}

Python 3.12, uv, Polars/Pandas/NumPy, Parquet/PyArrow, DuckDB SQL, SciPy/Statsmodels, scikit-learn, LightGBM, Optuna, EconML, SHAP, MLflow, Streamlit/Plotly, Pytest/Ruff and Docker/GitHub Actions. The dashboard needs only a small subset of this stack. A separate React/FastAPI service and PostgreSQL are unnecessary for precomputed local analytics; see [architecture decisions](docs/architecture/decisions.md).

## Methods and evaluation

**Prediction:** Logistic Regression, Random Forest and LightGBM; five seeded Optuna LightGBM trials; train-only scaling/imputation; independent sigmoid calibration; validation average precision for selection and validation F1 for thresholds. No class resampling is used because calibrated probability quality matters. Report ROC-AUC alongside average precision, log loss, Brier, precision/recall/F1 and confusion matrices.

{ptable}

**Causality:** S-, T-, X-, cross-fitted DR learner and honest Causal Forest DML. Use only `f0`–`f11`; exposure and visit cannot enter ordinary predictors. Original per-trial assignment probabilities are unavailable, so the training assignment fraction ({s["causal_diagnostics"]["propensity"]:.6f}) is an explicit benchmark assumption, not a claimed known design probability.

{ctable}

AUUC integrates normalized Horvitz–Thompson cumulative incremental outcomes over targeted fraction; Qini subtracts the straight-line random baseline area. DR policy gain is incremental to treating nobody. The test-set nuisance models are fitted only on training data. Bootstrap and normal policy intervals condition on the fitted models and propensity, excluding training/selection uncertainty. Quantile/half-test results are exploratory and not multiplicity-adjusted. See [mathematical methodology](docs/methodology/causal-inference.md), [evaluation report](reports/model-evaluation.md) and [model card](docs/model_cards/selected-models.md).

![Held-out uplift curves](reports/figures/uplift.png)

## Business optimization: explicitly simulated

Maximize `sum(decision_i * (CATE_i * contribution_value - intervention_cost))`, subject to budget and targeting capacity. Equal costs make sorting exact; negative-value interventions are skipped. Treat-everyone is flagged infeasible when it would violate constraints.

At the default $1,500 budget, $0.05 intervention cost, $50 contribution per conversion and 30% capacity, profit optimization selects **{int(profit.targeted):,} observations**, spends **${profit.spend:,.2f}**, and estimates **${profit.incremental_profit:,.2f} simulated incremental profit**. The separate held-out DR evaluation estimates {profit.heldout_dr_conversions:.2f} incremental conversions (95% CI {profit.heldout_dr_conversions_ci_low:.2f}–{profit.heldout_dr_conversions_ci_high:.2f}). The model-based scenario and experimental policy estimate are different estimators, not interchangeable financial facts.

{btable}

Do not describe these amounts as money saved or revenue generated at Criteo. The next business step would be a fresh randomized campaign with measured costs, eligibility and contribution margins.

## Testing and lifecycle

```bash
uv run pytest --cov=causal_target --cov-report=term-missing
uv run ruff check src app tests scripts
uv run ruff format --check src app tests scripts
uv run python scripts/verify_bundle.py
uv run python scripts/secret_scan.py
```

Tests cover ingestion/checksums, strict schema, disjoint splits, leakage exclusion, known-effect synthetic recovery, DR robustness, policy accounting, optimization against exhaustive search, zero/negative/invalid cases, serialization/inference, drift and all eight application views. Actual browser QA checked desktop/mobile layout, navigation, simulator recalculation and a 100,000-row CSV download. See [verification evidence](docs/verification.md) for final counts and unexecuted checks.

```bash
uv run causal-target predict --input data/processed/demo/observations.parquet --output artifacts/batch-scores.csv
uv run causal-target monitor --reference data/processed/demo/observations.parquet --input data/processed/demo/observations.parquet --output artifacts/drift.csv
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db
```

The monitoring example compares a dataset with itself to demonstrate invocation; replace `--input` with a new **baseline-schema** cohort for meaningful drift monitoring. PSI uses training-defined bins; KS is descriptive. Model manifests record checksums and package versions. Only load trusted local joblib artifacts.

## Deployment

```bash
docker compose up --build
```

The non-root container serves precomputed reports on port 8501 with a health check. Docker is not installed on the development host, so local image execution is **not verified**; CI includes a build and health smoke test. Streamlit Community Cloud is the recommended demonstration host; `app/requirements.txt` is a separate hashed runtime lock. Select Python 3.12 and `app/main.py`. No public deployment URL is claimed. [Deployment guide](docs/deployment.md).

## Repository map

```text
app/                 Eight Streamlit views, shared UI/data components, runtime lock
configs/             Quick / demo / full experiment profiles
src/causal_target/   Data, statistics, prediction, causality, evaluation, optimization
                     Monitoring, batch inference, reporting, CLI orchestration
sql/                 CTEs, window functions, experiment/segment/quality analytics
tests/               Unit, integration, known-effect and dashboard tests
reports/metrics/     Verified portable summaries and derived score table
reports/figures/     Actual statistical/model/explainability figures
notebooks/           Review notebooks backed by generated reports
docs/                Architecture, methodology, deployment, screenshots and career package
scripts/             Windows runner, documentation builder, checks
.github/workflows/   Test/lint/reproducibility and container CI
```

## Limitations and next experiments

Rare control conversions constrain heterogeneity estimates. The original experiment uses pooled, privacy-sampled data and anonymized features; customer identity, campaign costs, demographics and original design metadata are unavailable. Model-specific CATE intervals exist for the forest only; the selected DR learner has subgroup/policy intervals rather than valid individual intervals. No full-scale training, live production monitoring or real-campaign deployment was performed. Additional experiments should evaluate multiple training seeds, advertiser/time generalization when identifiers are available, richer cost structures and a preregistered fresh randomized holdout. DoWhy is not forced into a randomized benchmark where the identification argument can be stated directly.

## Portfolio and attribution

- [Portfolio case study](docs/portfolio-case-study.md) · [structured metadata](docs/project-metadata.json)
- [Resume / LinkedIn / interview package](docs/career/README.md)
- [Experiment report](reports/experimentation.md) · [Executive report](reports/executive_summary/report.md)
- [Troubleshooting](docs/troubleshooting.md) · [Project status](PROJECT_STATUS.md)

**Ashbin Karki** — Master's in Data Science and AI, specializing in Artificial Intelligence. This portfolio project was developed with AI-assisted implementation and validation; it is not a claim of employment or production impact at Criteo.

Dataset citation: Diemert, Betlei, Renaudin and Amini (2018), *A Large Scale Benchmark for Uplift Modeling*, AdKDD and TargetAd Workshop, KDD. Original code: [MIT](LICENSE). Data-derived artifacts: [CC BY-NC-SA 4.0](DATA_LICENSE.md).
"""
    write("README.md", readme)
    write(
        "docs/portfolio-case-study.md",
        f"""# CausalTarget AI — portfolio case study

![Project thumbnail](assets/project-thumbnail.svg)

## Summary
An end-to-end Data Science portfolio project connecting randomized experimentation, purchase prediction, causal machine learning and marketing allocation in a working decision-support application.

## Business problem and decision
High purchase probability does not imply high incremental response. The project separates those questions, estimates CATE, and allocates a constrained budget only where expected incremental contribution is positive.

## Evidence
{facts}

The selected predictive model achieved test ROC-AUC **{rf.roc_auc:.4f}** and average precision **{rf.pr_auc:.4f}**. {interpretation}

## Architecture
{arch}

## Technical approach
Use an official corrected dataset, verify its SHA-256 and gzip CRC, scan the entire release with uniform reservoir sampling, validate schema, and persist Parquet/DuckDB tables. Use independent train/calibration/selection/test partitions, train three predictive and five causal models, estimate IPW/DR policy values and paired intervals, then expose decisions through Streamlit and Plotly. Track runs in MLflow; validate with Pytest, Ruff and browser QA.

## Business scenario
At explicitly assumed $0.05 intervention cost and $50 contribution, the optimizer selected {int(profit.targeted):,} of 100,000 observations, left ${profit.unspent_budget:,.2f} of a $1,500 budget unspent, and estimated ${profit.incremental_profit:,.2f} model-based incremental profit. These are simulated outcomes, not realized company savings.

![Working dashboard](screenshots/executive-dashboard.jpg)
![Working simulator](screenshots/budget-simulator.jpg)

## Challenges and lessons
The historical download host had disappeared; the publisher-owned Hugging Face mirror and published checksum preserved provenance. Rare control conversions required cautious interpretation. A complex causal learner did not establish superiority over predictive targeting, illustrating why paired held-out evaluation matters. Uniform costs permit exact sorting without unnecessary optimization infrastructure. Precomputed artifacts separate expensive research from a lightweight interactive demo.

## Boundaries
Privacy sampling obscures original campaign lift; features cannot be given invented business meanings. No raw customer identity or actual cost/revenue data is available. Forest training is resource-capped and full-scale training was not executed. Deployment configuration is prepared; public URL is recorded only after verified hosting. Repository and live links, when verified, are stored in project-metadata.json.

Author: Ashbin Karki. AI-assisted portfolio development; no claimed employer deployment. Code MIT; Criteo data-derived artifacts CC BY-NC-SA 4.0.
""",
    )
    write(
        "docs/model_cards/selected-models.md",
        f"""# Model card — selected predictive and causal models

Version 1.0.0 · generated {s["created_at"]} · author Ashbin Karki.

## Intended use
Noncommercial portfolio research and demonstration of experimental targeting methodology. Inputs are twelve anonymous baseline projections. Outputs are purchase probability, estimated CATE, and scenario-specific allocation recommendations. IDs are source row positions, not contactable customers.

## Training and selection
{facts} Models use 300,000 training rows, with independent 50,000-row calibration and selection sets. The optional honest forest uses a uniform stratified 60,000-row training subset. Final test size is 100,000. The original design probability is unavailable: use training allocation fraction as a documented benchmark assumption. Random Forest uses sigmoid calibration; DR nuisance regressions use cross-fitting.

## Measured results
{ptable}

{ctable}

{interpretation}

## Uncertainty and failure modes
Rare outcomes, especially in control, cause noisy effect estimates. Policy/subgroup intervals are conditional on fitted models and a constant propensity; they exclude model selection, model-fitting and original privacy-sampling uncertainty. Forest intervals are stored for 1,000 held-out observations for inspection; they are approximate and do not reveal individual counterfactuals. The DR learner does not provide validated individual intervals. Poor calibration of nuisance regressions can increase finite-sample variance even under a correct propensity assumption. Matching anonymized rows may cross partitions because no valid deduplication identity exists.

## Exclusions and ethics
Exposure, visit, treatment and conversion cannot enter baseline features; treatment is appended only in the S learner by design. SHAP explains predictive LightGBM log odds, not causal feature effects. Protected attributes and real user context are unavailable, so no fairness guarantee is made. Do not use this release for real commercial targeting or decisions about financial/insurance/employment eligibility. Respect the data license and consent/eligibility requirements of any future experiment.

## Operations
Trusted-local joblib artifacts have SHA-256 manifests, package versions and data provenance. The app reads non-executable report tables. PSI/KS monitoring is implemented; no live monitoring service has been deployed. Retraining requires new representative experimental data and separate calibration/selection/test sets. Drift alerts alone must not trigger automatic campaign activation.
""",
    )
    # Review notebooks contain real rendered findings and executable inspection cells.
    for name, title, body, code in [
        (
            "01_data_and_experiment.ipynb",
            "Data and experimentation",
            facts,
            "summary = json.loads((root / 'reports/metrics/summary.json').read_text())\nsummary['experiment']",
        ),
        (
            "02_models_and_decisions.ipynb",
            "Models and decisions",
            interpretation,
            "pd.read_csv(root / 'reports/metrics/causal_test.csv')",
        ),
    ]:
        notebook = nbf.v4.new_notebook()
        notebook.metadata.kernelspec = {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        }
        notebook.cells = [
            nbf.v4.new_markdown_cell(
                f"# {title}\n\n{body}\n\nThis review notebook reads already executed pipeline outputs. It does not train models or claim that cells below have been executed in a notebook kernel."
            ),
            nbf.v4.new_code_cell(
                "from pathlib import Path\nimport json\nimport pandas as pd\nroot = Path.cwd() if (Path.cwd() / 'reports').exists() else Path.cwd().parent"
            ),
            nbf.v4.new_code_cell(code),
            nbf.v4.new_markdown_cell(
                "![Actual generated figure](../reports/figures/"
                + ("treatment_balance.png" if name.startswith("01") else "uplift.png")
                + ")"
            ),
        ]
        (ROOT / "notebooks").mkdir(exist_ok=True)
        nbf.write(notebook, ROOT / "notebooks" / name)
    print(
        "Generated README, model card, portfolio case study, metadata and two review notebooks from executed results."
    )


if __name__ == "__main__":
    main()
