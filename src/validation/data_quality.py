"""Reusable data quality helpers for the Bronze-to-Silver pipeline."""

from __future__ import annotations

import re
from typing import Any, Dict, List

import pandas as pd

VALID_TIMELINESS_PROCESSING_TYPES = {"Applications", "Redeterminations"}
TIMELINESS_WARNING_REGIONS = {"CCC", "DATA INT", "MEPD", "PERFORMANC", "ST OFFICE", "VIC", "UNKNOWN"}


def _is_timeliness_dataset(df: pd.DataFrame) -> bool:
    """Detect Timeliness-style data by the expected analytical grain and field names."""
    timeliness_columns = {"processing_type", "Region", "disposed_count", "timely_count"}
    present = timeliness_columns.intersection(df.columns)
    return len(present) >= 2 and ("processing_type" in df.columns or "disposed_count" in df.columns)


def _validate_timeliness_required_fields(df: pd.DataFrame) -> Dict[str, Any]:
    """Require Timeliness analytical fields when present in the current contract."""
    if not _is_timeliness_dataset(df):
        return {"rule": "Timeliness Required Fields", "status": "PASS", "failed_rows": 0}

    required_columns = ["processing_type", "Region", "disposed_count", "timely_count"]
    for column in ["reporting_month", "source_file"]:
        if column in df.columns:
            required_columns.append(column)

    if any(column not in df.columns for column in required_columns):
        return {"rule": "Timeliness Required Fields", "status": "FAIL", "failed_rows": len(df)}

    failed_rows = int(df[required_columns].isna().any(axis=1).sum())
    return {
        "rule": "Timeliness Required Fields",
        "status": "PASS" if failed_rows == 0 else "FAIL",
        "failed_rows": failed_rows,
    }


def _validate_timeliness_source_percent_warning(df: pd.DataFrame) -> Dict[str, Any]:
    """Missing source_percent should warn rather than block Timeliness Silver."""
    if not _is_timeliness_dataset(df):
        return {"rule": "Timeliness Source Percent Warning", "status": "PASS", "failed_rows": 0}

    if "source_percent" not in df.columns:
        return {
            "rule": "Timeliness Source Percent Warning",
            "status": "WARNING",
            "failed_rows": int(df.shape[0]),
            "message": "source_percent column missing; reconciliation metadata not yet available.",
        }

    failed_rows = int(df["source_percent"].isna().sum())
    return {
        "rule": "Timeliness Source Percent Warning",
        "status": "WARNING" if failed_rows > 0 else "PASS",
        "failed_rows": failed_rows,
    }


def _validate_timeliness_non_negative_counts(df: pd.DataFrame) -> Dict[str, Any]:
    """Timeliness counts must be non-negative when present."""
    if not _is_timeliness_dataset(df):
        return {"rule": "Timeliness Non-negative Counts", "status": "PASS", "failed_rows": 0}

    available_columns = [column for column in ["disposed_count", "timely_count"] if column in df.columns]
    if not available_columns:
        return {"rule": "Timeliness Non-negative Counts", "status": "PASS", "failed_rows": 0}

    failed_rows = int(df[available_columns].lt(0).any(axis=1).sum())
    return {
        "rule": "Timeliness Non-negative Counts",
        "status": "PASS" if failed_rows == 0 else "FAIL",
        "failed_rows": failed_rows,
    }


def _validate_timeliness_timeline_limit(df: pd.DataFrame) -> Dict[str, Any]:
    """Ensure timely_count does not exceed disposed_count when both are available."""
    if not _is_timeliness_dataset(df):
        return {"rule": "Timeliness Count Relationship", "status": "PASS", "failed_rows": 0}

    if "disposed_count" not in df.columns or "timely_count" not in df.columns:
        return {"rule": "Timeliness Count Relationship", "status": "PASS", "failed_rows": 0}

    valid_mask = df["disposed_count"].notna() & df["timely_count"].notna()
    failed_rows = int((df.loc[valid_mask, "timely_count"] > df.loc[valid_mask, "disposed_count"]).sum())
    return {
        "rule": "Timeliness Count Relationship",
        "status": "PASS" if failed_rows == 0 else "FAIL",
        "failed_rows": failed_rows,
    }


