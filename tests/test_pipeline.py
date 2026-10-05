from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.pipelines.silver_pipeline import ValidationError, run_silver_pipeline


def _eligibility_bronze_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "County Name": ["BEXAR", "DALLAS"],
            "report_month": ["2024-01", "2024-01"],
            "source_file": ["snap_01.xls", "snap_02.xls"],
            "Number of Cases": [10, 20],
            "Number of Eligible Individuals": [100, 200],
            "Total SNAP Payments": [500, 1000],
        }
    )


def _timeliness_workbook_df(report_month: str, source_file: str, first_region: str = "01", second_region: str = "02/09") -> pd.DataFrame:
    raw_df = pd.DataFrame(
        [
            ["SNAP Food Benefits Timeliness", None, None, None],
            [None, None, None, None],
            ["SNAP Food Benefits APPLICATIONS", None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            [first_region, "100", "38", "38.0%"],
            ["TOTAL", "100", "38", "38.0%"],
            ["SNAP Food Benefits REDETERMINATIONS", None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            [second_region, "80", "31", "38.75%"],
            ["TOTAL", "80", "31", "38.75%"],
        ],
        columns=[0, 1, 2, 3],
    )
    raw_df["report_month"] = report_month
    raw_df["source_file"] = source_file
    return raw_df


def _timeliness_bronze_df() -> pd.DataFrame:
    return _timeliness_workbook_df("2024-04", "timeliness_april_2024.xlsx")


def test_eligibility_pipeline_remains_backward_compatible(tmp_path: Path) -> None:
    bronze_path = tmp_path / "eligibility_bronze.parquet"
    silver_path = tmp_path / "silver" / "eligibility" / "silver.parquet"
    report_path = tmp_path / "reports" / "eligibility_report.json"

    _eligibility_bronze_df().to_parquet(bronze_path, index=False)

    result = run_silver_pipeline(
        bronze_path=bronze_path,
        silver_path=silver_path,
        quality_report_path=report_path,
        dataset_type="eligibility",
    )

    assert result["summary"]["status"] == "PASS"
    assert silver_path.exists()
    assert report_path.exists()
    assert result["data"].shape[0] == 2


def test_timeliness_pipeline_routes_and_writes_trusted_silver(tmp_path: Path) -> None:
    bronze_path = tmp_path / "timeliness_april_2024.parquet"
    silver_path = tmp_path / "silver" / "timeliness" / "trusted_timeliness.parquet"
    report_path = tmp_path / "reports" / "timeliness_report.json"

    _timeliness_bronze_df().to_parquet(bronze_path, index=False)

    result = run_silver_pipeline(
        bronze_path=bronze_path,
        silver_path=silver_path,
        quality_report_path=report_path,
        dataset_type="timeliness",
    )

    assert result["summary"]["status"] == "PASS"
    assert silver_path.exists()
    assert report_path.exists()
    assert result["report"]["timeliness_workbooks"][0]["timeliness_section_totals"]["Applications"]["Region"] == "TOTAL"
    assert result["report"]["dataset_type"] == "timeliness"
    assert set(["reporting_month", "source_file"]).issubset(result["data"].columns)
    assert "TOTAL" not in result["data"]["Region"].astype(str).tolist()
    assert result["data"]["reporting_month"].tolist() == ["2024-04", "2024-04"]
    assert result["data"]["source_file"].tolist() == ["timeliness_april_2024.xlsx", "timeliness_april_2024.xlsx"]


def test_timeliness_multiple_workbooks_are_processed_independently(tmp_path: Path) -> None:
    jan_df = _timeliness_workbook_df("2024-01", "timeliness-snap-jan-2024.xlsx", first_region="01", second_region="02/09")
    feb_df = _timeliness_workbook_df("2024-02", "timeliness-snap-feb-2024.xlsx", first_region="01", second_region="03")
    combined = pd.concat([jan_df, feb_df], ignore_index=True)

    bronze_path = tmp_path / "timeliness_combined.parquet"
    silver_path = tmp_path / "silver" / "timeliness" / "combined_timeliness.parquet"
    report_path = tmp_path / "reports" / "timeliness_combined_report.json"
    combined.to_parquet(bronze_path, index=False)

    result = run_silver_pipeline(
        bronze_path=bronze_path,
        silver_path=silver_path,
        quality_report_path=report_path,
        dataset_type="timeliness",
    )

    months = sorted(result["data"]["reporting_month"].unique().tolist())
    assert months == ["2024-01", "2024-02"]
    assert set(result["data"]["source_file"].unique().tolist()) == {
        "timeliness-snap-jan-2024.xlsx",
        "timeliness-snap-feb-2024.xlsx",
    }
    assert result["data"].shape[0] == 4
    assert report_path.exists()
    assert silver_path.exists()


def test_timeliness_workbook_metadata_mismatch_raises_clear_error(tmp_path: Path) -> None:
    jan_df = _timeliness_workbook_df("2024-01", "timeliness-snap-jan-2024.xlsx")
    jan_df = pd.concat(
        [
            jan_df,
            jan_df.assign(report_month="2024-02", source_file="timeliness-snap-jan-2024.xlsx"),
        ],
        ignore_index=True,
    )

    bronze_path = tmp_path / "bad_timing.parquet"
    jan_df.to_parquet(bronze_path, index=False)

    with pytest.raises(ValueError, match="multiple distinct report_month values"):
        run_silver_pipeline(
            bronze_path=bronze_path,
            silver_path=tmp_path / "silver" / "timeliness" / "bad.parquet",
            quality_report_path=tmp_path / "reports" / "bad_report.json",
            dataset_type="timeliness",
        )


def test_timeliness_pipeline_warning_only_still_publishes_silver(tmp_path: Path) -> None:
    bronze_df = pd.DataFrame(
        [
            ["SNAP Food Benefits Timeliness", None, None, None],
            [None, None, None, None],
            ["SNAP Food Benefits APPLICATIONS", None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            ["MEPD", "100", "80", "80.0%"],
            ["TOTAL", "100", "80", "80.0%"],
            ["SNAP Food Benefits REDETERMINATIONS", None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            ["01", "90", "72", "80.0%"],
            ["TOTAL", "90", "72", "80.0%"],
        ],
        columns=[0, 1, 2, 3],
    )
    bronze_df["reporting_month"] = "2024-04"
    bronze_df["source_file"] = "timeliness_warning.xlsx"

    bronze_path = tmp_path / "timeliness_warning.parquet"
    silver_path = tmp_path / "silver" / "timeliness_warning.parquet"
    report_path = tmp_path / "reports" / "timeliness_warning_report.json"
    bronze_df.to_parquet(bronze_path, index=False)

    result = run_silver_pipeline(
        bronze_path=bronze_path,
        silver_path=silver_path,
        quality_report_path=report_path,
        dataset_type="timeliness",
    )

    assert result["summary"]["status"] == "PASS"
    assert report_path.exists()
    assert silver_path.exists()
    assert json.loads(report_path.read_text(encoding="utf-8"))["summary"]["status"] == "PASS"


def test_timeliness_pipeline_fail_does_not_publish_and_raises_validation_error(tmp_path: Path) -> None:
    bronze_df = pd.DataFrame(
        [
            ["SNAP Food Benefits Timeliness", None, None, None],
            [None, None, None, None],
            ["SNAP Food Benefits APPLICATIONS", None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            ["01", "50", "60", "120.0%"],
            ["TOTAL", "50", "60", "120.0%"],
            ["SNAP Food Benefits REDETERMINATIONS", None, None, None],
            ["Region", "Disposed", "Timely", "Percent"],
            ["02/09", "40", "30", "75.0%"],
            ["TOTAL", "40", "30", "75.0%"],
        ],
        columns=[0, 1, 2, 3],
    )
    bronze_df["reporting_month"] = "2024-04"
    bronze_df["source_file"] = "timeliness_fail.xlsx"

    bronze_path = tmp_path / "timeliness_fail.parquet"
    silver_path = tmp_path / "silver" / "timeliness_fail.parquet"
    report_path = tmp_path / "reports" / "timeliness_fail_report.json"
    bronze_df.to_parquet(bronze_path, index=False)

    with pytest.raises(ValidationError):
        run_silver_pipeline(
            bronze_path=bronze_path,
            silver_path=silver_path,
            quality_report_path=report_path,
            dataset_type="timeliness",
        )

    assert report_path.exists()
    assert not silver_path.exists()
    report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert report_payload["summary"]["status"] == "FAIL"
