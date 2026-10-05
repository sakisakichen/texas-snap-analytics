# Module 5 — Analytics Environment Monitoring & Alerting

**Status:** COMPLETE / CLOSED  
**Baseline:** Trusted 2024 Analytics Environment  
**Next Production Batch:** 2025 (not loaded yet)

---

## 1. Module Goal

Module 5 extends the SNAP Analytics Platform from a trusted analytics pipeline into a **proactively monitored production analytics environment**.

> **Is the analytics environment healthy, and will the right owner know when it is not?**

Previous modules establish trust at specific boundaries: Bronze preserves source data; Silver validates data quality; Gold provides trusted analytical models; Semantic governs metric consumption. Module 5 continuously checks whether that environment remains healthy and proactively surfaces actionable failures.

> **Validation protects the pipeline. Monitoring protects the production environment. Alerting protects the response time.**

---

## 2. Scope

### In Scope

1. Data Freshness
2. Volume / Population Health
3. Model / Relationship Health
4. Metric Health
5. Pipeline / Operational Health
6. Monitoring result history / evidence
7. Severity classification
8. Proactive alerting for actionable failures
9. Failure simulation and validation

The existing **2024 Trusted environment** is the baseline. The 2025 batch will **not** be loaded during initial Module 5 implementation; it can later serve as a new production batch for end-to-end Production Acceptance Testing.

The MVP will avoid adding enterprise-scale observability or orchestration tools unless they solve a clearly defined requirement.

### Current Execution Boundary

SNAP is currently a hybrid workflow rather than a fully orchestrated production pipeline:

```text
Raw Excel
   ↓
Local Python ingestion / transformation / validation
   ↓
Trusted Silver
   ↓
Manual load boundary
   ↓
Snowflake SILVER → GOLD → SEMANTIC
   ↓
Module 5 Monitoring
   ↓
BI / Consumers
```

The local Python workflow is manually triggered. Module 5 therefore does **not** claim full end-to-end orchestration. Monitoring focuses on the analytics environment and execution evidence that currently exists. A later dbt Productionization Extension will add dependency-aware warehouse transformation, testing, documentation, and lineage without pretending to orchestrate the local Python ingestion layer.

---

## 3. High-Level Architecture

![Module 5 Monitoring & Alerting Architecture](assets/module5_monitoring_architecture.png)

**Analytics Environment → Automated Health Checks → Monitoring History → Severity → Alert → Human Investigation**

The five monitoring domains span the analytics environment rather than representing five separate pipelines.

---

## 4. Monitoring Domains

### 4.1 Data Freshness

**Question:** Did the expected reporting period arrive when it was supposed to?

MVP Freshness SLA is a portfolio simulation assumption and would require stakeholder confirmation in a real production environment. Eligibility/Caseload and Timeliness use the same SLA framework:

- Expected arrival: **by the 15th of the following month** → `PASS`
- Missing after the 15th but still within the following calendar month → `WARN`
- Still missing after the end of the following calendar month → `FAIL + Alert`

Example for January data:

```text
Arrives by Feb 15     → PASS
Missing Feb 16–EOM    → WARN
Still missing Mar 1   → FAIL + Alert
```

Calendar month-end must be calculated correctly for 28/29/30/31-day months.

Freshness is separate from completeness. If January exists but only 247 of 254 counties are present, Freshness may `PASS` while Population Completeness `FAIL`s.

### 4.2 Volume / Population Health

**Question:** Did the expected population arrive completely, at the expected grain, and without an unusual change in business volume?

#### Eligibility / Caseload Population Contract

- Grain: **County × Reporting Month**
- Expected population: **254 Texas counties per reporting month**
- Every expected county must exist, even when a legitimate measure value is `0`.
- Any missing expected county → `FAIL + Alert`

#### Timeliness Population Contract

- Grain: **Region × Reporting Month × Processing Type**
- Expected governed Gold population: **10 reporting regions × 2 processing types = 20 Region × Type combinations per month**
- Processing types: Applications and Redeterminations
- Every expected combination must exist **exactly once**.
- Missing or duplicate expected combination → `FAIL + Alert`