def _validate_timeliness_zero_denominator_rule(df: pd.DataFrame) -> Dict[str, Any]:
    """A zero disposed_count row is only valid when timely_count is also zero."""
    if not _is_timeliness_dataset(df):
        return {"rule": "Timeliness Zero Denominator Rule", "status": "PASS", "failed_rows": 0}

    if "disposed_count" not in df.columns or "timely_count" not in df.columns:
        return {"rule": "Timeliness Zero Denominator Rule", "status": "PASS", "failed_rows": 0}

    valid_mask = df["disposed_count"].notna() & df["timely_count"].notna()
    if not valid_mask.any():
        return {"rule": "Timeliness Zero Denominator Rule", "status": "PASS", "failed_rows": 0}

    failed_mask = df.loc[valid_mask, "disposed_count"].eq(0) & df.loc[valid_mask, "timely_count"].gt(0)
    failed_rows = int(failed_mask.sum())
    return {
        "rule": "Timeliness Zero Denominator Rule",
        "status": "PASS" if failed_rows == 0 else "FAIL",
        "failed_rows": failed_rows,
    }


def _validate_timeliness_processing_type(df: pd.DataFrame) -> Dict[str, Any]:
    """Only allow the documented Timeliness processing types."""
    if "processing_type" not in df.columns:
        return {"rule": "Timeliness Processing Type", "status": "PASS", "failed_rows": 0}

    values = df["processing_type"].astype(str).str.strip()
    failed_rows = int((~values.isin(VALID_TIMELINESS_PROCESSING_TYPES)).sum())
    return {
        "rule": "Timeliness Processing Type",
        "status": "PASS" if failed_rows == 0 else "FAIL",
        "failed_rows": failed_rows,
    }


def _validate_timeliness_region_warnings(df: pd.DataFrame) -> Dict[str, Any]:
    """Flag unresolved or undocumented region categories without deleting them from the dataset."""
    if "Region" not in df.columns:
        return {"rule": "Timeliness Region Warning", "status": "PASS", "failed_rows": 0}

    region_values = df["Region"].dropna().astype(str).str.strip()
    if region_values.empty:
        return {"rule": "Timeliness Region Warning", "status": "PASS", "failed_rows": 0}

    expected_region_mask = region_values.str.fullmatch(r"\d{2}(?:/\d{2})?", na=False)
    warning_mask = region_values.isin(TIMELINESS_WARNING_REGIONS)
    failed_rows = int(region_values[warning_mask].shape[0])
    if failed_rows > 0:
        return {
            "rule": "Timeliness Region Warning",
            "status": "WARNING",
            "failed_rows": failed_rows,
        }

    unresolved = region_values[~expected_region_mask & ~warning_mask]
    failed_rows = int(unresolved.shape[0])
    return {
        "rule": "Timeliness Region Warning",
        "status": "WARNING" if failed_rows > 0 else "PASS",
        "failed_rows": failed_rows,
    }


def _validate_timeliness_source_percent_reconciliation(df: pd.DataFrame) -> Dict[str, Any]:
    """Check source percentage against the computed count-based rate when comparable."""
    if not _is_timeliness_dataset(df):
        return {"rule": "Timeliness Source Percent Reconciliation", "status": "PASS", "failed_rows": 0}

    if "source_percent" not in df.columns:
        return {
            "rule": "Timeliness Source Percent Reconciliation",
            "status": "WARNING",
            "failed_rows": int(df.shape[0]),
            "message": "source_percent missing; reconciliation deferred to later review.",
        }

    comparable_mask = (
        df["disposed_count"].notna()
        & df["timely_count"].notna()
        & df["source_percent"].notna()
        & (df["disposed_count"] > 0)
    )
    if not comparable_mask.any():
        return {"rule": "Timeliness Source Percent Reconciliation", "status": "PASS", "failed_rows": 0}

    computed_rates = df.loc[comparable_mask, "timely_count"] / df.loc[comparable_mask, "disposed_count"]
    source_rates = df.loc[comparable_mask, "source_percent"]
    tolerance = 0.00005
    failed_rows = int((computed_rates.sub(source_rates).abs() > tolerance).sum())
    return {
        "rule": "Timeliness Source Percent Reconciliation",
        "status": "PASS" if failed_rows == 0 else "FAIL",
        "failed_rows": failed_rows,
    }


