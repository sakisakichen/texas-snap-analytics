"""Type conversion utilities for standardized SNAP data in the Silver layer."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd


STRING_COLUMNS = [
    "County Name",
    "report_month",
    "source_file",
]

INTEGER_COLUMNS = [
    "Number of Cases",
    "Number of Eligible Individuals",
    "Individuals:        Ages < 5",
    "Individuals:        Ages 5 - 17",
    "Individuals:        Ages 18 - 59",
    "Individuals:        Ages 60 - 64",
    "Individuals:        Ages 65 +",
    "Total SNAP Payments",
]

FLOAT_COLUMNS = [
    "Avg Payment / Case",
]


def _convert_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convert configured string columns to pandas nullable string dtype."""
    converted_df = df.copy()

    for column in STRING_COLUMNS:
        if column in converted_df.columns:
            converted_df[column] = converted_df[column].astype("string")

    # TODO: produce summary metadata for string conversion later.
    return converted_df


def _convert_integer_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convert configured integer columns to pandas nullable Int64 dtype."""
    converted_df = df.copy()

    for column in INTEGER_COLUMNS:
        if column in converted_df.columns:
            converted_df[column] = pd.to_numeric(converted_df[column], errors="coerce").astype("Int64")

    # TODO: collect conversion failure statistics for reporting later.
    return converted_df


def _convert_float_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convert configured float columns to pandas nullable Float64 dtype."""
    converted_df = df.copy()

    for column in FLOAT_COLUMNS:
        if column in converted_df.columns:
            converted_df[column] = pd.to_numeric(converted_df[column], errors="coerce").astype("Float64")

    # TODO: collect conversion failure statistics for reporting later.
    return converted_df


def convert_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Convert standardized Silver-layer data to its target pandas dtypes."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    working_df = df.copy()
    working_df = _convert_string_columns(working_df)
    working_df = _convert_integer_columns(working_df)
    working_df = _convert_float_columns(working_df)

    summary: Dict[str, Any] = {
        "input_row_count": int(df.shape[0]),
        "output_row_count": int(working_df.shape[0]),
        "converted_columns": {
            "string": list(STRING_COLUMNS),
            "integer": list(INTEGER_COLUMNS),
            "float": list(FLOAT_COLUMNS),
        },
        "conversion_failures": {},
    }

    return {
        "data": working_df,
        "summary": summary,
    }
