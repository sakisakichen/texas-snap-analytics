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
