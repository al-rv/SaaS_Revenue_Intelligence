# Business Findings

Evidence below comes from the Rivalytics / RavenStack synthetic warehouse rebuilt locally through December 2024. These are the method demonstrations, not real-company conclusions.

## Snapshot

| KPI | Latest month (Dec 2024) |
|---|---|
| Total MRR | $10.73M |
| ARR | $128.81M |
| Active accounts | 500 |
| NRR | 118.1% |
| ARPU | $21.5K |
| Weighted month-3 cohort retention | 86.9% |

## Finding 1: Revenue growth is expansion-led

**Evidence**

Across the modeled window:

- Expansion MRR: **$8.63M**
- New MRR: **$2.55M**
- Average NRR: **119%** (range 111.7%–151.8%)

In December 2024 alone, expansion (`$1.70M`) exceeded new MRR (`$521.8K`).

**Recommendation**

Protect and fund expansion motions (seat growth, plan upgrades, annual conversions) before optimizing acquisition spend.

## Finding 2: Recorded churn concentrates in early tenure

**Evidence**

- **64.4%** of recorded churn events occur when `months_since_signup < 6`.
- The largest absolute churn-event buckets are months 0–2 (191 events) and months 3–5 (123 events).

**Recommendation**

Create a 30/60/90-day onboarding health check for accounts with low feature adoption or rising support load.

## Finding 3: Edtech shows the highest next-month churn rate

**Evidence**

Next-month churn rate among active account-months:

| Industry | Next-month churn rate |
|---|---:|
| Edtech | 10.3% |
| Healthtech | 8.3% |
| Fintech | 8.1% |
| Devtools | 8.0% |
| Cybersecurity | 7.9% |

Plan-tier differences are smaller (enterprise 8.6%, basic 8.4%, pro 8.2%).

**Recommendation**

Investigate edtech packaging, time-to-value, and academic calendar seasonality separately from other verticals.

## Finding 4: Stated churn reasons point to product and budget friction

**Evidence**

Top recorded reason codes:

| Reason | Events |
|---|---:|
| Features | 105 |
| Budget | 102 |
| Support | 92 |
| Competitor | 87 |
| Pricing | 85 |

**Recommendation**

Route feature-gap feedback into the product roadmap and treat support experience as a retention workstream, not only a discount decision.

## Finding 5: SLA breaches coincide with elevated churn risk

**Evidence**

| Support condition | Next-month churn rate | Active account-months |
|---|---:|---:|
| Had SLA breach | 9.9% | 272 |
| No SLA breach | 8.3% | 4,847 |

**Recommendation**

Use SLA breaches, high-priority tickets, and usage declines as Customer Success triage inputs. The dashboard risk score encodes these signals transparently.