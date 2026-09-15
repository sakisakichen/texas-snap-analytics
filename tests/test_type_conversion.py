import pandas as pd
import pytest

from src.transformation.type_conversion import convert_data
from decimal import Decimal

def test_string_columns_convert_to_nullable_string_dtype() -> None:
    df = pd.DataFrame(
        {
            "county_name": ["BEXAR", None, "Dallas"],
            "report_month": ["2024-01", None, "2024-02"],
            "source_file": ["file_a.xls", None, "file_b.xls"],
            "Other": [1, 2, 3],
        }
    )

    result = convert_data(df)
    converted = result["data"]

    assert str(converted["county_name"].dtype) == "string"
    assert str(converted["report_month"].dtype) == "string"
    assert str(converted["source_file"].dtype) == "string"
    assert pd.isna(converted["county_name"].iloc[1])
    assert pd.isna(converted["report_month"].iloc[1])
    assert pd.isna(converted["source_file"].iloc[1])


def test_integer_columns_convert_to_nullable_int64() -> None:
    df = pd.DataFrame(
        {
            "case_count": ["100", 200.0, None, "300"],
            "eligible_individual_count": ["150", 250.0, None, "350"],
            "eligible_under_5_count": ["10", 20.0, None, "30"],
            "eligible_5_17_count": ["20", 30.0, None, "40"],
            "eligible_18_59_count": ["80", 140.0, None, "200"],
            "eligible_60_64_count": ["15", 25.0, None, "35"],
            "eligible_65_plus_count": ["25", 35.0, None, "45"],
            "Other": ["keep", "me", "as", "is"],
        }
    )

    result = convert_data(df)
    converted = result["data"]

    integer_columns = [
        "case_count",
        "eligible_individual_count",
        "eligible_under_5_count",
        "eligible_5_17_count",
        "eligible_18_59_count",
        "eligible_60_64_count",
        "eligible_65_plus_count",
    ]

    for column in integer_columns:
        assert str(converted[column].dtype) == "Int64"

    assert converted["case_count"].tolist() == [100, 200, pd.NA, 300]

def test_total_snap_payments_converts_to_decimal_money() -> None:
    df = pd.DataFrame(
        {
            "total_snap_payments": [
                "50",
                100.0,
                None,
                "150",
                "22368395.01",
            ]
        }
    )

    result = convert_data(df)
    converted = result["data"]

    assert converted["total_snap_payments"].tolist() == [
        Decimal("50.00"),
        Decimal("100.00"),
        None,
        Decimal("150.00"),
        Decimal("22368395.01"),
    ]

def test_invalid_integer_values_become_missing_without_raising() -> None:
    df = pd.DataFrame({"case_count": ["100", "ABC", "200", None]})

    result = convert_data(df)
    converted = result["data"]

    assert converted["case_count"].tolist() == [100, pd.NA, 200, pd.NA]
    assert str(converted["case_count"].dtype) == "Int64"


def test_float_columns_convert_to_nullable_float64() -> None:
    df = pd.DataFrame(
        {
            "avg_payment_per_case": ["10.5", 20.0, None, "30.25"],
            "Other": ["x", "y", "z", "w"],
        }
    )

    result = convert_data(df)
    converted = result["data"]

    assert str(converted["avg_payment_per_case"].dtype) == "Float64"
    assert converted["avg_payment_per_case"].tolist() == [10.5, 20.0, pd.NA, 30.25]
    assert pd.isna(converted["avg_payment_per_case"].iloc[2])


def test_invalid_float_values_become_missing_without_raising() -> None:
    df = pd.DataFrame({"avg_payment_per_case": ["10.5", "XYZ", "20.0", None]})

    result = convert_data(df)
    converted = result["data"]

    assert converted["avg_payment_per_case"].tolist() == [10.5, pd.NA, 20.0, pd.NA]
    assert str(converted["avg_payment_per_case"].dtype) == "Float64"


def test_conversion_only_affects_configured_columns() -> None:
    df = pd.DataFrame(
        {
            "county_name": ["BEXAR", "Dallas"],
            "Unconfigured Value": ["$1,000", "$2,000"],
            "case_count": ["10", "20"],
            "avg_payment_per_case": ["12.5", "15.0"],
        }
    )

    result = convert_data(df)
    converted = result["data"]

    assert converted["Unconfigured Value"].tolist() == ["$1,000", "$2,000"]
    assert str(converted["county_name"].dtype) == "string"
    assert str(converted["case_count"].dtype) == "Int64"
    assert str(converted["avg_payment_per_case"].dtype) == "Float64"


