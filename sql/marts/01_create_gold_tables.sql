-- SNAP Analytics Platform V2
-- Gold physical model DDL
-- Build order: dimensions first, then facts.

USE DATABASE SNAP_ANALYTICS;
USE SCHEMA GOLD;

CREATE TABLE IF NOT EXISTS DIM_MONTH (
    month_key          INTEGER        NOT NULL,
    reporting_month    VARCHAR        NOT NULL,
    year               INTEGER        NOT NULL,
    quarter            VARCHAR        NOT NULL,
    month_number       INTEGER        NOT NULL,
    month_name         VARCHAR        NOT NULL
);

CREATE TABLE IF NOT EXISTS DIM_REGION (
    region_key         INTEGER        NOT NULL,
    region_code        VARCHAR        NOT NULL,
    region_name        VARCHAR
);

CREATE TABLE IF NOT EXISTS DIM_COUNTY (
    county_key         INTEGER        NOT NULL,
    county_fips        VARCHAR        NOT NULL,
    county_name        VARCHAR        NOT NULL,
    region_key         INTEGER        NOT NULL
);

CREATE TABLE IF NOT EXISTS FACT_SNAP_PROCESSING (
    region_key         INTEGER        NOT NULL,
    month_key          INTEGER        NOT NULL,
    processing_type    VARCHAR        NOT NULL,
    disposed_count     INTEGER,
    timely_count       INTEGER
);

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

-- Snowflake note:
-- Primary-key and foreign-key declarations on standard tables are informational
-- rather than enforced. Gold trust is therefore established through the
-- validation queries in 04_validate_gold.sql.
