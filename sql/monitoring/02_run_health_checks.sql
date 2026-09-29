-- SNAP Analytics Platform | Module 5
-- Representative monitoring health checks
-- Portfolio MVP: manually executed. Production target: scheduled/orchestrated.

USE DATABASE SNAP_ANALYTICS;
USE SCHEMA MONITORING;

SET RUN_ID = 'M5_RUN_003';

-- 1) Eligibility freshness
INSERT INTO MONITORING_RESULTS
(run_id,run_timestamp,reporting_month,health_domain,check_name,object_name,
 expected_value,actual_value,status,severity,message)
SELECT $RUN_ID,CURRENT_TIMESTAMP(),TO_DATE('2024-12-01'),'FRESHNESS',
'ELIGIBILITY_MONTH_ARRIVAL','SILVER.SNAP_ELIGIBILITY','2024-12',
IFF(COUNT(*)>0,'ARRIVED','NOT ARRIVED'),
IFF(COUNT(*)>0,'PASS','FAIL'),IFF(COUNT(*)>0,'INFO','HIGH'),
IFF(COUNT(*)>0,'Expected reporting month has arrived.','Expected reporting month is missing.')
FROM SNAP_ANALYTICS.SILVER.SNAP_ELIGIBILITY
WHERE REPORT_MONTH='2024-12';

-- 2) Timeliness freshness
INSERT INTO MONITORING_RESULTS
(run_id,run_timestamp,reporting_month,health_domain,check_name,object_name,
 expected_value,actual_value,status,severity,message)
SELECT $RUN_ID,CURRENT_TIMESTAMP(),TO_DATE('2024-12-01'),'FRESHNESS',
'TIMELINESS_MONTH_ARRIVAL','SILVER.SNAP_TIMELINESS','2024-12',
IFF(COUNT(*)>0,'ARRIVED','NOT ARRIVED'),
IFF(COUNT(*)>0,'PASS','FAIL'),IFF(COUNT(*)>0,'INFO','HIGH'),
IFF(COUNT(*)>0,'Expected reporting month has arrived.','Expected reporting month is missing.')
FROM SNAP_ANALYTICS.SILVER.SNAP_TIMELINESS
WHERE REPORTING_MONTH='2024-12';

-- 3) Eligibility population completeness: 254 Texas counties
INSERT INTO MONITORING_RESULTS
(run_id,run_timestamp,reporting_month,health_domain,check_name,object_name,
 expected_value,actual_value,status,severity,message)
SELECT $RUN_ID,CURRENT_TIMESTAMP(),TO_DATE('2024-12-01'),'VOLUME_POPULATION',
'ELIGIBILITY_COUNTY_COMPLETENESS','SILVER.SNAP_ELIGIBILITY','254',
COUNT(DISTINCT COUNTY_NAME)::VARCHAR,
IFF(COUNT(DISTINCT COUNTY_NAME)=254,'PASS','FAIL'),
IFF(COUNT(DISTINCT COUNTY_NAME)=254,'INFO','HIGH'),
'Expected 254 Texas counties; checked distinct county population.'
FROM SNAP_ANALYTICS.SILVER.SNAP_ELIGIBILITY
WHERE REPORT_MONTH='2024-12';

-- 4) Timeliness population: 10 governed regions x 2 processing types
INSERT INTO MONITORING_RESULTS
(run_id,run_timestamp,reporting_month,health_domain,check_name,object_name,
 expected_value,actual_value,status,severity,message)
SELECT $RUN_ID,CURRENT_TIMESTAMP(),TO_DATE('2024-12-01'),'VOLUME_POPULATION',
'TIMELINESS_REGION_TYPE_COMPLETENESS','SILVER.SNAP_TIMELINESS','20',
COUNT(DISTINCT "Region"||'|'||PROCESSING_TYPE)::VARCHAR,
IFF(COUNT(*)=20 AND COUNT(DISTINCT "Region"||'|'||PROCESSING_TYPE)=20,'PASS','FAIL'),
IFF(COUNT(*)=20 AND COUNT(DISTINCT "Region"||'|'||PROCESSING_TYPE)=20,'INFO','HIGH'),
'Expected 10 governed reporting regions x 2 processing types = 20 unique combinations.'
FROM SNAP_ANALYTICS.SILVER.SNAP_TIMELINESS
WHERE REPORTING_MONTH='2024-12'
AND "Region" NOT IN ('CCC','DATA INT','MEPD','PERFORMANC','ST OFFICE','VIC');

-- 5) Caseload volume anomaly: current month vs previous 3-month average, +/-25%
INSERT INTO MONITORING_RESULTS
(run_id,run_timestamp,reporting_month,health_domain,check_name,object_name,
 expected_value,actual_value,status,severity,message)
