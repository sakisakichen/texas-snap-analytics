# SNAP Analytics Platform V2 --- Dashboard Design

**Module:** Module 3 --- Analytics Modeling / Gold Layer\
**Status:** v0.5 --- Gold Design Package Complete / Implementation Ready\
**Primary Audience:** Program Leadership

## 1. Purpose

The SNAP dashboard is designed as a **decision-support tool**, rather
than a reporting-only interface.

Its primary goal is to help program leadership identify geographic areas
that may warrant greater attention when planning future program
resources.

The design follows a decision-first principle:

> Start with the decision the user needs to make, then work backward to
> the business questions, metrics, trusted source data, model grain, and
> dashboard experience required to support that decision.

## 2. Primary User and Dashboard Type

### Primary User --- Program Leadership

Program leadership is responsible for strategic program planning and
resource allocation. The first SNAP dashboard is therefore designed
primarily as a **Strategic Dashboard**, rather than an operational or
root-cause-analysis dashboard.

### Primary Decision

> **Which geographic areas warrant leadership attention when planning
> future SNAP program resources?**

### Design Principle

> **Leadership needs the signal; analysts need the investigation.**

Leadership should be able to identify where attention may be required.
Analysts can then investigate why an issue exists, whether it is
persistent, and what factors may be driving it.

## 3. Core Business Questions --- Gold v1

Gold v1 is intentionally decision-driven. During modeling, the original
three-question structure was challenged against the actual source data
and the leadership decision.

The primary decision remains:

> **Which geographic areas warrant leadership attention when planning
> future SNAP program resources?**

Gold v1 therefore uses two primary Business Questions.

### BQ1 --- Workload

> **Where is SNAP workload high?**

Gold v1 uses two complementary workload signals:

-   **Caseload / Program Load:** Month-end SNAP cases represent ongoing
    program load.
-   **Processing Workload:** Disposed cases represent processing
    activity completed during a reporting period.

These measures must not be added together. Caseload is a periodic
snapshot; disposed volume is a processing flow.

### BQ2 --- Processing Performance

> **How well is that workload being processed?**

Processing performance is evaluated separately by processing type:

-   **Application Timeliness:** compare the actual rate with the
    validated USDA FNS acceptable-performance benchmark of **95% or
    above**.
-   **Redetermination / Recertification Timeliness:** show the actual
    rate, trend, and regional comparison. Do **not** apply the 95%
    Application Processing Timeliness benchmark unless an authoritative
    redetermination benchmark is validated.

The USDA-reported **87.50% Texas FY2024 Recertification Processing
Timeliness** is a historical actual performance value, **not a target or
benchmark**.

Application and Redetermination should not be combined into one primary
Timeliness KPI because different processing volumes and performance can
mask problems in one processing type.

### Analytical Context --- Not a Primary Leadership BQ

The caseload fact may still retain:

-   Eligible individual count
-   Eligible individuals by age group
-   Total SNAP payments
-   Derived average payment per case

These are source-supported analytical measures, but Gold v1 does not
force them into the primary leadership dashboard without a demonstrated
decision use.

> **Gold model availability does not imply dashboard KPI relevance.**

Population and poverty remain potential future enrichments and are not
current project datasets.

## 4. Metric Design --- Gold v1

### 4.1 Program Load --- Month-End SNAP Case Count

**Metric:** SNAP Case Count\
**Source meaning:** Number of SNAP cases reported at month end for a
county and benefit month.\
**Business use:** Indicates ongoing program / caseload load.\
**Candidate grain:** County × Benefit Month.\
**Aggregation behavior:** **Semi-additive.**

Across counties within the same benefit month, case counts may be summed
to a larger geography when the geography crosswalk is valid.

Across months, monthly case counts must **not** be summed and
interpreted as unique annual cases because the same case may appear in
multiple monthly snapshots.

### 4.2 Eligible Individuals

**Metric:** Eligible Individual Count\
**Business use:** Describes the number of eligible people represented in
the month-end SNAP caseload.\
**Candidate grain:** County × Benefit Month.\
**Aggregation behavior:** **Semi-additive** for the same reason as case
count.

Age-band counts are stored as base measures:

-   Under age 5
-   Age 5--17
-   Age 18--59
-   Age 60--64
-   Age 65+

