-- SNAP Analytics Platform V2
-- Trusted Silver warehouse tables
-- Physical schema aligned with validated Trusted Silver Parquet artifacts.

USE DATABASE SNAP_ANALYTICS;
USE SCHEMA SILVER;


-- ============================================================
-- SNAP Eligibility / Caseload
-- Grain: County × Reporting Month
-- ============================================================

CREATE TABLE IF NOT EXISTS SNAP_ELIGIBILITY (
    county_name                 VARCHAR,
    case_count                  INTEGER,
    eligible_individual_count   INTEGER,
    eligible_under_5_count      INTEGER,
    eligible_5_17_count         INTEGER,
    eligible_18_59_count        INTEGER,
    eligible_60_64_count        INTEGER,
    eligible_65_plus_count      INTEGER,
    total_snap_payments         NUMBER(18,2),
    avg_payment_per_case        NUMBER(18,2),
    report_month                VARCHAR,
    source_file                 VARCHAR
);


-- ============================================================
-- SNAP Processing Timeliness
-- Grain: Region × Reporting Month × Processing Type
-- ============================================================

CREATE TABLE IF NOT EXISTS SNAP_TIMELINESS (
    processing_type    VARCHAR,
    "Region"           VARCHAR,
    disposed_count     INTEGER,
    timely_count       INTEGER,
    source_percent     FLOAT,
    reporting_month    VARCHAR,
    source_file        VARCHAR
);


-- ============================================================
-- County to Region Reference
-- Grain: One row per Texas county
-- ============================================================

CREATE TABLE IF NOT EXISTS COUNTY_REGION_REFERENCE (
    COUNTY_NAME VARCHAR,
    COUNTY_FIPS VARCHAR(5),
    REGION_CODE VARCHAR(2)
);