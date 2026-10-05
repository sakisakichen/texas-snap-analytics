-- SNAP Analytics Platform V2
-- Load validated Trusted Silver Parquet files into Snowflake SILVER tables.
--
-- Workflow:
--   Local Trusted Silver Parquet
--      -> Snowflake internal stage
--      -> SILVER warehouse tables

USE DATABASE SNAP_ANALYTICS;
USE SCHEMA SILVER;


-- ============================================================
-- File Format and Internal Stage
-- ============================================================

CREATE FILE FORMAT IF NOT EXISTS SNAP_PARQUET_FORMAT
    TYPE = PARQUET;

CREATE STAGE IF NOT EXISTS SNAP_SILVER_STAGE
    FILE_FORMAT = SNAP_PARQUET_FORMAT;


-- ============================================================
-- Stage Inspection
-- ============================================================

-- Confirm uploaded Trusted Silver files.
LIST @SNAP_SILVER_STAGE;

-- Expected files:
--   snap_eligibility_2024.parquet
--   timeliness_2024.parquet


-- ============================================================
-- Load SNAP Eligibility / Caseload
-- Source grain: County × Reporting Month
-- Expected 2024 rows: 3,048
-- ============================================================

COPY INTO SNAP_ELIGIBILITY
FROM (
    SELECT
        $1:county_name::VARCHAR,
        $1:case_count::INTEGER,
        $1:eligible_individual_count::INTEGER,
        $1:eligible_under_5_count::INTEGER,
        $1:eligible_5_17_count::INTEGER,
        $1:eligible_18_59_count::INTEGER,
        $1:eligible_60_64_count::INTEGER,
        $1:eligible_65_plus_count::INTEGER,
        $1:total_snap_payments::NUMBER(18,2),
        $1:avg_payment_per_case::NUMBER(18,2),
        $1:report_month::VARCHAR,
        $1:source_file::VARCHAR
    FROM @SNAP_SILVER_STAGE/snap_eligibility_2024.parquet
        (FILE_FORMAT => SNAP_PARQUET_FORMAT)
);


-- ============================================================
-- Load SNAP Processing Timeliness
-- Source grain: Region × Reporting Month × Processing Type
-- Expected 2024 rows: 384
-- ============================================================

COPY INTO SNAP_TIMELINESS
FROM (
    SELECT
        $1:processing_type::VARCHAR,
        $1:Region::VARCHAR,
        $1:disposed_count::INTEGER,
        $1:timely_count::INTEGER,
        $1:source_percent::FLOAT,
        $1:reporting_month::VARCHAR,
        $1:source_file::VARCHAR
    FROM @SNAP_SILVER_STAGE/timeliness_2024.parquet
        (FILE_FORMAT => SNAP_PARQUET_FORMAT)
);