**Validation rule:**

`Sum of age-band eligible counts = eligible_individual_count`

A mismatch should trigger investigation rather than automatic
correction.

### 4.3 Total SNAP Payments

**Metric:** Total SNAP Payments\
**Business use:** Measures benefit dollars paid for the reporting
geography / benefit month.\
**Candidate grain:** County × Benefit Month.\
**Aggregation behavior:** **Additive** across geography and time when
the source definition represents monthly payments.

Unlike caseload snapshots, payments made in separate months represent
separate dollar flows and can be accumulated for period spending.

### 4.4 Average Payment per Case

**Metric:** Average Payment per Case\
**Type:** Derived metric.

`Average Payment per Case = SUM(total_snap_payments) / SUM(case_count)`

The source-reported average may be retained for reconciliation, but Gold
should derive the analytical metric from its base components rather than
averaging pre-calculated averages.

### 4.5 Processing Volume

**Metric:** Disposed Count\
**Business use:** Measures processing workload completed during a
reporting period.\
**Candidate grain:** Region × Reporting Month × Processing Type.\
**Base measure:** Stored.

`processing_type` currently distinguishes Application and
Redetermination. Gold v1 keeps this low-cardinality category in the fact
rather than creating a separate dimension with no meaningful descriptive
attributes.

Disposed counts are additive across regions and reporting periods when
the resulting aggregation answers a valid business question. Aggregation
across processing types is mathematically possible, but the combined
result must be labeled as total processing workload rather than
application volume.

### 4.6 Timely Count and Timeliness Rate

**Base measure:** `timely_count`\
**Derived metric:** `timeliness_rate`

`Timeliness Rate = SUM(timely_count) / SUM(disposed_count)`

Timeliness Rate is **non-additive**. It should not be summed or naively
averaged across regions or periods because the underlying disposed
volumes may differ.

Example:

-   Month A: 90 timely / 100 disposed = 90%
-   Month B: 800 timely / 1,000 disposed = 80%

Naive average = 85%, but the correct combined rate is:

`(90 + 800) / (100 + 1,000) = 80.9%`

**Production rule:** Store additive base components and derive ratios
from numerator and denominator whenever possible.

**Benchmark governance:**

-   Application Timeliness: **95% or above** is the validated USDA FNS
    acceptable-performance benchmark.
-   Redetermination / Recertification Timeliness: no validated 95%
    benchmark is assigned in Gold v1.
-   Texas FY2024 Recertification Timeliness of **87.50%** is reference
    actual performance only.
-   A combined Application + Redetermination Timeliness rate is not a
    primary KPI.

## 5. Gold Logical Model v1

Gold v1 uses a **multi-fact dimensional model** because the two source
domains represent different business processes and natural grains.

**Design status:** **Gold Logical Schema v1 Frozen 🔒**

The frozen logical model contains **2 fact tables + 3 dimensions**. No
additional fact or dimension is required for Gold v1 unless
implementation validation reveals a material source/grain issue.

![SNAP Gold Logical Model v1](snap_gold_logical_model_v1.png)

### 5.1 Fact #1 --- `fact_snap_processing`

**Business process:** SNAP Processing Performance\
**Final grain:** One row per **Region × Reporting Month × Processing
Type**

Core fields:

-   `region_key`
-   `month_key`
-   `processing_type`
-   `disposed_count`
-   `timely_count`

Derived:

-   `timeliness_rate`

### 5.2 Fact #2 --- `fact_snap_caseload_monthly`

**Business process:** Monthly SNAP Benefit Caseload & Eligibility
Snapshot\
**Final grain:** One row per **County × Reporting Month**

Core fields:

-   `county_key`
-   `month_key`
-   `case_count`
-   `eligible_individual_count`
-   age-band eligible counts
-   `total_snap_payments`

Derived:

-   `avg_payment_per_case`

### 5.3 `dim_month` --- Shared / Conformed Monthly Dimension

Both facts use the same conformed calendar-month dimension.

**Final grain:** One row per calendar month.

Physical columns:

-   `month_key INT` --- meaningful `YYYYMM` key, e.g. `202401`
-   `reporting_month STRING` --- source-friendly `YYYY-MM`
-   `year INT`
-   `quarter STRING`
-   `month_number INT`
-   `month_name STRING`