A simple `COUNT(*) = 20` is insufficient because a missing combination plus a duplicate could still total 20 rows.

#### Zero vs NULL vs Missing Record

> **Zero ≠ NULL ≠ Missing Record**

- `0` = observed legitimate value; not automatically a failure
- `NULL` in a required measure = unavailable/missing value → Data Quality `FAIL`
- Missing expected row = Population Completeness `FAIL`

#### Volume Anomaly

Population can be complete while aggregate business volume is still unusual. MVP anomaly detection uses an explainable historical baseline rather than ML:

- Baseline: **previous 3-month average**
- Compare current aggregate volume with the baseline
- Absolute deviation **< 25%** → `PASS`
- Absolute deviation **≥ 25%** → `WARN + Investigate`

Both unexpected decreases and increases are monitored. A volume anomaly does not by itself prove that data is invalid.

> **Deterministic contract violation → FAIL. Behavioral/statistical anomaly → WARN first.**

### 4.3 Model / Relationship Health

**Question:** Are warehouse relationships and governed layer contracts still intact?

#### Referential Integrity

Every fact foreign key must resolve to its corresponding dimension:

```text
FACT_SNAP_CASELOAD_MONTHLY
  month_key  → DIM_MONTH
  county_key → DIM_COUNTY

FACT_SNAP_PROCESSING
  month_key  → DIM_MONTH
  region_key → DIM_REGION
```

Expected orphan count = `0`. Any orphan foreign key → `FAIL + Alert`.

This converts Module 3 one-time Trusted Gold validation into continuous production monitoring.

#### Gold → Semantic Reconciliation

Semantic consumption must reconcile to its trusted Gold source.

`VW_PROCESSING_METRICS` critical reconciliation:
- row population
- `SUM(disposed_count)`
- `SUM(timely_count)`

`VW_CASELOAD_METRICS` critical reconciliation:
- row population
- `SUM(case_count)`
- `SUM(eligible_individual_count)`
- `SUM(total_snap_payments)`

Mismatch between governed Gold and Semantic totals → `FAIL + Alert`.

> **Build → Validate → Trust → Continuously Monitor**

### 4.4 Metric Health

**Question:** Are governed business metrics meeting defined benchmarks and behaving within reasonable historical expectations?

Metric Health deliberately separates **business performance** from **data health**.

#### Benchmark Monitoring

Applications Timeliness uses the governed **95% benchmark**:

- Rate ≥ 95% → Meets Benchmark
- Rate < 95% → Below Benchmark business signal

Below benchmark does **not** mean the data environment failed. Redeterminations do not use this Applications benchmark.

#### Metric Anomaly Monitoring

Applications and Redeterminations are monitored for unusual Timeliness Rate movement.

Baseline must preserve the governed weighted-rate definition:

```text
3-month baseline rate
= SUM(timely_count across previous 3 months)
  / SUM(disposed_count across previous 3 months)
```

Do **not** use `AVG(monthly timeliness_rate)`.

Compare current rate with the previous 3-month weighted baseline using **percentage-point change**:

- Absolute difference **< 10 percentage points** → `PASS`
- Absolute difference **≥ 10 percentage points** → `WARN + Investigate`

> **Business underperformance ≠ Data failure.**

### 4.5 Pipeline / Operational Health

**Question:** Did the expected analytics workflow and monitoring process actually execute?

SNAP does not currently have a full end-to-end orchestrator. The local Python ingestion / Silver workflow is manually triggered, so Module 5 will not introduce Airflow, Dagster, or Prefect merely for portfolio decoration.

MVP Operational Health focuses on observable execution evidence:

1. **Execution Status** — expected warehouse/monitoring process completed successfully. Failure → `FAIL + Alert`.
2. **Latest Successful Run** — most recent successful execution remains within the expected cadence. Overdue → `FAIL + Alert`.
3. **Monitoring Execution Completeness** — every expected health check actually ran. Missing expected check → `FAIL + Alert`.

This protects against a silent failure where monitoring never ran and therefore produced no alert.

> **No Alert ≠ Healthy. The monitoring process itself must be observable.**

