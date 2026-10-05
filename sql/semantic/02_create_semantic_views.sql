-- SNAP Analytics Platform V2 | Module 4 — Semantic Views

CREATE OR REPLACE VIEW SNAP_ANALYTICS.SEMANTIC.VW_PROCESSING_METRICS AS
SELECT
    f.region_key, f.month_key,
    r.region_code, r.region_name,
    m.reporting_month, m.year, m.quarter, m.month_number, m.month_name,
    f.processing_type, f.disposed_count, f.timely_count,
    f.timely_count::FLOAT / NULLIF(f.disposed_count, 0) AS timeliness_rate,
    CASE WHEN f.processing_type = 'Applications' THEN 0.95 ELSE NULL END AS benchmark_rate,
    CASE WHEN f.processing_type = 'Applications' AND f.disposed_count > 0
         THEN (f.timely_count::FLOAT / NULLIF(f.disposed_count, 0)) - 0.95
         ELSE NULL END AS benchmark_gap,
    CASE
        WHEN f.processing_type <> 'Applications' THEN NULL
        WHEN f.disposed_count = 0 THEN NULL
        WHEN (f.timely_count::FLOAT / NULLIF(f.disposed_count, 0)) >= 0.95 THEN 'Meets Benchmark'
        ELSE 'Below Benchmark'
    END AS benchmark_status
FROM SNAP_ANALYTICS.GOLD.FACT_SNAP_PROCESSING f
JOIN SNAP_ANALYTICS.GOLD.DIM_REGION r ON f.region_key = r.region_key
JOIN SNAP_ANALYTICS.GOLD.DIM_MONTH m ON f.month_key = m.month_key;

CREATE OR REPLACE VIEW SNAP_ANALYTICS.SEMANTIC.VW_CASELOAD_METRICS AS
SELECT
    f.county_key, f.month_key, c.region_key,
    c.county_fips, c.county_name, r.region_code, r.region_name,
    m.reporting_month, m.year, m.quarter, m.month_number, m.month_name,
    f.case_count, f.eligible_individual_count,
    f.eligible_under_5_count, f.eligible_5_17_count,
    f.eligible_18_59_count, f.eligible_60_64_count, f.eligible_65_plus_count,
    f.total_snap_payments,
    f.total_snap_payments::FLOAT / NULLIF(f.case_count, 0) AS avg_payment_per_case
FROM SNAP_ANALYTICS.GOLD.FACT_SNAP_CASELOAD_MONTHLY f
JOIN SNAP_ANALYTICS.GOLD.DIM_COUNTY c ON f.county_key = c.county_key
JOIN SNAP_ANALYTICS.GOLD.DIM_REGION r ON c.region_key = r.region_key
JOIN SNAP_ANALYTICS.GOLD.DIM_MONTH m ON f.month_key = m.month_key;
