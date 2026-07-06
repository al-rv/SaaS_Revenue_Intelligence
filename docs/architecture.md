# Architecture

The project follows a production-style analytics architecture: raw source files are ingested into DuckDB, transformed through SQL layers, validated, exported to dashboard-ready files, and served through Streamlit.

##  Proposed System Diagram

```mermaid
flowchart TB
    Raw["Raw CSVs<br/>accounts, subscriptions, usage, tickets, churn"]
    Ingest["Python ingestion scripts"]
    DuckDB[("DuckDB warehouse")]
    Staging["staging schema<br/>clean types and names"]
    Intermediate["intermediate schema<br/>account-month spine"]
    Marts["marts schema<br/>revenue, churn, cohorts, usage"]
    Tests["pytest + SQL validation"]
    Exports["processed parquet files"]
    App["Streamlit dashboard"]
    Deploy["Streamlit Cloud"]

    Raw --> Ingest --> DuckDB
    DuckDB --> Staging --> Intermediate --> Marts
    Marts --> Tests
    Marts --> Exports --> App --> Deploy
```

## Layer Responsibilities

| Layer | Purpose |
|---|---|
| Raw | Preserve downloaded source tables without business transformations |
| Staging | Clean names, cast types, standardize values, enforce basic quality |
| Intermediate | Build reusable business grains such as account-month |
| Marts | Create KPI-ready facts and dimensions for reporting |
| Exports | Store dashboard-ready Parquet files for fast app loading |
| App | Present metrics, trends, filters, and recommendations |

## Planned Schemas

```text
raw
staging
intermediate
marts
```

## Core Modeling Grain

The most important modeling table will be the account-month spine:

```text
one row per account per calendar month
```

This grain makes MRR movement, churn, cohort retention, support impact, and product usage analysis reliable and repeatable.