Relationships:

-   `dim_month (1) → fact_snap_processing (Many)`
-   `dim_month (1) → fact_snap_caseload_monthly (Many)`

Both facts store `month_key` as the physical foreign key. The shared
dimension provides one consistent calendar definition across business
processes.

### 5.4 `dim_region`

**Final grain:** One row per geographic reporting region.

Physical columns:

-   `region_key INT` --- warehouse surrogate key
-   `region_code STRING` --- source / business region code
-   `region_name STRING`

Relationships:

-   `dim_region (1) → fact_snap_processing (Many)`
-   `dim_region (1) → dim_county (Many)`

### 5.5 `dim_county`

**Final grain:** One row per geographic county.

Physical columns:

-   `county_key INT` --- warehouse surrogate key
-   `county_fips STRING` --- standardized geographic identifier
-   `county_name STRING`
-   `region_key INT` --- foreign key to `dim_region`

Relationships:

-   `dim_county (1) → fact_snap_caseload_monthly (Many)`
-   `dim_region (1) → dim_county (Many)`

The expected analytical population is 254 Texas counties.

### 5.6 County → Region Geography Crosswalk

The project should not discard a broadly valid geography relationship
because a small number of exceptions require investigation.

Implementation pattern:

`County Source → Join Authoritative County/Region Reference → Validate Matches → Investigate Unmatched Counties → Publish Crosswalk`

The source-defined `02/09` reporting region is treated as a **known
exception / validation item**. Authoritative mappings should be used
wherever available; remaining exceptions should be isolated and
documented rather than silently inferred.

A useful validation report should include:

-   Expected Texas counties
-   Successfully mapped counties
-   Unmatched counties
-   Duplicate / ambiguous mappings
-   Explicit exception handling

## 6. Measure Additivity Rules

  ----------------------------------------------------------------------------
  Measure                       Across         Across Time    Classification
                                Geography                     
  ----------------------------- -------------- -------------- ----------------
  `disposed_count`              Yes            Yes            Additive

  `timely_count`                Yes            Yes            Additive

  `timeliness_rate`             No direct      No direct      Non-additive /
                                SUM/AVG        SUM/AVG        Derived

  `case_count`                  Yes at same    Not as unique  Semi-additive
                                snapshot       caseload       
                                period                        

  `eligible_individual_count`   Yes at same    Not as unique  Semi-additive
                                snapshot       individuals    
                                period                        

  Age-band eligible counts      Yes at same    Not as unique  Semi-additive
                                snapshot       individuals    
                                period                        

  `total_snap_payments`         Yes            Yes            Additive

  `avg_payment_per_case`        No direct SUM  No naive AVG   Non-additive /
                                                              Derived
  ----------------------------------------------------------------------------

### Production Interpretation Rule

> **Technical aggregation does not automatically equal meaningful
> business aggregation.**

Before aggregating a measure, confirm that the resulting number still
answers a valid business question.

## 7. Grain and Join Safety

### Grain Principle

> **Grain defines what one row represents. Measures define what is
> quantified at that grain.**

Gold v1 preserves each business process at its natural grain rather than
forcing all source data into one table.

### Fact-to-Dimension Joins

Safe examples:

`fact_snap_processing.month_key = dim_month.month_key`

`fact_snap_caseload_monthly.month_key = dim_month.month_key`

### Fact-to-Fact Join Warning

The two facts must not be directly joined only because their month keys
match.

Processing fact:

`Region × Month × Processing Type`

Caseload fact:

`County × Month`

A month-only fact-to-fact join would create row duplication /
many-to-many behavior. County-level caseload must first be rolled up
through a validated County → Region crosswalk when a Region-level
comparison is required.

## 8. KPI Governance Principles Applied to SNAP

Research Question #2 established the following governance model:

`Business Objective → Business Meaning → Metric Definition → Business Alignment → Owner/Steward → Central Implementation → Testing → Dashboard → Change Management`

### Business Governance vs. Technical Governance

> **Business Governance defines what the metric means. Technical
> Governance ensures that meaning is implemented consistently
> everywhere.**

For each governed metric, explicitly consider:

-   Business purpose
-   Business definition
-   Formula
-   Grain
-   Time window
-   Filters
-   Inclusions / exclusions
-   Source / system of record
-   Business owner or steward
-   Technical implementation
-   Validation / testing
-   Change management

### Consistency Does Not Mean Forced Standardization

Different teams may legitimately need different metrics when they answer
different business questions. Governance means that business meaning is
explicit and that a given definition is calculated consistently wherever
it is used.

### Official vs. Analyst-Derived Metrics

Official / source-defined metrics should follow authoritative
definitions and benchmarks when available.

Analyst-derived metrics must document their business purpose, formula,
assumptions, source, limitations, and validation status. They should not
be presented as official policy metrics without supporting evidence.

## 9. Metric Conflict Resolution --- Production Pattern

Example:

> Finance reports Active Customers = 12,400, while Product reports
> Active Customers = 15,800.

Do not assume one team is wrong or begin by debugging SQL. First
compare:

1.  Business purpose
2.  Business definition
3.  Grain
4.  Formula
5.  Time window
6.  Filters
7.  Inclusion / exclusion rules
8.  Source data

Then determine whether the organization needs one shared definition or
two legitimately different metrics with clearer names and ownership.
Once aligned, implement shared logic centrally, validate it, update
downstream assets, and govern future definition changes.

## 10. Dashboard Decision Flow --- Gold v1

The final primary decision flow is:

`Workload → Processing Performance → Leadership Attention → Analyst Investigation`

### Workload

Use both:

-   Ongoing program load (`case_count`)
-   Operational processing workload (`disposed_count`)

These measures are complementary but must not be combined into one
total.

### Processing Performance

Use:

-   `disposed_count`
-   `timely_count`
-   Derived `timeliness_rate`
-   `processing_type`

Application Timeliness is evaluated against the validated **95% USDA FNS
benchmark**.

Redetermination / Recertification Timeliness is presented as actual
performance and trend without assigning the Application benchmark.

### Analytical Context

Eligible individuals, age profile, total payments, and average payment
per case remain available for analytical exploration. They are not
primary leadership KPIs in Gold v1 because a direct resource-planning
decision use has not yet been established.

### No Unsupported Composite Priority Score

Gold v1 will not create an arbitrary composite priority score because no
authoritative business evidence currently supports weighting workload,
context, and performance into a resource-allocation formula.

## 11. Information Hierarchy

Current direction:

`Leadership Signal → Supporting Context → Geographic Area → Analytical Investigation`

The exact visual hierarchy will be finalized after Gold implementation
validates the model and available analytical combinations.

## 12. Analytical Investigation Boundary

Detailed questions belong primarily to the analytical layer:

-   Why did performance change?
-   When did the issue begin?
-   Is the issue temporary or persistent?
-   Which operational factor is driving the change?

Leadership may receive concise trend signals, but the Strategic
Dashboard should not become a full root-cause-analysis workspace.

## 13. Current Data State and Implementation Readiness

### 13.1 Eligible / Caseload Domain

Current state:

`Raw/Bronze → Structure Cleaning → Standardization → Type Conversion → Business Validation → Validation Gate → Trusted Silver ✅`

The Eligibility / Caseload Trusted Silver layer is complete.

**Validated grain:** County × Reporting Month.  
**Validated 2024 analytical population:** 254 Texas counties × 12 months
= **3,048 rows**.

### 13.2 Timeliness Domain

Current state:

`Raw/Source → Structure Cleaning → Standardization → Type Conversion → Business Validation → Validation Gate → Trusted Silver ✅`

The Timeliness Trusted Silver layer is complete.

**Validated grain:** Region × Reporting Month × Processing Type.

Applications and Redeterminations remain separate processing types.

### 13.3 Geography Reference

County → Region remains a governed Gold implementation relationship.
The authoritative County / Region reference should define the canonical
mapping, with unmatched / ambiguous mappings and the `02/09` reporting
exception handled explicitly through validation.

### 13.4 Gold Implementation Readiness

Both source domains have passed the Trusted Silver boundary. The Silver
dependency that previously blocked Physical Gold has therefore been
cleared.

The Gold design package now includes the frozen logical model, final
physical schema, source-to-target transformation design, and Gold
acceptance criteria / validation design.

## 14. Physical Gold Model Design

**Status: Complete ✅**

