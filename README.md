# Texas SNAP Analytics Dashboard 2024

An end-to-end analytics pipeline built on publicly available Texas Health and Human Services (HHS) SNAP data — designed to help program stakeholders quickly identify caseload trends, regional disparities, and federal timeliness compliance.

---

## Project Overview

| Layer | Tool | Description |
|---|---|---|
| Ingestion | Python (pandas) | Cleaned and standardized raw Excel files from Texas HHS |
| Storage | Snowflake | Loaded into Bronze → Gold layer schema |
| Modeling | Snowflake Views (Gold) | Joined enrollment + timeliness data; removed data quality issues |
| Visualization | Tableau Desktop | Live Connection to Snowflake Gold Layer |

> **Phase 1** covers SNAP Enrollment and Timeliness data (2024). Future phases may include TANF and WIC program data.

---

## Dashboard Preview

![Texas SNAP Analytics Dashboard 2024](./dashboard_preview.png)

> Built with Tableau Desktop using Snowflake Live Connection. Data refreshes automatically when the underlying Snowflake views are updated.

---

## Data Sources

**Texas Health and Human Services — Open Data Portal**

- [SNAP Enrollment by County](https://www.hhs.texas.gov/about/records-statistics/data-statistics/snap-statistics)
- [SNAP Timeliness Report](https://www.hhs.texas.gov/about/records-statistics/data-statistics/snap-statistics)
- Coverage: January 2024 – December 2024

---

## Pipeline Architecture

```
Texas HHS Excel Files
        ↓
  Python (pandas)
  - Remove state-level summary rows
  - Fix county name typos (e.g., "Matagorda1")
  - Filter out non-county entries (Call Centers, State Office)
  - Standardize column types & date formats
        ↓
  Snowflake (Bronze Layer)
  - Raw tables loaded as-is
        ↓
  Snowflake (Gold Layer Views)
  - vw_snap_enrollment_gold
  - vw_snap_timeliness_gold
  - vw_snap_combined (JOIN on county + month)
        ↓
  Tableau Desktop
  - Live Connection to Gold Layer
  - 7 Sheets + 1 Dashboard
```

---

## Dashboard Sheets

| Sheet | Chart Type | Key Question Answered |
|---|---|---|
| County Caseload Map | Filled Map | Which counties have the highest SNAP caseload? |
| Top Counties Ranking | Horizontal Bar | Which are the Top 10 counties by cases? |
| Monthly Enrollment Trend | Line Chart | How has total SNAP enrollment changed month-over-month? |
| Total Payment Trend | Line Chart | How has total SNAP payment amount trended in 2024? |
| Age Group Distribution | Line Chart | Which age segments receive the most SNAP benefits? |
| Case Composition | Pie Chart | What is the breakdown of individual vs household cases? |
| Timeliness Rate by Region | Bar Chart + Reference Line | Which regions meet the federal 95% timeliness target? |

---

## Key Data Quality Issues Resolved

During the visualization process, the following issues were discovered and fixed at the **Gold Layer** rather than patching in Tableau:

1. **State-level summary rows** mixed into county-level data → filtered out in Gold View
2. **County name typo**: `Matagorda1` → corrected to `Matagorda`
3. **Non-geographic entries** (Call Centers, State Office) → excluded from county analysis

---

## Key Findings

- **Harris County** accounts for nearly **2× the caseload** of the second-largest county (Dallas), reflecting its role as Texas's most populous urban center
- SNAP enrollment **peaks in Q3–Q4**, likely correlated with seasonal employment patterns and end-of-year economic pressures
- The **18–59 working-age population** represents the largest SNAP recipient group, consistent with national trends where employment instability — not age — is the primary driver of food insecurity
- **10 of 254 counties** account for a disproportionate share of total cases, suggesting resource allocation should be regionally targeted
- Several regions **fall below the federal 95% timeliness target**, pointing to processing bottlenecks that could affect benefit delivery

---

## Repository Structure

```
texas-snap-analytics/
│
├── data/
│   └── raw/              # Original Excel files from Texas HHS (not committed)
│
├── python/
│   └── snap_etl.py       # Data cleaning and Snowflake load script
│
├── snowflake/
│   ├── bronze_load.sql   # Raw table creation
│   └── gold_views.sql    # Gold Layer view definitions
│
├── assets/
│   └── dashboard_preview.png   # Dashboard screenshot
│
└── README.md
```

---

## Tech Stack

`Python` · `pandas` · `Snowflake` · `SQL` · `Tableau Desktop` · `Snowflake Live Connection`

---

## About

Built as a portfolio project to demonstrate an end-to-end data analytics pipeline using real government data. The domain mirrors professional work supporting state health and human services programs.

**Author:** Saki Chen | [GitHub](https://github.com/sakisakichen) | [LinkedIn](https://www.linkedin.com/in/sakichen)