WITH monthly_volume AS (
 SELECT REPORT_MONTH,SUM(CASE_COUNT) TOTAL_CASES
 FROM SNAP_ANALYTICS.SILVER.SNAP_ELIGIBILITY
 WHERE REPORT_MONTH IN ('2024-09','2024-10','2024-11','2024-12')
 GROUP BY REPORT_MONTH
), baseline AS (
 SELECT AVG(TOTAL_CASES) BASELINE_3M FROM monthly_volume
 WHERE REPORT_MONTH IN ('2024-09','2024-10','2024-11')
), result AS (
 SELECT m.TOTAL_CASES CURRENT_VOLUME,b.BASELINE_3M,
 (m.TOTAL_CASES-b.BASELINE_3M)/NULLIF(b.BASELINE_3M,0) DEVIATION_RATE
 FROM monthly_volume m CROSS JOIN baseline b WHERE m.REPORT_MONTH='2024-12'
)
SELECT $RUN_ID,CURRENT_TIMESTAMP(),TO_DATE('2024-12-01'),'VOLUME',
'CASELOAD_VOLUME_ANOMALY','SILVER.SNAP_ELIGIBILITY',
'Previous 3-month average +/-25%',ROUND(DEVIATION_RATE*100,2)::VARCHAR||'%',
IFF(ABS(DEVIATION_RATE)>=0.25,'WARN','PASS'),
IFF(ABS(DEVIATION_RATE)>=0.25,'MEDIUM','INFO'),
'Current monthly case volume compared with previous 3-month average.'
FROM result;

-- 6) Model health: fact county keys must resolve to DIM_COUNTY
INSERT INTO MONITORING_RESULTS
(run_id,run_timestamp,reporting_month,health_domain,check_name,object_name,
 expected_value,actual_value,status,severity,message)
SELECT $RUN_ID,CURRENT_TIMESTAMP(),TO_DATE('2024-12-01'),'MODEL',
'CASELOAD_COUNTY_FK_INTEGRITY','GOLD.FACT_SNAP_CASELOAD_MONTHLY',
'0 orphan county keys',COUNT(*)::VARCHAR,
IFF(COUNT(*)=0,'PASS','FAIL'),IFF(COUNT(*)=0,'INFO','HIGH'),
'Fact county keys checked against DIM_COUNTY.'
FROM SNAP_ANALYTICS.GOLD.FACT_SNAP_CASELOAD_MONTHLY f
LEFT JOIN SNAP_ANALYTICS.GOLD.DIM_COUNTY d ON f.COUNTY_KEY=d.COUNTY_KEY
WHERE d.COUNTY_KEY IS NULL;

-- 7) Applications timeliness anomaly: previous 3-month weighted baseline, +/-10pp
INSERT INTO MONITORING_RESULTS
(run_id,run_timestamp,reporting_month,health_domain,check_name,object_name,
 expected_value,actual_value,status,severity,message)
WITH monthly_applications AS (
 SELECT REPORTING_MONTH,SUM(TIMELY_COUNT) TIMELY_COUNT,SUM(DISPOSED_COUNT) DISPOSED_COUNT
 FROM SNAP_ANALYTICS.SILVER.SNAP_TIMELINESS
 WHERE PROCESSING_TYPE='Applications'
 AND "Region" NOT IN ('CCC','DATA INT','MEPD','PERFORMANC','ST OFFICE','VIC')
 AND REPORTING_MONTH IN ('2024-09','2024-10','2024-11','2024-12')
 GROUP BY REPORTING_MONTH
), baseline AS (
 SELECT SUM(TIMELY_COUNT)/NULLIF(SUM(DISPOSED_COUNT),0) BASELINE_RATE
 FROM monthly_applications WHERE REPORTING_MONTH IN ('2024-09','2024-10','2024-11')
), current_month AS (
 SELECT TIMELY_COUNT/NULLIF(DISPOSED_COUNT,0) CURRENT_RATE
 FROM monthly_applications WHERE REPORTING_MONTH='2024-12'
)
SELECT $RUN_ID,CURRENT_TIMESTAMP(),TO_DATE('2024-12-01'),'METRIC',
'APPLICATION_TIMELINESS_ANOMALY','SILVER.SNAP_TIMELINESS',
'Previous 3-month weighted rate +/-10pp',
ROUND((c.CURRENT_RATE-b.BASELINE_RATE)*100,2)::VARCHAR||' pp',
IFF(ABS(c.CURRENT_RATE-b.BASELINE_RATE)>=0.10,'WARN','PASS'),
IFF(ABS(c.CURRENT_RATE-b.BASELINE_RATE)>=0.10,'MEDIUM','INFO'),
'Applications timeliness compared with previous 3-month weighted baseline.'
FROM current_month c CROSS JOIN baseline b;
