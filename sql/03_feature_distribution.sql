SELECT treatment, AVG(f0) AS f0_mean, STDDEV_SAMP(f0) AS f0_std,
       QUANTILE_CONT(f0, 0.5) AS f0_median, MIN(f0) AS f0_min, MAX(f0) AS f0_max,
       COUNT(*) FILTER (WHERE f0 IS NULL) AS f0_missing
FROM observations GROUP BY treatment ORDER BY treatment;
