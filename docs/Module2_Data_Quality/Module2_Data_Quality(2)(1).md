# Module 2 --- Data Quality (Silver Layer)

## Purpose

Transform Bronze data into a **trusted Silver dataset** that is ready
for downstream analytics, data modeling, and reporting.

### Layer Responsibilities

  Layer        Responsibility
  ------------ ---------------------------
  **Bronze**   Read the data
  **Silver**   Trust the data
  **Gold**     Answer business questions

------------------------------------------------------------------------

# Module Workflow

``` text
Bronze Parquet
→ Structure Cleaning
→ Normalization
→ Data Type Conversion
→ Business Validation
→ Validation Report (JSON)
→ Validation Gate

PASS → Write Silver Parquet
FAIL → Raise ValidationError (Do NOT publish Silver)
```

# Stage 1 --- Structure Cleaning

-   Remove unexpected structural rows
-   Remove empty rows
-   Verify required columns
-   Ensure consistent row granularity

# Stage 2 --- Normalization

-   Standardize column names
-   Trim whitespace
-   Standardize text case
-   Remove formatting characters
-   Standardize date format

# Stage 3 --- Data Type Conversion

**Design Principle**

Business Meaning determines Data Type.

-   Count → Int64
-   Monetary Amount → Float64
-   Text → string (nullable)

# Stage 4 --- Business Validation

Validation Rules (MVP)

-   County Name Required
-   report_month Required
-   Required Numeric Fields
-   Non-negative Numeric Values
-   Valid Reporting Entity *(currently uses a simplified reference set)*

# Dataset-Specific Design — Timeliness

## Business Meaning and Expected Structure

The Timeliness source is a human-readable Excel report rather than a single tidy table. Each monthly worksheet contains two vertically stacked logical tables:

- **SNAP Food Benefits APPLICATIONS**
- **SNAP Food Benefits REDETERMINATIONS**

Both blocks use the source columns `Region`, `Disposed`, `Timely`, and `Percent`. The worksheet also contains report titles, blank rows, `TOTAL` rows, and source notes / definitions.

The trusted Timeliness Silver dataset must support the analytical grain:

`Reporting Month × Processing Type × Region`

Expected standardized fields:

| Field | Target Representation | Purpose |
|---|---|---|
| `reporting_month` | string, `YYYY-MM` | Reporting period; same format as Eligibility / Caseload Silver |
| `processing_type` | string | Source business category: `APPLICATIONS` or `REDETERMINATIONS` |
| `region` | string | Reporting geography / category identifier; preserve values such as `01` and `02/09` |
| `disposed_count` | integer | Disposed case count |
| `timely_count` | integer | Timely disposed case count |
| `source_percent` | float decimal rate | Source-provided percentage stored as a decimal, e.g. `38.47% → 0.3847` |
| `source_file` | string | Source lineage |

The percentage symbol is presentation formatting and is not stored in Silver.

## Timeliness Stage 1 — Structure Cleaning Rules

1. Parse the worksheet by **business section/header**, not by fixed row numbers.
2. Identify the `APPLICATIONS` and `REDETERMINATIONS` logical blocks from their section labels.
3. Validate that each block contains the expected table header: `Region`, `Disposed`, `Timely`, `Percent`. Unexpected structural changes are treated as schema drift and should not be silently mapped.
4. Derive `processing_type` from the section label.
5. Exclude report titles, blank rows, repeated table headers, notes, and definitions from analytical records. The original workbook remains preserved in Bronze.
6. Use logical section boundaries as the primary table-boundary mechanism. For the final Redetermination block, a validated `TOTAL` row may be used as the end-of-block marker.
7. Retain `TOTAL` temporarily as a reconciliation control, but do not publish it as an analytical Silver row.
8. Derive reporting month from source metadata and cross-check the filename month against the Excel report title. A critical mismatch is a structural validation failure.
9. Automated schema validation must be applied to every monthly file so schema drift is detected without manual file-by-file inspection.

## Timeliness Stage 2 — Normalization / Standardization Rules

- Preserve source business terminology for processing types; do not transform values solely for cosmetic consistency.
- Trim unnecessary whitespace from text fields.
- Preserve Region as a categorical string identifier, including leading zeros (`01`) and combined reporting values such as `02/09`.
- Preserve undocumented source categories such as `CCC`, `DATA INT`, `MEPD`, `PERFORMANC`, `ST OFFICE`, `VIC`, and `UNKNOWN`; do not infer undocumented meanings. These values are flagged for review rather than deleted.
- Standardize source column names:
  - `Disposed` → `disposed_count`
  - `Timely` → `timely_count`
  - `Percent` → `source_percent`

`source_percent` is explicitly treated as a source reconciliation field rather than the governed analytical timeliness metric.

