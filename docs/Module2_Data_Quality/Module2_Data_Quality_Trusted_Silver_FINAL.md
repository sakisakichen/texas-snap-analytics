# Module 2 — Data Quality & Trusted Silver

**Final Closeout — August 27, 2026**

## 1. Purpose

Module 2 transforms Bronze source data into **trusted Silver datasets**
that are ready for governed analytics, Gold modeling, and reporting.

| Layer  | Responsibility                                                           |
|:-------|:-------------------------------------------------------------------------|
| Bronze | Preserve source data and source structure                                |
| Silver | Clean, standardize, type, validate, and establish trust                  |
| Gold   | Model governed analytical facts/dimensions and answer business questions |

The reusable Silver workflow is:

``` text
Bronze Parquet
→ Structure Cleaning
→ Standardization
→ Data Type Conversion
→ Business Validation
→ Validation Report (JSON)
→ Validation Gate
→ Trusted Silver Parquet
```

Gate behavior:

``` text
PASS         → publish Trusted Silver
WARNING only → publish while preserving warnings
FAIL         → stop publication, preserve validation evidence, raise ValidationError
```

Design principle:

> **Trusted Silver = transformed + validated data. Transformation
> success alone does not make data trusted.**

------------------------------------------------------------------------

# 2. Development History

Module 2 was built in two passes.

### Pass 1 — Eligibility / Caseload Silver

Eligibility was the first dataset used to build the Silver framework. We
implemented and tested:

``` text
Structure Cleaning
→ Standardization
→ Data Type Conversion
→ Business Validation
→ Validation Report
→ Validation Gate
→ Silver Pipeline
```

At that point, the reusable Silver framework existed and Eligibility
transformation/validation was substantially complete.

### Module 3 Design Review Exposed a Missing Dependency

While designing the Gold layer in Module 3, we recognized that the
Leadership Dashboard also depended on **Timeliness** data, but
Timeliness had not yet been transformed into Trusted Silver.

Rather than implementing Gold against an incomplete upstream layer, work
returned to Module 2.

### Pass 2 — Timeliness Silver

Timeliness was then taken through the same Silver contract:

``` text
Structure Cleaning
→ Standardization
→ Data Type Conversion
→ Business Validation
→ Validation Report
→ Validation Gate
→ Trusted Silver
```

After Timeliness was integrated and human-validated, we returned to
Eligibility for final E2E publication. That final run exposed additional
production issues in the county reference population and non-geographic
source rows. Those issues were resolved before Module 2 was closed.

This chronology matters because Module 2 did not begin with Timeliness.
**Eligibility established the framework; Module 3 exposed the missing
Timeliness dependency; Timeliness was added; then both datasets were
closed out as Trusted Silver.**

------------------------------------------------------------------------

# 3. Dataset A — Eligibility / Caseload Silver

## 3.1 Business Meaning and Grain

The Eligibility source contains monthly SNAP caseload,
eligible-individual, demographic, and payment measures by reporting
entity.

Target analytical grain:

> **County × Reporting Month**

Final trusted geographic population:

``` text
254 Texas counties × 12 reporting months = 3,048 rows
```

### Target Fields and Types

| Field                            | Silver Representation | Meaning                   |
|:---------------------------------|:----------------------|:--------------------------|
| `County Name`                    | nullable `string`     | Texas county              |
| `Number of Cases`                | nullable `Int64`      | SNAP case count           |
| `Number of Eligible Individuals` | nullable `Int64`      | Eligible individual count |
| `Individuals: Ages < 5`          | nullable `Int64`      | Age-band count            |
| `Individuals: Ages 5 - 17`       | nullable `Int64`      | Age-band count            |
| `Individuals: Ages 18 - 59`      | nullable `Int64`      | Age-band count            |
| `Individuals: Ages 60 - 64`      | nullable `Int64`      | Age-band count            |
| `Individuals: Ages 65 +`         | nullable `Int64`      | Age-band count            |
| `Total SNAP Payments`            | two-decimal `Decimal` | Exact monetary amount     |
| `Avg Payment / Case`             | nullable `Float64`    | Source average            |
| `report_month`                   | `string`, `YYYY-MM`   | Reporting month           |
| `source_file`                    | `string`              | Source lineage            |

