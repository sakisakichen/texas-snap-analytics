import pandas as pd
import pytest

from src.validation.data_quality import (
    _validate_county_name_required,
    _validate_non_negative_numeric_values,
    _validate_report_month_required,
    _validate_reporting_entity,
    _validate_required_numeric_fields,
    _validate_timeliness_required_fields,
    validate_data,
)


def test_county_name_required_passes_when_present_and_non_null() -> None:
    df = pd.DataFrame({"County Name": ["BEXAR", "Dallas", "HARRIS"]})

    result = _validate_county_name_required(df)

    assert result == {"rule": "County Name Required", "status": "PASS", "failed_rows": 0}


def test_county_name_required_fails_for_missing_values() -> None:
    df = pd.DataFrame({"County Name": ["BEXAR", None, "HARRIS"]})

    result = _validate_county_name_required(df)

    assert result == {"rule": "County Name Required", "status": "FAIL", "failed_rows": 1}


def test_county_name_required_fails_when_column_missing() -> None:
    df = pd.DataFrame({"Other": [1, 2, 3]})

    result = _validate_county_name_required(df)

    assert result == {"rule": "County Name Required", "status": "FAIL", "failed_rows": 3}


def test_report_month_required_passes_for_valid_yyyy_mm_format() -> None:
    df = pd.DataFrame({"report_month": ["2024-01", "2024-02", "2024-12"]})

    result = _validate_report_month_required(df)

    assert result == {"rule": "report_month Required", "status": "PASS", "failed_rows": 0}


def test_report_month_required_fails_for_missing_values() -> None:
    df = pd.DataFrame({"report_month": ["2024-01", None, "2024-03"]})

    result = _validate_report_month_required(df)

    assert result == {"rule": "report_month Required", "status": "FAIL", "failed_rows": 1}


def test_report_month_required_fails_for_invalid_yyyy_mm_format() -> None:
    df = pd.DataFrame({"report_month": ["2024-01", "2024/02", "2024-03"]})

    result = _validate_report_month_required(df)

    assert result == {"rule": "report_month Required", "status": "FAIL", "failed_rows": 1}


def test_required_numeric_fields_pass_when_all_required_numbers_present() -> None:
    df = pd.DataFrame(
        {
            "Number of Cases": [10, 15, 20],
            "Number of Eligible Individuals": [100, 200, 300],
            "Total SNAP Payments": [1500.0, 2000.0, 2500.0],
        }
    )

    result = _validate_required_numeric_fields(df)

    assert result == {"rule": "Required Numeric Fields", "status": "PASS", "failed_rows": 0}


def test_required_numeric_fields_fail_when_required_numeric_value_missing() -> None:
    df = pd.DataFrame(
        {
            "Number of Cases": [10, None, 20],
            "Number of Eligible Individuals": [100, 200, 300],
            "Total SNAP Payments": [1500.0, 2000.0, 2500.0],
        }
    )

    result = _validate_required_numeric_fields(df)

    assert result == {"rule": "Required Numeric Fields", "status": "FAIL", "failed_rows": 1}


def test_non_negative_numeric_values_pass_when_values_are_non_negative() -> None:
    df = pd.DataFrame(
        {
            "Number of Cases": [0, 10, 25],
            "Total SNAP Payments": [0.0, 1500.0, 2000.0],
        }
    )

    result = _validate_non_negative_numeric_values(df)

    assert result == {"rule": "Non-negative Numeric Values", "status": "PASS", "failed_rows": 0}


def test_non_negative_numeric_values_fail_when_negative_values_exist() -> None:
    df = pd.DataFrame(
        {
            "Number of Cases": [0, -1, 25],
            "Total SNAP Payments": [0.0, 1500.0, 2000.0],
        }
    )

    result = _validate_non_negative_numeric_values(df)

    assert result == {"rule": "Non-negative Numeric Values", "status": "FAIL", "failed_rows": 1}


def test_valid_reporting_entity_passes_for_known_county_name() -> None:
    df = pd.DataFrame({"County Name": ["BEXAR", "DALLAS", "HARRIS"]})

    result = _validate_reporting_entity(df)

    assert result == {"rule": "Valid Reporting Entity", "status": "PASS", "failed_rows": 0}


def test_valid_reporting_entity_fails_for_invalid_county_name() -> None:
    df = pd.DataFrame({"County Name": ["BEXAR", "NOT_A_COUNTY", "HARRIS"]})

    result = _validate_reporting_entity(df)

    assert result == {"rule": "Valid Reporting Entity", "status": "FAIL", "failed_rows": 1}


