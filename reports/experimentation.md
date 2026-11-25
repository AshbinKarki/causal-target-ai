# Experimentation report

Executed at 2026-11-25T09:26:35.596160+00:00. Source: **Criteo corrected v2.1 release, uniform sample**. Analyzed 500,000 rows; final test 100,000. Original campaign effects are not identifiable from this privacy-sampled release. Figures are benchmark estimates; financial numbers are assumption-based simulations.

| Metric | Value |
| --- | --- |
| control_n | 74732 |
| treatment_n | 425268 |
| control_events | 126 |
| treatment_events | 1330 |
| control_rate | 0.00168602 |
| treatment_rate | 0.00312744 |
| ate | 0.00144141 |
| relative_lift | 0.854919 |
| ci_low | 0.00108135 |
| ci_high | 0.00176143 |
| bootstrap_ci_low | 0.00110769 |
| bootstrap_ci_high | 0.00175148 |
| z_statistic | 6.74413 |
| p_value | 1.53942e-11 |
| chi_square_p_value | 1.53942e-11 |
| cohen_h | 0.0297599 |
| significant_005 | True |
| practical_lift_threshold | 0.001 |
| practically_positive | True |
| planned_power_at_mde | 0.999744 |
| required_total_n_80pct_power | 132891 |
| analysis | Intention-to-treat difference within released benchmark sample |
| interval | 95% Newcombe-Wilson; within-arm bootstrap also reported |

Treatment denotes assignment, not actual exposure. Newcombe-Wilson confidence intervals accompany the two-proportion Z and equivalent uncorrected chi-square tests. Bootstrap resamples within each arm. Power is prospective at a 0.1 percentage-point MDE, alpha 0.05, preserving the observed allocation ratio. Practical significance requires the entire interval to exceed the MDE. These are descriptive full-sample ITT statistics, separate from model-selection evidence.
