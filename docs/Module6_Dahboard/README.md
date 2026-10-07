# Module 6 — Tableau Dashboard / Decision Experience

## Business Goal

Support SNAP program managers in reviewing 2024 processing performance and monthly service volume. The intended decisions are to identify months and reporting regions requiring performance review, and to review county caseload and payment trends for follow-up planning.

The dashboards identify where and when to investigate. They do not establish causes or determine staffing allocations.

## Architecture

Tableau consumes existing Snowflake Semantic views:
- `SNAP_ANALYTICS.SEMANTIC.VW_PROCESSING_METRICS`
- `SNAP_ANALYTICS.SEMANTIC.VW_CASELOAD_METRICS`

These views continue to read Trusted GOLD. The completed dbt extension is a separate representative processing transformation slice with outputs in DBT_SAKI.

Two Tableau data sources preserve different grains:
- Processing: Region × Reporting Month × Processing Type.
- Caseload: County × Reporting Month.

The facts are not directly joined. Local extracts support development and demonstration without an active Snowflake connection; refresh requires Snowflake access. The upstream Python workflow is manually triggered, with no automated end-to-end orchestration.

## Dashboard Design

### Processing Overview

- KPI cards show Applications timeliness, target gap, and disposed volume.
- Monthly lines compare Applications and Redeterminations over time.
- Region bars show lower Applications timeliness first.
- The 95% benchmark applies to Applications only. No governed Redeterminations benchmark is applied.

![Processing Overview](screenshots/processing_dashboard_2024.png)

### Caseload Overview

- Separate monthly lines show cases, eligible individuals, and SNAP payments.
- A shared County filter keeps all three charts on the same geographic scope.
- Default County selection: All.

![Caseload Overview](screenshots/caseload_dashboard_2024.png)

Lines support temporal comparison; sorted bars support ranking. Maps were not selected because the primary questions concern trends and performance comparison rather than spatial clusters or adjacency.

## Metric Rules

- Timeliness = `SUM(timely_count) / SUM(disposed_count)`; do not average lower-grain rates.
- Applications target gap is expressed in percentage points.
- Cases and eligible individuals are monthly counts. Summing months does not produce annual distinct cases or people.
- If average payment per case is used, calculate `SUM(total_snap_payments) / SUM(case_count)` rather than averaging county-level payment rates.
- Processing includes 10 reporting regions × 12 months × 2 types = 240 rows. Reporting regions: 01, 02/09, 03, 04, 05, 06, 07, 08, 10, 11.
- Excluded non-geographic units: CCC, DATA INT, MEPD, PERFORMANC, ST OFFICE, VIC.

## Validation Record

Reconciliation compared Tableau with the same Semantic views using matching scope, aggregation, and display precision. This validates consumption of governed warehouse metrics; it is not an independent audit of original source files.

| Check | Observed result |
|---|---|
| Applications annual KPI | Matched: 68.2%, 2,002,129 disposed, −26.84 pp target gap |
| Applications region rates and ordering | All 10 reporting regions matched |
| Monthly timeliness, both types | All 24 values matched to 1 decimal place |
| Statewide monthly cases | All 12 months matched |
| Statewide monthly eligible individuals | All 12 months matched |
| Statewide monthly payments | All 12 months matched at whole-dollar precision |
| Statewide county coverage | 254 rows and 254 distinct counties per month |
| Shared County filter | Confirmed across all three caseload charts |
| Harris monthly cases | All 12 months matched |

Harris individuals and payments were not numerically reconciled. Payments were not reconciled to cents. Validation was concluded at the agreed scope; no further tests are required for this closeout.

An earlier offline check confirmed that worksheets remained usable from saved extracts without Snowflake sign-in. A Data Source page sign-in prompt does not by itself demonstrate that worksheet extracts are unavailable.

## Decision Coverage and Limits

| Business question | Current support | Boundary |
|---|---|---|
| Which months have Applications timeliness below 95%? | Monthly Applications line and reference line | Statewide month comparison |
| Which regions have lower Applications timeliness? | Sorted annual region bars | Annual ranking; not a complete Region × Month assessment |
| How do Applications and Redeterminations change? | Two monthly trend lines | Descriptive trends, not causal explanation |
| How do county cases, individuals, and payments change? | Three trends and shared County filter | Explore a selected county; no automatic ranking of all counties by growth |
| Where should management investigate first? | Low rates and changes flag review candidates | Regional workload, staffing, backlog, and case complexity are needed for resource-allocation decisions |

The current dashboards support screening and investigation prioritization. Rate-only region ranking should not be interpreted as a final resource-allocation priority. Low rate and high late-case volume answer different questions.

Future additions should follow a specific unmet decision need, rather than increasing chart count. Potential examples include regional late-case volumes, a Region × Month detail view, or county growth rankings. These are not implemented or required in this module closeout.

## Deliverables and Closeout

- Workbook and local processing/caseload extracts retained by the project owner.
- Two dashboard PNGs exported by the project owner.
- This README: business purpose, design rationale, metric rules, validation scope, and decision limits.

Place this file at `docs/Module6_Dashboard/README.md` and the PNGs under its `screenshots/` folder. The images are relative references and are not bundled into this downloaded Markdown file.

The previously executed reconciliation SQL can be retained as `validation.sql`; that file has not been included in this deliverable. Documentation and screenshots are not yet confirmed committed to GitHub. The latest workbook screenshot showed a `.twb` recent-file entry, so final packaged `.twbx` retention has not been independently confirmed from the file bytes.

Scope remains 2024 only. Modules 1–5 are closed; dbt remains a separately completed extension. Repository closeout precedes Module 7 — Interview Lab.
