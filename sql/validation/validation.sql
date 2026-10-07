-- Module 6: Tableau / Snowflake reconciliation
-- Validation date: 2026-10-07. Scope: 2024 existing Semantic views.
-- Read-only queries; no infrastructure or transformation changes.
-- Compare Tableau using the same filters and aggregation.
-- These queries produce reference values; they do not automatically test Tableau.

-- 1. Applications annual KPI
-- Observed: 120 rows; disposed 2,002,129; timely 1,364,581;
-- timeliness 68.2%; target gap -26.84 percentage points.
SELECT
    COUNT(*) AS row_count,
    SUM(disposed_count) AS applications_disposed,
    SUM(timely_count) AS applications_timely,
    ROUND(100.0 * SUM(timely_count)
        / NULLIF(SUM(disposed_count), 0), 1) AS timeliness_pct,
    ROUND(100.0 * SUM(timely_count)
        / NULLIF(SUM(disposed_count), 0) - 95, 2) AS gap_percentage_points
FROM SNAP_ANALYTICS.SEMANTIC.VW_PROCESSING_METRICS
WHERE year = 2024
  AND processing_type = 'Applications';

-- 2. Applications annual region rates and ascending order
-- All 10 reporting regions matched Tableau at 1 decimal place.
-- Each region had 12 monthly records.
-- Unique aggregate aliases avoid collision with source column names.
SELECT
    region_code,
    COUNT(*) AS month_count,
    SUM(disposed_count) AS total_disposed,
    SUM(timely_count) AS total_timely,
    ROUND(100.0 * SUM(timely_count)
        / NULLIF(SUM(disposed_count), 0), 1) AS timeliness_pct
FROM SNAP_ANALYTICS.SEMANTIC.VW_PROCESSING_METRICS
WHERE year = 2024
  AND processing_type = 'Applications'
GROUP BY region_code
ORDER BY total_timely / NULLIF(total_disposed, 0), region_code;

-- 3. Monthly timeliness: Applications and Redeterminations
-- All 24 month/type values matched Tableau at 1 decimal place.
-- Each result contained 10 region records.
-- No Redeterminations benchmark is applied.
SELECT
    reporting_month,
    processing_type,
    COUNT(*) AS region_count,
    SUM(disposed_count) AS total_disposed,
    SUM(timely_count) AS total_timely,
    ROUND(100.0 * SUM(timely_count)
        / NULLIF(SUM(disposed_count), 0), 1) AS timeliness_pct
FROM SNAP_ANALYTICS.SEMANTIC.VW_PROCESSING_METRICS
WHERE year = 2024
GROUP BY reporting_month, processing_type
ORDER BY reporting_month, processing_type;

-- 4. Statewide monthly caseload: Tableau County filter = All
-- Observed: 12 months, 254 rows and 254 distinct counties each month.
-- Cases and individuals: all 12 monthly values matched.
-- Payments: all 12 values matched at whole-dollar precision only.
-- Keep cents in SQL output; cents were not reconciled in Tableau.
-- Cases/individuals are monthly counts, not annual distinct counts.
SELECT
    reporting_month,
    COUNT(*) AS row_count,
    COUNT(DISTINCT county_fips) AS county_count,
    SUM(case_count) AS total_cases,
    SUM(eligible_individual_count) AS total_individuals,
    SUM(total_snap_payments) AS total_payments
FROM SNAP_ANALYTICS.SEMANTIC.VW_CASELOAD_METRICS
WHERE year = 2024
GROUP BY reporting_month
ORDER BY reporting_month;

-- 5. Harris monthly caseload: Tableau County filter = Harris
-- Observed: 12 months, 1 row and 1 distinct county each month.
-- Cases: all 12 monthly values matched Tableau.
-- Individuals/payments were returned by this query but NOT numerically
-- reconciled with Tableau. Do not label those comparisons as passed.
-- Shared County filter behavior across all three charts was confirmed.
SELECT
    reporting_month,
    COUNT(*) AS row_count,
    COUNT(DISTINCT county_fips) AS county_count,
    SUM(case_count) AS total_cases,
    SUM(eligible_individual_count) AS total_individuals,
    SUM(total_snap_payments) AS total_payments
FROM SNAP_ANALYTICS.SEMANTIC.VW_CASELOAD_METRICS
WHERE year = 2024
  AND county_name = 'Harris'
GROUP BY reporting_month
ORDER BY reporting_month;