## Timeliness Stage 3 — Data Type Conversion

| Field | Target Type | Rationale |
|---|---|---|
| `reporting_month` | string | Preserve shared `YYYY-MM` representation used by Eligibility / Caseload |
| `processing_type` | string | Categorical business field |
| `region` | string | Identifier, not a numeric measure |
| `disposed_count` | integer / nullable integer | Count |
| `timely_count` | integer / nullable integer | Count |
| `source_percent` | float / nullable float | Decimal rate, e.g. `0.3847` |
| `source_file` | string | Lineage metadata |

Before implementing percent conversion logic, inspect the actual ingested value. Excel may display `38.47%` while storing `0.3847`; conversion logic must avoid dividing an already-decimal value by 100.

## Timeliness Stage 4 — Business Validation Matrix

| Validation Rule | Expected Behavior | Severity | Silver Gate |
|---|---|---|---|
| Required `reporting_month` | Non-null | FAIL | Block |
| Required `processing_type` | Non-null | FAIL | Block |
| Required `region` | Non-null | FAIL | Block |
| Required `disposed_count` | Non-null | FAIL | Block |
| Required `timely_count` | Non-null | FAIL | Block |
| `source_percent` null | Allowed when base counts are present; reconciliation unavailable | WARNING | Allow |
| Required `source_file` | Non-null for lineage | FAIL | Block |
| Non-negative disposed count | `disposed_count >= 0` | FAIL | Block |
| Non-negative timely count | `timely_count >= 0` | FAIL | Block |
| Timely cannot exceed disposed | `timely_count <= disposed_count` | FAIL | Block |
| Zero denominator | If `disposed_count = 0`, `timely_count` must also equal `0`; rate is `NULL`, not `0%` | FAIL if violated | Block |
| Processing type domain | Only `APPLICATIONS` and `REDETERMINATIONS` are expected | FAIL | Block |
| Grain uniqueness | `reporting_month + processing_type + region` must be unique | FAIL | Block |
| Rate reconciliation | `ABS((timely_count / disposed_count) - source_percent) <= 0.00005` when denominator > 0 and source percent is present | FAIL on mismatch | Block |
| Region exception / undocumented category | `02/09`, undocumented reporting categories, and `UNKNOWN` are preserved and flagged for human review | WARNING | Allow |
| Filename vs report-title month | Must agree | FAIL | Block |
| Expected Applications block | Must exist and match expected structure | FAIL | Block |
| Expected Redeterminations block | Must exist and match expected structure | FAIL | Block |
| TOTAL reconciliation | Compare sum of extracted detail counts with source TOTAL for disposed and timely counts | PROFILE FIRST | TBD after source behavior is confirmed |

### TOTAL Reconciliation Decision

Counts should not receive an arbitrary rounding tolerance. During implementation, profile all 12 months × 2 processing blocks. If source TOTAL consistently equals the sum of extracted detail rows, promote an exact mismatch to a critical FAIL rule. If the source uses a different aggregation methodology, document the methodology and retain the reconciliation as a warning/control until the business meaning is resolved.

## Timeliness Validation Severity Principle

Validation severity is based on business impact rather than anomaly type alone:

- **FAIL** when the issue breaks the expected business grain, structural contract, base-measure integrity, or ability to trust the analytical record.
- **WARNING** when the record can still support the governed analytical calculation but contains an unresolved source limitation or missing reconciliation field.

Do not automatically correct, deduplicate, or delete unexpected records when the business meaning is unresolved.

# Validation Report

Output:

``` text
data/quality_reports/silver_validation_report.json
```

# Business-first Design Philosophy

Business Goal → Business Questions → Business Rules → Validation Rules →
Implementation

# Pipeline Architecture

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

# Current Status

| Item | Eligibility / Caseload | Timeliness |
|---|---|---|
| Framework Design | ✅ Complete | ✅ Complete |
| Structure Cleaning Design | ✅ Complete | ✅ Complete |
| Normalization Design | ✅ Complete | ✅ Complete |
| Data Type Design | ✅ Complete | ✅ Complete |
| Business Validation Design | ✅ Complete | ✅ Complete (TOTAL gate pending profiling) |
| Transformation Implementation | ✅ Existing | ⏳ Next |
| Validation Implementation | ✅ Existing | ⏳ Next |
| Validation Report / Gate | ✅ Existing framework | ⏳ Extend for Timeliness |
| Trusted Silver Publish | ⏳ Pending | ⏳ Pending |
| Automated Silver Pipeline | ✅ Existing framework | ⏳ Integrate Timeliness |
| Pipeline Health / Failure Testing | ✅ Prior framework | ⏳ Add Timeliness cases |
| Official County Reference Dataset | ⏳ Future Enhancement | N/A |
