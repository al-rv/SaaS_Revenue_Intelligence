-- Phase 6: SaaS revenue marts (MRR, movement waterfall, executive KPIs).

CREATE OR REPLACE TABLE marts.dim_account AS
SELECT
    a.account_id,
    a.account_name,
    a.industry,
    a.country,
    a.signup_date,
    a.signup_month,
    a.referral_source,
    a.plan_tier AS initial_plan_tier,
    a.seats AS initial_seats,
    a.is_trial AS is_trial_at_signup,
    a.churn_flag,
    fc.first_churn_month,
    fc.first_churn_date,
    CASE
        WHEN a.signup_month IS NULL THEN NULL
        WHEN DATE_DIFF('month', a.signup_month, CURRENT_DATE) < 3 THEN '0-2 months'
        WHEN DATE_DIFF('month', a.signup_month, CURRENT_DATE) < 6 THEN '3-5 months'
        WHEN DATE_DIFF('month', a.signup_month, CURRENT_DATE) < 12 THEN '6-11 months'
        ELSE '12+ months'
    END AS tenure_bucket
FROM staging.stg_accounts AS a
LEFT JOIN intermediate.int_first_churn_by_account AS fc
    ON a.account_id = fc.account_id;

CREATE OR REPLACE TABLE marts.fct_account_monthly_mrr AS
WITH monthly_subscription_mrr AS (
    SELECT
        s.account_id,
        cal.month_start,
        SUM(COALESCE(s.mrr_amount, 0)) AS mrr,
        COUNT(*) AS active_subscription_count,
        SUM(COALESCE(s.seats, 0)) AS active_seats
    FROM staging.stg_subscriptions AS s
    INNER JOIN intermediate.int_calendar_months AS cal
        ON s.start_date <= (cal.month_start + INTERVAL 1 MONTH - INTERVAL 1 DAY)
        AND (
            s.end_date IS NULL
            OR s.end_date >= cal.month_start
        )
    GROUP BY s.account_id, cal.month_start
),
account_month_mrr AS (
    SELECT
        spine.account_id,
        spine.signup_month,
        spine.month_start,
        spine.months_since_signup,
        spine.is_active_month,
        spine.is_churn_month,
        COALESCE(msm.mrr, 0) AS mrr,
        COALESCE(msm.active_subscription_count, 0) AS active_subscription_count,
        COALESCE(msm.active_seats, 0) AS active_seats
    FROM intermediate.int_account_month_spine AS spine
    LEFT JOIN monthly_subscription_mrr AS msm
        ON spine.account_id = msm.account_id
        AND spine.month_start = msm.month_start
),
with_prior AS (
    SELECT
        account_id,
        signup_month,
        month_start,
        months_since_signup,
        is_active_month,
        is_churn_month,
        mrr,
        active_subscription_count,
        active_seats,
        LAG(mrr) OVER (
            PARTITION BY account_id
            ORDER BY month_start
        ) AS prior_mrr,
        MAX(CASE WHEN mrr > 0 THEN 1 ELSE 0 END) OVER (
            PARTITION BY account_id
            ORDER BY month_start
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS had_prior_positive_mrr
    FROM account_month_mrr
)
SELECT
    account_id,
    signup_month,
    month_start,
    months_since_signup,
    is_active_month,
    is_churn_month,
    mrr,
    COALESCE(prior_mrr, 0) AS prior_mrr,
    active_subscription_count,
    active_seats,
    CASE
        WHEN mrr > 0 AND COALESCE(prior_mrr, 0) = 0 AND COALESCE(had_prior_positive_mrr, 0) = 0
            THEN mrr
        ELSE 0
    END AS new_mrr,
    CASE
        WHEN mrr > 0 AND COALESCE(prior_mrr, 0) = 0 AND COALESCE(had_prior_positive_mrr, 0) = 1
            THEN mrr
        ELSE 0
    END AS reactivation_mrr,
    CASE
        WHEN COALESCE(prior_mrr, 0) > 0 AND mrr > prior_mrr
            THEN mrr - prior_mrr
        ELSE 0
    END AS expansion_mrr,
    CASE
        WHEN COALESCE(prior_mrr, 0) > 0 AND mrr > 0 AND mrr < prior_mrr
            THEN prior_mrr - mrr
        ELSE 0
    END AS contraction_mrr,
    CASE
        WHEN COALESCE(prior_mrr, 0) > 0 AND mrr = 0
            THEN prior_mrr
        ELSE 0
    END AS churned_mrr,
    CASE
        WHEN COALESCE(prior_mrr, 0) > 0 AND mrr > 0
            THEN LEAST(mrr, prior_mrr)
        ELSE 0
    END AS retained_mrr
FROM with_prior;

CREATE OR REPLACE TABLE marts.fct_mrr_movement_monthly AS
SELECT
    month_start,
    SUM(mrr) AS ending_mrr,
    SUM(prior_mrr) AS starting_mrr,
    SUM(new_mrr) AS new_mrr,
    SUM(reactivation_mrr) AS reactivation_mrr,
    SUM(expansion_mrr) AS expansion_mrr,
    SUM(contraction_mrr) AS contraction_mrr,
    SUM(churned_mrr) AS churned_mrr,
    SUM(retained_mrr) AS retained_mrr,
    SUM(new_mrr)
        + SUM(reactivation_mrr)
        + SUM(expansion_mrr)
        - SUM(contraction_mrr)
        - SUM(churned_mrr) AS net_mrr_change
FROM marts.fct_account_monthly_mrr
GROUP BY month_start
ORDER BY month_start;

CREATE OR REPLACE TABLE marts.mart_executive_monthly AS
WITH account_month_kpis AS (
    SELECT
        month_start,
        SUM(mrr) AS total_mrr,
        COUNT(*) FILTER (WHERE mrr > 0) AS active_accounts,
        COUNT(*) FILTER (WHERE new_mrr > 0) AS new_accounts,
        COUNT(*) FILTER (WHERE reactivation_mrr > 0) AS reactivated_accounts,
        COUNT(*) FILTER (WHERE churned_mrr > 0) AS churned_accounts,
        COUNT(*) FILTER (WHERE prior_mrr > 0) AS prior_active_accounts,
        SUM(prior_mrr) AS starting_mrr,
        SUM(new_mrr) AS new_mrr,
        SUM(reactivation_mrr) AS reactivation_mrr,
        SUM(expansion_mrr) AS expansion_mrr,
        SUM(contraction_mrr) AS contraction_mrr,
        SUM(churned_mrr) AS churned_mrr,
        SUM(retained_mrr) AS retained_mrr
    FROM marts.fct_account_monthly_mrr
    GROUP BY month_start
)
SELECT
    month_start,
    total_mrr,
    total_mrr * 12 AS arr,
    active_accounts,
    new_accounts,
    reactivated_accounts,
    churned_accounts,
    prior_active_accounts,
    starting_mrr,
    new_mrr,
    reactivation_mrr,
    expansion_mrr,
    contraction_mrr,
    churned_mrr,
    retained_mrr,
    CASE
        WHEN prior_active_accounts > 0
            THEN CAST(churned_accounts AS DOUBLE) / prior_active_accounts
        ELSE NULL
    END AS logo_churn_rate,
    CASE
        WHEN starting_mrr > 0
            THEN (starting_mrr - churned_mrr - contraction_mrr) / starting_mrr
        ELSE NULL
    END AS gross_revenue_retention,
    CASE
        WHEN starting_mrr > 0
            THEN (starting_mrr + expansion_mrr - contraction_mrr - churned_mrr) / starting_mrr
        ELSE NULL
    END AS net_revenue_retention,
    CASE
        WHEN active_accounts > 0
            THEN total_mrr / active_accounts
        ELSE NULL
    END AS arpu
FROM account_month_kpis
ORDER BY month_start;
