# Module 4 --- Semantic Metric Layer

## 1. Purpose

Module 4 establishes a governed semantic metric layer on top of
**Trusted Gold**.

The goal is to ensure that business metrics are calculated, aggregated,
filtered, and interpreted consistently across analytics products.

Trusted Gold answers:

> **Can we trust the analytical data?**

The Semantic Metric Layer answers:

> **Can we trust that everyone calculates and interprets the metric the
> same way?**

Module 4 does **not** redesign the existing Gold fact and dimension
model.

------------------------------------------------------------------------

## 2. Business Problem

Trusted Gold provides validated facts and dimensions, but trusted data
alone does not guarantee consistent business metrics.

Different consumers can use the same Gold data and still calculate the
same KPI differently.

For example, **Timeliness Rate** should be calculated as:

``` text
SUM(timely_count)
-----------------
SUM(disposed_count)
```

Incorrect approaches may include:

``` text
AVG(source_percent)
```

or averaging previously calculated regional or monthly percentages.

These approaches can produce inconsistent results even when all
consumers use the same Trusted Gold data.

The Semantic Metric Layer therefore creates a governed
business-definition boundary between the Gold analytical model and
downstream analytics products.

------------------------------------------------------------------------

## 3. Architecture Boundary

``` text
SILVER
   ↓
TRUSTED GOLD
   ↓
SEMANTIC METRIC LAYER
   ↓
BI / ANALYTICS PRODUCTS
```

### Layer Responsibilities

  Layer      Responsibility
  ---------- ---------------------------------------------
  Silver     Trusted records and validated data
  Gold       Trusted analytical facts and dimensions
  Semantic   Governed business metric definitions
  BI         Decision-oriented presentation and analysis

A useful mental model is:

``` text
Bronze   = Read the data
Silver   = Trust the data
Gold     = Answer business questions
Semantic = Trust the meaning
BI       = Support the decision
```

------------------------------------------------------------------------

## 4. Trusted Gold Input

Module 4 starts from the existing **Trusted Gold** model.

### FACT_SNAP_PROCESSING

**Grain**

``` text
Region × Reporting Month × Processing Type
```

**Base Measures**

-   `disposed_count`
-   `timely_count`

**Processing Types**

-   Applications
-   Redeterminations

Applications and Redeterminations must remain semantically distinct.

### FACT_SNAP_CASELOAD_MONTHLY

**Grain**

``` text
County × Reporting Month
```

**Base Measures**

-   `case_count`
-   `eligible_individual_count`
-   `eligible_under_5_count`
-   `eligible_5_17_count`
-   `eligible_18_59_count`
-   `eligible_60_64_count`
-   `eligible_65_plus_count`
-   `total_snap_payments`

### Shared Dimensions

-   `DIM_MONTH`
-   `DIM_REGION`
-   `DIM_COUNTY`

------------------------------------------------------------------------

## 5. Metric Governance Principles

### 5.1 Derived Metrics Must Be Calculated from Base Measures

Rates and averages should be recomputed from their underlying base
measures at the requested analytical context.

Previously calculated percentages or averages should not be averaged
again unless the metric contract explicitly defines that behavior.

### 5.2 Processing Types Remain Semantically Distinct

Applications and Redeterminations must remain separate when evaluating
processing timeliness.

The semantic layer must not create a misleading combined timeliness KPI
by mixing the two processing populations.

### 5.3 Aggregation Behavior Is Part of the Metric Definition

A metric is more than a formula.

Its contract must also define:

-   valid aggregation behavior
-   time behavior
-   dimensional/filter context
-   population rules
-   benchmark applicability
-   edge-case behavior

### 5.4 Benchmark Logic Is Governed Business Logic

A benchmark must only be applied to the population for which it is
defined.

For the current SNAP analytics scope:

-   **Applications:** 95% benchmark
-   **Redeterminations:** actual performance and trend; do not apply the
    95% benchmark

