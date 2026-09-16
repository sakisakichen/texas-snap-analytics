-- ============================================================
-- SNAP Analytics Platform V2
-- Gold Acceptance Criteria / Validation Gate
--
-- Purpose:
--   Validate Gold population, grain, keys, relationships,
--   business rules, Silver-to-Gold reconciliation, and
--   governed metric calculations.
--
-- Expected result:
--   Exception queries should return 0 rows / 0 failures.
--
-- Do not publish Trusted Gold until failures are investigated.
-- ============================================================

USE DATABASE SNAP_ANALYTICS;
USE SCHEMA GOLD;


-- ============================================================
-- 1. DIM_MONTH
-- Grain: One row per reporting month
-- Expected complete 2024 population: 12
-- ============================================================

SELECT COUNT(*) AS dim_month_row_count
FROM DIM_MONTH;


-- Expected: 0 rows
SELECT
    month_key,
    COUNT(*) AS row_count
FROM DIM_MONTH
GROUP BY month_key
HAVING COUNT(*) > 1;


-- Expected: 0
SELECT COUNT(*) AS null_month_keys
FROM DIM_MONTH
WHERE month_key IS NULL;


-- Every Trusted Silver month should resolve to DIM_MONTH.
-- Expected: 0 rows
WITH silver_months AS (

    SELECT report_month AS reporting_month
    FROM SNAP_ANALYTICS.SILVER.SNAP_ELIGIBILITY

    UNION

    SELECT reporting_month
    FROM SNAP_ANALYTICS.SILVER.SNAP_TIMELINESS
)

SELECT s.reporting_month
FROM silver_months s

LEFT JOIN DIM_MONTH m
    ON s.reporting_month = m.reporting_month

WHERE m.month_key IS NULL;


-- ============================================================
-- 2. DIM_REGION
--
-- Expected population:
--   11 canonical geographic regions
--   + combined Timeliness reporting region 02/09
--   = 12 rows
-- ============================================================

SELECT COUNT(*) AS dim_region_row_count
FROM DIM_REGION;


-- Expected: 0 rows
SELECT
    region_key,
    COUNT(*) AS row_count
FROM DIM_REGION
GROUP BY region_key
HAVING COUNT(*) > 1;


-- Expected: 0 rows
SELECT
    region_code,
    COUNT(*) AS row_count
FROM DIM_REGION
GROUP BY region_code
HAVING COUNT(*) > 1;


-- Expected: 0
SELECT COUNT(*) AS null_region_keys
FROM DIM_REGION
WHERE region_key IS NULL;


-- Governed Timeliness reporting units used by Gold
-- should resolve to DIM_REGION.
-- Expected: 0 rows

SELECT DISTINCT
    s."Region" AS region_code
FROM SNAP_ANALYTICS.SILVER.SNAP_TIMELINESS s

LEFT JOIN DIM_REGION r
    ON s."Region" = r.region_code

WHERE s."Region" IN (
    '01',
    '02/09',
    '03',
    '04',
    '05',
    '06',
    '07',
    '08',
    '10',
    '11'
)
AND r.region_key IS NULL;


-- ============================================================
-- 3. DIM_COUNTY
--
-- Expected Texas analytical population: 254 counties
-- ============================================================

SELECT COUNT(*) AS dim_county_row_count
FROM DIM_COUNTY;


-- Expected: 0 rows
SELECT
    county_key,
    COUNT(*) AS row_count
FROM DIM_COUNTY
GROUP BY county_key
HAVING COUNT(*) > 1;


-- Expected: 0 rows
SELECT
    county_fips,
    COUNT(*) AS row_count
FROM DIM_COUNTY
GROUP BY county_fips
HAVING COUNT(*) > 1;


-- Expected: 0
SELECT COUNT(*) AS null_county_keys
FROM DIM_COUNTY
WHERE county_key IS NULL;


-- Expected: 0
SELECT COUNT(*) AS null_county_fips
FROM DIM_COUNTY
WHERE county_fips IS NULL;


-- Expected: 0
SELECT COUNT(*) AS null_region_keys
FROM DIM_COUNTY
WHERE region_key IS NULL;


-- Every County region_key should resolve to DIM_REGION.
-- Expected: 0 rows

SELECT
    c.county_fips,
    c.county_name,
    c.region_key
FROM DIM_COUNTY c

LEFT JOIN DIM_REGION r
    ON c.region_key = r.region_key

WHERE r.region_key IS NULL;


-- Every Eligibility county should resolve to DIM_COUNTY.
-- Expected: 0 rows

SELECT
    e.county_name
FROM SNAP_ANALYTICS.SILVER.SNAP_ELIGIBILITY e