def test_validate_data_returns_data_and_summary_dictionary() -> None:
    df = pd.DataFrame(
        {
            "County Name": ["BEXAR", "DALLAS"],
            "report_month": ["2024-01", "2024-02"],
            "Number of Cases": [10, 15],
            "Number of Eligible Individuals": [100, 150],
            "Total SNAP Payments": [1500.0, 2000.0],
        }
    )

    result = validate_data(df)

    assert isinstance(result, dict)
    assert "data" in result
    assert "summary" in result
    assert isinstance(result["data"], pd.DataFrame)
    assert isinstance(result["summary"], dict)


def test_validate_data_summary_contains_status_counts_and_results() -> None:
    df = pd.DataFrame(
        {
            "County Name": ["BEXAR", "DALLAS"],
            "report_month": ["2024-01", "2024-02"],
            "Number of Cases": [10, 15],
            "Number of Eligible Individuals": [100, 150],
            "Total SNAP Payments": [1500.0, 2000.0],
        }
    )

    result = validate_data(df)
    summary = result["summary"]

    assert "status" in summary
    assert "rules_passed" in summary
    assert "rules_failed" in summary
    assert "validation_results" in summary
    assert isinstance(summary["validation_results"], list)


def test_validate_data_pass_dataset_returns_pass_summary() -> None:
    df = pd.DataFrame(
        {
            "County Name": ["BEXAR", "DALLAS"],
            "report_month": ["2024-01", "2024-02"],
            "Number of Cases": [10, 15],
            "Number of Eligible Individuals": [100, 150],
            "Total SNAP Payments": [1500.0, 2000.0],
        }
    )

    result = validate_data(df)

    assert result["summary"]["status"] == "PASS"


def test_validate_data_fail_dataset_returns_fail_summary() -> None:
    df = pd.DataFrame(
        {
            "County Name": ["BEXAR", "NOT_A_COUNTY"],
            "report_month": ["2024-01", "2024-02"],
            "Number of Cases": [10, 15],
            "Number of Eligible Individuals": [100, 150],
            "Total SNAP Payments": [1500.0, 2000.0],
        }
    )

    result = validate_data(df)

    assert result["summary"]["status"] == "FAIL"


def test_validate_data_does_not_modify_input_dataframe() -> None:
    df = pd.DataFrame(
        {
            "County Name": ["BEXAR", "DALLAS"],
            "report_month": ["2024-01", "2024-02"],
            "Number of Cases": [10, 15],
            "Number of Eligible Individuals": [100, 150],
            "Total SNAP Payments": [1500.0, 2000.0],
        }
    )
    original = df.copy(deep=True)

    validate_data(df)

    assert df.equals(original)


def test_validate_data_non_dataframe_input_raises_type_error() -> None:
    with pytest.raises(TypeError):
        validate_data({"County Name": ["BEXAR"]})


def test_timeliness_valid_dataset_passes_blocking_validation() -> None:
    df = pd.DataFrame(
        {
            "reporting_month": ["2024-01", "2024-01"],
            "processing_type": ["Applications", "Redeterminations"],
            "Region": ["01", "02/09"],
            "disposed_count": [100, 80],
            "timely_count": [38, 31],
            "source_percent": [0.38, 0.3875],
            "source_file": ["snap_01.xlsx", "snap_02.xlsx"],
        }
    )

    result = validate_data(df)

    assert result["summary"]["status"] == "PASS"
    assert all(item["status"] != "FAIL" for item in result["summary"]["validation_results"])


def test_timeliness_missing_required_field_fails() -> None:
    df = pd.DataFrame(
        {
            "reporting_month": ["2024-01"],
            "processing_type": ["Applications"],
            "Region": ["01"],
            "disposed_count": [100],
            "source_file": ["snap.xlsx"],
        }
    )

    result = validate_data(df)
    rules = {item["rule"]: item for item in result["summary"]["validation_results"]}

    assert rules["Timeliness Required Fields"]["status"] == "FAIL"
    assert result["summary"]["status"] == "FAIL"


def test_timeliness_missing_source_percent_warns_not_fail() -> None:
    df = pd.DataFrame(
        {
            "reporting_month": ["2024-01"],
            "processing_type": ["Applications"],
            "Region": ["01"],
            "disposed_count": [100],
            "timely_count": [40],
            "source_file": ["snap.xlsx"],
        }
    )

    result = validate_data(df)
    rules = {item["rule"]: item for item in result["summary"]["validation_results"]}

    assert rules["Timeliness Source Percent Warning"]["status"] == "WARNING"
    assert result["summary"]["status"] == "PASS"


