# 45 technical interview questions and answers

## Business and data

1. **What problem does uplift solve that ordinary prediction does not?** Prediction estimates the probability of an outcome. Uplift estimates how that probability changes with intervention. A high-propensity customer can have low incremental response, so the rankings answer different decisions.

2. **Why use the corrected Criteo release?** The original release had advertiser-related leakage from differing experiment allocation structures. The publisher's corrected v2.1 is the appropriate benchmark. Its checksum and row count are verified before analysis.

3. **How was the sample selected?** Every row in the full compressed stream received a seeded IID random priority; the pipeline retained the 500,000 smallest. Sampling was independent of treatment and outcome, unlike taking a potentially ordered prefix.

4. **Did you process the complete dataset?** All 13,979,592 source rows were scanned and schema-validated, but models used a uniform 500,000-row sample. Full-scale model training was not executed. The forest additionally used 60,000 training rows for resource reasons.

5. **Why not remove matching rows?** Anonymized projections can map different observations to identical values. Without original identity and time keys, equality does not establish a duplicate. The pipeline reports matching rows and retains them; generated source-position IDs must be unique.

6. **What are f0–f11?** Anonymous projected baseline features. Their original meanings are not released, so I cannot call them income, age or customer value. Descriptive patterns and predictive importance do not recover those semantics.

7. **What was the event rate?** The executed sample had 1,456 conversions among 500,000 observations. Control and treatment rates were approximately 0.169% and 0.313%. Rare control events constrain uncertainty in heterogeneous effects.

8. **How is data integrity established?** A pinned publisher revision, expected SHA-256, optional content-length comparison, full gzip CRC read, exact schema, binary/finite checks and source-row count. Processed Parquet has its own checksum and sampling manifest.

9. **Why DuckDB instead of PostgreSQL?** The workload is local, analytical and file-based, without concurrent transactional updates. DuckDB queries Arrow/Parquet efficiently and makes SQL reproducible without operating a server. PostgreSQL would become useful for a persistent multi-user operational application.

## Statistics and causal identification

10. **What is the estimand?** CATE, E[Y(1)−Y(0)|X=x], within the released benchmark population. The policy objective averages that effect over selected observations. The privacy-sampled release does not identify original campaign lift.

11. **How does treatment differ from exposure?** Treatment is randomized assignment or eligibility. Exposure records actual ad delivery after assignment. Conditioning on exposure changes the comparison and can induce post-treatment selection bias; this project uses intention-to-treat.

12. **Why exclude visit?** Visit is another post-assignment outcome, not a baseline predictor available before the intervention. Including it would introduce leakage and potentially causal bias for conversion targeting.

13. **What assumptions identify the effect?** Consistency, no interference, positivity and exchangeability of assignment with potential outcomes, conditional on baseline features where needed. The release construction and missing original design information remain limitations.

14. **Is the propensity known?** Not the original per-trial probability. The project uses the training assignment fraction, about 0.850537, as a documented constant benchmark assumption. It supports an explicit configured design probability when one is actually known.

15. **How do you assess treatment balance?** Standardized mean differences for each baseline feature and a held-out assignment-prediction AUC diagnostic. These can reveal imbalance or predictability; they do not prove randomization or exclude every hidden bias.

16. **Why report a Newcombe interval?** Binary events are rare, and a simple unpooled Wald interval can behave poorly near boundaries. Newcombe combines Wilson score intervals and remains nondegenerate when one or both arms have zero events.

17. **How does the bootstrap work?** ITT resamples independently within assignment arms; for a binary outcome the resampled event count is binomial with the observed arm rate. Policy inference resamples held-out contribution rows with the model and propensity fixed.

18. **What is practical significance?** A predeclared minimum effect matters beyond merely rejecting zero. The report uses a 0.001 absolute probability difference as an explicit MDE and asks whether the whole primary interval exceeds it. It is not a claim that this threshold guarantees profitability.

19. **Why avoid observed post-hoc power?** It largely restates the p-value using the estimated effect. The report instead computes prospective power and sample size at a stated MDE, alpha and allocation ratio.

20. **Can you observe individual treatment effects?** No. Each row reveals one potential outcome. Predictions are conditional averages under assumptions, not observed individual counterfactual differences.

## Modeling and evaluation

21. **Why four partitions?** Training fits models and preprocessing; calibration fits probability adjustment; selection tunes/chooses models and thresholds; final test estimates performance once choices are fixed. This avoids using final outcomes to select a winner.

22. **How did you address class imbalance?** Use stratified partitions, regularized models and rare-event-aware metrics, then calibrate on an independent set. I avoided uncorrected oversampling/class weights that could distort probability interpretation.

23. **Why report average precision as well as ROC-AUC?** ROC-AUC can look strong when negatives dominate. Average precision reflects positive retrieval under low prevalence. Neither directly evaluates causal targeting.

24. **Why was Random Forest selected when LightGBM has higher test AP?** Random Forest won the predeclared validation criterion. Switching after seeing test results would leak test information into model selection. The difference is reported without changing the selected baseline.