LEFT JOIN DIM_COUNTY c
    ON UPPER(TRIM(e.county_name))
     = UPPER(TRIM(c.county_name))

WHERE c.county_key IS NULL

GROUP BY e.county_name
ORDER BY e.county_name;


-- ============================================================
-- 4. FACT_SNAP_PROCESSING
--
-- Grain:
--   Region x Reporting Month x Processing Type
--
-- Expected 2024 population:
--   10 reporting regions x 12 months x 2 processing types
--   = 240 rows
--
-- Gold scope intentionally excludes non-geographic
-- Timeliness reporting units.
-- ============================================================

SELECT COUNT(*) AS fact_processing_row_count
FROM FACT_SNAP_PROCESSING;


-- Grain uniqueness.
-- Expected: 0 rows

SELECT
    region_key,
    month_key,
    processing_type,
    COUNT(*) AS row_count
FROM FACT_SNAP_PROCESSING

GROUP BY
    region_key,
    month_key,
    processing_type

HAVING COUNT(*) > 1;


-- Null dimension keys.
-- Expected: 0

SELECT COUNT(*) AS null_dimension_keys
FROM FACT_SNAP_PROCESSING
WHERE region_key IS NULL
   OR month_key IS NULL;


-- Dimension relationship integrity.
-- Expected: 0 / 0

SELECT
    COUNT_IF(r.region_key IS NULL) AS bad_region_fk,
    COUNT_IF(m.month_key IS NULL) AS bad_month_fk
FROM FACT_SNAP_PROCESSING f

LEFT JOIN DIM_REGION r
    ON f.region_key = r.region_key

LEFT JOIN DIM_MONTH m
    ON f.month_key = m.month_key;


-- Valid processing types.
-- Expected: 0 rows

SELECT DISTINCT processing_type
FROM FACT_SNAP_PROCESSING
WHERE processing_type NOT IN (
    'Applications',
    'Redeterminations'
);


-- Business plausibility.
-- Expected: 0 rows

SELECT *
FROM FACT_SNAP_PROCESSING
WHERE disposed_count < 0
   OR timely_count < 0
   OR timely_count > disposed_count;


-- ------------------------------------------------------------
-- Processing Silver -> Gold Overall Reconciliation
--
-- IMPORTANT:
-- Reconciliation uses the SAME governed geographic/reporting
-- population used to build the Gold fact.
-- ------------------------------------------------------------

SELECT
    'SILVER' AS layer,
    COUNT(*) AS row_count,
    SUM(disposed_count) AS disposed_count,
    SUM(timely_count) AS timely_count

FROM SNAP_ANALYTICS.SILVER.SNAP_TIMELINESS

WHERE "Region" IN (
    '01',
    '02/09',
    '03',
    '04',
    '05',
    '06',
    '07',
    '08',
    '10',
    '11'
)

UNION ALL

SELECT
    'GOLD' AS layer,
    COUNT(*) AS row_count,
    SUM(disposed_count) AS disposed_count,
    SUM(timely_count) AS timely_count

FROM FACT_SNAP_PROCESSING;


-- ------------------------------------------------------------
-- Processing Grain-Level Reconciliation
-- Expected: 0 rows
-- ------------------------------------------------------------

WITH silver AS (

    SELECT
        "Region" AS region_code,
        reporting_month,
        processing_type,
        SUM(disposed_count) AS disposed_count,
        SUM(timely_count) AS timely_count

    FROM SNAP_ANALYTICS.SILVER.SNAP_TIMELINESS

    WHERE "Region" IN (
        '01',
        '02/09',
        '03',
        '04',
        '05',
        '06',
        '07',
        '08',
        '10',
        '11'
    )

    GROUP BY
        "Region",
        reporting_month,
        processing_type
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

    GROUP BY
        r.region_code,
        m.reporting_month,
        f.processing_type
)

SELECT
    COALESCE(s.region_code, g.region_code) AS region_code,
    COALESCE(
        s.reporting_month,
        g.reporting_month
    ) AS reporting_month,
    COALESCE(
        s.processing_type,
        g.processing_type
    ) AS processing_type,

    s.disposed_count AS silver_disposed,
    g.disposed_count AS gold_disposed,

    s.timely_count AS silver_timely,
    g.timely_count AS gold_timely

FROM silver s

FULL OUTER JOIN gold g
    ON s.region_code = g.region_code
   AND s.reporting_month = g.reporting_month
   AND s.processing_type = g.processing_type

WHERE
    COALESCE(s.disposed_count, -1)
        <> COALESCE(g.disposed_count, -1)

 OR COALESCE(s.timely_count, -1)
        <> COALESCE(g.timely_count, -1);


