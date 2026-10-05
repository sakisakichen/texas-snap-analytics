# dbt Productionization Extension

## Purpose

Existing Snowflake SQL already builds Trusted Gold successfully.

This extension adds a repeatable workflow for managing warehouse transformations through:

- Modular SQL models
- Source definitions and dependency management
- Automated data tests
- Model and column documentation
- Lineage
- Git version control

Existing business logic remains the baseline. Modules 1–5 are preserved.

This extension sits between Module 5 and **Module 6 — Tableau Dashboard**.

## Architecture and Scope

dbt Cloud executes warehouse SQL in Snowflake. Development outputs are isolated in `SNAP_ANALYTICS.DBT_SAKI`.

| Component | Responsibility |
|---|---|
| Local Python | File parsing, normalization, cleaning, and pre-warehouse validation |
| Snowflake SILVER | Existing Trusted Silver source tables |
| dbt staging | Consistent source-column interface |
| dbt marts | Dimensions and the processing fact |
| dbt tests | Repeatable data-quality and business-rule checks |
| Existing SEMANTIC | Governed consumption interface over Trusted Gold |

The Python pipeline is manually executed on Mac. There is no automated end-to-end orchestration.

### Implemented Models

| Model | Materialization | Purpose |
|---|---|---|
| `stg_snap_timeliness` | View | Standardize the Timeliness source interface |
| `dim_month` | Table | Reporting months from Eligibility and Timeliness |
| `dim_region` | Table | Governed geographic and combined reporting regions |
| `fact_snap_processing` | Table | Governed SNAP processing measures |

Eligibility and County Region Reference are read-only dependencies needed to reproduce the existing dimensions.

Caseload transformations, the county dimension, and monitoring were not migrated.

## Business Rules

### Fact Grain

**Region × Reporting Month × Processing Type**

### Governed Reporting Population

Included regions:

`01`, `02/09`, `03`, `04`, `05`, `06`, `07`, `08`, `10`, `11`

Excluded non-geographic units:

`CCC`, `DATA INT`, `MEPD`, `PERFORMANC`, `ST OFFICE`, `VIC`

Processing types:

- Applications
- Redeterminations

The trusted 2024 population is:

**10 regions × 12 months × 2 processing types = 240 rows**

`DIM_REGION` contains 12 rows: geographic regions 01–11 plus combined reporting region `02/09`, assigned `region_key = 12`. The processing fact uses 10 reporting regions.

### Timeliness Metric

```sql
SUM(timely_count) / NULLIF(SUM(disposed_count), 0)
```

Do not average source percentages or lower-grain rates.

- **Applications benchmark:** 95%
- **Redeterminations benchmark:** No governed benchmark

## Reconciliation Against Trusted Gold

Existing `SNAP_ANALYTICS.GOLD` is the validation baseline.

The aggregate comparison confirmed matching results:

| Measure | Trusted Gold | dbt Development |
|---|---:|---:|
| Fact rows | 240 | 240 |
| Reporting regions | 10 | 10 |
| Reporting months | 12 | 12 |
| Processing types | 2 | 2 |
| Disposed cases | 3,095,222 | 3,095,222 |
| Timely cases | 2,069,657 | 2,069,657 |

Final reconciliation evidence remains to be confirmed for:

- Fact row-level equality, including keys, measures, and duplicate counts
- Month dimension keys and attributes
- Region dimension keys and attributes

Matching aggregate totals alone does not prove row-level equality.

## Automated Tests

### Generic Tests

Configured in `dbt/models/marts/schema.yml`:

- `not_null` — required keys and fact measures
- `unique` — dimension keys and business identifiers
- `relationships` — fact keys must exist in their dimensions

### Custom SQL Tests

| Test | Rule |
|---|---|
| `assert_processing_counts_valid.sql` | Counts cannot be negative; timely counts cannot exceed disposed counts |
| `assert_processing_grain_unique.sql` | Region × Month × Processing Type cannot contain duplicate rows |

SQL data tests return violating rows. **Zero violating rows means PASS.**

## Build and Documentation

These commands completed successfully in dbt Cloud Studio:

```bash
dbt test --select dim_month dim_region fact_snap_processing
dbt test --select fact_snap_processing
dbt build
dbt docs generate
```

`dbt build` creates models and executes tests in dependency order.

YAML contains model and column descriptions. The Studio lineage graph displays dependencies defined through `source()` and `ref()`.

## Semantic Layer Boundary

Existing Semantic views continue to read Trusted Gold:

- `SNAP_ANALYTICS.SEMANTIC.VW_PROCESSING_METRICS`
- `SNAP_ANALYTICS.SEMANTIC.VW_CASELOAD_METRICS`

They have not been repointed to `DBT_SAKI`.

This extension demonstrates a tested development implementation. A production cutover has not been performed.

## Evidence to Retain

- [ ] Final reconciliation results
- [ ] Full dbt build and test results
- [ ] Processing model lineage screenshot

Generated dbt `target/` artifacts and logs are reproducible outputs. Credentials and private keys must remain outside version control.

## Production Takeaway

Working SQL defines transformation logic. dbt adds a repeatable workflow for building, testing, documenting, and tracing that logic.

This extension preserves governed business definitions while making dependencies and validation rules explicit.


## Final Validation — October 5, 2026

Row-level reconciliation against Trusted GOLD passed:

| Model | Difference Count |
|---|---:|
| FACT_SNAP_PROCESSING | 0 |
| DIM_MONTH | 0 |
| DIM_REGION | 0 |

All compared column values and row multiplicities match.
dbt build and tests passed; documentation and lineage were reviewed.
The implementation was merged into main.

Status: COMPLETE / CLOSED.

dbt outputs remain in DBT_SAKI. Existing SEMANTIC views continue
to use Trusted GOLD. Pre-warehouse Python execution remains manua

## Next Step

Complete reconciliation evidence and repository review, then proceed to **Module 6 — Tableau Dashboard / Decision Experience**.
