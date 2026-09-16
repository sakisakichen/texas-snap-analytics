-- ============================================================
-- SNAP Analytics Platform V2
-- Build Gold Facts
--
-- Purpose:
--   Build analytics-ready fact tables from Trusted Silver
--   using governed dimension-key lookups.
--
-- Prerequisite:
--   Gold dimensions must be built and validated first.
-- ============================================================

USE DATABASE SNAP_ANALYTICS;
USE SCHEMA GOLD;


-- ============================================================
-- FACT_SNAP_PROCESSING
--
-- Business Process:
--   SNAP Processing Performance
--
-- Grain:
--   One row per Region x Reporting Month x Processing Type
--
-- Source:
--   Trusted Silver SNAP_TIMELINESS
--
-- Included reporting units:
--   01, 02/09, 03, 04, 05, 06, 07, 08, 10, 11
--
-- Non-geographic reporting units are excluded.
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

JOIN DIM_REGION r
    ON s."Region" = r.region_code

JOIN DIM_MONTH m
    ON s.reporting_month = m.reporting_month

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
);


-- ============================================================
-- FACT_SNAP_CASELOAD_MONTHLY
--
-- Business Process:
--   Monthly SNAP Caseload & Benefit Activity
--
-- Grain:
--   One row per County x Reporting Month
--
-- Source:
--   Trusted Silver SNAP_ELIGIBILITY
--
-- County identity is resolved through county_name because
-- county_fips is supplied by the governed County reference,
-- not by the Eligibility Silver dataset.
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

JOIN DIM_COUNTY c
    ON UPPER(TRIM(s.county_name)) = UPPER(TRIM(c.county_name))

JOIN DIM_MONTH m
    ON s.report_month = m.reporting_month;


-- ============================================================
-- Governed Derived Metrics
--
-- Derived metrics are intentionally NOT stored as physical
-- fact-table columns.
--
-- Timeliness Rate:
--   SUM(timely_count)
--   / NULLIF(SUM(disposed_count), 0)
--
-- Average Payment per Case:
--   SUM(total_snap_payments)
--   / NULLIF(SUM(case_count), 0)
--
-- These definitions are governed downstream in the
-- Semantic Metric Layer.
-- ============================================================