-- Phase 7: support, usage, and chur-driver marts

CREATE OR REPLACE TABLE marts.fct_support_monthly AS
SELECT
    account_id, 
    DATE_TRUNC('month', CAST(submitted_at AS DATE)) AS month_start,
    COUNT(*) AS ticket_count,
    COUNT(*) FILTER (WHERE priority IN ('high', 'urgent')) AS high_priority_ticket_count
    COUNT(*) FILTER (WHERE escalation_flag IS TRUE) AS escalated_ticket_count,
    AVG(resolution_time_hours) AS avg_resoultion_hours,
    COUNT(*) FILTER (WHERE resolution_time_hours > 48) AS sla_breach_count,
    AVG(satisfaction_score) AS avg_satisfaction_score, 
    AVG(first_response_time_minutes) AS avg_first_response_minutes
FROM staging.stg_support_tickets
WHERE submitted_at IS NOT NULL
GROUP BY account_id, DATE_TRUNC('month', CAST(submitted_at AS DATE));

CREATE OR REPLACE TABLE marts.fct_usage_monthly AS
SELECT
    s.account_id,
    DATE_TRUNC('monht', f.usage_date) AS month_start,
    COUNT(*) AS usage_event_count,
    SUM(COALESCE(f.usage_count, 0)) AS total_usage_count,
    COUNT(DISTINCT f.feature_name) AS active_feature_count,
    SUM(COALESCE(f.usage_duration_secs, 0)) / 60.0 AS total_duration_minutes,
    SUM(COALESCE(f.error_count, 0)) AS error_count
    CASE
        WHEN SUM(COALESCE(f.usage_count, 0)) > 0
        THEN CAST(SUM(COALESCE(f.error_count, 0)) AS DOUBLE) / SUM(COALESCE(f.usage_count, 0))
        ELSE NULL
    END AS error_rate,
    COUNT(*) FILTER (WHERE f.is_beta_feature IS TRUE) AS beta_feature_event_count
FROM staging.stg_feature_usage AS f
INNER JOIN staging.stg_subscriptions AS s 
ON f.subscription_id = s.subscription_id
WHERE f.usage_date IS NOT NULL
GROUP BY s.account_id, DATE_TRUNC('month', f.usage_date);

CREATE OR REPLACE TABLE marts.mart_churn_drivers AS
WITH base AS (
    SELECT
        spine.account_id,
        spine.signup_month,
        spine.month_start,
        spine.months_since_signup,
        spine.account_age_months,
        spine.is_active_month,
        spine.is_churn_month,
        spine.months_until_churn,
        dim.industry,
        dim.country,
        dim.initial_plan_tier,
        dim.referral_source,
        dim.tenure_bucket,
        COALESCE(mrr.mrr, 0) AS mrr,
        COALESCE(mrr.prior_mrr, 0) AS prior_mrr,
        COALESCE(mrr.new_mrr, 0) AS new_mrr,
        COALESCE(mrr.expansion_mrr, 0) AS expansion_mrr,
        COALESCE(mrr.contraction_mrr, 0) AS contraction_mrr,
        COALESCE(mrr.churned_mrr, 0) AS churned_mrr,
        COALESCE(support.ticket_count, 0) AS ticket_count,
        COALESCE(support.high_priority_ticket_count, 0) AS high_priority_ticket_count,
        COALESCE(support.escalated_ticket_count, 0) AS escalated_ticket_count,
        support.avg_resolution_hours,
        COALESCE(support.sla_breach_count, 0) AS sla_breach_count,
        support.avg_satisfaction_score,
        COALESCE(usage.usage_event_count, 0) AS usage_event_count,
        COALESCE(usage.total_usage_count, 0) AS total_usage_count,
        COALESCE(usage.active_feature_count, 0) AS active_feature_count,
        COALESCE(usage.total_duration_minutes, 0) AS total_duration_minutes,
        COALESCE(usage.error_count, 0) AS error_count,
        usage.error_rate
    FROM intermediate.int_account_month_spine AS spine
    LEFT JOIN marts.dim_account AS dim
        ON spine.account_id = dim.account_id
    LEFT JOIN marts.fct_account_monthly_mrr AS mrr
        ON spine.account_id = mrr.account_id
        AND spine.month_start = mrr.month_start
    LEFT JOIN marts.fct_support_monthly AS support
        ON spine.account_id = support.account_id
        AND spine.month_start = support.month_start
    LEFT JOIN marts.fct_usage_monthly AS usage
        ON spine.account_id = usage.account_id
        AND spine.month_start = usage.month_start
)
SELECT
    account_id,
    signup_month,
    month_start,
    months_since_signup,
    account_age_months,
    is_active_month,
    is_churn_month,
    months_until_churn,
    industry,
    country,
    initial_plan_tier,
    referral_source,
    tenure_bucket,
    mrr,
    prior_mrr,
    new_mrr,
    expansion_mrr,
    contraction_mrr,
    churned_mrr,
    ticket_count,
    high_priority_ticket_count,
    escalated_ticket_count,
    avg_resolution_hours,
    sla_breach_count,
    avg_satisfaction_score,
    usage_event_count,
    total_usage_count,
    active_feature_count,
    total_duration_minutes,
    error_count,
    error_rate,
    COALESCE(
        LEAD(is_churn_month) OVER (
            PARTITION BY account_id
            ORDER BY month_start
        ),
        FALSE
    ) AS churns_next_month,
    COALESCE(
        LEAD(churned_mrr) OVER (
            PARTITION BY account_id
            ORDER BY month_start
        ),
        0
    ) AS next_month_churned_mrr
FROM base;
