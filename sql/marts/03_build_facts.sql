-- SNAP Analytics Platform V2
-- Build Gold facts from Trusted Silver using dimension-key lookups.

USE DATABASE SNAP_ANALYTICS;
USE SCHEMA GOLD;

-- ============================================================
-- FACT_SNAP_PROCESSING
-- Silver grain = Gold grain:
-- Region x Reporting Month x Processing Type
-- ============================================================

TRUNCATE TABLE FACT_SNAP_PROCESSING;

INSERT INTO FACT_SNAP_PROCESSING (
    region_key,
    month_key,
    processing_type,
    disposed_count,
    timely_count
)
SELECT
    r.region_key,
    m.month_key,
    s.processing_type,
    s.disposed_count,
    s.timely_count
FROM SNAP_ANALYTICS.SILVER.SNAP_TIMELINESS s
LEFT JOIN DIM_REGION r
    ON s.region_code = r.region_code
LEFT JOIN DIM_MONTH m
    ON s.reporting_month = m.reporting_month;

-- ============================================================
-- FACT_SNAP_CASELOAD_MONTHLY
-- Silver grain = Gold grain:
-- County x Reporting Month
-- ============================================================

TRUNCATE TABLE FACT_SNAP_CASELOAD_MONTHLY;

INSERT INTO FACT_SNAP_CASELOAD_MONTHLY (
    county_key,
    month_key,
    case_count,
    eligible_individual_count,
    eligible_under_5_count,
    eligible_5_17_count,
    eligible_18_59_count,
    eligible_60_64_count,
    eligible_65_plus_count,
    total_snap_payments
)
SELECT
    c.county_key,
    m.month_key,
    s.case_count,
    s.eligible_individual_count,
    s.eligible_under_5_count,
    s.eligible_5_17_count,
    s.eligible_18_59_count,
    s.eligible_60_64_count,
    s.eligible_65_plus_count,
    s.total_snap_payments
FROM SNAP_ANALYTICS.SILVER.SNAP_ELIGIBILITY s
LEFT JOIN DIM_COUNTY c
    ON s.county_fips = c.county_fips
LEFT JOIN DIM_MONTH m
    ON s.reporting_month = m.reporting_month;

-- Governed derived metrics should be calculated at query / semantic level:
--
-- Timeliness Rate:
--   SUM(timely_count) / NULLIF(SUM(disposed_count), 0)
--
-- Average Payment per Case:
--   SUM(total_snap_payments) / NULLIF(SUM(case_count), 0)
