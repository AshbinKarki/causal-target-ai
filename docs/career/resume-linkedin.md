# Resume and LinkedIn materials

## Four ATS-friendly resume bullets

- Developed an AI-assisted Python causal inference portfolio project using a uniform 500,000-row Criteo sample, with SHA-256 validation, Parquet/DuckDB analytics and reproducible 60/10/10/20 data partitions.
- Compared three calibrated purchase-prediction models and five causal learners; the validation-selected Random Forest achieved 0.965 held-out ROC-AUC and 0.242 average precision on 100,000 observations.
- Implemented cross-fitted doubly robust policy evaluation, bootstrap intervals and paired comparisons; the selected DR policy estimated 116.95 incremental conversions at 30% targeting, without a statistically established advantage over predictive targeting.
- Built an eight-page Streamlit decision dashboard with budget-constrained optimization, sensitivity controls, CSV export, MLflow tracking, automated tests and Docker/GitHub Actions configuration; clearly separated simulated financial scenarios from observed experimental outcomes.

## LinkedIn project description

CausalTarget AI explores an important marketing distinction: customers likely to purchase are not necessarily those whose behavior changes because of an ad. The project uses Criteo's corrected uplift benchmark, processes a uniform 500,000-row sample, and compares calibrated predictive models with S-, T-, X-, DR-learners and Causal Forest DML. A Streamlit application connects statistical experimentation, held-out policy evaluation, model explanations and budget simulation.

The selected DR policy estimated 116.95 incremental conversions at 30% targeting on a 100,000-row test cohort. A paired comparison did not establish superiority over predictive targeting. Financial outputs use assumed costs/contribution values and are not actual Criteo revenue. Built as an AI-assisted Data Science portfolio project with reproducible pipelines and transparent limitations.

## LinkedIn announcement draft

I built CausalTarget AI, a portfolio project exploring how causal inference can inform marketing allocation.

The question is simple: who might buy anyway, and whose conversion probability changes when we intervene?

The implementation includes verified Criteo data ingestion, three predictive models, five causal learners, held-out doubly robust evaluation, and an interactive eight-page dashboard. I analyzed a uniform 500,000-row sample and reserved 100,000 observations for final evaluation.

One useful result was that the causal model did not establish a significant advantage over the predictive targeting baseline. That makes the project a useful exercise in honest evaluation rather than a story about guaranteed uplift. The budget simulator also keeps modeled financial scenarios separate from realized business outcomes.

This was AI-assisted portfolio development. The repository includes the assumptions, code, verification evidence and reproducible workflow. Add verified repository/live links from docs/project-metadata.json when sharing; do not claim a public deployment unless one exists.

Suggested tags: #DataScience #CausalInference #MachineLearning #UpliftModeling
