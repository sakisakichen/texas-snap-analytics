-- SNAP Analytics Platform V2
-- Gold Acceptance Criteria / Validation Queries
--
-- Expected result for most exception queries = 0 rows.
-- Do not publish Trusted Gold until failures are investigated.

USE DATABASE SNAP_ANALYTICS;
USE SCHEMA GOLD;

-- ============================================================
-- 1. DIM_MONTH
-- ============================================================

-- Expected for complete 2024 model: 12
SELECT COUNT(*) AS dim_month_row_count
FROM DIM_MONTH;

-- Expected: 0 rows
SELECT month_key, COUNT(*) AS row_count
FROM DIM_MONTH
GROUP BY month_key
HAVING COUNT(*) > 1;

-- Expected: 0
SELECT COUNT(*) AS null_month_keys
FROM DIM_MONTH
WHERE month_key IS NULL;

-- Every Silver month should resolve exactly once.
WITH silver_months AS (
    SELECT reporting_month FROM SNAP_ANALYTICS.SILVER.SNAP_ELIGIBILITY
    UNION
    SELECT reporting_month FROM SNAP_ANALYTICS.SILVER.SNAP_TIMELINESS
)
SELECT s.reporting_month
FROM silver_months s
LEFT JOIN DIM_MONTH m
    ON s.reporting_month = m.reporting_month
WHERE m.month_key IS NULL;

-- ============================================================
-- 2. DIM_REGION
-- ============================================================

-- Expected: 0 rows
SELECT region_key, COUNT(*) AS row_count
FROM DIM_REGION
GROUP BY region_key
HAVING COUNT(*) > 1;

-- Expected: 0 rows
SELECT region_code, COUNT(*) AS row_count
FROM DIM_REGION
GROUP BY region_code
HAVING COUNT(*) > 1;

-- Timeliness Silver mapping coverage. Expected: 0 rows.
SELECT DISTINCT s.region_code
FROM SNAP_ANALYTICS.SILVER.SNAP_TIMELINESS s
LEFT JOIN DIM_REGION r
    ON s.region_code = r.region_code
WHERE r.region_key IS NULL;

-- ============================================================
-- 3. DIM_COUNTY
-- ============================================================

-- Expected for Texas analytical population: 254
SELECT COUNT(*) AS dim_county_row_count
FROM DIM_COUNTY;

-- Expected: 0 rows
SELECT county_key, COUNT(*) AS row_count
FROM DIM_COUNTY
GROUP BY county_key
HAVING COUNT(*) > 1;

-- Expected: 0 rows
SELECT county_fips, COUNT(*) AS row_count
FROM DIM_COUNTY
GROUP BY county_fips
HAVING COUNT(*) > 1;

-- Expected: 0
SELECT COUNT(*) AS null_region_keys
FROM DIM_COUNTY
WHERE region_key IS NULL;

-- Expected: 0 rows
SELECT c.county_fips, c.county_name, c.region_key
FROM DIM_COUNTY c
LEFT JOIN DIM_REGION r
    ON c.region_key = r.region_key
WHERE r.region_key IS NULL;

-- ============================================================
-- 4. FACT_SNAP_PROCESSING
-- ============================================================

-- Grain uniqueness. Expected: 0 rows.
SELECT
    region_key,
    month_key,
    processing_type,
    COUNT(*) AS row_count
FROM FACT_SNAP_PROCESSING
GROUP BY region_key, month_key, processing_type
HAVING COUNT(*) > 1;

-- Null / orphan key checks. Expected: 0.
SELECT COUNT(*) AS null_dimension_keys
FROM FACT_SNAP_PROCESSING
WHERE region_key IS NULL
   OR month_key IS NULL;

-- Business plausibility. Expected: 0 rows.
SELECT *
FROM FACT_SNAP_PROCESSING
WHERE disposed_count < 0
   OR timely_count < 0
   OR timely_count > disposed_count;

-- Overall Silver -> Gold reconciliation.
SELECT
    (SELECT SUM(disposed_count)
     FROM SNAP_ANALYTICS.SILVER.SNAP_TIMELINESS) AS silver_disposed,
    (SELECT SUM(disposed_count)
     FROM FACT_SNAP_PROCESSING) AS gold_disposed,
    (SELECT SUM(timely_count)
     FROM SNAP_ANALYTICS.SILVER.SNAP_TIMELINESS) AS silver_timely,
    (SELECT SUM(timely_count)
     FROM FACT_SNAP_PROCESSING) AS gold_timely;

