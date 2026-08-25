# Module 2 — Data Quality (Silver Layer)

## Purpose
Transform Bronze data into a **trusted Silver dataset** ready for downstream analytics, data modeling, and reporting.

### Layer Responsibilities
| Layer | Responsibility |
|---|---|
| Bronze | Read and preserve source data |
| Silver | Transform and establish trust in the data |
| Gold | Answer governed business questions |

## Module Workflow
```text
Bronze Parquet
→ Structure Cleaning
→ Standardization
→ Data Type Conversion
→ Business Validation
→ Validation Report (JSON)
→ Validation Gate

PASS → Write Trusted Silver Parquet
FAIL → Stop publish / raise validation error
```

Decision-first workflow: **Business Meaning → Expected Structure → Cleaning Rule → Validation Rule → Implementation**

## Timeliness — Business Meaning and Expected Structure
The Timeliness source is a human-readable Excel report containing two logical tables: **SNAP Food Benefits APPLICATIONS** and **SNAP Food Benefits REDETERMINATIONS**. Both use `Region | Disposed | Timely | Percent`, with titles, blank rows, TOTAL rows, and notes/definitions around the analytical data.

Target Silver grain: **Reporting Month × Processing Type × Region**

| Field | Target Representation |
|---|---|
| `reporting_month` | string, `YYYY-MM` |
| `processing_type` | string (`Applications` / `Redeterminations`) |
| `Region` | string |
| `disposed_count` | nullable `Int64` |
| `timely_count` | nullable `Int64` |
| `source_percent` | nullable `Float64` decimal rate |
| `source_file` | string |

`source_percent` is retained for reconciliation; it is not the governed Gold timeliness metric.

## Stage 1 — Timeliness Structure Cleaning ✅
Implemented rules:
- Parse by business section/header, not fixed row positions.
- Detect both Applications and Redeterminations sections.
- Require expected header `Region | Disposed | Timely | Percent`.
- Derive `processing_type` from the section.
- Exclude titles, blank rows, repeated headers, notes, and definitions.
- Keep TOTAL outside analytical detail but retain it separately for future reconciliation.
- Do not assume Applications appears before Redeterminations.
- Preserve source rows even when measure values are missing.
- Preserve column positions when intermediate cells are missing.
- Do not depend on default DataFrame index labels.

Implementation defects found and fixed:
1. Collapsing empty cells could shift `Percent` into `Timely`.
2. Mixing DataFrame index labels with positional `.iloc` slicing could skip valid rows.

Both defects were converted into regression tests.

Verification: `tests/test_structure_cleaning.py` → **17 passed**.

## Stage 2 — Timeliness Standardization ✅
Implemented rules:
- Preserve `Applications` / `Redeterminations`.
- Trim unnecessary whitespace.
- Preserve Region as a string, including `01` and `02/09`.
- Preserve unresolved source categories such as `CCC`, `DATA INT`, `MEPD`, `PERFORMANC`, `ST OFFICE`, `VIC`, and `UNKNOWN`.
- Do not guess or silently correct undocumented meanings.
- Rename `Disposed → disposed_count`, `Timely → timely_count`, `Percent → source_percent`.
- Do not drop records because business values are missing.

## Stage 3 — Timeliness Data Type Conversion ✅
Target types:
- `reporting_month` → pandas `string`
- `processing_type` → pandas `string`
- `Region` → pandas `string`
- `disposed_count` → nullable `Int64`
- `timely_count` → nullable `Int64`
- `source_percent` → nullable `Float64`
- `source_file` → pandas `string`

Percent handling:
- `"38.47%"` → `0.3847`
- numeric `0.3847` → `0.3847`
- missing → `<NA>`
- bare numeric `38.47` → ambiguous; fail rather than silently guess.

