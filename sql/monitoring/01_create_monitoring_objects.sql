-- SNAP Analytics Platform | Module 5
-- Create monitoring objects
USE DATABASE SNAP_ANALYTICS;
CREATE SCHEMA IF NOT EXISTS MONITORING;
USE SCHEMA MONITORING;

CREATE TABLE IF NOT EXISTS MONITORING_RESULTS (
    run_id VARCHAR,
    run_timestamp TIMESTAMP_TZ,
    reporting_month DATE,
    health_domain VARCHAR,
    check_name VARCHAR,
    object_name VARCHAR,
    expected_value VARCHAR,
    actual_value VARCHAR,
    status VARCHAR,
    severity VARCHAR,
    message VARCHAR
);