> **Pipeline Health ≠ Data Health ≠ Metric Health**

---

## 5. MVP Monitoring Contract

| Health Domain | Check | Healthy / Expected State | Abnormal Condition | Severity / Action |
|---|---|---|---|---|
| Freshness | Monthly reporting period | Arrives by following-month 15th | Missing after 15th but before/equal month-end | WARN / Record + review |
| Freshness | Monthly reporting period | Available before hard deadline | Still missing after following calendar month-end | FAIL + Alert |
| Volume / Population | Eligibility population | 254 expected counties/month | Any expected county missing | FAIL + Alert |
| Volume / Population | Timeliness population / grain | All 10 Region × 2 Type combinations exactly once/month | Missing or duplicate combination | FAIL + Alert |
| Data Quality | Required measure | Required value is present; legitimate zero allowed | Required value is NULL | FAIL + Alert |
| Volume / Population | Volume anomaly | Current within ±25% of previous 3-month average | Absolute deviation ≥25% | WARN + Investigate |
| Model / Relationship | Fact → Dimension integrity | 0 orphan foreign keys | Any orphan key | FAIL + Alert |
| Model / Relationship | Gold → Semantic reconciliation | Governed row populations and critical totals match | Any governed mismatch | FAIL + Alert |
| Metric | Applications benchmark | Timeliness ≥95% | Timeliness <95% | Business signal; not Data FAIL |
| Metric | Timeliness anomaly | Current rate within ±10 percentage points of weighted 3-month baseline | Absolute difference ≥10 pp | WARN + Investigate |
| Operational | Execution status | Expected process succeeds | Execution failure | FAIL + Alert |
| Operational | Latest successful run | Successful execution within expected cadence | Overdue | FAIL + Alert |
| Operational | Monitoring execution | All expected checks execute | Missing expected check | FAIL + Alert |

### Severity Philosophy

> **Contract violation → FAIL**  
> **Behavioral / statistical anomaly → WARN + Investigation**  
> **Business underperformance ≠ Data failure**

---

## 6. Severity & Alerting Strategy

**PASS** — within expected contract. Record result; no notification.

**WARN** — unusual condition that does not necessarily invalidate the environment. Persist evidence and investigate; critical notification is not automatic for the MVP.

**FAIL** — trusted contract, availability requirement, model integrity, or critical operational condition is violated. Persist failure and proactively notify the responsible owner.

> **Not every anomaly should generate an alert. Alerts should be actionable.**

The alerting layer should communicate enough context to begin investigation: check name, monitored object, expected state, actual state, severity, reporting period, and diagnostic message.

---

## 7. Monitoring Evidence / History

All checks should persist execution evidence rather than existing only as ad hoc SQL output.

Implemented `SNAP_ANALYTICS.MONITORING.MONITORING_RESULTS` fields:

| Field | Description |
|---|---|
| `run_id` | Identifier grouping checks from the same monitoring execution |
| `run_timestamp` | Check execution time |
| `reporting_month` | Reporting period evaluated when applicable |
| `check_name` | Business-readable health check identifier |
| `health_domain` | Freshness, Volume, Relationship, Metric, or Operational |
| `object_name` | Monitored dataset, table, view, process, or metric |
| `expected_value` | Expected state/value |
| `actual_value` | Observed state/value |
| `status` | PASS / WARN / FAIL |
| `severity` | Operational severity / notification priority |
| `message` | Human-readable diagnostic context |

Monitoring history supports investigation of when an issue began, whether it recurred, and whether monitoring itself executed.

The physical evidence layer is implemented as `SNAP_ANALYTICS.MONITORING.MONITORING_RESULTS` at the grain of one check result × one execution × one reporting period × one monitored object.

---

## 8. Implemented Architecture

Module 5 is implemented as a lightweight Snowflake monitoring evidence layer.

```text
Health Checks
    ↓
SNAP_ANALYTICS.MONITORING.MONITORING_RESULTS
    ↓
PASS / WARN / FAIL
    ↓
Actionable WARN / FAIL
    ↓
Production future state: notification
    ↓
Human Investigation
```

Repository implementation:

