"""Type conversion utilities for standardized SNAP data in the Silver layer."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd


STRING_COLUMNS = [
    "County Name",
    "report_month",
    "reporting_month",
    "source_file",
    "processing_type",
    "Region",
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
    "disposed_count",
    "timely_count",
]

FLOAT_COLUMNS = [
    "Avg Payment / Case",
    "source_percent",
]


def _parse_count_value(value: Any) -> Any:
    """Normalize comma-formatted count strings while preserving missing values."""
    if pd.isna(value):
        return pd.NA
    if isinstance(value, str):
        text = value.strip()
        if text == "":
            return pd.NA
        return text.replace(",", "")
    return value


def _parse_percent_value(value: Any) -> Any:
    """Convert a source percent value to a canonical decimal rate without guessing ambiguous inputs."""
    if pd.isna(value):
        return pd.NA

    if isinstance(value, str):
        text = value.strip()
        if text == "":
            return pd.NA
        if text.endswith("%"):
            number_text = text[:-1].replace(",", "").strip()
            try:
                return float(number_text) / 100.0
            except ValueError as exc:
                raise ValueError(f"Invalid percentage representation: {value!r}") from exc

        try:
            numeric = float(text)
        except ValueError as exc:
            raise ValueError(f"Invalid percentage representation: {value!r}") from exc

        if 0 <= numeric <= 1:
            return numeric
        raise ValueError(
            f"Ambiguous percentage representation {value!r}; provide a decimal rate in [0, 1] or a percent string like '38.47%'."
        )

    if isinstance(value, (int, float)):
        numeric = float(value)
        if 0 <= numeric <= 1:
            return numeric
        raise ValueError(
            f"Ambiguous percentage representation {value!r}; provide a decimal rate in [0, 1] or a percent string like '38.47%'."
        )

    return value


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
            normalized = converted_df[column].map(_parse_count_value)
            converted_df[column] = pd.to_numeric(normalized, errors="coerce").astype("Int64")

    # TODO: collect conversion failure statistics for reporting later.
    return converted_df


def _convert_float_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convert configured float columns to pandas nullable Float64 dtype."""
    converted_df = df.copy()

    for column in FLOAT_COLUMNS:
        if column in converted_df.columns:
            if column == "source_percent":
                converted_df[column] = converted_df[column].map(_parse_percent_value).astype("Float64")
            else:
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
