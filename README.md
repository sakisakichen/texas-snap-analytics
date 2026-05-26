# Texas SNAP & TANF Analytics Dashboard 2024

An end-to-end analytics pipeline built on publicly available Texas Health and Human Services (HHS) data — designed to help program stakeholders quickly identify caseload trends, regional disparities, and service coverage gaps across SNAP and TANF programs.

---

## Project Overview

| Layer | Tool | Description |
|-------|------|-------------|
| Ingestion | Python (pandas) | Cleaned and standardized raw Excel files from Texas HHS |
| Storage | Snowflake | Loaded into Bronze → Silver → Gold layer schema |
| Modeling | Snowflake Views (Gold) | Aggregated enrollment and timeliness data; removed data quality issues |
| Visualization | Tableau Desktop | Live Connection to Snowflake Gold Layer |

**Phase 1** covers SNAP Enrollment and Timeliness data (2024).  
**Phase 2** adds TANF Enrollment data (2024) — coverage gap analysis and program type comparison.

---

## Dashboard Preview

![Texas SNAP & TANF Analytics Dashboard 2024](./Texas%20SNAP%20%26%20TANF%20Analytics%20Dashboard%202024.png)

> Built with Tableau Desktop using a Live Connection to Snowflake.  
> Shared via exported screenshots. In a production setting, this dashboard  
> would be published to Tableau Cloud or Tableau Server for secure, interactive sharing.

---

## Data Sources

Texas Health and Human Services — [Open Data Portal](https://www.hhs.texas.gov/about/records-statistics/data-statistics)

**Phase 1 — SNAP:**
- SNAP Enrollment by County
- SNAP Timeliness Report

**Phase 2 — TANF:**
- TANF Case and Recipients by County (Recipients sheet)

Coverage: January 2024 – December 2024 *(June 2024 unavailable from source)*

---

## Pipeline Architecture

```
Texas HHS Excel Files
        ↓
  Python (pandas)
  - Remove state-level summary rows
  - Fix county name typos
  - Filter out non-county entries
  - Standardize column types & date formats
  - Shared utility functions: clean_currency(), clean_numeric(), extract_month()
        ↓
  Snowflake
  TEXAS_HHS.SNAP   — SNAP_ENROLLMENT, SNAP_TIMELINESS
  TEXAS_HHS.TANF   — TANF_ENROLLMENT
        ↓
  Snowflake Gold Layer Views (TEXAS_HHS.GOLD)
  - V_SNAP_COUNTY_MONTHLY
  - V_SNAP_STATEWIDE_TREND
  - V_SNAP_TIMELINESS
  - V_TANF_COUNTY_SUMMARY
  - V_TANF_MONTHLY_TREND
        ↓
  Tableau Desktop
  - Live Connection to Gold Layer
  - 9 Sheets + 1 Dashboard
```

---

## Dashboard Sheets

| Sheet | Chart Type | Key Question Answered |
|-------|-----------|----------------------|
| TX SNAP Cases Distribution | Filled Map | Which counties have the highest SNAP caseload? |
| TX SNAP Cases by County | Horizontal Bar | Top 15 counties by cases |
| TX SNAP Monthly Trend 2024 | Line Chart | How has SNAP enrollment trended month-over-month? |
| TX SNAP Total Payment Trend | Line Chart | How has total SNAP payment amount trended? |
| TX SNAP Age Distribution | Line Chart | Which age segments receive the most SNAP benefits? |
| TX SNAP Age Group Distribution | Pie Chart | Breakdown of SNAP recipients by age group |
| TX SNAP Timeliness Rate | Line Chart + Reference Line | Which regions meet the federal 95% timeliness target? |
| TX TANF Cases Distribution | Filled Map | Which counties have no TANF coverage (cases = 0)? |
| TX TANF Monthly Trend 2024 | Line Chart | TANF Basic vs State Program cases trend |

---

## Key Data Quality Issues Resolved

**SNAP:**
- State-level summary rows mixed into county-level data → filtered in Gold View
- County name typo: `Matagorda1` → corrected to `Matagorda`
- Non-geographic entries (Call Centers, State Office) → excluded

**TANF:**
- County names in Col 1, not Col 0 → confirmed via exploratory print
- December sheet named `Recipients with SF completion` → renamed manually
- Excel floating point display issue (e.g., `15.154` displayed as `15`) → applied `round()` in `utils.py`
- Blank rows between counties contained `$0` values → filtered via `is_valid_county()`
- Temporary Excel files (`~$`) in data folder → filtered via `startswith('~$')` check

*All data quality fixes applied at the Gold Layer or Python cleaning stage — not patched in Tableau.*

---

## Key Findings

**SNAP:**
- Harris County accounts for nearly 2× the caseload of Dallas (second-largest county)
- Full-year Timeliness Rate never reached the federal 95% target — Applications dropped to 54% in September
- SNAP enrollment peaks in Q3–Q4, correlating with seasonal employment patterns
- Pre-school children (under 5) represent a significant share of recipients, indicating food insecurity affects very young children

**TANF:**
- TANF Basic (federally funded) is the primary program — State Program cases are significantly smaller
- Multiple counties across Texas have zero TANF cases, representing clear service coverage gaps
- TANF Basic caseload grew steadily through the second half of 2024

---

## Repository Structure

```
texas-snap-analytics/
│
├── SNAP/
│   ├── clean_snap_data.py
│   ├── clean_timeliness_data.py
│   ├── texas_snap_enrollment_2024.csv
│   └── texas_snap_timeliness_2024.csv
│
├── TANF/
│   ├── clean_tanf_data.py
│   └── texas_tanf_enrollment_2024.csv
│
├── utils.py                         # Shared utility functions
├── gold_views.sql                   # All Gold Layer view definitions (SNAP + TANF)
├── Texas SNAP Analytics Dashboard 2024.png
└── README.md
```

---

## Tech Stack

Python · pandas · Snowflake · SQL · Tableau Desktop · Snowflake Live Connection

---

## About

Built as a portfolio project to demonstrate an end-to-end analytics pipeline using real government data. The domain mirrors professional work supporting state health and human services programs through a nonprofit-government collaboration model.

**Author:** Saki Chen | [GitHub](https://github.com/sakisakichen) | [LinkedIn](https://linkedin.com/in/sakichen)
