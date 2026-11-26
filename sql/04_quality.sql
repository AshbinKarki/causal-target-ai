SELECT COUNT(*) AS total_rows, COUNT(DISTINCT observation_id) AS unique_source_rows,
       SUM(CASE WHEN treatment NOT IN (0,1) THEN 1 ELSE 0 END) AS invalid_assignments,
       SUM(CASE WHEN conversion IS NULL THEN 1 ELSE 0 END) AS missing_outcomes,
       SUM(CASE WHEN treatment = 0 AND exposure = 1 THEN 1 ELSE 0 END) AS exposed_controls
FROM observations;