-- Governed Timeliness Rate sanity check.
--
-- Do NOT AVG source_percent.
--
-- Governed formula:
--   SUM(timely_count) / SUM(disposed_count)

SELECT
    m.reporting_month,
    f.processing_type,

    SUM(f.timely_count)
        / NULLIF(SUM(f.disposed_count), 0)
        AS timeliness_rate

FROM FACT_SNAP_PROCESSING f

JOIN DIM_MONTH m
    ON f.month_key = m.month_key

GROUP BY
    m.reporting_month,
    f.processing_type

ORDER BY
    m.reporting_month,
    f.processing_type;


-- ============================================================
-- 5. FACT_SNAP_CASELOAD_MONTHLY
--
-- Grain:
--   County x Reporting Month
--
-- Expected complete 2024 population:
--   254 counties x 12 months = 3,048 rows
-- ============================================================

SELECT COUNT(*) AS fact_caseload_row_count
FROM FACT_SNAP_CASELOAD_MONTHLY;


-- Grain uniqueness.
-- Expected: 0 rows

SELECT
    county_key,
    month_key,
    COUNT(*) AS row_count
FROM FACT_SNAP_CASELOAD_MONTHLY

GROUP BY
    county_key,
    month_key

HAVING COUNT(*) > 1;


-- Null dimension keys.
-- Expected: 0

SELECT COUNT(*) AS null_dimension_keys
FROM FACT_SNAP_CASELOAD_MONTHLY
WHERE county_key IS NULL
   OR month_key IS NULL;


-- Dimension relationship integrity.
-- Expected: 0 / 0 / 0

SELECT
    COUNT_IF(c.county_key IS NULL) AS bad_county_fk,
    COUNT_IF(m.month_key IS NULL) AS bad_month_fk,
    COUNT_IF(r.region_key IS NULL) AS bad_region_fk

FROM FACT_SNAP_CASELOAD_MONTHLY f

LEFT JOIN DIM_COUNTY c
    ON f.county_key = c.county_key

LEFT JOIN DIM_MONTH m
    ON f.month_key = m.month_key

LEFT JOIN DIM_REGION r
    ON c.region_key = r.region_key;


-- Negative measure check.
-- Expected: 0 rows

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


-- Age-band reconciliation.
--
-- Age bands should reconcile to eligible individuals,
-- NOT case_count.
--
-- Expected: 0 rows

SELECT *
FROM FACT_SNAP_CASELOAD_MONTHLY

WHERE
      COALESCE(eligible_under_5_count, 0)
    + COALESCE(eligible_5_17_count, 0)
    + COALESCE(eligible_18_59_count, 0)
    + COALESCE(eligible_60_64_count, 0)
    + COALESCE(eligible_65_plus_count, 0)

    <> COALESCE(eligible_individual_count, 0);


-- ------------------------------------------------------------
-- Caseload Silver -> Gold Overall Reconciliation
--
-- Base measures should remain unchanged during
-- Silver-to-Gold dimensional transformation.
-- ------------------------------------------------------------

SELECT
    'SILVER' AS layer,
    COUNT(*) AS row_count,
    SUM(case_count) AS case_count,
    SUM(eligible_individual_count)
        AS eligible_individual_count,
    SUM(eligible_under_5_count)
        AS eligible_under_5_count,
    SUM(eligible_5_17_count)
        AS eligible_5_17_count,
    SUM(eligible_18_59_count)
        AS eligible_18_59_count,
    SUM(eligible_60_64_count)
        AS eligible_60_64_count,
    SUM(eligible_65_plus_count)
        AS eligible_65_plus_count,
    SUM(total_snap_payments)
        AS total_snap_payments

FROM SNAP_ANALYTICS.SILVER.SNAP_ELIGIBILITY

UNION ALL

SELECT
    'GOLD' AS layer,
    COUNT(*) AS row_count,
    SUM(case_count),
    SUM(eligible_individual_count),
    SUM(eligible_under_5_count),
    SUM(eligible_5_17_count),
    SUM(eligible_18_59_count),
    SUM(eligible_60_64_count),
    SUM(eligible_65_plus_count),
    SUM(total_snap_payments)

FROM FACT_SNAP_CASELOAD_MONTHLY;


-- Governed Average Payment per Case sanity check.
--
-- Do NOT AVG row-level averages.
--
-- Governed formula:
--   SUM(total_snap_payments) / SUM(case_count)

SELECT
    SUM(total_snap_payments)
        / NULLIF(SUM(case_count), 0)
        AS avg_payment_per_case

FROM FACT_SNAP_CASELOAD_MONTHLY;