## Stage 4 — Timeliness Business Validation ✅
| Validation Rule | Severity | Gate |
|---|---|---|
| Required analytical fields missing | FAIL | Block |
| `source_percent` missing | WARNING | Allow |
| Negative counts | FAIL | Block |
| `timely_count > disposed_count` | FAIL | Block |
| disposed = 0 and timely > 0 | FAIL | Block |
| disposed = 0 and timely = 0 | PASS; rate undefined/NULL | Allow |
| Unexpected processing type | FAIL | Block |
| Duplicate `reporting_month × processing_type × Region` | FAIL when full grain available | Block |
| Rate reconciliation outside tolerance | FAIL | Block |
| `02/09` | WARNING / documented exception | Allow |
| Unresolved Region/category | WARNING | Allow |
| TOTAL reconciliation | PROFILE FIRST | Not blocking yet |

Rate reconciliation uses `calculated_rate = timely_count / disposed_count` when disposed > 0 and compares against `source_percent` using rounding-aware tolerance of approximately `0.00005`.

A severity compatibility issue was found and fixed: warning-only Timeliness conditions were initially being counted as failures. WARNING now remains non-blocking, while unresolved categories stay visible.

## TOTAL Reconciliation — Profile First
TOTAL is retained as control metadata but excluded from analytical detail. During pipeline integration, profile:
- SUM(detail disposed_count) vs source TOTAL Disposed
- SUM(detail timely_count) vs source TOTAL Timely
for Applications and Redeterminations.

Do not block Silver on TOTAL mismatch yet. Profile all 12 months × 2 processing blocks first; promote exact mismatch to FAIL only if source behavior confirms exact reconciliation.

## Automated Test Evidence
Current combined component suite:
```text
Structure Cleaning
+ Standardization
+ Type Conversion
+ Business Validation
= 78 tests passed
```
The combined suite was independently rerun and confirmed at **78 passed**.

## AI Agent Development Workflow
```text
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

Agent responsibilities: inspect repo patterns, implement within boundaries, add/run tests, diagnose technical failures, fix defects, report assumptions.

Human responsibilities: define business meaning and acceptance criteria, set stage boundaries and severity, inspect business behavior, validate real source/output, approve unresolved assumptions, and decide whether data is trustworthy enough to publish.

## Validation Report
Target output:
```text
data/quality_reports/silver_validation_report.json
```
Timeliness validation logic is implemented, but a Timeliness Validation Report has **not yet been generated through an end-to-end Silver pipeline run**.

Status: **⏳ Pipeline integration pending**

## Validation Gate
Target behavior:
```text
PASS → publish Trusted Silver
WARNING only → allow publish while retaining warnings
FAIL → do not publish; preserve validation evidence; raise pipeline error
```
Status: **⏳ Timeliness integration pending**

## Pipeline Architecture
```text
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

Pipeline responsibility: **Call → Collect → Decide → Publish**

## Current Status — August 24, 2026
| Item | Eligibility / Caseload | Timeliness |
|---|---|---|
| Framework Design | ✅ Complete | ✅ Complete |
| Structure Cleaning | ✅ Complete | ✅ Complete |
| Standardization | ✅ Complete | ✅ Complete |
| Data Type Conversion | ✅ Complete | ✅ Complete |
| Business Validation | ✅ Complete | ✅ Complete |
| Component Tests | ✅ Existing | ✅ 78-test combined suite passed |
| Validation Report | ✅ Existing framework | ⏳ End-to-end integration pending |
| Validation Gate | ✅ Existing framework | ⏳ End-to-end integration pending |
| Trusted Silver Publish | ⏳ Final publish pending | ⏳ Pending |
| Automated Silver Pipeline | ✅ Existing framework | ⏳ Timeliness integration next |
| TOTAL Reconciliation | N/A | 🔎 PROFILE FIRST |
| County → Region Reference | ⏳ Pending validation | N/A |

## Immediate Next Step
Do **not** return to Gold implementation yet.

```text
Inspect silver_pipeline.py
→ Design smallest Timeliness integration
→ Carry reporting_month / source_file metadata
→ Preserve timeliness_section_totals for profiling
→ Generate Validation Report
→ Apply Validation Gate
→ Run end-to-end Timeliness pipeline
→ Human validate real source/output
→ Publish Trusted Timeliness Silver
→ Final Module 2 closeout
```

After Timeliness Silver and Eligible/Caseload Silver are fully published and geography dependencies are validated, return to Module 3 for Physical Gold implementation.