------------------------------------------------------------------------

## 6. Initial Governed Metric Scope

Module 4 intentionally begins with a small number of high-value metrics
rather than creating a large metric catalog.

### 6.1 Timeliness Rate

**Business Purpose**

Measure the proportion of disposed processing workload completed timely.

**Formula**

``` text
SUM(timely_count)
-----------------
SUM(disposed_count)
```

**Aggregation Behavior**

``` text
Derived / Non-additive
```

Do not use:

``` text
AVG(source_percent)
```

and do not average already-calculated regional or monthly timeliness
rates to derive a higher-level rate.

**Processing Type Rule**

Applications and Redeterminations remain separate.

**Benchmark Governance**

  Processing Type    Benchmark Treatment
  ------------------ ----------------------------------------------
  Applications       95% benchmark
  Redeterminations   Actual performance + trend; no 95% benchmark

The production Metric Contract is implemented in the semantic layer.

At the declared Processing view grain, `timeliness_rate` is exposed for
convenient row-level consumption. For any higher-level aggregation,
consumers must recompute the metric from `timely_count` and
`disposed_count` rather than averaging lower-grain rates.

**Zero-Denominator Rule**

``` text
disposed_count = 0 → timeliness_rate = NULL
```

The 2024 Trusted Gold population contains no zero-denominator Processing
rows, so this defensive rule is implemented but has no real 2024 test
row.

------------------------------------------------------------------------

### 6.2 Average Payment per Case

**Formula**

``` text
SUM(total_snap_payments)
------------------------
SUM(case_count)
```

**Aggregation Behavior**

``` text
Derived / Non-additive
```

Do not calculate higher-level Average Payment per Case using:

``` text
AVG(row-level avg_payment_per_case)
```

The metric must be recomputed from total payments and total cases for
the requested analytical context.

------------------------------------------------------------------------

## 7. Base Measure Aggregation Behavior

  Measure                       Aggregation Behavior
  ----------------------------- ------------------------
  `disposed_count`              Additive
  `timely_count`                Additive
  `timeliness_rate`             Derived / Non-additive
  `case_count`                  Semi-additive
  `eligible_individual_count`   Semi-additive
  Age-band counts               Semi-additive
  `total_snap_payments`         Additive
  `avg_payment_per_case`        Derived / Non-additive

### Time-Aggregation Rule

`case_count`, `eligible_individual_count`, and age-band counts can be
aggregated across counties **within the same reporting month**.

They must not be summed across multiple months and interpreted as unique
annual cases or unique annual people.

For example:

``` text
January cases + February cases + ... + December cases
```

does not represent unique annual SNAP cases because the same case may
appear in multiple monthly snapshots.

------------------------------------------------------------------------

## 8. Geography Governance

Module 4 inherits the geography governance established in Trusted Gold.

`DIM_REGION` contains:

-   canonical Regions `01–11`
-   legitimate combined reporting region `02/09`

`02/09` remains its own reporting region and is not split into Regions
02 and 09.

County geography continues to map only to canonical Regions 01--11.

The following non-geographic Timeliness units were intentionally
excluded from the Gold Processing Fact and therefore are not part of the
governed semantic population:

-   `CCC`
-   `DATA INT`
-   `MEPD`
-   `PERFORMANC`
-   `ST OFFICE`
-   `VIC`

Semantic metrics must use the same governed population as the Gold
model.

------------------------------------------------------------------------

## 9. Physical Implementation

Module 4 is implemented in Snowflake using a dedicated semantic schema:

``` text
SNAP_ANALYTICS
│
├── GOLD
│   ├── FACT_SNAP_PROCESSING
│   ├── FACT_SNAP_CASELOAD_MONTHLY
│   ├── DIM_MONTH
│   ├── DIM_REGION
│   └── DIM_COUNTY
│
└── SEMANTIC
    ├── VW_PROCESSING_METRICS
    └── VW_CASELOAD_METRICS
```