The frozen logical model has been converted into an implementation-ready
physical schema.

> **Logical modeling defines what the model should represent. Physical
> modeling defines how the tables should actually be built.**

The physical-design framework is:

`Purpose → Grain → Columns → Keys → Data Types → Relationships`

### 14.1 `dim_month`

**Purpose:** Provide one consistent calendar definition shared across
Gold facts.  
**Grain:** One row per calendar month.

Physical columns:

-   `month_key INT` --- meaningful `YYYYMM` key, e.g. `202401`
-   `reporting_month STRING` --- source-friendly `YYYY-MM`
-   `year INT`
-   `quarter STRING`
-   `month_number INT`
-   `month_name STRING`

Relationships:

-   `dim_month (1) → fact_snap_processing (Many)`
-   `dim_month (1) → fact_snap_caseload_monthly (Many)`

### 14.2 `dim_region`

**Purpose:** Centralize reusable reporting-region definitions and
attributes.  
**Grain:** One row per geographic reporting region.

Physical columns:

-   `region_key INT` --- warehouse surrogate key
-   `region_code STRING` --- business / source region code
-   `region_name STRING`

Relationships:

-   `dim_region (1) → fact_snap_processing (Many)`
-   `dim_region (1) → dim_county (Many)`

### 14.3 `dim_county`

**Purpose:** Centralize County identity and the governed County → Region
relationship.  
**Grain:** One row per geographic county.

Physical columns:

-   `county_key INT` --- warehouse surrogate key
-   `county_fips STRING` --- standardized geographic identifier
-   `county_name STRING`
-   `region_key INT` --- foreign key to `dim_region`

Relationships:

-   `dim_county (1) → fact_snap_caseload_monthly (Many)`
-   `dim_region (1) → dim_county (Many)`

Expected analytical population: **254 Texas counties**.

### 14.4 `fact_snap_processing`

**Purpose:** Represent SNAP processing workload and timeliness
performance.  
**Grain:** One row per Region × Reporting Month × Processing Type.

Physical columns:

-   `region_key INT`
-   `month_key INT`
-   `processing_type STRING`
-   `disposed_count INT`
-   `timely_count INT`

No separate fact surrogate key is required in Gold v1. Natural grain
uniqueness is enforced through:

`region_key + month_key + processing_type`

`timeliness_rate` remains derived rather than stored as a base analytical
measure.

### 14.5 `fact_snap_caseload_monthly`

**Purpose:** Represent monthly County-level SNAP caseload and benefit
activity.  
**Grain:** One row per County × Reporting Month.

Physical columns:

-   `county_key INT`
-   `month_key INT`
-   `case_count INT`
-   `eligible_individual_count INT`
-   `eligible_under_5_count INT`
-   `eligible_5_17_count INT`
-   `eligible_18_59_count INT`
-   `eligible_60_64_count INT`
-   `eligible_65_plus_count INT`
-   `total_snap_payments DECIMAL / NUMBER`

`avg_payment_per_case` remains a derived metric rather than a governed
base measure.

### 14.6 Physical Data-Type Principles

-   Count → `INT`
-   Warehouse surrogate key → `INT`
-   Business identifier / code → `STRING`
-   Money → fixed-precision `DECIMAL / NUMBER`
-   Names / categories → `STRING`
-   Corresponding PK / FK data types must match

A value that looks numeric is not automatically a numeric measure.
Storage type follows the business role of the field.

## 15. Gold Transformation Design

**Status: Complete ✅**

Gold transformation design defines how Trusted Silver and authoritative
reference data become the five physical Gold tables.

The reusable framework is:

> **Source → Mapping → Transformation → Expected Output**

Transformation patterns used in Gold v1:

-   **Direct** --- preserve source value and business meaning
-   **Rename** --- preserve the value while standardizing the target name
-   **Derive** --- calculate a target value from source data
-   **Lookup** --- resolve a dimension / reference key
-   **Generate** --- create a warehouse surrogate key
-   **Aggregate** --- combine rows only when the target grain requires it

> **Silver → Gold does not automatically require aggregation.**

When Trusted Silver already matches the target fact grain, Gold primarily
performs dimension-key lookup and preserves trusted base measures.

### 15.1 `dim_month`

**Sources:** Eligibility Trusted Silver + Timeliness Trusted Silver.

