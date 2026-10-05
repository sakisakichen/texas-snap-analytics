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

A full production Metric Contract will be finalized during Module 4.

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

## 9. Physical Implementation --- Design in Progress

The physical implementation will be selected after the metric contracts
are finalized.

Current architectural direction:

``` text
GOLD
   ↓
SEMANTIC
   ↓
BI
```

A dedicated `SEMANTIC` schema is being considered as the governed
consumption boundary between Trusted Gold and downstream BI products.

Potential implementation approaches include:

-   Snowflake Views
-   BI semantic model logic
-   a combination of warehouse and BI semantic responsibilities

The implementation will not be selected simply because a technology
feature exists. The design must support metric consistency, reuse,
governance, and maintainability.

### Current Performance Consideration

The 2024 Gold dataset is small:

``` text
FACT_SNAP_PROCESSING         = 240 rows
FACT_SNAP_CASELOAD_MONTHLY   = 3,048 rows
```

Therefore, Materialized Views are not currently justified as a
performance optimization.

------------------------------------------------------------------------

## 10. Semantic Validation Requirements

Validation will be implemented after the semantic objects and metric
contracts are finalized.

The validation gate must demonstrate that semantic metrics:

-   reconcile to Trusted Gold base measures
-   preserve required processing populations
-   preserve required grain and filter behavior
-   apply aggregation rules correctly
-   apply benchmark logic only to valid populations
-   handle denominator and edge cases consistently
-   produce consistent results across supported analytical contexts

The principle from Module 3 continues to apply:

> **Build Success ≠ Trusted Output.**

Creating a semantic object successfully does not make the metric
trusted.

The metric must pass its semantic validation contract before it is
considered ready for downstream BI use.

------------------------------------------------------------------------

## 11. Module 4 Deliverables

Expected Module 4 outputs:

1.  Governed Metric Contracts
2.  Metric aggregation and filter rules
3.  Benchmark governance
4.  Semantic-layer physical design
5.  Snowflake / BI implementation
6.  Semantic validation gate
7.  Module documentation
8.  Production and interview takeaways

The objective is **not** to create as many metrics as possible.

The objective is to demonstrate:

> **How to make business metrics consistent, governed, reusable, and
> trustworthy across analytics products.**

------------------------------------------------------------------------

## 12. Production Principles

> **Trusted Data ≠ Trusted Metric.**

Trusted Gold establishes confidence in analytical data.

The Semantic Metric Layer establishes confidence in business meaning.

A governed metric is not only a formula. It is a business contract
defining how a metric is calculated, aggregated, filtered, benchmarked,
and interpreted.

------------------------------------------------------------------------

## 13. Next Design Decision

The next Module 4 task is to define the first complete production Metric
Contract:

``` text
Timeliness Rate
```

The contract will establish:

``` text
Business Definition
        ↓
Numerator / Denominator
        ↓
Grain
        ↓
Aggregation Behavior
        ↓
Filter Context
        ↓
Processing Type Rules
        ↓
Benchmark Semantics
        ↓
Edge Cases
        ↓
Validation
```

Only after the metric contract is finalized will the physical Snowflake
/ BI implementation be selected.
