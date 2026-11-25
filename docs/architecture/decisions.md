# Architecture decision records

## ADR 001 — Python and Streamlit for the complete system

**Decision:** one modular Python package and a Streamlit/Plotly application. The eight views read precomputed data. No HTTP model service or JavaScript frontend is required.

**Reason:** the key interaction is changing analysis/financial assumptions over a fixed scored cohort. Streamlit supplies accessible native controls, tables and downloads without duplicating schemas across services. A polished custom theme remains small and maintainable. React/Next.js/FastAPI would increase build and deployment complexity without improving the project's core causal evidence.

**Trade-off:** Streamlit reruns view code on interaction and has limited bespoke layout control. Cached report loading, bounded displayed tables and precomputed predictions keep interactions lightweight. A future multi-tenant campaign platform would justify a separate API, authentication, job queue and database.

## ADR 002 — Corrected publisher-owned data, pinned by content

**Decision:** Criteo v2.1 from the Criteo-owned Hugging Face repository, pinned revision and expected SHA-256. The legacy Azure URL failed DNS on 2026-11-25. Verify content length when available, full gzip CRC, header, row count and numerical/binary schema.

**Reason:** the initial dataset version has a documented advertiser leakage problem. A successful HTTP request alone does not establish the correct dataset. Published checksums and explicit provenance make the fallback auditable.

**Trade-off:** quick/demo sampling still scans the complete compressed archive. This is deliberate: taking only the first records would silently assume a random source order. An IID-priority reservoir yields a fixed-size uniform sample without retaining every row in memory.

## ADR 003 — Parquet plus DuckDB

**Decision:** Parquet for processed data; DuckDB for local analytical tables and checked-in SQL. Polars transfers a typed Arrow table into DuckDB. Pandas supports ML/library interoperability.

**Reason:** columnar compression, portable files and SQL execution are sufficient for this research workflow. PostgreSQL adds service management without a transactional requirement. SQL covers CTEs, windows, group aggregation, conversion rates, score deciles and quality checks.

**Trade-off:** the pipeline uses several in-memory arrays during training. Full mode is workstation-scale, not a distributed Spark training claim. The available-memory guard is a minimum safety floor, not a formal peak-memory prediction.

## ADR 004 — Four independent partitions

**Decision:** 60% training, 10% sigmoid calibration, 10% model/threshold selection, 20% final test, stratified on treatment and outcome. No post-treatment feature engineering. Preprocessing and nuisance cross-fitting use only training rows.

**Reason:** separate probability calibration and model selection reduce contamination of final estimates. Test tables compare all fixed models but do not decide the winner. The validation-selected Random Forest remains selected even though LightGBM scores slightly higher on final average precision.

**Trade-off:** splitting reduces already rare control events. A future preregistered repeated cross-validation study could use data more efficiently but would need carefully nested selection and independent final evaluation.

## ADR 005 — Simple, explicit causal learners

**Decision:** implement S/T/X/DR learners transparently with LightGBM regressions and three-fold cross-fitted nuisance outcomes; add EconML's honest Causal Forest DML as an optional extra.

**Reason:** the estimators have different bias/variance behavior and make useful comparisons. The original design propensity is unavailable; the default is a training-only constant allocation estimate, explicitly labeled. DoWhy is unnecessary for an identification argument based on a published randomized benchmark with acknowledged release limitations.

**Trade-off:** the selected DR regression lacks validated individual CATE intervals. Policy and subgroup uncertainty are available; forest intervals are separately inspected. The forest is capped at 60,000 training rows for demo and 250,000 for full mode. No expensive XGBoost duplicate is added because LightGBM satisfies the boosted-tree baseline requirement.

## ADR 006 — Exact allocation by sorting

**Decision:** sort estimated incremental contribution under equal per-treatment costs and a maximum treatment count; drop nonpositive marginal values.

**Reason:** this is the exact solution to the resulting cardinality-constrained additive problem. SciPy Optimize or OR-Tools would add no value for this formulation. Exhaustive enumeration on small cases tests correctness.

**Trade-off:** unequal treatment costs, cross-customer interference, multiple interventions, minimum group quotas and risk constraints require a richer optimization problem. The current engine does not claim to solve those variants.

## ADR 007 — Precomputed public app and local model lifecycle

**Decision:** dashboard runtime uses a small hashed dependency file; full training uses uv.lock. Track experiments in local MLflow SQLite and checksum trusted-local joblib artifacts. The public bundle contains derived scores and aggregates, no raw feature records or executable model files.

**Reason:** avoid retraining on app startup, keep demo hosting manageable and prevent dashboard deserialization of untrusted models. Dataset-derived assets retain separate CC BY-NC-SA attribution.

**Trade-off:** local artifacts must be regenerated to update predictions. There is no live ingestion service, live customer connector or deployed model registry. Docker/CI configurations are supplied; verification status is tracked separately from configuration presence.
