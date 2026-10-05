# Module 1 — Source Ingestion (Bronze Layer)

## Purpose
The purpose of this module is to ingest source files into the SNAP Analytics Platform while preserving the original business data.

This module prepares a machine-readable Bronze dataset that can be safely processed by downstream modules.

---

# Layer Responsibility

| Layer | Responsibility |
|-------|----------------|
| Raw | Preserve the original source files exactly as received |
| Bronze | Read and preserve the business data while adding ingestion metadata |
| Silver | Transform the data into a trustworthy analytical dataset |
| Gold | Answer business questions |

---

# Design Principles

- Preserve original business values.
- Do not modify business data.
- Parse the source into a machine-readable format.
- Add only ingestion metadata (e.g. source_file, report_month).
- Keep transformations minimal.
- Prepare the dataset for downstream processing.

---

# Module Workflow

```text
Raw Source Files
        │
        ▼
Read Source Files
        │
        ▼
Extract Tabular Data
        │
        ▼
(Optional) Data Profiling
        │
        ▼
Add Ingestion Metadata
        │
        ▼
Generate Bronze Dataset
```

---

# Phase 1 — Read Source Files

## Goal

Load source files without changing business values.

### Responsibilities

- Read source files
- Identify worksheets
- Parse source layout
- Extract tabular data
- Preserve business values

---

# Phase 2 — Data Profiling

## Goal

Understand the incoming dataset before downstream processing.

### Core Question

> What does this dataset look like?

### Profiling

- Dataset overview
- Schema profiling
- Content profiling
- Generate profiling report

**Profiling is descriptive only.**

It does **not** modify data or perform business validation.

---

# Phase 3 — Add Ingestion Metadata

## Goal

Add metadata that improves lineage without changing business values.

### Examples

- report_month
- source_file
- ingestion_timestamp (future)

---

# Outputs

| Output | Description |
|--------|-------------|
| Bronze Dataset | Machine-readable dataset preserving business values |
| Profiling Report | Dataset assessment |
| Dataset Statistics | Rows, columns, worksheets |
| Schema Summary | Schema overview |
| Warning Messages | Profiling warnings |

---

# Out of Scope

These belong to Module 2 (Data Quality):

- Structure Cleaning
- Normalization
- Data Type Conversion
- Business Validation
- Validation Report

---

# Relationship with Module 2

```text
Raw
        │
        ▼
Module 1 (Bronze)
Source Ingestion
        │
        ▼
Bronze Dataset
        │
        ▼
Module 2 (Silver)
Data Quality
        │
        ▼
Silver Dataset
```

---

# Why This Module Matters

Module 1 creates a reliable Bronze dataset by preserving original business values, adding ingestion metadata, and providing an initial understanding of incoming data before any transformations occur.
