-- SNAP Analytics Platform | Module 5
-- Monitoring validation gate
USE DATABASE SNAP_ANALYTICS;
USE SCHEMA MONITORING;

-- Review evidence
SELECT * FROM MONITORING_RESULTS ORDER BY run_timestamp DESC;

-- Expected: 0
SELECT COUNT(*) AS INVALID_STATUS_COUNT
FROM MONITORING_RESULTS
WHERE status IS NULL OR status NOT IN ('PASS','WARN','FAIL');

-- Expected: 0
SELECT COUNT(*) AS INVALID_SEVERITY_COUNT
FROM MONITORING_RESULTS
WHERE severity IS NULL OR severity NOT IN ('INFO','MEDIUM','HIGH');

-- Expected: 0
SELECT COUNT(*) AS INCOMPLETE_RESULT_COUNT
FROM MONITORING_RESULTS
WHERE run_id IS NULL OR run_timestamp IS NULL OR health_domain IS NULL
   OR check_name IS NULL OR object_name IS NULL OR status IS NULL OR severity IS NULL;

-- Health summary
SELECT health_domain,status,COUNT(*) AS CHECK_COUNT
FROM MONITORING_RESULTS
GROUP BY health_domain,status
ORDER BY health_domain,status;

-- Actionable evidence
SELECT run_id,reporting_month,health_domain,check_name,object_name,
       expected_value,actual_value,status,severity,message
FROM MONITORING_RESULTS
WHERE status IN ('WARN','FAIL')
ORDER BY run_timestamp DESC;

-- Production target:
-- Scheduler/orchestrator -> checks -> MONITORING_RESULTS
-- -> WARN/FAIL routing -> notification -> human investigation.
-- Monitoring execution itself must also be observable:
-- No alert does not necessarily mean the environment is healthy.
