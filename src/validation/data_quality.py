"""Reusable data quality helpers for the Bronze-to-Silver pipeline."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pandas as pd


def _profile_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Inspect a DataFrame without modifying it."""
    return {
        "total_rows": int(df.shape[0]),
        "total_columns": int(df.shape[1]),
        "column_names": list(df.columns),
        "data_types": df.dtypes.astype(str).to_dict(),
        "missing_values_by_column": {
            column: int(count)
            for column, count in df.isna().sum().items()
        },
        "duplicate_row_count": int(df.duplicated().sum()),
    }


def _run_validation_rules(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, List[Dict[str, Any]], Dict[str, int]]:
    """Run the current validation-rule framework and return issues and counts."""
    validated_df = df.copy()
    validation_issues: List[Dict[str, Any]] = []

    validation_counts = {
        "passed_row_count": int(validated_df.shape[0]),
        "warning_count": 0,
        "error_count": 0,
    }

    if validated_df.empty:
        validation_issues.append(
            {
                "level": "error",
                "scope": "dataset",
                "rule": "empty_dataset",
                "message": "The input DataFrame is empty.",
            }
        )
        validation_counts["passed_row_count"] = 0
        validation_counts["error_count"] += 1

    return validated_df, validation_issues, validation_counts


def _build_validation_summary(
    profile_result: Dict[str, Any],
    validation_result: Tuple[
        pd.DataFrame,
        List[Dict[str, Any]],
        Dict[str, int],
    ],
) -> Dict[str, Any]:
    """Combine profiling and validation results into a concise summary."""
    validated_df, issues, counts = validation_result

    return {
        "input_row_count": profile_result["total_rows"],
        "output_row_count": int(validated_df.shape[0]),
        "passed_row_count": counts.get("passed_row_count", 0),
        "warning_count": counts.get("warning_count", 0),
        "error_count": counts.get("error_count", 0),
        "duplicate_row_count": profile_result["duplicate_row_count"],
        "issue_details": issues,
    }


def validate_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate a DataFrame and return profiling, issues, and a summary."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    working_df = df.copy()

    profile_result = _profile_data(working_df)
    validation_result = _run_validation_rules(working_df)
    summary = _build_validation_summary(
        profile_result,
        validation_result,
    )

    validated_df, validation_issues, _ = validation_result

    return {
        "validated_df": validated_df,
        "profile": profile_result,
        "issues": validation_issues,
        "summary": summary,
    }