Transformation flow:

`Months from Both Silvers → UNION → DISTINCT → Derive Calendar Attributes → dim_month`

Mapping:

-   `reporting_month` → Direct
-   `month_key` → Derive as `YYYYMM`
-   `year` → Derive
-   `quarter` → Derive
-   `month_number` → Derive
-   `month_name` → Derive

**Expected 2024 output:** 12 rows.

### 15.2 `dim_region`

**Canonical source:** authoritative Region reference / County → Region
crosswalk.

Timeliness Trusted Silver is used for reconciliation rather than as the
sole canonical Region definition.

Mapping:

-   `region_key` → Generate
-   `region_code` → Direct from authoritative reference
-   `region_name` → Direct from authoritative reference

Every valid Timeliness Silver Region must reconcile to exactly one
canonical Gold Region.

### 15.3 `dim_county`

**Canonical source:** authoritative County reference / County → Region
crosswalk.

Eligibility Trusted Silver is used for reconciliation and County
coverage validation.

Mapping:

-   `county_key` → Generate
-   `county_fips` → Direct
-   `county_name` → Direct
-   `region_key` → Lookup through `dim_region`

**Expected output:** 254 Texas counties.

### 15.4 `fact_snap_processing`

**Primary source:** Timeliness Trusted Silver only.

Silver grain and Gold grain are both:

`Region × Reporting Month × Processing Type`

No aggregation is required.

Mapping:

-   Region → Lookup `dim_region` → `region_key`
-   Reporting Month → Lookup `dim_month` → `month_key`
-   `processing_type` → Direct
-   `disposed_count` → Direct
-   `timely_count` → Direct

`source_percent` remains reconciliation evidence and is not promoted as
the governed Gold analytical rate.

### 15.5 `fact_snap_caseload_monthly`

**Primary source:** Eligibility Trusted Silver only.

Silver grain and Gold grain are both:

`County × Reporting Month`

No aggregation is required.

Mapping:

-   County → Lookup `dim_county` → `county_key`
-   Reporting Month → Lookup `dim_month` → `month_key`
-   Cases → Rename / preserve as `case_count`
-   Eligible individuals → Rename / preserve as
    `eligible_individual_count`
-   Age-band counts → Rename / preserve
-   Total payments → Rename / preserve with fixed decimal precision

**Expected 2024 output:** 254 × 12 = **3,048 rows**.

### 15.6 Transformation Principle

> **Trusted Silver rows → Dimension Key Lookup → Preserve Base Measures
> → Analytics-ready Gold Fact**

Dimensions may integrate shared canonical entities across sources. Facts
remain aligned to their specific business process and natural grain.

## 16. Gold Acceptance Criteria and Validation Design

**Status: Design Complete ✅**

Gold acceptance criteria define what must be true before the implemented
Gold layer can be considered trusted.

The validation framework is:

> **Grain → Keys → Relationships → Reconciliation → Business Metrics**

The purpose is not simply to prove that transformation SQL executed. It
is to prove that Gold preserves the intended business meaning and that
Silver → Gold transformation did not introduce duplication, data loss,
broken mappings, measure drift, or incorrect analytical calculations.

### 16.1 `dim_month`

-   `month_key` must be unique and not null.
-   Complete 2024 model must contain exactly 12 calendar months.
-   Every valid month appearing in either Trusted Silver dataset must map
    to exactly one `dim_month` row.
-   `month_key`, `reporting_month`, year, quarter, month number, and
    month name must be internally consistent.

### 16.2 `dim_region`

-   `region_key` must be unique and not null.
-   Canonical `region_code` values must not be duplicated.
-   Every valid Timeliness Silver Region must map to exactly one
    `dim_region` row.
-   Unmapped or ambiguous Region values fail mapping coverage.
-   `02/09` handling must be explicit and documented.

### 16.3 `dim_county`

-   Exactly 254 analytical Texas counties must be represented.
-   `county_key` must be unique and not null.
-   `county_fips` must be unique and not null.
-   `region_key` must not be null.
-   Every `region_key` must resolve to `dim_region`.
-   Every analytical County must map to exactly one reporting Region.
-   Duplicate, unmatched, or ambiguous County → Region mappings fail
    validation unless handled as an explicitly governed exception.