------------------------------------------------------------------------

## 3.2 Eligibility Stage 1 — Structure Cleaning ✅

Original responsibilities: - Remove empty/unexpected structural rows. -
Remove fully empty columns. - Verify that the dataset remains
structurally usable. - Preserve the source in Bronze while producing an
analytical Silver population. - Maintain consistent row granularity.

### Final Geographic Population Rule

During final E2E validation, the source was found to contain three
recurring reporting entities that are not Texas counties:

- `State Total`
- `State Office`
- `Call Centers`

They appear across the monthly source files but do not belong to the
**County × Month** analytical grain.

Decision:

| Source Entity  | Silver Decision            | Reason                                                                                     |
|:---------------|:---------------------------|:-------------------------------------------------------------------------------------------|
| `State Total`  | Exclude from county detail | Statewide aggregate; mixing it with county rows creates mixed grain / double-counting risk |
| `State Office` | Exclude                    | Non-county reporting entity                                                                |
| `Call Centers` | Exclude                    | Operational reporting entity, not a geographic county                                      |

The original source remains preserved in Bronze. Exclusion from this
Silver dataset means **out of analytical scope**, not “bad source data.”

Final structure result:

``` text
3,084 source rows
− 36 non-geographic reporting rows
= 3,048 county-level rows
```

Production principle:

> **Valid source data is not automatically valid analytical population.
> Grain determines population.**

------------------------------------------------------------------------

## 3.3 Eligibility Stage 2 — Standardization ✅

Implemented representation rules: - Trim whitespace. - Standardize
county-name casing. - Remove presentation formatting such as `$` and
commas from configured currency-like fields before type conversion. -
Preserve metadata such as `report_month` and `source_file`. - Apply
explicit known source corrections rather than fuzzy guessing.

Examples:

``` text
Mclennan    → McLennan
Matagorda¹  → Matagorda
State Total¹ → State Total
```

Known source-specific corrections are handled in Standardization so
downstream validation evaluates canonical representations.

Production principle:

> **Known representation defects should be corrected explicitly before
> business validation.**

------------------------------------------------------------------------

## 3.4 Eligibility Stage 3 — Data Type Conversion ✅

Original design principle:

> **Business meaning determines data type.**

Counts are converted to nullable `Int64`; text/metadata fields use
nullable `string`.

### Monetary Type Troubleshooting

`Total SNAP Payments` was initially treated as an integer-like field
because most observed values appeared to contain whole dollars.

Real-source inspection found legitimate cents:

``` text
El Paso
Total SNAP Payments = 22368395.01
```

Therefore the final contract is:

``` text
Total SNAP Payments → Decimal, quantized to 0.01
Avg Payment / Case  → Float64
```

This avoids truncating legitimate cents and gives `Total SNAP Payments`
exact monetary semantics.

Production principle:

> **Choose data types from business semantics and real source evidence,
> not from the majority pattern in a sample.**

------------------------------------------------------------------------

## 3.5 Eligibility Stage 4 — Business Validation ✅

Final MVP validation rules:

| Rule                        | Purpose                                                        | Gate        |
|:----------------------------|:---------------------------------------------------------------|:------------|
| County Name Required        | Analytical geography must exist                                | FAIL blocks |
| `report_month` Required     | Reporting period must exist and follow expected representation | FAIL blocks |
| Required Numeric Fields     | Required business measures must be present                     | FAIL blocks |
| Non-negative Numeric Values | Counts/amounts cannot be negative                              | FAIL blocks |
| Valid Reporting Entity      | County must belong to governed Texas county population         | FAIL blocks |

