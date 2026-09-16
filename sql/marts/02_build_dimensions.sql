-- ============================================================
-- SNAP Analytics Platform V2
-- Build Gold Dimensions
--
-- Sources:
--   - Trusted Silver Eligibility
--   - Trusted Silver Timeliness
--   - Governed County-to-Region Reference
--
-- Build order:
--   1. DIM_MONTH
--   2. DIM_REGION
--   3. DIM_COUNTY
-- ============================================================

USE DATABASE SNAP_ANALYTICS;
USE SCHEMA GOLD;


-- ============================================================
-- DIM_MONTH
--
-- Grain:
--   One row per reporting month
--
-- Source:
--   Union of reporting months from both Trusted Silver datasets
-- ============================================================

TRUNCATE TABLE DIM_MONTH;

INSERT INTO DIM_MONTH (
    month_key,
    reporting_month,
    year,
    quarter,
    month_number,
    month_name
)
WITH all_months AS (

    SELECT report_month AS reporting_month
    FROM SNAP_ANALYTICS.SILVER.SNAP_ELIGIBILITY

    UNION

    SELECT reporting_month
    FROM SNAP_ANALYTICS.SILVER.SNAP_TIMELINESS
),

parsed AS (
    SELECT
        reporting_month,
        TO_DATE(reporting_month || '-01', 'YYYY-MM-DD') AS month_date
    FROM all_months
)

SELECT
    TO_NUMBER(TO_CHAR(month_date, 'YYYYMM')) AS month_key,
    reporting_month,
    YEAR(month_date)                         AS year,
    'Q' || QUARTER(month_date)               AS quarter,
    MONTH(month_date)                        AS month_number,
    MONTHNAME(month_date)                    AS month_name
FROM parsed
ORDER BY month_key;


-- ============================================================
-- DIM_REGION
--
-- Grain:
--   One row per governed geographic/reporting region
--
-- Canonical geographic regions are sourced from the governed
-- County-to-Region reference.
--
-- Timeliness also contains the combined reporting region 02/09.
-- It is preserved as a governed reporting region so processing
-- measures are not split, duplicated, or misattributed.
--
-- Non-geographic Timeliness reporting units are excluded.
-- ============================================================

TRUNCATE TABLE DIM_REGION;

-- Canonical geographic regions 01-11
INSERT INTO DIM_REGION (
    region_key,
    region_code,
    region_name
)
SELECT
    region_code::INTEGER AS region_key,
    region_code,
    'Region ' || region_code AS region_name
FROM (
    SELECT DISTINCT region_code
    FROM SNAP_ANALYTICS.SILVER.COUNTY_REGION_REFERENCE
)
ORDER BY region_code;


-- Combined Timeliness reporting region
INSERT INTO DIM_REGION (
    region_key,
    region_code,
    region_name
)
VALUES (
    12,
    '02/09',
    'Region 02/09'
);


-- ============================================================
-- DIM_COUNTY
--
-- Grain:
--   One row per Texas county
--
-- Source:
--   Governed County-to-Region reference
--
-- Expected population:
--   254 Texas counties
--
-- county_key:
--   Generated surrogate key
--
-- region_key:
--   Resolved through DIM_REGION
-- ============================================================

TRUNCATE TABLE DIM_COUNTY;

INSERT INTO DIM_COUNTY (
    county_key,
    county_fips,
    county_name,
    region_key
)
SELECT
    ROW_NUMBER() OVER (
        ORDER BY c.county_fips
    ) AS county_key,

    c.county_fips,
    c.county_name,
    r.region_key

FROM SNAP_ANALYTICS.SILVER.COUNTY_REGION_REFERENCE c

LEFT JOIN DIM_REGION r
    ON c.region_code = r.region_code

ORDER BY c.county_fips;