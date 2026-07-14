-- Phase 5: account-month spine (one row per account per calendar month).

CREATE OR REPLACE TABLE intermediate.int_calendar_months AS
WITH date_bounds AS (
    SELECT
        DATE_TRUNC(
            'month',
            MIN(event_date)
        ) AS min_month,
        DATE_TRUNC(
            'month',
            MAX(event_date)
        ) AS max_month
    FROM (
        SELECT signup_date AS event_date
        FROM staging.stg_accounts
        WHERE signup_date IS NOT NULL

        UNION ALL

        SELECT start_date AS event_date
        FROM staging.stg_subscriptions
        WHERE start_date IS NOT NULL

        UNION ALL

        SELECT end_date AS event_date
        FROM staging.stg_subscriptions
        WHERE end_date IS NOT NULL

        UNION ALL

        SELECT usage_date AS event_date
        FROM staging.stg_feature_usage
        WHERE usage_date IS NOT NULL

        UNION ALL

        SELECT churn_date AS event_date
        FROM staging.stg_churn_events
        WHERE churn_date IS NOT NULL

        UNION ALL

        SELECT CAST(submitted_at AS DATE) AS event_date
        FROM staging.stg_support_tickets
        WHERE submitted_at IS NOT NULL
    ) all_dates
)
SELECT CAST(month_start AS DATE) AS month_start
FROM generate_series(
    (SELECT min_month FROM date_bounds),
    (SELECT max_month FROM date_bounds),
    INTERVAL 1 MONTH
) AS calendar(month_start);

CREATE OR REPLACE TABLE intermediate.int_first_churn_by_account AS
SELECT
    account_id,
    MIN(churn_month) AS first_churn_month,
    MIN(churn_date) AS first_churn_date
FROM staging.stg_churn_events
GROUP BY account_id;

CREATE OR REPLACE TABLE intermediate.int_account_month_spine AS
WITH account_months AS (
    SELECT
        a.account_id,
        a.signup_date,
        a.signup_month,
        c.month_start,
        DATE_DIFF('month', a.signup_month, c.month_start) AS months_since_signup
    FROM staging.stg_accounts AS a
    INNER JOIN intermediate.int_calendar_months AS c
        ON c.month_start >= a.signup_month
),
subscription_activity AS (
    SELECT DISTINCT
        s.account_id,
        cal.month_start
    FROM staging.stg_subscriptions AS s
    INNER JOIN intermediate.int_calendar_months AS cal
        ON s.start_date <= (cal.month_start + INTERVAL 1 MONTH - INTERVAL 1 DAY)
        AND (
            s.end_date IS NULL
            OR s.end_date >= cal.month_start
        )
),
churn_activity AS (
    SELECT
        account_id,
        churn_month AS month_start,
        TRUE AS is_churn_month
    FROM staging.stg_churn_events
    GROUP BY account_id, churn_month
)
SELECT
    am.account_id,
    am.signup_date,
    am.signup_month,
    am.month_start,
    am.months_since_signup,
    am.months_since_signup + 1 AS account_age_months,
    COALESCE(sa.month_start IS NOT NULL, FALSE) AS is_active_month,
    COALESCE(ca.is_churn_month, FALSE) AS is_churn_month,
    CASE
        WHEN fc.first_churn_month IS NULL THEN NULL
        WHEN am.month_start > fc.first_churn_month THEN NULL
        ELSE DATE_DIFF('month', am.month_start, fc.first_churn_month)
    END AS months_until_churn,
    fc.first_churn_month,
    fc.first_churn_date
FROM account_months AS am
LEFT JOIN subscription_activity AS sa
    ON am.account_id = sa.account_id
    AND am.month_start = sa.month_start
LEFT JOIN churn_activity AS ca
    ON am.account_id = ca.account_id
    AND am.month_start = ca.month_start
LEFT JOIN intermediate.int_first_churn_by_account AS fc
    ON am.account_id = fc.account_id;
