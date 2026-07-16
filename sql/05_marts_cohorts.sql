-- Phase 7: cohort retenetion mart.

CREATE OR REPLACE TABLE marts.fct_cohort_retention AS
WITH cohort_sizes AS (
    SELECT
        signup_month AS cohort_month,
        COUNT(*) AS cohort_size
    FROM staging.stg_accounts
    WHERE signup_month IS NOT NULL
    GROUP BY signup_month
),
account_month_status AS (
    SELECT
        spine.account_id,
        spine.signup_month AS cohort_month,
        spine.month_start,
        spine.months_since_signup AS month_number,
        COALESCE(mrr.mrr, 0) AS mrr,
        CASE 
            WHEN spine.months_since_signup = 0 THEN TRUE
            WHEN COALESCE(mrr.mrr, 0) > 0 THEN TRUE
            ELSE FALSE
        END AS is_retained 
    FROM intermediate.int_account_month_spine AS spine
    LEFT JOIN marts.fct_account_monthly_mrr AS mrr 
    ON spine.account_id = mrr.account_id
    AND spine.month_start = mrr.month_start 
)
SELECT
    status.cohort_month,
    status.month_number,
    status.month_start,
    sizes.cohort_size,
    COUNT(*) AS accounts_in_month,
    COUNT(*) FILTER (WHERE status.is_retained) AS retained_accounts,
    CAST(COUNT(*) FILTER (WHERE status.is_retained) AS DOUBLE) / NULLIF(sizes.cohort_size, 0) AS retention_rate
FROM account_month_status AS status 
INNER JOIN cohort_sizes AS sizes
ON status.cohort_month = sizes.cohort_month
GROUP BY 
    status.cohort_month,
    status.month_number,
    status.month_start,
    sizes.cohort_size
ORDER BY
    status.cohort_month,
    status.month_number;