### Reporting Entity Reference Troubleshooting

The initial validator contained only a small nine-county
`known_counties` sample.

During the final Eligibility E2E run:

``` text
Valid Reporting Entity = FAIL
failed_rows = 2,981
```

Investigation showed that the data was not mostly invalid—the
**validator reference set was incomplete**.

Troubleshooting sequence:

``` text
Validation FAIL
→ inspect validation report
→ profile unique County Name values
→ 259 unique source reporting names observed
→ discover known_counties contains only 9 counties
→ inspect remaining non-county entities
→ compare with raw monthly source
→ identify State Total / State Office / Call Centers
→ define County × Month analytical population
→ exclude non-geographic entities in Structure Cleaning
→ standardize known source representations
→ replace sample list with full 254-county Texas reference set
→ regression tests
→ E2E rerun
→ PASS
```

Production principle:

> **Validate the validator. Incomplete reference data can make valid
> data look bad.**

------------------------------------------------------------------------

## 3.6 Eligibility Final Validation Gate / Publish ✅

Final E2E result:

``` text
input_row_count:  3048
output_row_count: 3048
status: PASS
rules_passed: 5
rules_failed: 0
rules_warning: 0
```

Result:

> **Eligibility / Caseload Trusted Silver published successfully.**

------------------------------------------------------------------------

# 4. Dataset B — Timeliness Silver

## 4.1 Why Timeliness Was Added Later

The initial Module 2 implementation focused on Eligibility / Caseload.

During Module 3 Gold design, the governed business question **“How well
is that workload being processed?”** required processing timeliness
separated by processing type. That exposed an upstream dependency:
Timeliness still needed its own Trusted Silver transformation.

Work therefore returned from Module 3 to Module 2 before Physical Gold
implementation.

------------------------------------------------------------------------

## 4.2 Timeliness Business Meaning and Grain

Each monthly Timeliness worksheet is a human-readable Excel report
containing two vertically stacked logical tables:

- **SNAP Food Benefits APPLICATIONS**
- **SNAP Food Benefits REDETERMINATIONS**

Each block uses:

``` text
Region | Disposed | Timely | Percent
```

The workbook also contains titles, blank rows, TOTAL rows, repeated
headers, notes, and definitions.

Target Silver grain:

> **Reporting Month × Processing Type × Region**

| Field             | Silver Representation           |
|:------------------|:--------------------------------|
| `reporting_month` | string, `YYYY-MM`               |
| `processing_type` | string                          |
| `Region`          | string                          |
| `disposed_count`  | nullable `Int64`                |
| `timely_count`    | nullable `Int64`                |
| `source_percent`  | nullable `Float64` decimal rate |
| `source_file`     | string                          |

`source_percent` is retained as reconciliation evidence; the governed
Gold timeliness metric is derived from counts.

------------------------------------------------------------------------

## 4.3 Timeliness Stage 1 — Structure Cleaning ✅

Implemented rules: - Parse by stable **business section/header**, not
fixed Excel row positions. - Detect both Applications and
Redeterminations sections. - Require the expected
`Region | Disposed | Timely | Percent` header. - Derive
`processing_type` from the section. - Exclude titles, blank rows,
repeated headers, notes, and definitions. - Keep TOTAL outside
analytical detail while retaining it as control metadata. - Do not
assume Applications always appears before Redeterminations. - Preserve
records when business measures are missing. - Preserve column positions
when intermediate cells are missing. - Avoid mixing DataFrame index
labels with positional `.iloc` logic.

### Defects Found During Implementation

**Defect 1 — Empty-cell collapse**

Collapsing empty cells could shift:

``` text
Percent → Timely
```

This would silently corrupt business meaning.

**Defect 2 — Index vs position**

Mixing DataFrame index labels with `.iloc` positional slicing could skip
valid rows.

Both defects were fixed and converted into regression tests.

------------------------------------------------------------------------

## 4.4 Timeliness Stage 2 — Standardization ✅

