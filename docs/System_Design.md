# System Design

# Research Data Fulfillment Platform

**Version:** MVP 1.0

------------------------------------------------------------------------

# 1. Overview

The platform separates operational reporting from analytical workloads
by transforming approved operational exports into standardized,
validated research datasets.

The design emphasizes reusability, consistency, and data quality rather
than one-off manual reporting.

------------------------------------------------------------------------

# 2. Business Workflow

``` text
External Research Request
            │
Government Approval
            │
Research Data Fulfillment Platform
            │
Approved Research Dataset
            │
External Organization
```

------------------------------------------------------------------------

# 3. Technical Architecture

``` text
Legacy SQL Server
        │
 Monthly Export
        │
 Shared Folder
        │
Snowflake Bronze        (Technical Validation)
        │
Snowflake Silver        (Business Validation)
        │
Snowflake Gold          (Analytical Validation)
       / \
      /   \
Approved Research Dataset    Internal Analytics Dashboard
      │
 Excel / CSV
```

> Validation is performed at every layer but is intentionally shown as a
> supporting capability rather than the primary data flow.

------------------------------------------------------------------------

# 4. Data Flow

  Stage               Purpose
  ------------------- -------------------------------------------------
  Legacy SQL Server   Operational reporting database
  Monthly Export      Approved data extracted from legacy environment
  Shared Folder       Landing location for exported files
  Bronze              Raw ingestion with minimal transformation
  Silver              Standardized, cleaned, and conformed data
  Gold                Business-ready research datasets
  Consumers           Research exports and internal analytics

------------------------------------------------------------------------

# 5. High-Level Data Model

## Fact Tables

-   SNAP Applications
-   TANF Applications

## Dimension Tables

-   Date
-   County
-   Program

Future dimensions may include Household, Demographics, and Geographic
Region.

------------------------------------------------------------------------

# 6. Technology Stack

  Component         Technology
  ----------------- -------------------
  Source            Legacy SQL Server
  File Landing      Shared Folder
  Data Warehouse    Snowflake
  Transformation    SQL + Python
  Data Validation   SQL + Python
  Visualization     Tableau
  Export            Excel / CSV

------------------------------------------------------------------------

# 7. Design Principles

-   Separate operational systems from analytical workloads.
-   Standardize data before publishing.
-   Validate data throughout the pipeline.
-   Build reusable research datasets.
-   Support multiple downstream consumers from a single Gold layer.

------------------------------------------------------------------------

# 8. Future Evolution

The MVP focuses on manual monthly exports. Future versions may include:

-   Automated ingestion pipeline
-   Metadata catalog
-   Configurable validation framework
-   Semantic layer
-   Data quality monitoring
-   Request tracking
-   Self-service research dataset generation