def _validate_timeliness_grain_uniqueness(df: pd.DataFrame) -> Dict[str, Any]:
    """Fail if duplicate rows exist at the reporting_month × processing_type × Region grain."""
    if not _is_timeliness_dataset(df):
        return {"rule": "Timeliness Grain Uniqueness", "status": "PASS", "failed_rows": 0}

    if "reporting_month" not in df.columns:
        return {
            "rule": "Timeliness Grain Uniqueness",
            "status": "PROFILE",
            "failed_rows": 0,
            "message": "Full grain validation deferred until reporting_month metadata is available.",
        }

    if not {"processing_type", "Region"}.issubset(df.columns):
        return {"rule": "Timeliness Grain Uniqueness", "status": "PROFILE", "failed_rows": 0}

    duplicate_mask = df.duplicated(subset=["reporting_month", "processing_type", "Region"], keep=False)
    failed_rows = int(duplicate_mask.sum())
    return {
        "rule": "Timeliness Grain Uniqueness",
        "status": "PASS" if failed_rows == 0 else "FAIL",
        "failed_rows": failed_rows,
    }


def _validate_timeliness_total_reconciliation_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """Defer TOTAL reconciliation profiling until total metadata is supplied upstream."""
    if not _is_timeliness_dataset(df):
        return {"rule": "Timeliness Total Reconciliation", "status": "PROFILE", "failed_rows": 0}

    total_columns = [column for column in df.columns if "total" in column.lower()]
    if not total_columns:
        return {
            "rule": "Timeliness Total Reconciliation",
            "status": "PROFILE",
            "failed_rows": 0,
            "message": "TOTAL reconciliation deferred: column-level total metadata not available in the current Timeliness dataset.",
        }

    return {"rule": "Timeliness Total Reconciliation", "status": "PROFILE", "failed_rows": 0}


def _validate_county_name_required(
    df: pd.DataFrame,
) -> Dict[str, Any]:
    """Validate that the County Name column contains no missing values."""
    if "County Name" not in df.columns:
        return {
            "rule": "County Name Required",
            "status": "FAIL",
            "failed_rows": len(df),
        }

    failed_rows = int(df["County Name"].isna().sum())

    return {
        "rule": "County Name Required",
        "status": "PASS" if failed_rows == 0 else "FAIL",
        "failed_rows": failed_rows,
    }


def _validate_report_month_required(
    df: pd.DataFrame,
) -> Dict[str, Any]:
    """Validate that report_month is present and follows the YYYY-MM format."""
    if "report_month" not in df.columns:
        return {
            "rule": "report_month Required",
            "status": "FAIL",
            "failed_rows": len(df),
        }

    month_series = df["report_month"]
    invalid_mask = month_series.isna() | ~month_series.astype(str).str.fullmatch(r"\d{4}-\d{2}", na=False)
    if "report_month" in df.columns:
        valid_months = month_series.astype(str).str[5:7]
        invalid_mask = invalid_mask | ~valid_months.str.fullmatch(r"0[1-9]|1[0-2]", na=False)

    failed_rows = int(invalid_mask.sum())

    return {
        "rule": "report_month Required",
        "status": "PASS" if failed_rows == 0 else "FAIL",
        "failed_rows": failed_rows,
    }