The `SEMANTIC` schema is the governed consumption boundary between
Trusted Gold and downstream analytics products. This separation supports
access governance/security boundaries, separation of analytical storage
from business-facing consumption, reusable metric logic, and clearer
ownership of business definitions.

The semantic layer is not tied to Power BI. Any authorized downstream
consumer can use the governed Snowflake views.

### 9.1 `VW_PROCESSING_METRICS`

**Source:** `FACT_SNAP_PROCESSING` + `DIM_REGION` + `DIM_MONTH`

**Declared Grain**

``` text
Region × Reporting Month × Processing Type
```

The view preserves Gold base measures and exposes business-friendly
region and month attributes.

Governed semantic fields include `timeliness_rate`, `benchmark_rate`,
`benchmark_gap`, and `benchmark_status`.

``` text
Applications
    benchmark_rate = 0.95
    benchmark_gap = timeliness_rate - 0.95
    benchmark_status = Meets Benchmark / Below Benchmark

Redeterminations
    benchmark_rate = NULL
    benchmark_gap = NULL
    benchmark_status = NULL
```

### 9.2 `VW_CASELOAD_METRICS`

**Source:** `FACT_SNAP_CASELOAD_MONTHLY` + `DIM_COUNTY` + `DIM_REGION` +
`DIM_MONTH`

**Declared Grain**

``` text
County × Reporting Month
```

The view exposes governed county, region, and month attributes while
preserving trusted Gold caseload measures.

``` text
avg_payment_per_case
= total_snap_payments / case_count

case_count = 0 → avg_payment_per_case = NULL
```

County geography resolves only to canonical Regions 01--11. The
Processing-only combined reporting region `02/09` does not appear in the
Caseload semantic population.

### 9.3 View vs. Materialized View Decision

Standard Snowflake Views were selected for the Module 4 MVP.

``` text
FACT_SNAP_PROCESSING         = 240 rows
FACT_SNAP_CASELOAD_MONTHLY   = 3,048 rows
```

Materialized Views are not justified as a performance optimization at
this stage. Standard Views preserve governance and maintainability
without unnecessary physical storage or refresh complexity.

------------------------------------------------------------------------

## 10. Final Semantic Validation Gate

The Final Semantic Validation Gate was executed after both semantic
views were created.

> **View Creation Success ≠ Trusted Semantic Layer.**

A semantic object is trusted only after its population, grain, base
measures, metric behavior, and governance rules reconcile to the
established contracts.

### 10.1 Processing Validation

  Validation                                             Actual Result Status
  -------------------------------------------- ----------------------- --------------------------------
  Gold row count vs Semantic row count                       240 = 240 PASS
  Gold vs Semantic `disposed_count`              3,095,222 = 3,095,222 PASS
  Gold vs Semantic `timely_count`                2,069,657 = 2,069,657 PASS
  Duplicate Region × Month × Processing Type                         0 PASS
  Applications benchmark                                           95% PASS
  Redeterminations benchmark / gap / status                       NULL PASS
  Zero `disposed_count` rows                                         0 N/A --- no 2024 edge-case data

Gold → Semantic reconciliation demonstrates that dimension enrichment
did not introduce row loss, row duplication, or base-measure distortion.

### 10.2 Processing Aggregation Validation

January 2024 Applications demonstrated the aggregation risk:

``` text
AVG(lower-grain timeliness_rate)
≈ 64.06%                         WRONG

SUM(timely_count) / SUM(disposed_count)
≈ 65.7%                          CORRECT
```

The differing results confirm that higher-grain Timeliness Rate must be
recomputed from the additive numerator and denominator.

