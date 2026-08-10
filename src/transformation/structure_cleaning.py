"""Structure-cleaning utilities for the Silver layer.

This module is responsible only for tabular structure repair before
normalization, type conversion, and business validation are applied.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pandas as pd


def _remove_empty_rows(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Remove rows whose cells are all missing values."""
    original_row_count = int(df.shape[0])
    cleaned_df = df.dropna(axis=0, how="all").copy()
    removed_row_count = original_row_count - int(cleaned_df.shape[0])
    return cleaned_df, removed_row_count


def _remove_empty_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Remove columns whose cells are all missing values."""
    original_column_count = int(df.shape[1])
    cleaned_df = df.dropna(axis=1, how="all").copy()
    removed_column_count = original_column_count - int(cleaned_df.shape[1])
    return cleaned_df, removed_column_count


def _detect_duplicated_header_rows(df: pd.DataFrame) -> List[str]:
    """Detect repeated header rows as a placeholder for future structure rules."""
    issues: List[str] = []

    if df.empty:
        return issues

    columns = list(df.columns)
    for idx, row in df.head(10).iterrows():
        row_values = [str(value).strip() for value in row.tolist()]
        if row_values and row_values == [str(col).strip() for col in columns]:
            issues.append(f"Duplicate header row detected at index {idx}.")

    return issues


def _validate_structure(df: pd.DataFrame) -> None:
    """Raise an error when the DataFrame is empty after structural cleaning."""
    if df.empty:
        raise ValueError("DataFrame is empty after structure cleaning.")


def clean_structure(df: pd.DataFrame) -> Dict[str, Any]:
    """Apply structure-only cleaning to a DataFrame.

    This function removes empty rows and columns and checks for duplicated header
    rows. It does not perform normalization, data type conversion, or business
    validation.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    working_df = df.copy()

    cleaned_df, removed_row_count = _remove_empty_rows(working_df)
    cleaned_df, removed_column_count = _remove_empty_columns(cleaned_df)
    structure_issues = _detect_duplicated_header_rows(cleaned_df)

    _validate_structure(cleaned_df)

    summary = {
        "input_row_count": int(df.shape[0]),
        "output_row_count": int(cleaned_df.shape[0]),
        "removed_row_count": removed_row_count,
        "removed_column_count": removed_column_count,
        "structure_issues": structure_issues,
    }

    return {
        "cleaned_df": cleaned_df,
        "summary": summary,
    }