def _validate_required_numeric_fields(
    df: pd.DataFrame,
) -> Dict[str, Any]:
    """Validate that required numeric columns are present and non-null."""
    required_columns = [
        "Number of Cases",
        "Number of Eligible Individuals",
        "Total SNAP Payments",
    ]

    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        return {
            "rule": "Required Numeric Fields",
            "status": "FAIL",
            "failed_rows": len(df),
        }

    failed_rows = int(
        df[required_columns].isna().any(axis=1).sum()
    )

    return {
        "rule": "Required Numeric Fields",
        "status": "PASS" if failed_rows == 0 else "FAIL",
        "failed_rows": failed_rows,
    }


def _validate_non_negative_numeric_values(
    df: pd.DataFrame,
) -> Dict[str, Any]:
    """Validate that numeric fields present in the DataFrame are not negative."""
    numeric_columns = [
        "Number of Cases",
        "Number of Eligible Individuals",
        "Total SNAP Payments",
    ]
    available_columns = [column for column in numeric_columns if column in df.columns]

    if not available_columns:
        return {
            "rule": "Non-negative Numeric Values",
            "status": "FAIL",
            "failed_rows": len(df),
        }

    failed_rows = int(df[available_columns].lt(0).any(axis=1).sum())

    return {
        "rule": "Non-negative Numeric Values",
        "status": "PASS" if failed_rows == 0 else "FAIL",
        "failed_rows": failed_rows,
    }


def _validate_reporting_entity(
    df: pd.DataFrame,
) -> Dict[str, Any]:
    """Validate that County Name values match a known reporting entity."""
    known_counties = {
        "BEXAR",
        "DALLAS",
        "HARRIS",
        "TRAVIS",
        "MCLENNAN",
        "NACOGDOCHES",
        "MATAGORDA",
        "TARRANT",
        "EL PASO",
    }

    if "County Name" not in df.columns:
        return {
            "rule": "Valid Reporting Entity",
            "status": "FAIL",
            "failed_rows": len(df),
        }

    county_values = df["County Name"].astype(str).str.upper()
    failed_rows = int((~county_values.isin(known_counties)).sum())

    return {
        "rule": "Valid Reporting Entity",
        "status": "PASS" if failed_rows == 0 else "FAIL",
        "failed_rows": failed_rows,
    }


def validate_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Run the current validation rules and return the data plus a simple summary."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    working_df = df.copy()

    if _is_timeliness_dataset(working_df):
        validation_results: List[Dict[str, Any]] = [
            _validate_timeliness_required_fields(working_df),
            _validate_timeliness_source_percent_warning(working_df),
            _validate_timeliness_non_negative_counts(working_df),
            _validate_timeliness_timeline_limit(working_df),
            _validate_timeliness_zero_denominator_rule(working_df),
            _validate_timeliness_processing_type(working_df),
            _validate_timeliness_region_warnings(working_df),
            _validate_timeliness_source_percent_reconciliation(working_df),
            _validate_timeliness_grain_uniqueness(working_df),
            _validate_timeliness_total_reconciliation_profile(working_df),
        ]
    else:
        validation_results = [
            _validate_county_name_required(working_df),
            _validate_report_month_required(working_df),
            _validate_required_numeric_fields(working_df),
            _validate_non_negative_numeric_values(working_df),
            _validate_reporting_entity(working_df),
        ]

    rules_passed = sum(1 for result in validation_results if result["status"] == "PASS")
    rules_failed = sum(1 for result in validation_results if result["status"] == "FAIL")
    rules_warning = sum(1 for result in validation_results if result["status"] == "WARNING")
    rules_profile = sum(1 for result in validation_results if result["status"] == "PROFILE")
    status = "PASS" if rules_failed == 0 else "FAIL"

    summary: Dict[str, Any] = {
        "input_row_count": int(df.shape[0]),
        "output_row_count": int(working_df.shape[0]),
        "status": status,
        "rules_passed": rules_passed,
        "rules_failed": rules_failed,
        "rules_warning": rules_warning,
        "rules_profile": rules_profile,
        "validation_results": validation_results,
    }

    return {
        "data": working_df,
        "summary": summary,
    }
