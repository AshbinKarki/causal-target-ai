# Project explanations

## 30-second recruiter explanation

“CausalTarget AI is my Data Science portfolio project for smarter marketing allocation. Instead of only predicting who will buy, it estimates whose behavior might change because of an intervention. I analyzed a uniform 500,000-row Criteo sample, compared three predictive and five causal models, and built an interactive dashboard with budget simulation. The results include uncertainty and an honest finding: causal targeting did not establish a significant advantage over the predictive baseline. The project demonstrates reproducible analysis and decision-making, not claimed company revenue.”

## Two-minute technical explanation

“The business problem is that high conversion probability can lead a marketer to spend on customers who would buy anyway. I used the corrected Criteo uplift release, verified its published hash, scanned all 13.98 million records and retained a uniform 500,000-row sample.

I used twelve baseline features and excluded exposure and visit because they are post-assignment variables or outcomes. I split data into training, independent calibration, model selection and a final 100,000-row test set. The predictive baselines were Logistic Regression, Random Forest and LightGBM; the causal models were S, T, X, cross-fitted DR and an honest causal forest.

For policy evaluation, I reported IPW and doubly robust estimates, uplift/Qini curves and paired confidence intervals. Validation selected Random Forest for purchase prediction and the DR learner for causal ranking. The DR policy estimated about 117 incremental conversions at 30% targeting, but its paired difference from predictive targeting included zero. That is why I do not claim a causal-model improvement over the predictive baseline.

The optimizer maximizes assumed incremental contribution under uniform treatment costs, a budget and a capacity constraint. It can leave money unspent. A precomputed Streamlit app makes these assumptions interactive without retraining. The pipeline is locked with uv, tracked with MLflow and tested with synthetic known effects, unit/integration tests and browser checks. The central limitation is that privacy sampling prevents interpreting these results as original campaign lift, and financial values are simulations.”

## Five-minute presentation with timing

**0:00–0:45 — Frame the decision.** Show the executive dashboard. Explain purchase propensity versus incremental response. State the decision rule: treat only when expected additional contribution exceeds the intervention cost, subject to constraints.

**0:45–1:30 — Establish trustworthy data.** Show the data explorer and provenance. The corrected Criteo release contains 13,979,592 rows; all were scanned, 500,000 uniformly retained. Explain the publisher checksum, original-release leakage erratum, anonymous features and privacy-sampling limitation. Exposure is not treatment assignment.

**1:30–2:15 — Explain experimental evidence.** Show assignment groups: control conversion approximately 0.169%, treatment 0.313%, released-sample ITT lift about 0.144 percentage points. Explain the confidence interval and why statistical/practical/financial significance are different. Mention low absolute event rates and control-event scarcity.

**2:15–3:15 — Compare models fairly.** Show predictive and causal pages. Three predictive models, five causal learners, four data partitions, independent sigmoid calibration and cross-fitted nuisances. Validation chooses models; test does not. DR policy at 30% targeting estimates 116.95 incremental conversions, normal interval 55.52–178.38. Predictive targeting estimates 121.10. The paired difference, −4.14 with interval −36.28 to +27.99, does not establish superiority. Explain why an honest null comparison is still valuable.

**3:15–4:15 — Demonstrate an actual decision.** Open Budget simulator. Start at $1,500 budget, $0.05 cost and $50 contribution. Profit optimization selects 8,408 observations, spends $420.40 and leaves $1,079.60 unspent. Label the $5,964.68 model-implied profit as a simulation. Set budget to zero to demonstrate the boundary, then restore it. Increase cost or reduce assumed effect to show the recommendation changes. Export the anonymous score list.

**4:15–5:00 — Discuss engineering and limitations.** Show model card, test evidence and architecture. Explain uv locking, Parquet/DuckDB, MLflow, trusted artifact checksums and precomputed serving. Docker and CI files do not alone prove deployment. Finish with a concrete next experiment: a fresh randomized holdout using measured margins/costs, eligibility and consent. This project supports that design; it does not replace it.