def test_convert_data_does_not_modify_input_dataframe() -> None:
    df = pd.DataFrame(
        {
            "county_name": ["BEXAR", None],
            "case_count": ["10", "20"],
            "avg_payment_per_case": ["10.5", "20.0"],
        }
    )
    original = df.copy(deep=True)

    convert_data(df)

    assert df.equals(original)


def test_convert_data_returns_public_dictionary_contract() -> None:
    df = pd.DataFrame(
        {
            "county_name": ["BEXAR"],
            "report_month": ["2024-01"],
            "source_file": ["file_a.xls"],
            "case_count": ["10"],
            "total_snap_payments": ["100"],
            "avg_payment_per_case": ["10.5"],
        }
    )

    result = convert_data(df)

    assert isinstance(result, dict)
    assert "data" in result
    assert "summary" in result
    assert isinstance(result["data"], pd.DataFrame)
    assert isinstance(result["summary"], dict)


def test_summary_contains_expected_metadata() -> None:
    df = pd.DataFrame(
        {
            "county_name": ["BEXAR"],
            "report_month": ["2024-01"],
            "source_file": ["file_a.xls"],
            "case_count": ["10"],
            "total_snap_payments": ["100"],
            "avg_payment_per_case": ["10.5"],
        }
    )

    result = convert_data(df)
    summary = result["summary"]

    assert summary["input_row_count"] == 1
    assert summary["output_row_count"] == 1
    assert "converted_columns" in summary
    assert "conversion_failures" in summary
    assert summary["conversion_failures"] == {}



def test_timeliness_type_conversion_handles_counts_and_percent_values() -> None:
    df = pd.DataFrame(
        {
            "processing_type": ["Applications", "Redeterminations"],
            "Region": ["01", "02/09"],
            "disposed_count": ["13,228", "9,000"],
            "timely_count": ["11,202", None],
            "source_percent": ["38.47%", 0.3847],
            "reporting_month": ["2024-01", "2024-02"],
            "source_file": ["snap.xls", "snap2.xls"],
        }
    )

    result = convert_data(df)
    converted = result["data"]

    assert str(converted["processing_type"].dtype) == "string"
    assert str(converted["Region"].dtype) == "string"
    assert str(converted["disposed_count"].dtype) == "Int64"
    assert str(converted["timely_count"].dtype) == "Int64"
    assert converted["disposed_count"].tolist() == [13228, 9000]
    assert converted["timely_count"].tolist() == [11202, pd.NA]
    assert str(converted["source_percent"].dtype) == "Float64"
    assert converted["source_percent"].tolist() == [0.3847, 0.3847]
    assert str(converted["reporting_month"].dtype) == "string"
    assert str(converted["source_file"].dtype) == "string"


def test_timeliness_type_conversion_keeps_missing_values_nullable() -> None:
    df = pd.DataFrame(
        {
            "processing_type": ["Applications"],
            "Region": ["MEPD"],
            "disposed_count": [None],
            "timely_count": [None],
            "source_percent": [None],
        }
    )

    result = convert_data(df)
    converted = result["data"]

    assert str(converted["disposed_count"].dtype) == "Int64"
    assert str(converted["timely_count"].dtype) == "Int64"
    assert str(converted["source_percent"].dtype) == "Float64"
    assert pd.isna(converted["disposed_count"].iloc[0])
    assert pd.isna(converted["timely_count"].iloc[0])
    assert pd.isna(converted["source_percent"].iloc[0])


def test_timeliness_type_conversion_rejects_ambiguous_percent_values() -> None:
    df = pd.DataFrame(
        {
            "processing_type": ["Applications"],
            "Region": ["01"],
            "disposed_count": ["100"],
            "timely_count": ["90"],
            "source_percent": [38.47],
        }
    )

    with pytest.raises(ValueError, match="Ambiguous percentage representation"):
        convert_data(df)


def test_convert_data_raises_type_error_for_non_dataframe_input() -> None:
    with pytest.raises(TypeError):
        convert_data({"county_name": ["BEXAR"]})
