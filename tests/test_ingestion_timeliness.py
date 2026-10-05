from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.ingestion.ingestion import combine_source_files, read_source_files, save_bronze_parquet


ELIGIBILITY_RAW_DIR = Path("data/raw/eligibility/2024")
TIMELINESS_RAW_DIR = Path("data/raw/timeliness/2024 ")


def test_timeliness_files_are_discovered() -> None:
    frames = read_source_files(data_dir=TIMELINESS_RAW_DIR, dataset_type="timeliness")
    assert len(frames) == 12
    assert all("report_month" in frame.columns for frame in frames)
    assert all("source_file" in frame.columns for frame in frames)


def test_timeliness_report_month_is_derived_from_filename() -> None:
    frames = read_source_files(data_dir=TIMELINESS_RAW_DIR, dataset_type="timeliness")
    report_months = sorted({frame["report_month"].iloc[0] for frame in frames})
    assert report_months == [f"2024-{month:02d}" for month in range(1, 13)]


def test_timeliness_source_file_preserves_original_filename() -> None:
    frames = read_source_files(data_dir=TIMELINESS_RAW_DIR, dataset_type="timeliness")
    names = {frame["source_file"].iloc[0] for frame in frames}
    assert "timeliness-snap-jan-2024.xlsx" in names
    assert "timeliness-snap-april-2024.xlsx" in names


def test_timeliness_combined_bronze_keeps_monthly_workbook_boundaries() -> None:
    frames = read_source_files(data_dir=TIMELINESS_RAW_DIR, dataset_type="timeliness")
    combined = combine_source_files(frames, dataset_type="timeliness")

    assert len(combined) >= 12
    assert "report_month" in combined.columns
    assert "source_file" in combined.columns
    assert combined["report_month"].nunique() == 12
    assert combined["source_file"].nunique() == 12


def test_eligibility_ingestion_remains_backward_compatible() -> None:
    frames = read_source_files(data_dir=ELIGIBILITY_RAW_DIR, dataset_type="eligibility")
    assert len(frames) == 12
    assert all("report_month" in frame.columns for frame in frames)
    assert all("source_file" in frame.columns for frame in frames)
    assert all("County Name" in frame.columns for frame in frames)


def test_timeliness_output_is_separate_from_eligibility_output(tmp_path: Path) -> None:
    timeliness_output = tmp_path / "timeliness" / "snap_timeliness_2024.parquet"
    eligibility_output = tmp_path / "eligibility" / "snap_eligibility_2024.parquet"

    timeliness_frames = read_source_files(data_dir=TIMELINESS_RAW_DIR, dataset_type="timeliness")
    timeliness_df = combine_source_files(timeliness_frames, dataset_type="timeliness")
    save_bronze_parquet(timeliness_df, output_path=timeliness_output)
    save_bronze_parquet(pd.DataFrame({"County Name": ["BEXAR"]}), output_path=eligibility_output)

    assert timeliness_output.exists()
    assert eligibility_output.exists()
    assert timeliness_output != eligibility_output


def test_timeliness_bronze_ingestion_does_not_perform_silver_transforms() -> None:
    frames = read_source_files(data_dir=TIMELINESS_RAW_DIR, dataset_type="timeliness")
    combined = combine_source_files(frames, dataset_type="timeliness")

    assert "report_month" in combined.columns
    assert "source_file" in combined.columns
    assert "processing_type" not in combined.columns
    assert "disposed_count" not in combined.columns
    assert "timely_count" not in combined.columns
    assert "source_percent" not in combined.columns