Implemented rules: - Preserve `Applications` / `Redeterminations`. -
Trim unnecessary whitespace. - Preserve `Region` as a string so values
such as `01` remain identifiers rather than numbers. - Preserve combined
values such as `02/09`. - Preserve unresolved source categories rather
than guessing their meaning: - `CCC` - `DATA INT` - `MEPD` -
`PERFORMANC` - `ST OFFICE` - `VIC` - `UNKNOWN` - Rename: -
`Disposed → disposed_count` - `Timely → timely_count` -
`Percent → source_percent`

Production principle:

> **Unknown does not automatically mean invalid. Preserve first; govern
> explicitly.**

------------------------------------------------------------------------

## 4.5 Timeliness Stage 3 — Data Type Conversion ✅

| Field             | Type               |
|:------------------|:-------------------|
| `reporting_month` | nullable string    |
| `processing_type` | nullable string    |
| `Region`          | nullable string    |
| `disposed_count`  | nullable `Int64`   |
| `timely_count`    | nullable `Int64`   |
| `source_percent`  | nullable `Float64` |
| `source_file`     | nullable string    |

### Percentage Contract

Accepted:

``` text
"38.47%" → 0.3847
0.3847    → 0.3847
missing   → <NA>
```

Rejected as ambiguous:

``` text
38.47
```

The pipeline does not guess whether bare `38.47` means `38.47%` or a
decimal rate.

------------------------------------------------------------------------

## 4.6 Timeliness Stage 4 — Business Validation ✅

| Validation Rule                            | Severity                    | Gate         |
|:-------------------------------------------|:----------------------------|:-------------|
| Required analytical fields missing         | FAIL                        | Block        |
| `source_percent` missing                   | WARNING                     | Allow        |
| Negative counts                            | FAIL                        | Block        |
| `timely_count > disposed_count`            | FAIL                        | Block        |
| disposed = 0 and timely \> 0               | FAIL                        | Block        |
| disposed = 0 and timely = 0                | PASS; rate undefined / NULL | Allow        |
| Unexpected processing type                 | FAIL                        | Block        |
| Duplicate Month × Processing Type × Region | FAIL                        | Block        |
| Rate reconciliation outside tolerance      | FAIL                        | Block        |
| `02/09` / unresolved category              | WARNING                     | Allow        |
| TOTAL reconciliation                       | PROFILE FIRST               | Non-blocking |

Rate reconciliation:

``` text
calculated_rate = timely_count / disposed_count
```

when `disposed_count > 0`, compared with `source_percent` using
rounding-aware tolerance of approximately `0.00005`.

### Severity Troubleshooting

A pipeline compatibility defect initially caused warning-only Timeliness
conditions to be counted as failures.

The contract was corrected:

``` text
WARNING → visible but non-blocking
FAIL    → block publication
```

Production principle:

> **Validation severity is part of the data contract and must control
> publish behavior explicitly.**

------------------------------------------------------------------------

## 4.7 TOTAL Reconciliation — Profile First

TOTAL rows are not part of analytical Silver detail.

They are retained as control metadata for:

``` text
SUM(detail disposed_count) vs source TOTAL Disposed
SUM(detail timely_count)   vs source TOTAL Timely
```

Decision: do not make TOTAL mismatch a blocking rule until source
aggregation behavior is sufficiently profiled.

------------------------------------------------------------------------

## 4.8 Timeliness Validation / Publish ✅

Timeliness was integrated into `silver_pipeline.py` with
dataset-specific routing while reusing the same overall Silver pattern:

``` text
Call
→ Transform
→ Collect validation evidence
→ Decide
→ Publish
```

Validation reports are generated before the publish decision so failed
runs remain diagnosable.

Result:

> **Timeliness Trusted Silver published and human-validated
> successfully.**

------------------------------------------------------------------------

# 5. Shared Silver Pipeline Architecture

