-- ============================================================
-- Texas SNAP Analytics Pipeline
-- Snowflake Gold Layer Views
-- Database: TEXAS_HHS | Schema: GOLD
-- ============================================================

-- ------------------------------------------------------------
-- View 1: V_SNAP_COUNTY_MONTHLY
-- County-level monthly SNAP enrollment summary
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW TEXAS_HHS.GOLD.V_SNAP_COUNTY_MONTHLY AS
SELECT
    BENEFIT_MONTH,
    COUNTY_NAME,
    SUM(NUM_CASES)        AS TOTAL_CASES,
    SUM(NUM_INDIVIDUALS)  AS TOTAL_INDIVIDUALS,
    SUM(TOTAL_BENEFITS)   AS TOTAL_BENEFITS
FROM TEXAS_HHS.SNAP.SNAP_ENROLLMENT
WHERE
    COUNTY_NAME IS NOT NULL
    AND COUNTY_NAME NOT IN ('State Total', 'State Office')  -- remove summary rows
    AND COUNTY_NAME NOT ILIKE '%call center%'               -- remove non-geographic entries
GROUP BY
    BENEFIT_MONTH,
    COUNTY_NAME;


-- ------------------------------------------------------------
-- View 2: V_SNAP_STATEWIDE_TREND
-- Statewide monthly trend for enrollment and payment
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW TEXAS_HHS.GOLD.V_SNAP_STATEWIDE_TREND AS
SELECT
    BENEFIT_MONTH,
    SUM(NUM_CASES)        AS TOTAL_CASES,
    SUM(NUM_INDIVIDUALS)  AS TOTAL_INDIVIDUALS,
    SUM(TOTAL_BENEFITS)   AS TOTAL_PAYMENTS
FROM TEXAS_HHS.SNAP.SNAP_ENROLLMENT
WHERE
    COUNTY_NAME IS NOT NULL
    AND COUNTY_NAME NOT IN ('State Total', 'State Office')
    AND COUNTY_NAME NOT ILIKE '%call center%'
GROUP BY
    BENEFIT_MONTH
ORDER BY
    BENEFIT_MONTH;


-- ------------------------------------------------------------
-- View 3: V_SNAP_TIMELINESS
-- Timeliness rate by benefit month and section
-- Compared against federal 95% target
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW TEXAS_HHS.GOLD.V_SNAP_TIMELINESS AS
SELECT
    BENEFIT_MONTH,
    SECTION,
    AVG(TIMELINESS_RATE)        AS AVG_TIMELINESS_RATE,
    95.0                        AS FEDERAL_TARGET_PCT,
    CASE
        WHEN AVG(TIMELINESS_RATE) >= 95.0 THEN 'Met'
        ELSE 'Not Met'
    END                         AS TARGET_STATUS
FROM TEXAS_HHS.SNAP.SNAP_TIMELINESS
WHERE TIMELINESS_RATE IS NOT NULL
GROUP BY
    BENEFIT_MONTH,
    SECTION
ORDER BY
    BENEFIT_MONTH,
    SECTION;
