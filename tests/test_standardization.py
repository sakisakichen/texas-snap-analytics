import pandas as pd

from src.transformation.standardization import (
    _apply_county_case_overrides,
    _apply_county_name_mapping,
    _remove_formatting_symbols,
    _standardize_county_name_case,
    _trim_whitespace,
    standardize_data,
)


def test_standardize_county_name_case_uses_generic_title_case() -> None:
    df = pd.DataFrame({"County Name": ["BEXAR", "DALLAS", "MCLENNAN"]})

    result = _standardize_county_name_case(df)

    assert result["County Name"].tolist() == ["Bexar", "Dallas", "Mclennan"]


def test_county_case_overrides_correct_title_case_exception() -> None:
    df = pd.DataFrame({"County Name": ["Mclennan", "MCLENNAN"]})
    standardized = _standardize_county_name_case(df)

    result = _apply_county_case_overrides(standardized)

    assert result["County Name"].tolist() == ["McLennan", "McLennan"]


def test_apply_county_name_mapping_corrects_source_specific_values() -> None:
    df = pd.DataFrame({"County Name": ["Matagorda¹", "State Total¹"]})

    result = _apply_county_name_mapping(df)

    assert result["County Name"].tolist() == ["Matagorda", "State Total"]


def test_trim_whitespace_removes_surrounding_whitespace() -> None:
    df = pd.DataFrame(
        {
            "County Name": ["  BEXAR  ", "DALLAS", "  TRAVIS  "],
            "Notes": ["  keep  ", "value", "  trailing  "],
        }
    )

    result = _trim_whitespace(df)

    assert result["County Name"].tolist() == ["BEXAR", "DALLAS", "TRAVIS"]
    assert result["Notes"].tolist() == ["keep", "value", "trailing"]


def test_trim_whitespace_preserves_internal_whitespace() -> None:
    df = pd.DataFrame({"County Name": ["San  Antonio", "New Braunfels", "North  East"]})

    result = _trim_whitespace(df)

    assert result["County Name"].tolist() == ["San  Antonio", "New Braunfels", "North  East"]


def test_trim_whitespace_preserves_null_values() -> None:
    df = pd.DataFrame(
        {
            "County Name": [None, "  BEXAR  ", pd.NA],
            "Total SNAP Payments": [pd.NA, " $123 ", None],
        }
    )

    result = _trim_whitespace(df)

    assert pd.isna(result["County Name"].iloc[0])
    assert result["County Name"].iloc[1] == "BEXAR"
    assert pd.isna(result["County Name"].iloc[2])
    assert pd.isna(result["Total SNAP Payments"].iloc[0])
    assert result["Total SNAP Payments"].iloc[1] == "$123"
    assert pd.isna(result["Total SNAP Payments"].iloc[2])


def test_standardize_county_name_case_preserves_numeric_values() -> None:
    df = pd.DataFrame({"County Name": ["BEXAR", "DALLAS"], "Population": [123, 456]})

    result = _standardize_county_name_case(df)

    assert result["Population"].tolist() == [123, 456]


def test_remove_formatting_symbols_removes_currency_symbols_and_commas() -> None:
    df = pd.DataFrame(
        {
            "Total SNAP Payments": ["$1,234", "$5,678"],
            "Avg Payment / Case": ["$9,012", "$10,345"],
        }
    )

    result = _remove_formatting_symbols(df)

    assert result["Total SNAP Payments"].tolist() == ["1234", "5678"]
    assert result["Avg Payment / Case"].tolist() == ["9012", "10345"]


def test_remove_formatting_symbols_only_targets_configured_currency_columns() -> None:
    df = pd.DataFrame(
        {
            "County Name": ["BEXAR"],
            "Other Metric": ["$1,234"],
            "Total SNAP Payments": ["$5,678"],
        }
    )

    result = _remove_formatting_symbols(df)

    assert result["County Name"].tolist() == ["BEXAR"]
    assert result["Other Metric"].tolist() == ["$1,234"]
    assert result["Total SNAP Payments"].tolist() == ["5678"]


def test_standardize_data_does_not_mutate_input_dataframe() -> None:
    df = pd.DataFrame(
        {
            "County Name": ["  BEXAR  ", " Matagorda¹ "],
            "Total SNAP Payments": ["$1,234", "$5,678"],
        }
    )
    original = df.copy(deep=True)

    _, _ = standardize_data(df)

    assert df.equals(original)


def test_standardize_timeliness_renames_expected_columns_and_preserves_business_terms() -> None:
    df = pd.DataFrame(
        {
            "processing_type": ["Applications", " Redeterminations ", "Applications"],
            "Region": [" 01 ", "02/09", " CCC "],
            "Disposed": ["13,228", "9,000", "1,200"],
            "Timely": ["11,202", "8,200", None],
            "Percent": ["84.7%", "91.1%", "80.0%"],
        }
    )

    result, _ = standardize_data(df)

    assert result.columns.tolist() == [
        "processing_type",
        "Region",
        "disposed_count",
        "timely_count",
        "source_percent",
    ]
    assert result["processing_type"].tolist() == ["Applications", "Redeterminations", "Applications"]
    assert result["Region"].tolist() == ["01", "02/09", "CCC"]
    assert result["disposed_count"].tolist() == ["13,228", "9,000", "1,200"]
    assert result["timely_count"].iloc[0] == "11,202"
    assert result["timely_count"].iloc[1] == "8,200"
    assert pd.isna(result["timely_count"].iloc[2])
    assert result["source_percent"].tolist() == ["84.7%", "91.1%", "80.0%"]


def test_standardize_timeliness_preserves_undocumented_categories_and_missing_values() -> None:
    df = pd.DataFrame(
        {
            "processing_type": ["Applications", "Redeterminations"],
            "Region": ["MEPD", "  UNKNOWN  "],
            "Disposed": [None, " 7 "],
            "Timely": [None, " 5 "],
            "Percent": [None, "71.4%"],
        }
    )

    result, _ = standardize_data(df)

    assert result["Region"].tolist() == ["MEPD", "UNKNOWN"]
    assert result["processing_type"].tolist() == ["Applications", "Redeterminations"]
    assert pd.isna(result["disposed_count"].iloc[0])
    assert pd.isna(result["timely_count"].iloc[0])
    assert pd.isna(result["source_percent"].iloc[0])
    assert result["source_percent"].iloc[1] == "71.4%"


def test_standardize_timeliness_does_not_convert_numeric_types_or_drop_rows() -> None:
    df = pd.DataFrame(
        {
            "processing_type": ["Applications"],
            "Region": ["01"],
            "Disposed": [" 13,228 "],
            "Timely": [" 11,202 "],
            "Percent": [" 84.7% "],
        }
    )

    result, _ = standardize_data(df)

    assert result["disposed_count"].tolist() == ["13,228"]
    assert result["timely_count"].tolist() == ["11,202"]
    assert result["source_percent"].tolist() == ["84.7%"]
    assert result["Region"].tolist() == ["01"]
    assert result.shape[0] == 1


def test_standardize_timeliness_does_not_modify_input_dataframe_in_place() -> None:
    df = pd.DataFrame(
        {
            "processing_type": [" Applications ", "Redeterminations"],
            "Region": [" 01 ", " 02/09 "],
            "Disposed": [" 100 ", " 200 "],
            "Timely": [" 90 ", " 180 "],
            "Percent": [" 90.0% ", " 90.0% "],
        }
    )
    original = df.copy(deep=True)

    _, _ = standardize_data(df)

    pd.testing.assert_frame_equal(df, original)
