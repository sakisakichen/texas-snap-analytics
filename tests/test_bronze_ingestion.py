from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest


DATASET_PATH = Path("data/bronze/eligibility/snap_eligibility_2024.parquet")
EXPECTED_TOTAL_ROWS = 3084
EXPECTED_ROWS_PER_MONTH = 257
EXPECTED_UNIQUE_MONTHS = 12
EXPECTED_UNIQUE_SOURCE_FILES = 12
EXPECTED_REPORTING_PERIODS = [f"2024-{month:02d}" for month in range(1, 13)]
REQUIRED_METADATA_COLUMNS = ["report_month", "source_file"]
FORBIDDEN_LAYOUT_PREFIXES = ["Data Source:", "Prepared by", "Filename:", "Revised:", "HHSC changed"]
COUNTY_NAME_COLUMN = "County Name"


@pytest.fixture
def bronze_df() -> pd.DataFrame:
    return pd.read_parquet(DATASET_PATH)


def test_bronze_parquet_file_exists() -> None:
    assert DATASET_PATH.exists(), f"Bronze dataset not found: {DATASET_PATH}"


def test_bronze_dataset_has_expected_row_count(bronze_df: pd.DataFrame) -> None:
    assert len(bronze_df) == EXPECTED_TOTAL_ROWS


def test_bronze_dataset_has_12_unique_report_month_values(bronze_df: pd.DataFrame) -> None:
    assert bronze_df["report_month"].nunique() == EXPECTED_UNIQUE_MONTHS


def test_bronze_dataset_has_expected_reporting_periods(bronze_df: pd.DataFrame) -> None:
    unique_periods = sorted(bronze_df["report_month"].unique().tolist())
    assert unique_periods == EXPECTED_REPORTING_PERIODS


def test_bronze_dataset_has_12_unique_source_files(bronze_df: pd.DataFrame) -> None:
    assert bronze_df["source_file"].nunique() == EXPECTED_UNIQUE_SOURCE_FILES


def test_each_report_month_has_257_rows(bronze_df: pd.DataFrame) -> None:
    counts = bronze_df.groupby("report_month").size()
    assert counts.tolist() == [EXPECTED_ROWS_PER_MONTH] * EXPECTED_UNIQUE_MONTHS


def test_required_metadata_columns_exist(bronze_df: pd.DataFrame) -> None:
    for column in REQUIRED_METADATA_COLUMNS:
        assert column in bronze_df.columns


def test_footer_note_rows_are_not_present_in_county_name(bronze_df: pd.DataFrame) -> None:
    county_names = bronze_df[COUNTY_NAME_COLUMN].astype(str)

    for prefix in FORBIDDEN_LAYOUT_PREFIXES:
        assert not county_names.str.startswith(prefix).any(), (
            f"Found County Name values beginning with '{prefix}'"
        )