def test_timeliness_negative_disposed_count_fails() -> None:
    df = pd.DataFrame(
        {
            "reporting_month": ["2024-01"],
            "processing_type": ["Applications"],
            "Region": ["01"],
            "disposed_count": [-1],
            "timely_count": [0],
            "source_percent": [0.0],
            "source_file": ["snap.xlsx"],
        }
    )

    result = validate_data(df)
    rules = {item["rule"]: item for item in result["summary"]["validation_results"]}

    assert rules["Timeliness Non-negative Counts"]["status"] == "FAIL"
    assert result["summary"]["status"] == "FAIL"


def test_timeliness_negative_timely_count_fails() -> None:
    df = pd.DataFrame(
        {
            "reporting_month": ["2024-01"],
            "processing_type": ["Applications"],
            "Region": ["01"],
            "disposed_count": [10],
            "timely_count": [-1],
            "source_percent": [0.0],
            "source_file": ["snap.xlsx"],
        }
    )

    result = validate_data(df)
    rules = {item["rule"]: item for item in result["summary"]["validation_results"]}

    assert rules["Timeliness Non-negative Counts"]["status"] == "FAIL"


def test_timeliness_timely_exceeds_disposed_fails() -> None:
    df = pd.DataFrame(
        {
            "reporting_month": ["2024-01"],
            "processing_type": ["Applications"],
            "Region": ["01"],
            "disposed_count": [50],
            "timely_count": [51],
            "source_percent": [1.02],
            "source_file": ["snap.xlsx"],
        }
    )

    result = validate_data(df)
    rules = {item["rule"]: item for item in result["summary"]["validation_results"]}

    assert rules["Timeliness Count Relationship"]["status"] == "FAIL"


def test_timeliness_zero_disposed_with_positive_timely_fails() -> None:
    df = pd.DataFrame(
        {
            "reporting_month": ["2024-01"],
            "processing_type": ["Applications"],
            "Region": ["01"],
            "disposed_count": [0],
            "timely_count": [1],
            "source_percent": [0.0],
            "source_file": ["snap.xlsx"],
        }
    )

    result = validate_data(df)
    rules = {item["rule"]: item for item in result["summary"]["validation_results"]}

    assert rules["Timeliness Zero Denominator Rule"]["status"] == "FAIL"


def test_timeliness_zero_counts_are_allowed() -> None:
    df = pd.DataFrame(
        {
            "reporting_month": ["2024-01"],
            "processing_type": ["Applications"],
            "Region": ["01"],
            "disposed_count": [0],
            "timely_count": [0],
            "source_percent": [None],
            "source_file": ["snap.xlsx"],
        }
    )

    result = validate_data(df)
    rules = {item["rule"]: item for item in result["summary"]["validation_results"]}

    assert rules["Timeliness Zero Denominator Rule"]["status"] == "PASS"
    assert rules["Timeliness Source Percent Warning"]["status"] == "WARNING"


def test_timeliness_duplicate_grain_fails_when_reporting_month_is_available() -> None:
    df = pd.DataFrame(
        {
            "reporting_month": ["2024-01", "2024-01"],
            "processing_type": ["Applications", "Applications"],
            "Region": ["01", "01"],
            "disposed_count": [100, 100],
            "timely_count": [80, 80],
            "source_percent": [0.8, 0.8],
            "source_file": ["snap.xlsx", "snap.xlsx"],
        }
    )

    result = validate_data(df)
    rules = {item["rule"]: item for item in result["summary"]["validation_results"]}

    assert rules["Timeliness Grain Uniqueness"]["status"] == "FAIL"


def test_timeliness_unexpected_processing_type_fails() -> None:
    df = pd.DataFrame(
        {
            "reporting_month": ["2024-01"],
            "processing_type": ["Application"],
            "Region": ["01"],
            "disposed_count": [100],
            "timely_count": [80],
            "source_percent": [0.8],
            "source_file": ["snap.xlsx"],
        }
    )

    result = validate_data(df)
    rules = {item["rule"]: item for item in result["summary"]["validation_results"]}

    assert rules["Timeliness Processing Type"]["status"] == "FAIL"


