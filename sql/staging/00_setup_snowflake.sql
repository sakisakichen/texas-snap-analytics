-- SNAP Analytics Platform V2
-- Snowflake setup
-- Purpose: Create the database and schemas used by Trusted Silver and Gold.
-- Safe to review before running in a Snowflake trial.

CREATE DATABASE IF NOT EXISTS SNAP_ANALYTICS;

CREATE SCHEMA IF NOT EXISTS SNAP_ANALYTICS.SILVER;
CREATE SCHEMA IF NOT EXISTS SNAP_ANALYTICS.GOLD;

USE DATABASE SNAP_ANALYTICS;
