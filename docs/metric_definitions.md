# Metric Definitions

This document defines core business grains and lifecycle fields used in the SaaS Revenue Intelligence warehouse.

## Reporting grains

| Layer | Table | Grain | Description |
|---|---|---|---|
| Raw | `raw.*` | Source-dependent | Unmodified CSV loads |
| Staging | `staging.stg_*` | Entity/event grain | Cleaned and typed source tables |
| Intermediate | `intermediate.int_account_month_spine` | **Account x month** | Core reporting backbone |
| Marts | `marts.*` (Phase 6+) | KPI-ready | Executive and analyst metrics |

## Account-month spine

**Table:** `intermediate.int_account_month_spine`

**Grain:** one row per `account_id` per `month_start`

**Purpose:** stable monthly snapshot used for MRR movement, churn, retention, support impact, and usage rollups.

### Key fields

| Field | Definition |
|---|---|
| `account_id` | Unique customer account identifier |
| `signup_date` | Account creation date |
| `signup_month` | Month-truncated signup date (cohort anchor) |
| `month_start` | First day of reporting month |
| `months_since_signup` | Months elapsed since signup month (`0` in signup month) |
| `account_age_months` | 1-indexed account age in months (`months_since_signup + 1`) |
| `is_active_month` | `TRUE` when account has at least one active subscription in the month |
| `is_churn_month` | `TRUE` when account has a churn event in the month |
| `months_until_churn` | Months from current month to first churn month; `NULL` after churn or if never churned |
| `first_churn_month` | First churn month for the account |
| `first_churn_date` | First churn date for the account |

### Active month rule

An account is active in `month_start` when any subscription satisfies:

```text
subscription.start_date <= month_end
AND (subscription.end_date IS NULL OR subscription.end_date >= month_start)
```

Where:

- `month_start` = first calendar day of month
- `month_end` = last calendar day of month

## Planned SaaS KPI definitions (Phase 6+)

These metrics will be implemented in revenue marts:

| Metric | Definition |
|---|---|
| **MRR** | Sum of active subscription MRR for accounts active in the month |
| **ARR** | `MRR * 12` |
| **Logo churn** | Accounts active last month but inactive this month |
| **Revenue churn** | MRR lost from churned accounts divided by prior-month MRR |
| **NRR** | `(Starting MRR + Expansion - Contraction - Churn) / Starting MRR` |
| **ARPU** | `Total MRR / Active accounts` |
| **Cohort retention** | `% of signup cohort still active at month N` |

## Design principles

- Metrics are computed from staging + spine tables, not directly from raw CSVs.
- Month-level logic is centralized in the account-month spine.
- Churn and activity flags in the spine are inputs to downstream marts, not final KPIs.
