-- SNAP Analytics Platform V2 | Module 4 — Final Semantic Validation Gate
-- View Creation Success != Trusted Semantic Layer

-- PROCESSING: Gold -> Semantic reconciliation
SELECT
 (SELECT COUNT(*) FROM SNAP_ANALYTICS.GOLD.FACT_SNAP_PROCESSING) gold_row_count,
 (SELECT COUNT(*) FROM SNAP_ANALYTICS.SEMANTIC.VW_PROCESSING_METRICS) semantic_row_count,
 (SELECT SUM(disposed_count) FROM SNAP_ANALYTICS.GOLD.FACT_SNAP_PROCESSING) gold_disposed_count,
 (SELECT SUM(disposed_count) FROM SNAP_ANALYTICS.SEMANTIC.VW_PROCESSING_METRICS) semantic_disposed_count,
 (SELECT SUM(timely_count) FROM SNAP_ANALYTICS.GOLD.FACT_SNAP_PROCESSING) gold_timely_count,
 (SELECT SUM(timely_count) FROM SNAP_ANALYTICS.SEMANTIC.VW_PROCESSING_METRICS) semantic_timely_count;

-- PROCESSING: grain uniqueness (expected 0)
SELECT COUNT(*) duplicate_grain_count FROM (
 SELECT region_key, month_key, processing_type
 FROM SNAP_ANALYTICS.SEMANTIC.VW_PROCESSING_METRICS
 GROUP BY region_key, month_key, processing_type HAVING COUNT(*) > 1
);

-- PROCESSING: benchmark governance
SELECT COUNT(*) invalid_redetermination_benchmark_rows
FROM SNAP_ANALYTICS.SEMANTIC.VW_PROCESSING_METRICS
WHERE processing_type='Redeterminations'
AND (benchmark_rate IS NOT NULL OR benchmark_gap IS NOT NULL OR benchmark_status IS NOT NULL);

-- PROCESSING: zero denominator population (2024 baseline = 0; edge case has no test data)
SELECT COUNT(*) zero_disposed_count_rows
FROM SNAP_ANALYTICS.SEMANTIC.VW_PROCESSING_METRICS WHERE disposed_count=0;

-- PROCESSING: aggregation correctness demonstration
SELECT reporting_month, processing_type,
 AVG(timeliness_rate) wrong_avg_rate,
 SUM(timely_count)::FLOAT / NULLIF(SUM(disposed_count),0) correct_weighted_rate
FROM SNAP_ANALYTICS.SEMANTIC.VW_PROCESSING_METRICS
WHERE reporting_month='2024-01' AND processing_type='Applications'
GROUP BY reporting_month, processing_type;

-- CASELOAD: Gold -> Semantic reconciliation
SELECT
 (SELECT COUNT(*) FROM SNAP_ANALYTICS.GOLD.FACT_SNAP_CASELOAD_MONTHLY) gold_row_count,
 (SELECT COUNT(*) FROM SNAP_ANALYTICS.SEMANTIC.VW_CASELOAD_METRICS) semantic_row_count,
 (SELECT SUM(case_count) FROM SNAP_ANALYTICS.GOLD.FACT_SNAP_CASELOAD_MONTHLY) gold_case_count,
 (SELECT SUM(case_count) FROM SNAP_ANALYTICS.SEMANTIC.VW_CASELOAD_METRICS) semantic_case_count,
 (SELECT SUM(eligible_individual_count) FROM SNAP_ANALYTICS.GOLD.FACT_SNAP_CASELOAD_MONTHLY) gold_eligible_count,
 (SELECT SUM(eligible_individual_count) FROM SNAP_ANALYTICS.SEMANTIC.VW_CASELOAD_METRICS) semantic_eligible_count,
 (SELECT SUM(total_snap_payments) FROM SNAP_ANALYTICS.GOLD.FACT_SNAP_CASELOAD_MONTHLY) gold_total_payments,
 (SELECT SUM(total_snap_payments) FROM SNAP_ANALYTICS.SEMANTIC.VW_CASELOAD_METRICS) semantic_total_payments;

-- CASELOAD: grain uniqueness (expected 0)
SELECT COUNT(*) duplicate_grain_count FROM (
 SELECT county_key, month_key FROM SNAP_ANALYTICS.SEMANTIC.VW_CASELOAD_METRICS
 GROUP BY county_key, month_key HAVING COUNT(*) > 1
);

-- CASELOAD: age-band reconciliation (expected 0)
SELECT COUNT(*) age_mismatch_count
FROM SNAP_ANALYTICS.SEMANTIC.VW_CASELOAD_METRICS
WHERE eligible_under_5_count + eligible_5_17_count + eligible_18_59_count
    + eligible_60_64_count + eligible_65_plus_count <> eligible_individual_count;

-- CASELOAD: geography governance (expected canonical 01-11 only; no 02/09)
SELECT DISTINCT region_code
FROM SNAP_ANALYTICS.SEMANTIC.VW_CASELOAD_METRICS ORDER BY region_code;

-- CASELOAD: zero denominator population (2024 baseline = 0; edge case has no test data)
SELECT COUNT(*) zero_case_count_rows
FROM SNAP_ANALYTICS.SEMANTIC.VW_CASELOAD_METRICS WHERE case_count=0;

-- CASELOAD: aggregation correctness demonstration
SELECT reporting_month,
 AVG(avg_payment_per_case) wrong_avg_payment,
 SUM(total_snap_payments)::FLOAT / NULLIF(SUM(case_count),0) correct_avg_payment
FROM SNAP_ANALYTICS.SEMANTIC.VW_CASELOAD_METRICS
WHERE reporting_month='2024-01'
GROUP BY reporting_month;
