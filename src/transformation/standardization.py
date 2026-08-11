"""Representation standardization utilities for the Silver layer.

This module is responsible for standardizing textual representations before any
subsequent type conversion or business validation happens.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

import pandas as pd


CURRENCY_COLUMNS = [
    "Total SNAP Payments",
    "Avg Payment / Case",
]

COUNTY_CASE_OVERRIDES = {
    "Mclennan": "McLennan",
}

COUNTY_SOURCE_CORRECTIONS = {
    "Matagorda¹": "Matagorda",
    "State Total¹": "State Total",
}

COUNTY_NAME_MAPPING = COUNTY_SOURCE_CORRECTIONS


def _trim_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    """Trim leading and trailing whitespace from string values only."""
    trimmed_df = df.copy()

    for column in trimmed_df.columns:
        series = trimmed_df[column]
        if pd.api.types.is_string_dtype(series):
            trimmed_df[column] = series.map(lambda value: value.strip() if isinstance(value, str) else value)

    return trimmed_df


def _remove_formatting_symbols(df: pd.DataFrame) -> pd.DataFrame:
    """Remove presentation symbols from configured currency-like columns."""
    standardized_df = df.copy()

    for column in CURRENCY_COLUMNS:
        if column in standardized_df.columns:
            standardized_df[column] = standardized_df[column].map(
                lambda value: value.replace("$", "").replace(",", "") if isinstance(value, str) else value
            )

    return standardized_df


def _standardize_county_name_case(df: pd.DataFrame) -> pd.DataFrame:
    """Apply generic title-casing to county names without any source-specific fixes."""
    standardized_df = df.copy()

    if "County Name" in standardized_df.columns:
        standardized_df["County Name"] = standardized_df["County Name"].map(
            lambda value: value.title() if isinstance(value, str) else value
        )

    return standardized_df


def _apply_county_case_overrides(df: pd.DataFrame) -> pd.DataFrame:
    """Apply title-case exceptions using the already-normalized county value."""
    standardized_df = df.copy()

    if "County Name" in standardized_df.columns:
        standardized_df["County Name"] = standardized_df["County Name"].map(
            lambda value: COUNTY_CASE_OVERRIDES.get(value, value) if isinstance(value, str) else value
        )

    return standardized_df


def _apply_county_name_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """Apply known source-specific county name corrections via a constant lookup."""
    standardized_df = df.copy()

    if "County Name" in standardized_df.columns:
        standardized_df["County Name"] = standardized_df["County Name"].map(
            lambda value: COUNTY_SOURCE_CORRECTIONS.get(str(value).strip(), value) if isinstance(value, str) else value
        )

    return standardized_df


def standardize_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Apply representation-only standardization to a Bronze DataFrame.

    The function performs a narrow set of representation fixes in sequence:
    whitespace trimming, currency symbol cleanup, county title-casing, and
    county mapping corrections. It does not perform data type conversion,
    missing value handling, or business validation.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    working_df = df.copy()
    working_df = _trim_whitespace(working_df)
    working_df = _remove_formatting_symbols(working_df)
    working_df = _standardize_county_name_case(working_df)
    working_df = _apply_county_case_overrides(working_df)
    working_df = _apply_county_name_mapping(working_df)

    summary: Dict[str, Any] = {
        "input_row_count": int(df.shape[0]),
        "output_row_count": int(working_df.shape[0]),
        "currency_columns": list(CURRENCY_COLUMNS),
        "county_name_mapping_applied": bool(COUNTY_SOURCE_CORRECTIONS),
    }

    return working_df, summary
