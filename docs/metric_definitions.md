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

## Revenue marts (Phase 6)

### `marts.dim_account`

One row per account with industry, country, signup attributes, and tenure bucket.

### `marts.fct_account_monthly_mrr`

**Grain:** one row per account per month

| Field | Definition |
|---|---|
| `mrr` | Sum of active subscription `mrr_amount` in the month |
| `prior_mrr` | Previous month MRR for the same account (`0` if none) |
| `new_mrr` | First-time positive MRR (no prior positive history) |
| `reactivation_mrr` | Positive MRR after a prior positive period and a zero month |
| `expansion_mrr` | Increase vs prior month when both months have MRR |
| `contraction_mrr` | Decrease vs prior month when current MRR remains positive |
| `churned_mrr` | Prior MRR lost when current MRR becomes `0` |
| `retained_mrr` | `LEAST(mrr, prior_mrr)` when both are positive |

### `marts.fct_mrr_movement_monthly`

Company-level monthly waterfall rollup of movement components.

Reconciliation identity:

```text
ending_mrr =
  starting_mrr
  + new_mrr
  + reactivation_mrr
  + expansion_mrr
  - contraction_mrr
  - churned_mrr
```

### `marts.mart_executive_monthly`

| Metric | Definition |
|---|---|
| **Total MRR** | Sum of account MRR in the month |
| **ARR** | `Total MRR * 12` |
| **Active accounts** | Accounts with `mrr > 0` |
| **New accounts** | Accounts with `new_mrr > 0` |
| **Churned accounts** | Accounts with `churned_mrr > 0` |
| **Logo churn rate** | `churned_accounts / prior_active_accounts` |
| **Gross revenue retention (GRR)** | `(starting_mrr - churned_mrr - contraction_mrr) / starting_mrr` |
| **Net revenue retention (NRR)** | `(starting_mrr + expansion_mrr - contraction_mrr - churned_mrr) / starting_mrr` |
| **ARPU** | `Total MRR / Active accounts` |

Notes:

- NRR and GRR are calculated on the existing-customer base (`starting_mrr`).
- New and reactivation MRR are excluded from NRR/GRR denominators by design.
- Cohort retention remains planned for Phase 7.

## Cohort, support, and usage marts (Phase 7)

### `marts.fct_cohort_retention`

**Grain:** one row per `cohort_month` × `month_number`

| Field | Definition |
|---|---|
| `cohort_month` | Account signup month |
| `month_number` | Months since signup |
| `cohort_size` | Accounts that signed up in the cohort month |
| `retained_accounts` | Accounts still retained at that month number |
| `retention_rate` | `retained_accounts / cohort_size` |

Retention rule:

- Month 0 is always 100% (all signup accounts retained by definition).
- Later months count an account as retained when `mrr > 0`.

### `marts.fct_support_monthly`

**Grain:** one row per account × month

Includes ticket counts, high-priority and escalated tickets, average resolution hours, SLA breaches (`resolution_time_hours > 48`), and satisfaction.

### `marts.fct_usage_monthly`

**Grain:** one row per account × month

Includes usage events, usage count, active features, duration minutes, error count, and error rate.

### `marts.mart_churn_drivers`

**Grain:** one row per account × month

Joins spine + MRR + support + usage and adds:

- `churns_next_month`
- `next_month_churned_mrr`
- `churn_reason_code` on the recorded churn month

This table is the analysis layer for churn driver exploration and dashboards.

## Dashboard diagnostic metrics

### Segment next-month churn rate

```text
active account-months followed by churn / active account-months
```

This is a diagnostic comparison across plans and industries, not the executive
monthly logo churn KPI.

### At-risk account score

The dashboard uses a transparent 100-point prioritization heuristic:

- 35 points: usage declined at least 30% from the prior month
- 25 points: one or more SLA breaches
- 20 points: one or more high-priority tickets
- 20 points: error rate above the latest-month median

Risk bands are low (`0-24`), medium (`25-49`), and high (`50-100`). The score is
not a causal model or a trained churn prediction.

### SLA breach rate

```text
tickets resolved after 48 hours / all support tickets
```


## Design principles

- Metrics are computed from staging + spine tables, not directly from raw CSVs.
- Month-level logic is centralized in the account-month spine.
- Revenue marts implement KPI definitions once and are reused by dashboards.
- Support and usage are rolled up before joining so churn-driver grain stays unique.
