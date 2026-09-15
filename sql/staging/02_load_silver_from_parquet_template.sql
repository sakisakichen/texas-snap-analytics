-- SNAP Analytics Platform V2
-- Template: load Trusted Silver Parquet files into Snowflake SILVER tables.
--
-- IMPORTANT:
-- This file intentionally contains placeholders because the exact stage path
-- and uploaded file names will depend on the Snowflake trial environment.
--
-- Expected workflow:
--   Local Trusted Silver Parquet
--      -> Snowflake internal stage
--      -> COPY INTO SILVER table

USE DATABASE SNAP_ANALYTICS;
USE SCHEMA SILVER;

CREATE FILE FORMAT IF NOT EXISTS SNAP_PARQUET_FORMAT
    TYPE = PARQUET;

CREATE STAGE IF NOT EXISTS SNAP_SILVER_STAGE
    FILE_FORMAT = SNAP_PARQUET_FORMAT;

-- After opening the Snowflake trial:
-- 1) Upload the Trusted Silver Parquet files to @SNAP_SILVER_STAGE
-- 2) Confirm the uploaded names:
--       LIST @SNAP_SILVER_STAGE;
--
-- 3) Use SELECT from the stage first to inspect Parquet field names:
--
-- SELECT *
-- FROM @SNAP_SILVER_STAGE/<eligibility_file>.parquet
-- (FILE_FORMAT => 'SNAP_PARQUET_FORMAT')
-- LIMIT 10;
--
-- 4) Then build the final COPY INTO statements after the actual Parquet
--    field names are confirmed.
--
-- Example pattern only:
--
-- COPY INTO SNAP_ELIGIBILITY
-- FROM (
--     SELECT
--         $1:county_name::VARCHAR,
--         $1:county_fips::VARCHAR,
--         $1:reporting_month::VARCHAR,
--         $1:case_count::INTEGER,
--         $1:eligible_individual_count::INTEGER,
--         $1:eligible_under_5_count::INTEGER,
--         $1:eligible_5_17_count::INTEGER,
--         $1:eligible_18_59_count::INTEGER,
--         $1:eligible_60_64_count::INTEGER,
--         $1:eligible_65_plus_count::INTEGER,
--         $1:total_snap_payments::NUMBER(18,2)
--     FROM @SNAP_SILVER_STAGE/<eligibility_file>.parquet
-- )
-- FILE_FORMAT = (FORMAT_NAME = 'SNAP_PARQUET_FORMAT');
--
-- COPY INTO SNAP_TIMELINESS
-- FROM (
--     SELECT
--         $1:region_code::VARCHAR,
--         $1:region_raw::VARCHAR,
--         $1:processing_type::VARCHAR,
--         $1:disposed_count::INTEGER,
--         $1:timely_count::INTEGER,
--         $1:source_percent::FLOAT,
--         $1:reporting_month::VARCHAR
--     FROM @SNAP_SILVER_STAGE/<timeliness_file>.parquet
-- )
-- FILE_FORMAT = (FORMAT_NAME = 'SNAP_PARQUET_FORMAT');