def test_timeliness_02_09_region_is_not_blocking() -> None:
    df = pd.DataFrame(
        {
            "reporting_month": ["2024-01"],
            "processing_type": ["Applications"],
            "Region": ["02/09"],
            "disposed_count": [100],
            "timely_count": [80],
            "source_percent": [0.8],
            "source_file": ["snap.xlsx"],
        }
    )

    result = validate_data(df)
    rules = {item["rule"]: item for item in result["summary"]["validation_results"]}

    assert rules["Timeliness Region Warning"]["status"] == "PASS"


def test_timeliness_undocumented_region_warns_but_keeps_row() -> None:
    df = pd.DataFrame(
        {
            "reporting_month": ["2024-01"],
            "processing_type": ["Applications"],
            "Region": ["MEPD"],
            "disposed_count": [100],
            "timely_count": [80],
            "source_percent": [0.8],
            "source_file": ["snap.xlsx"],
        }
    )

    result = validate_data(df)
    rules = {item["rule"]: item for item in result["summary"]["validation_results"]}

    assert rules["Timeliness Region Warning"]["status"] == "WARNING"
    assert result["data"].iloc[0]["Region"] == "MEPD"


def test_timeliness_source_percent_reconciliation_within_tolerance_passes() -> None:
    df = pd.DataFrame(
        {
            "reporting_month": ["2024-01"],
            "processing_type": ["Applications"],
            "Region": ["01"],
            "disposed_count": [100],
            "timely_count": [38],
            "source_percent": [0.38],
            "source_file": ["snap.xlsx"],
        }
    )

    result = validate_data(df)
    rules = {item["rule"]: item for item in result["summary"]["validation_results"]}

    assert rules["Timeliness Source Percent Reconciliation"]["status"] == "PASS"


def test_timeliness_source_percent_reconciliation_outside_tolerance_fails() -> None:
    df = pd.DataFrame(
        {
            "reporting_month": ["2024-01"],
            "processing_type": ["Applications"],
            "Region": ["01"],
            "disposed_count": [100],
            "timely_count": [38],
            "source_percent": [0.39],
            "source_file": ["snap.xlsx"],
        }
    )

    result = validate_data(df)
    rules = {item["rule"]: item for item in result["summary"]["validation_results"]}

    assert rules["Timeliness Source Percent Reconciliation"]["status"] == "FAIL"


def test_timeliness_missing_percent_does_not_drop_row() -> None:
    df = pd.DataFrame(
        {
            "reporting_month": ["2024-01"],
            "processing_type": ["Applications"],
            "Region": ["MEPD"],
            "disposed_count": [100],
            "timely_count": [80],
            "source_file": ["snap.xlsx"],
        }
    )

    result = validate_data(df)
    assert result["data"].shape[0] == 1
    assert result["data"].iloc[0]["Region"] == "MEPD"
    assert result["summary"]["status"] == "PASS"


def test_validate_data_timeliness_does_not_mutate_input_dataframe() -> None:
    df = pd.DataFrame(
        {
            "reporting_month": ["2024-01"],
            "processing_type": ["Applications"],
            "Region": ["01"],
            "disposed_count": [100],
            "timely_count": [80],
            "source_percent": [0.8],
            "source_file": ["snap.xlsx"],
        }
    )
    original = df.copy(deep=True)

    validate_data(df)

    assert df.equals(original)

def test_timeliness_required_fields_allows_missing_measures_for_mepd_only() -> None:
    df = pd.DataFrame(
        {
            "processing_type": ["Applications", "Applications"],
            "Region": ["MEPD", "01"],
            "disposed_count": [pd.NA, 100],
            "timely_count": [pd.NA, 90],
            "source_percent": [pd.NA, 0.90],
            "reporting_month": ["2024-04", "2024-04"],
            "source_file": [
                "timeliness-snap-april-2024.xlsx",
                "timeliness-snap-april-2024.xlsx",
            ],
        }
    )

    result = _validate_timeliness_required_fields(df)

    assert result["status"] == "PASS"
    assert result["failed_rows"] == 0

def test_timeliness_required_fields_still_fails_missing_measures_for_regular_region() -> None:
    df = pd.DataFrame(
        {
            "processing_type": ["Applications"],
            "Region": ["01"],
            "disposed_count": [pd.NA],
            "timely_count": [pd.NA],
            "source_percent": [pd.NA],
            "reporting_month": ["2024-04"],
            "source_file": ["timeliness-snap-april-2024.xlsx"],
        }
    )

    result = _validate_timeliness_required_fields(df)

    assert result["status"] == "FAIL"
    assert result["failed_rows"] == 1