-- Phase 4 staging models: clean and typed tables for analytics.

CREATE OR REPLACE TABLE staging.stg_accounts AS 
SELECT
    TRIM(account_id) AS account_id,
    NULLIF(TRIM(account_name), '') AS account_name,
    NULLIF(LOWER(TRIM(industry)), '') AS industry,
    NULLIF(UPPER(TRIM(country,)), '') AS country,
    TRY_CAST(signup_date AS DATE) AS signup_date,
    DATE_TRUNC('month', TRY_CAST(signup_date AS DATE)) AS signup_month,
    NULLIF(LOWER(TRIM(referral_source)), '') AS referral_source,
    NULLIF(LOWER(TRIM(plan_tier)), '') AS plan_tier,
    TRY_CAST(seats AS INTEGER) AS seats,
    TRY_CAST(is_trial AS BOOLEAN) AS is_trial,
    TRY_CAST(churn_flag AS BOOLEAN) AS churn_flag
FROM raw.accounts;

CREATE OR REPLACE TABLE staging.stg_subscriptions AS
SELECT
    TRIM(subscription_id) AS subscription_id,
    TRIM(account_id) AS account_id,
    TRY_CAST(start_date AS DATE) AS start_date,
    DATE_TRUNC('month', TRY_CAST(start_date AS DATE)) AS subscription_start_month,
    TRY_CAST(end_date AS DATE) AS end_date,
    DATE_TRUNC('month', TRY_CAST(end_date AS DATE)) AS subscription_end_month,
    NULLIF(LOWER(TRIM(plan_tier)), '') AS plan_tier,
    TRY_CAST(seats AS INTEGER) AS seats,
    TRY_CAST(mrr_amount AS DOUBLE) AS mrr_amount,
    TRY_CAST(arr_amount AS DOUBLE) AS arr_amount,
    TRY_CAST(is_trial AS BOOLEAN) AS is_trial,
    TRY_CAST(upgrade_flag AS BOOLEAN) AS upgrade_flag,
    TRY_CAST(downgrade_flag AS BOOLEAN) AS downgrade_flag,
    TRY_CAST(churn_flag AS BOOLEAN) AS churn_flag,
    NULLIF(LOWER(TRIM(billing_frequency)), '') AS billing_frequency,
    TRY_CAST(auto_renew_flag AS BOOLEAN) AS auto_renew_flag,
    CASE WHEN
        LOWER(TRIM(plan_tier)) = 'enterprise' THEN TRUE
        ELSE FALSE
    END AS is_enterprise_plan,
    CASE WHEN
        LOWER(TRIM(billing_frequency)) = 'annual' THEN TRUE
        ELSE FALSE
    END AS is_annual_billing,
FROM raw.subscriptions;

CREATE OR REPLACE TABLE staging.stg_feature_usage AS
WITH ranked_usage AS (
    SELECT
        TRIM(usage_id) AS usage_id,
        TRIM(subscription_id) AS subscription_id,
        TRY_CAST(usage_date AS DATE) AS usage_date,
        NULLIF(LOWER(TRIM(feature_name)), '') AS feature_name,
        TRY_CAST(usage_count AS INTEGER) AS usage_count,
        TRY_CAST(usage_duration_secs AS INTEGER) AS usage_duration_secs,
        TRY_CAST(error_count AS INTEGER) AS error_count,
        TRY_CAST(is_beta_feature AS BOOLEAN) AS is_beta_feature,
        ROW_NUMBER() OVER (
            PARTITION BY TRIM(usage_id)
            ORDER BY TRY_CAST(usage_date AS DATE) DESC, TRIM(subscription_id) ASC 
        ) AS row_num 
    FROM raw.feature_usage    
)
SELECT
    usage_id, 
    subscription_id,
    usage_date,
    feature_name,
    usage_count,
    usage_duration_secs,
    error_count,
    is_beta_feature
FROM ranked_usage
WHERE row_num = 1;

CREATE OR REPLACE TABLE staging.stg_support_tickets AS
SELECT
    TRIM(ticket_id) AS ticket_id,
    TRIM(account_id) AS account_id,
    TRY_CAST(submitted_at AS TIMESTAMP) AS submitted_at,
    TRY_CAST(closed_at AS TIMESTAMP) AS closed_at,
    TRY_CAST(resolution_time_hours AS DOUBLE) AS resolution_time_hours,
    NULLIF(LOWER(TRIM(priority)), '') AS priority,
    TRY_CAST(first_response_time_minutes AS INTEGER) AS first_response_time_minutes,
    TRY_CAST(satisfaction_score AS INTEGER) AS satisfaction_score,
    TRY_CAST(escalation_flag AS BOOLEAN) AS escalation_flag
FROM raw.support_tickets;

CREATE OR REPLACE TABLE staging.stg_churn_events AS
SELECT
    TRIM(churn_event_id) AS churn_event_id,
    TRIM(account_id) AS account_id,
    TRY_CAST(churn_date AS DATE) AS churn_date,
    DATE_TRUNC('month', TRY_CAST(churn_date AS DATE)) AS churn_month,
    NULLIF(LOWER(TRIM(reason_code)), '') AS reason_code,
    TRY_CAST(refund_amount_usd AS DOUBLE) AS refund_amount_usd,
    TRY_CAST(preceding_upgrade_flag AS BOOLEAN) AS preceding_upgrade_flag,
    TRY_CAST(preceding_downgrade_flag AS BOOLEAN) AS preceding_downgrade_flag,
    TRY_CAST(is_reactivation AS BOOLEAN) AS is_reactivation,
    NULLIF(TRIM(feedback_text), '') AS feedback_text
FROM raw.churn_events;