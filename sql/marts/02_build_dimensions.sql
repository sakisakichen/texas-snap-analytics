-- SNAP Analytics Platform V2
-- Build Gold dimensions from Trusted Silver / authoritative references.

USE DATABASE SNAP_ANALYTICS;
USE SCHEMA GOLD;

-- ============================================================
-- DIM_MONTH
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
    SELECT reporting_month
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
    TO_NUMBER(TO_CHAR(month_date, 'YYYYMM'))                          AS month_key,
    reporting_month,
    YEAR(month_date)                                                 AS year,
    'Q' || QUARTER(month_date)                                       AS quarter,
    MONTH(month_date)                                                AS month_number,
    MONTHNAME(month_date)                                            AS month_name
FROM parsed
ORDER BY month_key;

-- ============================================================
-- DIM_REGION
-- ============================================================
-- Production design:
-- DIM_REGION should be sourced from an authoritative Region reference /
-- County-to-Region crosswalk, not defined solely from a fact source.
--
-- When the authoritative reference is loaded into Snowflake, replace the
-- placeholder table name below and run this block.
--
-- Expected source columns:
--   region_code
--   region_name

-- TRUNCATE TABLE DIM_REGION;
--
-- INSERT INTO DIM_REGION (
--     region_key,
--     region_code,
--     region_name
-- )
-- SELECT
--     ROW_NUMBER() OVER (ORDER BY region_code) AS region_key,
--     region_code,
--     region_name
-- FROM SNAP_ANALYTICS.SILVER.<AUTHORITATIVE_REGION_REFERENCE>
-- QUALIFY ROW_NUMBER() OVER (
--     PARTITION BY region_code
--     ORDER BY region_code
-- ) = 1;

-- ============================================================
-- DIM_COUNTY
-- ============================================================
-- Production design:
-- DIM_COUNTY should be sourced from the authoritative County reference /
-- County-to-Region crosswalk.
--
-- Expected source columns:
--   county_fips
--   county_name
--   region_code
--
-- Region surrogate key is resolved through DIM_REGION.

-- TRUNCATE TABLE DIM_COUNTY;
--
-- INSERT INTO DIM_COUNTY (
--     county_key,
--     county_fips,
--     county_name,
--     region_key
-- )
-- SELECT
--     ROW_NUMBER() OVER (ORDER BY c.county_fips) AS county_key,
--     c.county_fips,
--     c.county_name,
--     r.region_key
-- FROM SNAP_ANALYTICS.SILVER.<AUTHORITATIVE_COUNTY_REGION_REFERENCE> c
-- LEFT JOIN DIM_REGION r
--     ON c.region_code = r.region_code;