``` text
src/
  ingestion/
  transformation/
    structure_cleaning.py
    standardization.py
    type_conversion.py
  validation/
    data_quality.py
  pipelines/
    silver_pipeline.py
```

The transformation functions contain stage-specific behavior;
`silver_pipeline.py` orchestrates the end-to-end workflow and validation
gate.

Shared production pattern:

``` text
Source-specific behavior
        ↓
Reusable Silver stages
        ↓
Dataset-specific validation
        ↓
Common gate semantics
        ↓
Trusted Silver
```

------------------------------------------------------------------------

# 6. Validation Evidence, Gate Behavior, and Execution Logs

## 6.1 Validation Report

Every validation run produces a **Validation Report**, regardless of
whether the final status is PASS, WARNING, or FAIL.

Validation evidence is written under:

``` text
data/quality_reports/
```

The report answers:

> **Is the dataset trustworthy according to the defined data-quality
> contract?**

It preserves: - input/output row counts - overall validation status -
rule-level PASS / WARNING / FAIL results - failed row counts - warning
counts - stage summaries / profiling evidence where applicable

The operational sequence is:

``` text
Transformation
→ Business Validation
→ Generate Validation Report
→ Validation Gate
```

Gate behavior:

``` text
PASS
→ validation report generated
→ publish Trusted Silver

WARNING only
→ validation report generated with warnings
→ publish Trusted Silver
→ preserve warnings for later review / monitoring

FAIL
→ validation report generated with failure evidence
→ stop Trusted Silver publication
→ raise ValidationError
```

Generating the report **before** the gate decision is important. A
failed run must still leave enough evidence for troubleshooting.

## 6.2 Validation Report vs Execution Log

A **Validation Report** and an **Execution Log** serve different
purposes.

| Evidence          | Main Question                         | Example                                                                                    |
|:------------------|:--------------------------------------|:-------------------------------------------------------------------------------------------|
| Validation Report | Is the data trustworthy?              | Which rule failed? How many rows failed? Were there warnings?                              |
| Execution Log     | What happened while the pipeline ran? | Pipeline started, transformation completed, validation completed, publish succeeded/failed |

Conceptually:

``` text
Pipeline Run
   ├── Execution Log
   │     └── records pipeline events and stage execution
   │
   └── Validation Report
         └── records data-quality results and gate evidence
```

The current Module 2 implementation establishes validation reports and
pipeline execution behavior. Full production **observability,
monitoring, and alerting are intentionally outside the Module 2 scope**
and are deferred to the later Monitoring module.

Module 2’s responsibility is to produce reliable operational evidence
that monitoring can consume later:

``` text
Pipeline status
+ Execution logs
+ Validation reports
        ↓
Future Monitoring / Observability
        ↓
Alerting
```

This keeps responsibilities separated:

> **Module 2 produces quality and execution signals. The Monitoring
> module observes those signals over time and decides when intervention
> or alerting is required.**

# 7. Testing & Regression Strategy

Automated tests cover the four transformation/validation stages and
known production defects.

Timeliness component work reached a combined:

``` text
Structure Cleaning
+ Standardization
+ Type Conversion
+ Business Validation
= 78 tests passed
```

Eligibility validation was subsequently rerun after the county-reference
fix:

``` text
tests/test_validation.py
= 36 passed
```

The final Eligibility E2E pipeline also passed after the reference and
grain corrections.

Important rule:

> **When troubleshooting exposes a real defect, convert it into a
> regression test whenever practical.**

------------------------------------------------------------------------

# 8. Human Validation

Automated PASS is necessary but not sufficient.

Human validation was used to: - inspect actual source semantics -
compare Bronze/source values against transformed output - verify
analytical grain - inspect unexpected categories - distinguish valid
source records from valid analytical population - validate source
representation assumptions - approve unresolved/non-blocking conditions