```text
sql/monitoring/
├── 01_create_monitoring_objects.sql
├── 02_run_health_checks.sql
└── 03_validate_monitoring.sql
```

The portfolio implementation executes checks manually to validate the framework. In production, the checks would be scheduled through Snowflake Tasks or an external orchestrator and actionable failures routed to Email, Slack, webhook, or another operational channel.

Snowflake is not presented as orchestrating the local Mac/Python ingestion workflow. A later dbt Productionization Extension will add dependency-aware warehouse transformation, tests, documentation, and lineage; dbt is not treated as the end-to-end orchestrator.

> **Detect → Classify → Record → Notify → Investigate**

---

## 9. Validation Results

The monitoring framework was validated against the trusted 2024 baseline.

| Domain | Representative Check | Result |
|---|---|---|
| Freshness | Eligibility reporting-month arrival | PASS |
| Freshness | Timeliness reporting-month arrival | PASS |
| Volume / Population | Eligibility county completeness (254) | PASS |
| Volume / Population | Timeliness Region × Type completeness (20) | PASS |
| Volume | Caseload vs previous 3-month average (±25%) | PASS |
| Model / Relationship | Caseload fact → county dimension FK integrity | PASS |
| Metric | Applications Timeliness vs weighted 3-month baseline (±10 pp) | WARN |

A real metric signal was surfaced:

```text
Current Applications Timeliness Rate: 86.09%
Previous 3-month weighted baseline:   67.90%
Difference:                          +18.18 pp
Status:                               WARN
Severity:                             MEDIUM
```

This is intentionally `WARN`, not `FAIL`: unusual metric movement does not prove invalid data.

The final gate validates allowed statuses and severities, required monitoring metadata, domain/status summaries, and actionable WARN/FAIL evidence. Notification delivery remains a documented production target rather than an implemented claim in the current manually executed portfolio environment.

---

## 10. Production Lessons

> **Pipeline Success ≠ Data Health**

> **Validation ≠ Monitoring**

> **Monitoring ≠ Alerting**

> **Zero ≠ NULL ≠ Missing Record**

> **Contract violations and anomalies should not automatically receive the same severity.**

> **Business underperformance does not automatically mean the data is wrong.**

> **Ratio metrics must preserve their governed numerator/denominator logic during monitoring.**

> **Monitoring should leave historical evidence.**

> **No Alert ≠ Healthy. A monitoring system must provide evidence that its checks actually ran.**

> **A successful code or pipeline execution does not guarantee a healthy analytics environment.**

---

## 11. Module Deliverables

- Monitoring & Alerting architecture
- MVP Monitoring Contract
- Snowflake `MONITORING` schema
- Persistent `MONITORING_RESULTS` evidence table
- Representative Freshness, Population, Volume, Model, and Metric checks
- Monitoring validation gate
- PASS / WARN / FAIL severity and alert policy
- Operational / monitor-the-monitor design
- Production alerting target architecture
- Production Notes / interview takeaways

---

## 12. Current Status

**Module 5: COMPLETE / CLOSED**

Completed:

- Five monitoring domains and governed monitoring contract
- Freshness SLA with grace period and hard deadline
- Eligibility contract: 254 counties per month
- Timeliness contract: 10 governed regions × 2 processing types
- Zero vs NULL vs missing-record semantics
- ±25% previous 3-month Volume Anomaly threshold
- Fact-to-Dimension referential-integrity monitoring
- Gold-to-Semantic reconciliation design
- Applications 95% benchmark governance
- ±10 percentage-point weighted Timeliness anomaly threshold
- Operational execution / monitor-the-monitor contract
- Snowflake `MONITORING_RESULTS` evidence layer
- Representative checks persisted and validated
- Final monitoring validation gate
- Explicit execution boundary: local Python remains manually triggered
- Production notification path documented without claiming unimplemented automation

**2024 remains the trusted baseline. 2025 is intentionally not loaded as part of Module 5 and can later serve as a Production Acceptance Test batch.**

### Next Platform Step

Proceed to the scoped **dbt Productionization Extension** before Module 6 BI / Decision Experience.
