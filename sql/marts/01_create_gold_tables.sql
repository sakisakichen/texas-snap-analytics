-- ============================================================
-- SNAP Analytics Platform V2
-- Gold Physical Model DDL
--
-- Purpose:
--   Create the dimensional model used for governed analytics.
--
-- Build order:
--   1. Dimensions
--   2. Facts
--
-- Gold trust is established through validation and reconciliation
-- in 04_validate_gold.sql.
-- ============================================================

USE DATABASE SNAP_ANALYTICS;
USE SCHEMA GOLD;


-- ============================================================
-- DIM_MONTH
-- Grain: One row per reporting month
-- ============================================================

CREATE TABLE IF NOT EXISTS DIM_MONTH (
    month_key          INTEGER        NOT NULL,
    reporting_month    VARCHAR        NOT NULL,
    year               INTEGER        NOT NULL,
    quarter            VARCHAR        NOT NULL,
    month_number       INTEGER        NOT NULL,
    month_name         VARCHAR        NOT NULL
);


-- ============================================================
-- DIM_REGION
-- Grain: One row per governed geographic/reporting region
--
-- Includes:
--   - Canonical Regions 01-11
--   - Combined reporting region 02/09 used by Timeliness reporting
--
-- Non-geographic reporting units are not included.
-- ============================================================

CREATE TABLE IF NOT EXISTS DIM_REGION (
    region_key         INTEGER        NOT NULL,
    region_code        VARCHAR(5)     NOT NULL,
    region_name        VARCHAR        NOT NULL
);


-- ============================================================
-- DIM_COUNTY
-- Grain: One row per Texas county
--
-- Expected population: 254 counties
-- county_fips uses the 5-digit Census GEOID.
-- ============================================================

CREATE TABLE IF NOT EXISTS DIM_COUNTY (
    county_key         INTEGER        NOT NULL,
    county_fips        VARCHAR(5)     NOT NULL,
    county_name        VARCHAR        NOT NULL,
    region_key         INTEGER        NOT NULL
);


-- ============================================================
-- FACT_SNAP_PROCESSING
-- Business Process: SNAP Processing Performance
--
-- Grain:
--   One row per Region x Reporting Month x Processing Type
--
-- Processing Types:
--   Applications
--   Redeterminations
--
-- Source percentages are not promoted to Gold.
-- Timeliness rate is governed downstream as:
--   SUM(timely_count) / SUM(disposed_count)
--
-- Non-geographic Timeliness reporting units are excluded.
-- ============================================================

CREATE TABLE IF NOT EXISTS FACT_SNAP_PROCESSING (
    region_key         INTEGER        NOT NULL,
    month_key          INTEGER        NOT NULL,
    processing_type    VARCHAR        NOT NULL,
    disposed_count     INTEGER,
    timely_count       INTEGER
);


-- ============================================================
-- FACT_SNAP_CASELOAD_MONTHLY
-- Business Process: Monthly SNAP Caseload & Benefit Activity
--
-- Grain:
--   One row per County x Reporting Month
--
-- avg_payment_per_case is not stored as a base measure.
-- It is governed downstream as:
--   SUM(total_snap_payments) / SUM(case_count)
-- ============================================================

CREATE TABLE IF NOT EXISTS FACT_SNAP_CASELOAD_MONTHLY (
    county_key                    INTEGER        NOT NULL,
    month_key                     INTEGER        NOT NULL,
    case_count                    INTEGER,
    eligible_individual_count     INTEGER,
    eligible_under_5_count        INTEGER,
    eligible_5_17_count           INTEGER,
    eligible_18_59_count          INTEGER,
    eligible_60_64_count          INTEGER,
    eligible_65_plus_count        INTEGER,
    total_snap_payments           NUMBER(18,2)
);


-- ============================================================
-- Snowflake Constraint Note
--
-- Primary-key and foreign-key declarations on standard Snowflake
-- tables are generally informational rather than enforced.
--
-- Gold trust is therefore established through explicit validation:
--   - Grain uniqueness
--   - Key completeness
--   - Relationship integrity
--   - Business-rule validation
--   - Silver-to-Gold reconciliation
--   - Governed metric validation
--
-- See: 04_validate_gold.sql
-- ============================================================