Correct row count alone is insufficient when geography relationships are
incomplete.

### 16.4 `fact_snap_processing`

**Grain**

`region_key + month_key + processing_type` must be unique.

**Relationships**

-   `region_key` and `month_key` must not be null.
-   Every Region key must resolve to `dim_region`.
-   Every Month key must resolve to `dim_month`.

**Measure / source reconciliation**

-   Gold `disposed_count` must reconcile to Timeliness Trusted Silver.
-   Gold `timely_count` must reconcile to Timeliness Trusted Silver.
-   Reconciliation should be available at the natural Region × Month ×
    Processing Type grain, not only at overall totals.
-   Counts should not be negative.
-   `timely_count` should not exceed `disposed_count`.

**Governed business metric**

`timeliness_rate = SUM(timely_count) / SUM(disposed_count)`

Pre-calculated source percentages must not be naively averaged to produce
the governed metric.

### 16.5 `fact_snap_caseload_monthly`

**Grain**

`county_key + month_key` must be unique.

**Completeness**

Complete 2024 output must contain **3,048 rows**:

`254 counties × 12 months`

**Relationships**

-   `county_key` and `month_key` must not be null.
-   Every County key must resolve to `dim_county`.
-   Every Month key must resolve to `dim_month`.

**Measure / source reconciliation**

Gold base measures must reconcile to Eligibility Trusted Silver,
including:

-   `case_count`
-   `eligible_individual_count`
-   Age-band eligible counts
-   `total_snap_payments`

Reconciliation should support investigation at County × Month grain.

**Age reconciliation**

`eligible_under_5_count + eligible_5_17_count + eligible_18_59_count + eligible_60_64_count + eligible_65_plus_count = eligible_individual_count`

A mismatch is flagged for investigation rather than silently corrected.

**Governed business metric**

`avg_payment_per_case = SUM(total_snap_payments) / SUM(case_count)`

Pre-calculated row averages must not be naively averaged across Counties
or months.

### 16.6 Gold Validation Principle

> **Row count correct ≠ model correct.**

A Gold table can have the expected number of rows and still fail because
of duplicate grain, orphan foreign keys, incomplete mappings, measure
drift, or incorrect derived metrics.

Acceptance criteria are defined before implementation so the implemented
Gold model has an explicit trust gate.

## 17. Future External Data Enhancements

Population and Poverty Rate were considered during early dashboard
design but are **not current project datasets**.

Potential future enrichment includes:

-   County population
-   Poverty Rate
-   Program-specific SNAP-eligible population / household estimates

These should enter the model only after:

1.  A source is selected.
2.  Business meaning is validated.
3.  Temporal and geographic grain is understood.
4.  Refresh cadence is understood.
5.  Join compatibility with existing facts is validated.

Gold v1 should not model or advertise these metrics as currently
available.

## 18. Validation Rules Identified During Modeling

### Caseload / Eligibility

**Age reconciliation**

`under_5 + age_5_17 + age_18_59 + age_60_64 + age_65_plus = eligible_individual_count`

### Timeliness

**Rate reconciliation**

`calculated_timeliness_rate ≈ source_percent`

The source percentage can be retained for validation / reconciliation,
while the Gold analytical rate is derived from timely and disposed
counts.

### Geography

Validate:

-   County reference coverage
-   Unmatched counties
-   Duplicate mappings
-   Ambiguous mappings
-   `02/09` exception handling

## 19. Design Decisions and Trade-offs

### Decision 1 --- Preserve Natural Grain

**Selected:** Separate Processing Performance and Caseload Snapshot
facts.\
**Reason:** They represent different business processes and different
geographic grains.

### Decision 2 --- Use a Multi-Fact Model

**Selected:** Two facts sharing standardized dimensions where business
meaning supports it.\
**Reason:** This avoids forcing unrelated processes into one fact and
reduces incorrect aggregation risk.

### Decision 3 --- Shared Monthly Dimension

**Selected:** One `dim_month`, used as Reporting Month in the processing
fact and Benefit Month in the caseload fact.\
**Reason:** Both use monthly calendar analysis while retaining distinct
business roles.

### Decision 4 --- Geography Relationship

