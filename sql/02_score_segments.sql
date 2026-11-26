WITH ranked AS (
    SELECT *, NTILE(10) OVER (ORDER BY cate, observation_id) AS uplift_decile
    FROM scores
)
SELECT uplift_decile, COUNT(*) AS observations, AVG(cate) AS mean_cate,
       AVG(probability) AS purchase_probability, AVG(conversion) AS observed_rate,
       AVG(treatment) AS treatment_share
FROM ranked GROUP BY uplift_decile ORDER BY uplift_decile;
