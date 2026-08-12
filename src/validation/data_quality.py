"""Reusable data quality helpers for the Bronze-to-Silver pipeline."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


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

    validation_results: List[Dict[str, Any]] = [
        _validate_county_name_required(working_df),
        _validate_report_month_required(working_df),
        _validate_required_numeric_fields(working_df),
        _validate_non_negative_numeric_values(working_df),
        _validate_reporting_entity(working_df),
    ]

    rules_passed = sum(1 for result in validation_results if result["status"] == "PASS")
    rules_failed = sum(1 for result in validation_results if result["status"] == "FAIL")
    status = "PASS" if rules_failed == 0 else "FAIL"

    summary: Dict[str, Any] = {
        "input_row_count": int(df.shape[0]),
        "output_row_count": int(working_df.shape[0]),
        "status": status,
        "rules_passed": rules_passed,
        "rules_failed": rules_failed,
        "validation_results": validation_results,
    }

    return {
        "data": working_df,
        "summary": summary,
    }