**Selected:** Connect County to Region through a validated crosswalk.\
**Reason:** Most geography relationships can be authoritative; isolated
exceptions should be validated rather than causing the entire
relationship to be discarded.

### Decision 5 --- `processing_type` Remains in Fact for v1

**Selected:** No separate `dim_processing_type` yet.\
**Reason:** The current category has very low cardinality and no
meaningful descriptive hierarchy or attributes requiring a dedicated
dimension.

### Decision 6 --- Derive Ratios and Averages

**Selected:** Derive Timeliness Rate and Average Payment per Case from
base components.\
**Reason:** Base measures support correct weighted aggregation and
reconciliation.

### Decision 7 --- Do Not Sum Snapshot Counts Across Time as Unique Population

**Selected:** Treat case and eligible-individual counts as
semi-additive.\
**Reason:** The same case / individual may appear in multiple month-end
snapshots.

### Decision 8 --- External Population / Poverty Deferred

**Selected:** Future enhancement, not Gold v1.\
**Reason:** These datasets have not yet been sourced or modeled.

### Decision 9 --- Avoid Unsupported Decision Scores

**Selected:** Expose workload, caseload context, and performance
separately.\
**Reason:** The project lacks authoritative business rules for weighting
these signals into a composite resource-allocation score.

## 20. Research Status

### Research Question #1 --- Dashboard Design Process

**Status: Closed v1 ✅**

Key production pattern:

`Business Problem / Decision → Stakeholders & Users → Business Questions → Trusted Metrics → Prototype / Design → Summary / Context / Drill-down → Review / UAT → Release → Adoption / Feedback → Iterate`

### Research Question #2 --- KPI Governance

**Status: Closed v1 ✅**

Key production pattern:

`Business Objective → Business Meaning → Metric Definition → Alignment → Ownership → Central Implementation → Testing → Consumption → Change Management`

### Remaining Research Questions

-   #3 Analytics Development Lifecycle
-   #4 Analytics Review / Approval
-   #5 Analytics Design Trade-offs

## 21. Module 3 Design Closeout

### Design Status

**Module 3 Gold Analytics Modeling Design: Complete ✅**  
**Gold Logical Schema v1: Frozen 🔒**  
**Physical Gold Model Design: Complete ✅**  
**Gold Transformation Design: Complete ✅**  
**Gold Acceptance Criteria / Validation Design: Complete ✅**  
**Gold Design Package: Implementation Ready ✅**

### Completed in Module 3

-   Leadership decision and primary user defined
-   Primary Business Questions finalized
-   Two business processes and natural grains identified
-   Base vs. derived measures identified
-   Additivity behavior classified
-   Five-table logical model frozen
-   Physical columns, keys, data types, and relationships finalized
-   County → Region geography approach defined
-   Source-to-target transformation design completed for all five tables
-   Canonical dimension-source strategy defined
-   Fact dimension-key lookup strategy defined
-   Expected Gold output populations defined
-   Grain, key, relationship, and referential-integrity criteria defined
-   Silver → Gold measure reconciliation criteria defined
-   Age-band reconciliation defined
-   Weighted Timeliness Rate governed
-   Weighted Average Payment per Case governed
-   Application benchmark scope clarified
-   Application and Redetermination performance separated
-   Join-safety rules documented
-   Gold validation gate designed before implementation

### Remaining Execution Work

1.  Implement / publish the warehouse representation of Trusted Silver.
2.  Build `dim_month`, `dim_region`, and `dim_county`.
3.  Build `fact_snap_processing` and `fact_snap_caseload_monthly`.
4.  Execute the Step 9 Gold acceptance criteria.
5.  Publish Trusted Gold only after the validation gate passes.
6.  Proceed to governed semantic metrics and dashboard consumption.

### Execution Path

`Trusted Silver ✅ → Physical Gold Implementation → Gold Validation Gate → Trusted Gold → Semantic Metrics → Dashboard`

### Module 3 Production Mental Model

`Business Questions → Business Process → Grain → Measures → Dimensions → Logical Model → Physical Model → Transformation Design → Acceptance Criteria → Implementation → Validation`

> **Design what Gold should mean → Design how to build it → Define how
> to prove it is correct → Then implement it.**

The next active Module 3 task is **Physical Gold implementation in the
analytical warehouse**, followed by execution of the Step 9 acceptance
criteria.