Examples: - Inspecting the raw Excel cell proved `Total SNAP Payments`
genuinely contained cents. - Inspecting monthly Eligibility files showed
`State Total`, `State Office`, and `Call Centers` were recurring source
entities rather than random corrupt rows. - Timeliness source/output
reconciliation verified that section parsing and missing-value behavior
preserved business meaning.

------------------------------------------------------------------------

# 9. Reusable Troubleshooting Workflow

``` text
Validation Gate FAIL
→ Read validation report
→ Identify failing rule + affected population
→ Profile unique / representative failing values
→ Compare with Bronze / raw source
→ Classify root cause:
     source defect?
     transformation defect?
     reference-data defect?
     business-rule / grain issue?
→ Fix the correct layer
→ Add regression test
→ Re-run component tests
→ Re-run E2E pipeline
→ Human validate
→ Publish only after PASS
```

------------------------------------------------------------------------

# 10. AI-Assisted Development Workflow

``` text
Business Requirement
→ Acceptance Criteria
→ Agent reads repository
→ Implement
→ Automated Test
→ Inspect
→ Fix
→ Regression Test
→ Human Business Validation
```

**Agent responsibilities** - inspect repository patterns - implement
within defined boundaries - add/run tests - diagnose technical
failures - report assumptions and evidence

**Human responsibilities** - define business meaning - define grain and
analytical population - define acceptance criteria - decide validation
severity - inspect source semantics - approve unresolved assumptions -
decide whether the dataset is trustworthy enough to publish

------------------------------------------------------------------------

# 11. Final Module 2 Status

## 11.1 Completion Status

| Silver Capability         | Eligibility / Caseload |  Timeliness  |
|:--------------------------|:----------------------:|:------------:|
| Structure Cleaning        |      ✅ Complete       | ✅ Complete  |
| Standardization           |      ✅ Complete       | ✅ Complete  |
| Data Type Conversion      |      ✅ Complete       | ✅ Complete  |
| Business Validation       |      ✅ Complete       | ✅ Complete  |
| Validation Report         |      ✅ Generated      | ✅ Generated |
| Validation Gate           |        ✅ PASS         |   ✅ PASS    |
| Automated Silver Pipeline |      ✅ Complete       | ✅ Complete  |
| Regression Testing        |      ✅ Complete       | ✅ Complete  |
| Human Validation          |      ✅ Complete       | ✅ Complete  |
| Trusted Silver Publish    |      ✅ Complete       | ✅ Complete  |

## 11.2 Final Data Contracts

| Dataset                | Trusted Silver Grain                           | Final Analytical Population / Meaning                                               |
|:-----------------------|:-----------------------------------------------|:------------------------------------------------------------------------------------|
| Eligibility / Caseload | **County × Reporting Month**                   | 254 Texas counties × 12 months = **3,048 rows**                                     |
| Timeliness             | **Region × Reporting Month × Processing Type** | Processing workload and timeliness separated into Applications and Redeterminations |

## 11.3 Module Boundary

| Module 2 Owns                   | Deferred to Later Monitoring Module   |
|:--------------------------------|:--------------------------------------|
| Transformation execution        | Monitoring dashboards / health views  |
| Business validation             | Trend monitoring across pipeline runs |
| Validation reports              | Warning / failure trend analysis      |
| Validation gate                 | Operational alerting                  |
| Trusted Silver publish decision | Notifications / escalation            |
| Execution evidence / logs       | Observability over time               |

## 11.4 Module 2 Closeout

> **Module 2 — Data Quality / Silver Layer is COMPLETE.**

Module 2 now provides two governed upstream datasets:

``` text
Eligibility / Caseload Trusted Silver
+
Timeliness Trusted Silver
        ↓
Module 3 — Physical Gold Implementation
```

The central production principle is:

> **Silver is the trust boundary between preserved source data and
> governed analytics.**

The completed contract is:

``` text
Bronze
→ Structure Cleaning
→ Standardization
→ Data Type Conversion
→ Business Validation
→ Validation Report
→ Validation Gate
→ Trusted Silver
```
