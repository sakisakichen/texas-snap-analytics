from __future__ import annotations

import pandas as pd
import pytest

from src.transformation.structure_cleaning import clean_structure


def test_remove_completely_empty_rows() -> None:
    df = pd.DataFrame(
        {
            "col_a": [1.0, None],
            "col_b": [2.0, None],
        }
    )

    result = clean_structure(df)

    assert result["cleaned_df"].shape[0] == 1
    assert result["summary"]["removed_row_count"] == 1


def test_remove_completely_empty_columns() -> None:
    df = pd.DataFrame(
        {
            "keep_me": [1.0, 2.0],
            "drop_me": [None, None],
        }
    )

    result = clean_structure(df)

    assert result["cleaned_df"].columns.tolist() == ["keep_me"]
    assert result["summary"]["removed_column_count"] == 1


def test_do_not_remove_rows_with_partial_missing_values() -> None:
    df = pd.DataFrame(
        {
            "col_a": [1.0, None],
            "col_b": [None, 2.0],
        }
    )

    result = clean_structure(df)

    assert result["summary"]["removed_row_count"] == 0
    assert result["cleaned_df"].shape[0] == 2


def test_detect_duplicated_header_rows() -> None:
    df = pd.DataFrame(
        [["name", "value"], ["name", "value"], ["Alice", 10]],
        columns=["name", "value"],
    )

    result = clean_structure(df)

    assert result["summary"]["structure_issues"] == [
        "Duplicate header row detected at index 0.",
        "Duplicate header row detected at index 1.",
    ]


def test_raise_value_error_when_cleaned_dataframe_becomes_empty() -> None:
    df = pd.DataFrame({"col_a": [None, None], "col_b": [None, None]})

    with pytest.raises(ValueError, match="DataFrame is empty after structure cleaning"):
        clean_structure(df)


def test_summary_contains_expected_structure_metrics() -> None:
    df = pd.DataFrame(
        {
            "keep_me": [1.0, None],
            "drop_me": [None, None],
        }
    )

    result = clean_structure(df)
    summary = result["summary"]

    expected_keys = {
        "input_row_count",
        "output_row_count",
        "removed_row_count",
        "removed_column_count",
        "structure_issues",
    }

    assert expected_keys.issubset(summary.keys())
    assert summary["input_row_count"] == 2
    assert summary["output_row_count"] == 1
    assert summary["removed_row_count"] == 1
    assert summary["removed_column_count"] == 1


def test_input_dataframe_is_not_modified() -> None:
    df = pd.DataFrame(
        {
            "col_a": [1.0, None],
            "col_b": [None, None],
        }
    )
    original = df.copy(deep=True)

    clean_structure(df)

    pd.testing.assert_frame_equal(df, original)


def test_clean_structure_returns_cleaned_dataframe_and_summary() -> None:
    df = pd.DataFrame({"col_a": [1.0], "col_b": [2.0]})

    result = clean_structure(df)

    assert isinstance(result["cleaned_df"], pd.DataFrame)
    assert isinstance(result["summary"], dict)
    assert result["cleaned_df"].equals(df)
