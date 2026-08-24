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


def test_clean_structure_extracts_timeliness_sections_from_valid_workbook() -> None:
    df = pd.DataFrame(
        [
            ["SNAP Food Benefits Timeliness", None, None, None],
            [None, None, None, None],
            ["SNAP Food Benefits APPLICATIONS", None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            ["Bexar", "100", "90", "90.0"],
            ["Dallas", "200", "180", "90.0"],
            ["TOTAL", "300", "270", "90.0"],
            ["Definitions", "Not analytic", None, None],
            ["SNAP Food Benefits REDETERMINATIONS", None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            ["Bexar", "80", "70", "87.5"],
            ["TOTAL", "80", "70", "87.5"],
            ["Notes", "Not part of results", None, None],
        ],
        columns=[0, 1, 2, 3],
    )

    result = clean_structure(df)
    cleaned_df = result["cleaned_df"]

    assert cleaned_df["processing_type"].tolist() == ["Applications", "Applications", "Redeterminations"]
    assert cleaned_df["Region"].tolist() == ["Bexar", "Dallas", "Bexar"]
    assert cleaned_df["Disposed"].tolist() == ["100", "200", "80"]
    assert cleaned_df["Timely"].tolist() == ["90", "180", "70"]
    assert cleaned_df["Percent"].tolist() == ["90.0", "90.0", "87.5"]
    assert result["summary"]["timeliness_section_totals"]["Applications"]["Region"] == "TOTAL"
    assert result["summary"]["timeliness_section_totals"]["Redeterminations"]["Percent"] == "87.5"


def test_clean_structure_excludes_titles_blank_rows_notes_and_total_from_detail_rows() -> None:
    df = pd.DataFrame(
        [
            ["SNAP Food Benefits Timeliness", None, None, None],
            [None, None, None, None],
            ["SNAP Food Benefits APPLICATIONS", None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            ["Bexar", "100", "90", "90.0"],
            ["TOTAL", "300", "270", "90.0"],
            ["Notes", "Definitions", None, None],
            ["SNAP Food Benefits REDETERMINATIONS", None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            ["Bexar", "80", "70", "87.5"],
            ["TOTAL", "80", "70", "87.5"],
        ],
        columns=[0, 1, 2, 3],
    )

    result = clean_structure(df)

    assert result["cleaned_df"]["Region"].tolist() == ["Bexar", "Bexar"]
    assert result["cleaned_df"]["processing_type"].tolist() == ["Applications", "Redeterminations"]
    assert "TOTAL" not in result["cleaned_df"]["Region"].astype(str).tolist()


def test_clean_structure_fails_when_applications_section_missing() -> None:
    df = pd.DataFrame(
        [
            ["SNAP Food Benefits Timeliness", None, None, None],
            ["SNAP Food Benefits REDETERMINATIONS", None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            ["Bexar", "80", "70", "87.5"],
        ],
        columns=[0, 1, 2, 3],
    )

    with pytest.raises(ValueError, match="Missing required Timeliness section"):
        clean_structure(df)


def test_clean_structure_fails_when_redeterminations_section_missing() -> None:
    df = pd.DataFrame(
        [
            ["SNAP Food Benefits Timeliness", None, None, None],
            ["SNAP Food Benefits APPLICATIONS", None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            ["Bexar", "100", "90", "90.0"],
        ],
        columns=[0, 1, 2, 3],
    )

    with pytest.raises(ValueError, match="Missing required Timeliness section"):
        clean_structure(df)


def test_clean_structure_fails_when_required_header_is_missing_or_changed() -> None:
    df = pd.DataFrame(
        [
            ["SNAP Food Benefits Timeliness", None, None, None],
            ["SNAP Food Benefits APPLICATIONS", None, None, None],
            ["Region", "Disposed", "Percent", "Timely"],
            ["Bexar", "100", "90.0", "90"],
            ["SNAP Food Benefits REDETERMINATIONS", None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            ["Bexar", "80", "70", "87.5"],
        ],
        columns=[0, 1, 2, 3],
    )

    with pytest.raises(ValueError, match="Missing expected Timeliness table header"):
        clean_structure(df)


def test_clean_structure_handles_physical_row_position_changes() -> None:
    df = pd.DataFrame(
        [
            [None, None, None, None],
            ["SNAP Food Benefits Timeliness", None, None, None],
            [None, None, None, None],
            [None, None, None, None],
            ["SNAP Food Benefits REDETERMINATIONS", None, None, None],
            [None, None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            ["Bexar", "80", "70", "87.5"],
            ["TOTAL", "80", "70", "87.5"],
            ["SNAP Food Benefits APPLICATIONS", None, None, None],
            [None, None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            ["Bexar", "100", "90", "90.0"],
            ["TOTAL", "100", "90", "90.0"],
        ],
        columns=[0, 1, 2, 3],
    )

    result = clean_structure(df)
    cleaned_df = result["cleaned_df"]

    assert cleaned_df["processing_type"].tolist() == ["Redeterminations", "Applications"]
    assert cleaned_df["Region"].tolist() == ["Bexar", "Bexar"]
    assert result["summary"]["timeliness_section_totals"]["Applications"]["Disposed"] == "100"


def test_clean_structure_preserves_column_position_when_middle_value_is_missing() -> None:
    df = pd.DataFrame(
        [
            ["SNAP Food Benefits Timeliness", None, None, None],
            ["SNAP Food Benefits APPLICATIONS", None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            ["CCC", "100", None, "50.0"],
            ["TOTAL", "100", "50", "50.0"],
            ["SNAP Food Benefits REDETERMINATIONS", None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            ["DDD", "90", None, "45.0"],
            ["TOTAL", "90", "45", "45.0"],
        ],
        columns=[0, 1, 2, 3],
    )

    result = clean_structure(df)
    cleaned_df = result["cleaned_df"]

    assert cleaned_df["Region"].tolist() == ["CCC", "DDD"]
    assert cleaned_df["Disposed"].tolist() == ["100", "90"]
    assert cleaned_df["Timely"].isna().tolist() == [True, True]
    assert cleaned_df["Percent"].tolist() == ["50.0", "45.0"]


def test_clean_structure_preserves_source_record_with_only_region_populated() -> None:
    df = pd.DataFrame(
        [
            ["SNAP Food Benefits Timeliness", None, None, None],
            ["SNAP Food Benefits APPLICATIONS", None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            ["MEPD", None, None, None],
            ["TOTAL", "15", "10", "66.7"],
            ["SNAP Food Benefits REDETERMINATIONS", None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            ["Oth", "5", "4", "80.0"],
            ["TOTAL", "5", "4", "80.0"],
        ],
        columns=[0, 1, 2, 3],
    )

    result = clean_structure(df)
    cleaned_df = result["cleaned_df"]
    region_row = cleaned_df[cleaned_df["Region"] == "MEPD"].iloc[0]

    assert region_row["Region"] == "MEPD"
    assert pd.isna(region_row["Disposed"])
    assert pd.isna(region_row["Timely"])
    assert pd.isna(region_row["Percent"])


def test_clean_structure_ignores_dataframe_index_when_extracting_timeliness_sections() -> None:
    df = pd.DataFrame(
        [
            ["SNAP Food Benefits Timeliness", None, None, None],
            [None, None, None, None],
            ["SNAP Food Benefits APPLICATIONS", None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            ["Bexar", "100", "90", "90.0"],
            ["Dallas", "200", "180", "90.0"],
            ["TOTAL", "300", "270", "90.0"],
            ["Definitions", "Not analytic", None, None],
            ["SNAP Food Benefits REDETERMINATIONS", None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            ["Bexar", "80", "70", "87.5"],
            ["TOTAL", "80", "70", "87.5"],
            ["Notes", "Not part of results", None, None],
        ],
        columns=[0, 1, 2, 3],
    )
    df.index = range(100, 100 + len(df))

    result = clean_structure(df)
    cleaned_df = result["cleaned_df"]

    assert cleaned_df["processing_type"].tolist() == ["Applications", "Applications", "Redeterminations"]
    assert cleaned_df["Region"].tolist() == ["Bexar", "Dallas", "Bexar"]
    assert cleaned_df["Disposed"].tolist() == ["100", "200", "80"]
    assert cleaned_df["Timely"].tolist() == ["90", "180", "70"]
    assert cleaned_df["Percent"].tolist() == ["90.0", "90.0", "87.5"]