### 10.3 Caseload Validation

  --------------------------------------------------------------------------------
  Validation                                   Actual Result Status
  ----------------------------- ---------------------------- ---------------------
  Gold row count vs Semantic                   3,048 = 3,048 PASS
  row count                                                  

  Gold vs Semantic `case_count`      18,514,565 = 18,514,565 PASS

  Gold vs Semantic                   40,356,230 = 40,356,230 PASS
  `eligible_individual_count`                                

  Gold vs Semantic                        \$696,403,662.13 = PASS
  `total_snap_payments`                     \$696,403,662.13 

  Duplicate County × Month                                 0 PASS

  Age-band reconciliation                                  0 PASS
  mismatches                                                 

  Geography                         canonical Regions 01--11 PASS
                                                        only 

  `02/09` in Caseload geography                         none PASS

  Zero `case_count` rows                                   0 N/A --- no 2024
                                                             edge-case data
  --------------------------------------------------------------------------------

### 10.4 Average Payment Aggregation Validation

January 2024 statewide results:

``` text
AVG(county-level avg_payment_per_case)
= $337.472854133                         WRONG

SUM(total_snap_payments) / SUM(case_count)
= $370.864011113                         CORRECT
```

The material difference confirms that lower-grain averages must not be
averaged to produce a higher-grain Average Payment per Case.

### 10.5 Validation Conclusion

``` text
Population / Reconciliation       PASS
Grain Uniqueness                  PASS
Base Measure Preservation         PASS
Metric Calculation                PASS
Aggregation Behavior              PASS
Benchmark Governance              PASS
Geography Governance              PASS
Age Reconciliation                PASS
Zero-Denominator Edge Cases       N/A — no 2024 test rows
```

**Final Semantic Validation Gate: PASS**

------------------------------------------------------------------------

## 11. Module 4 Deliverables

Completed Module 4 outputs:

1.  Governed Metric Contracts
2.  Metric aggregation and filter rules
3.  Benchmark governance
4.  Dedicated `SEMANTIC` Snowflake schema
5.  `VW_PROCESSING_METRICS`
6.  `VW_CASELOAD_METRICS`
7.  Final Semantic Validation Gate
8.  Module documentation and production takeaways
9.  Repository SQL structure:

``` text
sql/
└── semantic/
    ├── 01_create_semantic_schema.sql
    ├── 02_create_semantic_views.sql
    └── 03_validate_semantic.sql
```

The objective is **not** to create as many metrics as possible.

> **How to make business metrics consistent, governed, reusable, and
> trustworthy across analytics products.**

------------------------------------------------------------------------

## 12. Production Principles

> **Trusted Data ≠ Trusted Metric.**

Trusted Gold establishes confidence in analytical data. The Semantic
Metric Layer establishes confidence in business meaning.

A governed metric is not only a formula. It is a business contract
defining how a metric is calculated, aggregated, filtered, benchmarked,
and interpreted.

### Ratio-of-Sums Principle

For non-additive derived metrics:

> **Aggregate the underlying components first, then derive the metric at
> the requested grain.**

``` text
Timeliness Rate
= SUM(timely_count) / SUM(disposed_count)
≠ AVG(lower-grain timeliness_rate)

Average Payment per Case
= SUM(total_snap_payments) / SUM(case_count)
≠ AVG(lower-grain avg_payment_per_case)
```

Keeping numerator and denominator components available in the semantic
views is an intentional governance decision.

### Validation Principle

> **View Creation Success ≠ Trusted Semantic Layer.**

Semantic enrichment must preserve the trusted Gold population and base
measures while applying metric contracts consistently.

------------------------------------------------------------------------

## 13. Module 4 Closeout Status

Module 4 implementation and validation are complete.

``` text
Trusted Gold
     ↓
SEMANTIC schema
     ↓
Governed Semantic Views
     ↓
Final Semantic Validation Gate
     ↓
Trusted Semantic Layer
```

**Status: COMPLETE / CLOSED**

The next platform stage is:

``` text
Module 5 — BI Environment Health / Monitoring
```

The 2025 production batch remains intentionally out of scope until the
2024 BI environment is complete. It will later be introduced as a new
production batch for end-to-end Production Acceptance Testing.
