-- SNAP Analytics Platform V2
-- Trusted Silver warehouse tables
-- Physical schema aligned with validated Trusted Silver Parquet artifacts.

USE DATABASE SNAP_ANALYTICS;
USE SCHEMA SILVER;

CREATE TABLE IF NOT EXISTS SNAP_ELIGIBILITY (
    "County Name"                     VARCHAR,
    "Number of Cases"                 INTEGER,
    "Number of Eligible Individuals"  INTEGER,
    "Individuals: Ages < 5"           INTEGER,
    "Individuals: Ages 5 - 17"        INTEGER,
    "Individuals: Ages 18 - 59"       INTEGER,
    "Individuals: Ages 60 - 64"       INTEGER,
    "Individuals: Ages 65 +"          INTEGER,
    "Total SNAP Payments"             NUMBER(18,2),
    "Avg Payment / Case"              NUMBER(18,2),
    report_month                      VARCHAR,
    source_file                       VARCHAR
);

CREATE TABLE IF NOT EXISTS SNAP_TIMELINESS (
    processing_type    VARCHAR,
    "Region"           VARCHAR,
    disposed_count     INTEGER,
    timely_count       INTEGER,
    source_percent     FLOAT,
    reporting_month    VARCHAR,
    source_file        VARCHAR
);