25. **What does sigmoid calibration do?** It fits a monotone parametric probability mapping on independent labeled data. This can improve reliability but does not guarantee it; log loss, Brier and calibration curves are inspected. Calibration is predictive, not a causal identification step.

26. **How does the S learner work?** One outcome model takes baseline features plus assignment. Predicting each row with T=1 and T=0 and subtracting yields CATE. Strong regularization can suppress treatment interactions, particularly with small effects.

27. **How does the T learner work?** Separate treated/control outcome models estimate m1(x) and m0(x); their difference is the effect estimate. It is simple but the smaller control arm can make one surface noisy.

28. **Why an X learner?** It imputes missing effects from outcome models and then learns effect regressions by arm. The weighting eτ0+(1−e)τ1 can help under treatment imbalance, but benefits depend on nuisance quality and structural assumptions.

29. **What is doubly robust about DR estimation?** A correctly specified propensity or correctly estimated outcome surfaces can remove first-order bias under identification conditions. This does not mean robustness to arbitrary unmeasured confounding or both nuisance components being wrong.

30. **Why cross-fit nuisances?** Each training pseudo-outcome uses outcome predictions from models that did not fit that row. This reduces first-stage overfitting bias and separates nuisance learning from the final effect regression.

31. **What does an honest causal forest add?** It estimates heterogeneous effects using forest splits and separate estimation samples, with residualization and supported inference. It is more computationally involved and may be limited by very rare events; complexity alone is not a selection criterion.

32. **How are uplift and Qini defined here?** Sort by the fixed score, accumulate HT transformed outcomes, divide by total N, and integrate over targeted fraction. Qini subtracts the diagonal random-policy area. Explicit normalization is important because libraries use different conventions.

33. **What is DR policy value?** It combines predicted potential outcomes with assignment-weighted residual corrections for the policy's chosen arm. Incremental value subtracts the never-treat policy. Conversion value is not inherently a financial amount.

34. **Why paired comparisons?** Policies are evaluated on the same rows and share noise. Using (πA−πB)Γ preserves this covariance. Comparing two independent intervals or their overlap is not an equivalent test of the difference.

35. **What did the key comparison show?** At 30% targeting, DR estimated 116.95 incremental conversions versus predictive targeting's 121.10. The paired difference was −4.14, with 95% normal interval −36.28 to +27.99; superiority was not established.

36. **What uncertainty is omitted?** The intervals condition on the fitted model, selected policy and propensity. They do not retrain/reselect models, propagate original privacy sampling or guarantee subgroup multiplicity control. A nested resampling/preregistered replication study would address more uncertainty.

37. **How did you validate without true Criteo CATE?** Check accounting identities, uplift endpoints, synthetic known-effect recovery and DR robustness under deliberately misspecified nuisance components. Final real-data validation uses observable randomized outcomes and policy estimators, not invented individual ground truth.

38. **Does SHAP explain causal effects?** The implemented SHAP plots explain predictive LightGBM log odds before calibration. They do not identify causal feature mechanisms or validate treatment effects. The dashboard states this explicitly.

## Optimization, engineering and deployment

39. **Why is sorting an exact optimizer here?** All treatments have equal cost, contribution is additive and there is a maximum count. Replacing a lower-value chosen item with a higher-value unchosen item improves or preserves profit at unchanged cost. Keep only positive-value items and obey the budget/count limit.

40. **When would OR-Tools or a MILP solver be needed?** Unequal costs, multiple treatment types, minimum quotas, fairness constraints or linked decisions can break simple sorting. Those would require a new formulation and tests rather than reusing this solution uncritically.

41. **Why leave budget unspent?** Spending is a constraint, not the objective. If the next intervention's estimated incremental contribution is below its cost, allocating the remaining budget reduces expected profit.

42. **What do the financial results mean?** With assumed $0.05 treatment cost and $50 contribution, the optimizer selects 8,408 rows, spends $420.40 and predicts $5,964.68 incremental profit. This is a model-based simulation, not actual revenue or savings. Held-out DR outcomes provide a separate noisy policy evaluation.

43. **How is reproducibility handled?** uv locks versions; seeds fix sampling/splits/training; input and model hashes identify artifacts; SQL/config/code are versioned; MLflow logs parameters/metrics; tests and CI inspect contracts. Bitwise identity across operating systems is not promised.

44. **Why precompute the dashboard?** Public serving only needs aggregates and derived score tables, not a 311 MB archive or fitted forests. This reduces memory/startup cost and avoids loading arbitrary executable pickle files in a public app. Updating the demo requires a new verified pipeline run.

45. **What would you do before real deployment?** Run a fresh randomized campaign with measured costs/margins, consent and eligibility rules; validate calibration and policy value on representative data; assess fairness/interference and distribution shift; add authentication/audit controls; and monitor outcomes with a retained randomized holdout. A configured Dockerfile or published URL is not equivalent to evidence of business effectiveness.
