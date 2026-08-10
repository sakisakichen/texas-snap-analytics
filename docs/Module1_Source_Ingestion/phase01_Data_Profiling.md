
# Module 01 - Data Profiling

## Overview

Data Profiling is the first analytical checkpoint in the SNAP Analytics Platform.

Its purpose is to understand the structure, completeness, and overall quality of incoming datasets **before** applying business rules or data transformations.

**Core Question**

> What does this dataset look like?

---

# Objectives

- Understand the overall structure of the incoming dataset.
- Detect schema changes before downstream processing.
- Identify basic data quality issues early.
- Generate a standardized profiling report for analysts and data engineers.

---

# Pipeline Position

```text
Receive Source Data
        │
        ▼
Data Profiling
        │
        ▼
Data Validation
        │
        ▼
Transformation
        │
        ▼
Semantic Layer
        │
        ▼
Dashboard
```

---

# Scope

## In Scope

- Dataset overview
- Schema profiling
- Content profiling
- Profiling report generation

## Out of Scope

The following belong to **Module 02 – Data Validation**:

- Business rule validation
- County validation
- KPI validation
- Cross-table reconciliation
- Threshold checking

---

# Inputs

| Input | Description |
|-------|-------------|
| Source Dataset | Excel file received from external reporting source |

---

# Outputs

| Output | Description |
|--------|-------------|
| Profiling Report | Summary of dataset structure and quality |
| Dataset Statistics | Rows, columns, worksheets |
| Schema Summary | Column names, data types, schema changes |
| Data Summary | Nulls, duplicates, ranges, distinct values |
| Warning Messages | Potential issues requiring attention |

---

# Core Components

## 1. Dataset Overview

### Purpose

Understand the overall size and composition of the dataset.

### Checks

| Check | Description |
|--------|-------------|
| Row Count | Total number of records |
| Column Count | Total number of columns |
| Worksheet Count | Number of worksheets in the Excel file |

---

## 2. Schema Profiling

### Purpose

Understand the dataset structure and detect schema changes.

### Checks

| Check | Description |
|--------|-------------|
| Column Names | Available columns |
| Data Types | Inferred data types |
| Missing Columns | Expected columns not found |
| New Columns | Unexpected columns detected |

---

## 3. Content Profiling

### Purpose

Understand the overall quality of data values.

### Checks

| Check | Description |
|--------|-------------|
| Null Count | Missing values |
| Duplicate Count | Duplicate records |
| Distinct Values | Number of unique values |
| Numeric Range | Minimum and maximum values |
| Date Range | Earliest and latest dates |

---

# Workflow

```text
Receive Source Data
        │
        ▼
Dataset Overview
        │
        ▼
Schema Profiling
        │
        ▼
Content Profiling
        │
        ▼
Generate Profiling Report
        │
        ▼
Pass Dataset to Data Validation
```

---

# Sample Profiling Report

```text
===========================================
SNAP DATA PROFILING REPORT
===========================================

Dataset
--------------------------------
Rows              : 254
Columns           : 15
Worksheets        : 3

Schema Summary
--------------------------------
✓ All expected columns found
⚠ New column detected: Pending

Content Summary
--------------------------------
Null Values       : 2
Duplicate Records : 0
Date Range        : 2025-01-01 ~ 2025-01-31

Warnings
--------------------------------
• New column: Pending
• 2 null values detected

Status
--------------------------------
PASS
```

---

# Design Decisions

- Separate **Data Profiling** from **Data Validation**.
- Keep profiling descriptive rather than prescriptive.
- Detect structural issues before business validation.
- Produce a standardized report for downstream modules.

---

# Future Enhancements

- File metadata management
- Historical profiling comparison
- Schema version tracking
- Automated profiling dashboard
- Data drift monitoring

---

# Why This Module Matters

Without profiling, downstream transformations may fail silently because of unexpected schema changes, missing values, or abnormal data patterns.

Data Profiling serves as the first quality checkpoint, allowing analysts and data engineers to understand incoming datasets before applying business logic.