-- Grain-level reconciliation. Expected: 0 rows.
WITH silver AS (
    SELECT
        region_code,
        reporting_month,
        processing_type,
        SUM(disposed_count) AS disposed_count,
        SUM(timely_count) AS timely_count
    FROM SNAP_ANALYTICS.SILVER.SNAP_TIMELINESS
    GROUP BY 1,2,3
),
gold AS (
    SELECT
        r.region_code,
        m.reporting_month,
        f.processing_type,
        SUM(f.disposed_count) AS disposed_count,
        SUM(f.timely_count) AS timely_count
    FROM FACT_SNAP_PROCESSING f
    JOIN DIM_REGION r
        ON f.region_key = r.region_key
    JOIN DIM_MONTH m
        ON f.month_key = m.month_key
    GROUP BY 1,2,3
)
SELECT
    COALESCE(s.region_code, g.region_code) AS region_code,
    COALESCE(s.reporting_month, g.reporting_month) AS reporting_month,
    COALESCE(s.processing_type, g.processing_type) AS processing_type,
    s.disposed_count AS silver_disposed,
    g.disposed_count AS gold_disposed,
    s.timely_count AS silver_timely,
    g.timely_count AS gold_timely
FROM silver s
FULL OUTER JOIN gold g
    ON s.region_code = g.region_code
   AND s.reporting_month = g.reporting_month
   AND s.processing_type = g.processing_type
WHERE COALESCE(s.disposed_count, -1) <> COALESCE(g.disposed_count, -1)
   OR COALESCE(s.timely_count, -1) <> COALESCE(g.timely_count, -1);

-- Governed Timeliness Rate example.
SELECT
    processing_type,
    SUM(timely_count)
        / NULLIF(SUM(disposed_count), 0) AS timeliness_rate
FROM FACT_SNAP_PROCESSING
GROUP BY processing_type;

-- ============================================================
-- 5. FACT_SNAP_CASELOAD_MONTHLY
-- ============================================================

-- Expected complete 2024 population: 3048
SELECT COUNT(*) AS fact_caseload_row_count
FROM FACT_SNAP_CASELOAD_MONTHLY;

-- Grain uniqueness. Expected: 0 rows.
SELECT
    county_key,
    month_key,
    COUNT(*) AS row_count
FROM FACT_SNAP_CASELOAD_MONTHLY
GROUP BY county_key, month_key
HAVING COUNT(*) > 1;

-- Null dimension keys. Expected: 0.
SELECT COUNT(*) AS null_dimension_keys
FROM FACT_SNAP_CASELOAD_MONTHLY
WHERE county_key IS NULL
   OR month_key IS NULL;

-- Negative measure check. Expected: 0 rows.
SELECT *
FROM FACT_SNAP_CASELOAD_MONTHLY
WHERE case_count < 0
   OR eligible_individual_count < 0
   OR eligible_under_5_count < 0
   OR eligible_5_17_count < 0
   OR eligible_18_59_count < 0
   OR eligible_60_64_count < 0
   OR eligible_65_plus_count < 0
   OR total_snap_payments < 0;

-- Age-band reconciliation. Expected: 0 rows.
SELECT *
FROM FACT_SNAP_CASELOAD_MONTHLY
WHERE COALESCE(eligible_under_5_count, 0)
    + COALESCE(eligible_5_17_count, 0)
    + COALESCE(eligible_18_59_count, 0)
    + COALESCE(eligible_60_64_count, 0)
    + COALESCE(eligible_65_plus_count, 0)
    <> COALESCE(eligible_individual_count, 0);

-- Overall Silver -> Gold measure reconciliation.
SELECT
    (SELECT SUM(case_count)
     FROM SNAP_ANALYTICS.SILVER.SNAP_ELIGIBILITY) AS silver_cases,
    (SELECT SUM(case_count)
     FROM FACT_SNAP_CASELOAD_MONTHLY) AS gold_cases,

    (SELECT SUM(eligible_individual_count)
     FROM SNAP_ANALYTICS.SILVER.SNAP_ELIGIBILITY) AS silver_eligible,
    (SELECT SUM(eligible_individual_count)
     FROM FACT_SNAP_CASELOAD_MONTHLY) AS gold_eligible,

    (SELECT SUM(total_snap_payments)
     FROM SNAP_ANALYTICS.SILVER.SNAP_ELIGIBILITY) AS silver_payments,
    (SELECT SUM(total_snap_payments)
     FROM FACT_SNAP_CASELOAD_MONTHLY) AS gold_payments;

-- Governed Average Payment per Case example.
SELECT
    SUM(total_snap_payments)
        / NULLIF(SUM(case_count), 0) AS avg_payment_per_case
FROM FACT_SNAP_CASELOAD_MONTHLY;
