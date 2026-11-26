# Executive decision brief

Executed at 2026-11-25T09:26:35.596160+00:00. Source: **Criteo corrected v2.1 release, uniform sample**. Analyzed 500,000 rows; final test 100,000. Original campaign effects are not identifiable from this privacy-sampled release. Figures are benchmark estimates; financial numbers are assumption-based simulations.

The released sample's control conversion rate is 0.169%; treatment conversion is 0.313%. The ITT difference is 0.144% (95% CI 0.108% to 0.176%).

| strategy | feasible | targeted | incremental_conversions | spend | incremental_profit | roi |
| --- | --- | --- | --- | --- | --- | --- |
| No intervention | True | 0 | 0 | 0 | 0 | nan |
| Random targeting | True | 30000 | 38.1098 | 1500 | 405.492 | 0.270328 |
| Treat everyone | False | 0 | 0 | 0 | 0 | nan |
| Predictive targeting | True | 30000 | 117.913 | 1500 | 4395.64 | 2.93042 |
| Uplift targeting | True | 30000 | 132.185 | 1500 | 5109.23 | 3.40616 |
| Profit optimized | True | 8408 | 127.702 | 420.4 | 5964.68 | 14.1881 |

Use this benchmark to demonstrate decision methodology, not to forecast Criteo revenue. A production rollout requires a new randomized holdout, measured contribution margins and treatment costs, consent/eligibility rules and a staged experiment. Prefer no intervention when estimated marginal profit is nonpositive; a positive point estimate alone does not establish reliable gain.
