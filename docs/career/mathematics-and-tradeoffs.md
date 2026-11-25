# Mathematics and design trade-offs

## Concepts to derive at a whiteboard

**Potential outcomes:** Y=TY(1)+(1−T)Y(0). Explain why only one counterfactual is observed and why CATE is a conditional average, not individual truth.

**ITT:** Δ=p1−p0. The unpooled variance approximation is p1(1−p1)/n1+p0(1−p0)/n0. Explain why the implementation favors score-based Newcombe bounds near zero and why rare control events dominate uncertainty.

**IPW:** E[TY/e−(1−T)Y/(1−e)]=E[Y(1)−Y(0)] under exchangeability and positivity. Derive by conditioning on X and using E[T|X]=e(X).

**DR:** Γ=m1−m0+T(Y−m1)/e−(1−T)(Y−m0)/(1−e). If m is correct, residual conditional means vanish. If e is correct, weighted residuals cancel outcome-model error. State that identification assumptions still apply.

**Policy contrast:** ΔV=E[(πA−πB)Γ]. Explain why paired variance is based on differences, not the sum of separate variance estimates. A confidence interval spanning zero cannot establish one policy's advantage.

**Qini normalization:** G(k/N)=N⁻¹Σj≤k Z(j), where Z is the HT transformed outcome. AUUC=∫G(q)dq and Qini=AUUC−G(1)/2. The coefficient depends on the chosen scale; never compare unnormalized library outputs without checking definitions.

**Profit allocation:** maximize Σai(vτi−c), with ai binary and Σai bounded by both capacity and floor(B/c). Show the exchange argument for sorting and the reason to discard nonpositive terms. When costs differ, ranking profit alone is no longer sufficient for a general integer knapsack.

**Calibration and proper scores:** Brier is mean((p−y)²); log loss is −mean(y log p+(1−y)log(1−p)). Both reflect probability quality beyond rank, but neither alone isolates calibration nor evaluates causal policy value.

## Follow-up questions to anticipate

- Would a 0.85 propensity be known or estimated? In this release it is a benchmark assumption estimated only on training data; original per-trial design metadata is missing.
- Is a positive uplift curve evidence of superiority over propensity targeting? No. Use a paired policy comparison at a fixed decision rule and an independent final test.
- What if the selected CATE is badly calibrated? Rankings may still be useful, but the profit threshold depends on effect magnitude. A fresh randomized validation and sensitivity analysis are needed.
- What if costs differ by customer? Add costs to the objective/constraints, reconsider optimization and document the changed estimand/eligibility population.
- What if repeated customers cross splits? Original identity is unavailable. Matching anonymized rows are not proof of repetition, and this remains a generalization limitation.
- What if the best test model differs from validation? Keep the selected model and report the discrepancy. Use new independent data for any subsequent selection decision.
- What if users adjust many scenarios after seeing outcomes? Dashboard scenarios are exploratory. Confirmatory decisions need a preregistered policy and fresh evaluation.

## Engineering trade-offs

Streamlit trades bespoke frontend flexibility for one-language maintainability. DuckDB trades a long-running transactional service for portable analytical files. A local MLflow store trades shared registry governance for simple reproducibility. A capped forest trades some statistical power for bounded memory. Separate dashboard/training locks reduce deployment weight. Precomputed scores trade live adaptation for a predictable, inspectable demonstration.

Neither a missing production service nor an omitted second boosted-tree library is a hidden placeholder: the project explicitly targets a noncommercial research/demo workflow. Future operational requirements should justify each additional service.
