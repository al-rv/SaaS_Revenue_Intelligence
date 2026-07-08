# Data Dictionary (Raw Layer)

This document describes the raw ingestion layer built.

Source dataset: Rivalytics / RavenStack SaaS Subscription & Churn Analytics (synthetic, MIT-like).

## Raw tables loaded to DuckDB schema `raw`

| Table | Source file | Expected rows | Grain | Primary key |
|---|---|---:|---|---|
| `raw.accounts` | `ravenstack_accounts.csv` | 500 | one row per account | `account_id` |
| `raw.subscriptions` | `ravenstack_subscriptions.csv` | 5,000 | one row per subscription lifecycle | `subscription_id` |
| `raw.feature_usage` | `ravenstack_feature_usage.csv` | 25,000 | one row per feature usage event | `usage_id` |
| `raw.support_tickets` | `ravenstack_support_tickets.csv` | 2,000 | one row per ticket | `ticket_id` |
| `raw.churn_events` | `ravenstack_churn_events.csv` | 600 | one row per churn event | `churn_event_id` |

## Table columns

### `raw.accounts`

- `account_id`
- `account_name`
- `industry`
- `country`
- `signup_date`
- `referral_source`
- `plan_tier`
- `seats`
- `is_trial`
- `churn_flag`

### `raw.subscriptions`

- `subscription_id`
- `account_id`
- `start_date`
- `end_date`
- `plan_tier`
- `seats`
- `mrr_amount`
- `arr_amount`
- `is_trial`
- `upgrade_flag`
- `downgrade_flag`
- `churn_flag`
- `billing_frequency`
- `auto_renew_flag`

### `raw.feature_usage`

- `usage_id`
- `subscription_id`
- `usage_date`
- `feature_name`
- `usage_count`
- `usage_duration_secs`
- `error_count`
- `is_beta_feature`

### `raw.support_tickets`

- `ticket_id`
- `account_id`
- `submitted_at`
- `closed_at`
- `resolution_time_hours`
- `priority`
- `first_response_time_minutes`
- `satisfaction_score`
- `escalation_flag`

### `raw.churn_events`

- `churn_event_id`
- `account_id`
- `churn_date`
- `reason_code`
- `refund_amount_usd`
- `preceding_upgrade_flag`
- `preceding_downgrade_flag`
- `is_reactivation`
- `feedback_text`

## Validation queries

```sql
select count(*) from raw.accounts;
select count(*) from raw.subscriptions;
select count(*) from raw.feature_usage;
select count(*) from raw.support_tickets;
select count(*) from raw.churn_events;
```

