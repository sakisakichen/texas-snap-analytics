# Module 2 --- Data Quality (Silver Layer)

## Purpose

Transform Bronze data into a **trustworthy Silver dataset** for
downstream analytics.

### Layer Responsibilities

  Layer        Responsibility
  ------------ -------------------------------
  **Bronze**   **Read the data**
  **Silver**   **Trust the data**
  **Gold**     **Answer business questions**

------------------------------------------------------------------------

# Module Workflow

``` text
Bronze Dataset
      │
      ▼
Structure Cleaning
      │
      ▼
Normalization
      │
      ▼
Data Type Conversion
      │
      ▼
Validation
      │
      ▼
Validation Report
      │
      ▼
Silver Dataset
```

------------------------------------------------------------------------

# Stage 1 --- Structure Cleaning

## Goal

Ensure the dataset has the correct structure before business processing.

### Typical Responsibilities

-   Remove unexpected structural rows
-   Remove empty records
-   Verify required columns exist
-   Ensure record granularity is consistent

> Note: Bronze is responsible for reading and profiling source files.
> Silver begins with structural cleaning for analytics readiness.

------------------------------------------------------------------------

# Stage 2 --- Normalization

## Goal

**Ensure a consistent representation of the data.**

### Generic Rules

-   Column Name Standardization
-   Trim Whitespace
-   Standardize Text Case
-   Remove Formatting Characters
-   Standardize Date Format

### Example

Before

``` text
" texas "
```

↓

After

``` text
"Texas"
```

Business meaning remains unchanged.

------------------------------------------------------------------------

# Stage 3 --- Data Type Conversion

## Goal

Convert normalized values into the correct data types.

### Examples

-   String → Integer
-   String → Float
-   String → Datetime
-   String → Boolean

------------------------------------------------------------------------

# Stage 4 --- Validation

## Goal

**Ensure the data is trustworthy for its intended business use.**

## Validation Framework V1

### 1. Required Fields

Verify all required business fields exist.

### 2. Data Type Validation

Verify fields have the expected data types.

### 3. Basic Range Validation

Verify values fall within acceptable business ranges.

------------------------------------------------------------------------

# Business-first Design Philosophy

``` text
Business Goal
      │
      ▼
Business Questions
      │
      ▼
Business Rules
      │
      ▼
Validation Rules
      │
      ▼
Implementation
```

Validation rules should always originate from business requirements
rather than arbitrary technical checks.

------------------------------------------------------------------------

# Key Design Principles

## Bronze

**Read the data.**

## Silver

**Trust the data.**

## Gold

**Answer business questions.**

------------------------------------------------------------------------

## Normalize

Ensure a consistent representation of the data.

## Convert

Convert normalized values into the correct data types.

## Validate

Ensure the data is trustworthy for its intended business use.

------------------------------------------------------------------------

# Current Status

  Item                   Status
  ---------------------- -------------
  Framework Design       ✅ Complete
  Structure Cleaning     ⬜ Planned
  Normalization          ⬜ Planned
  Data Type Conversion   ⬜ Planned
  Validation Rules       ⬜ Planned
  Validation Report      ⬜ Planned
  Implementation         ⬜ Planned
