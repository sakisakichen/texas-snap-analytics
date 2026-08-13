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

  Item                                Status
  ----------------------------------- -----------------------
  Framework Design                    ✅ Complete
  Structure Cleaning                  ✅ Complete
  Normalization                       ✅ Complete
  Data Type Conversion                ✅ Complete
  Business Validation                 ✅ Complete
  Validation Report (JSON)            ✅ Complete
  Validation Gate                     ✅ Complete
  Silver Pipeline                     ✅ Complete
  Unit Tests                          ✅ Complete
  Production Troubleshooting          ✅ Complete
  Official County Reference Dataset   ⏳ Future Enhancement
