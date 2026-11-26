WITH arm_summary AS (
    SELECT treatment, COUNT(*) AS observations, SUM(conversion) AS conversions,
           AVG(conversion) AS conversion_rate, AVG(visit) AS visit_rate,
           AVG(exposure) AS exposure_rate
    FROM observations GROUP BY treatment
)
SELECT *, conversion_rate - FIRST_VALUE(conversion_rate) OVER (ORDER BY treatment) AS lift_vs_control
FROM arm_summary ORDER BY treatment;
