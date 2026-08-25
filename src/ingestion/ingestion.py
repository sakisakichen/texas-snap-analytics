"""Bronze-layer ingestion for SNAP Eligibility and Timeliness source datasets."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def _resolve_existing_data_dir(data_dir: str | Path) -> Path:
    """Resolve the canonical repo data directory while tolerating the repository's trailing-space path quirk."""
    candidate = Path(data_dir)
    if candidate.exists():
        return candidate

    alternate = Path(f"{candidate} ")
    if alternate.exists():
        return alternate

    return candidate


def _extract_reporting_period(file_name: str) -> str:
    """Extract the reporting period in YYYY-MM format from the source file name."""
    match = re.search(
        r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\D+(\d{4})",
        file_name.lower(),
    )
    if match is None:
        raise ValueError(f"Filename does not match the expected reporting period format: {file_name}")

    month_name = match.group(1)
    year = match.group(2)
    month_map = {
        "jan": "01",
        "january": "01",
        "feb": "02",
        "february": "02",
        "mar": "03",
        "march": "03",
        "apr": "04",
        "april": "04",
        "may": "05",
        "jun": "06",
        "june": "06",
        "jul": "07",
        "july": "07",
        "aug": "08",
        "august": "08",
        "sep": "09",
        "september": "09",
        "oct": "10",
        "october": "10",
        "nov": "11",
        "november": "11",
        "dec": "12",
        "december": "12",
    }
    return f"{year}-{month_map[month_name]}"


def _resolve_sheet_name(file_path: str | Path) -> str:
    """Resolve the canonical SNAP sheet name across case and spacing variants."""
    excel_file = pd.ExcelFile(file_path, engine="xlrd")
    sheet_names = excel_file.sheet_names

    canonical = "SNAP CNTY WEB DATA"
    normalized = {name.strip().upper().replace(" ", ""): name for name in sheet_names}
    if canonical.replace(" ", "") in normalized:
        return normalized[canonical.replace(" ", "")]

    if len(sheet_names) == 1:
        return sheet_names[0]

    raise ValueError(f"No compatible SNAP sheet found in workbook: {file_path}")


def _read_eligibility_workbook(file_path: str | Path) -> pd.DataFrame:
    """Read a single Eligibility workbook in the established repository pattern."""
    sheet_name = _resolve_sheet_name(file_path)
    frame = pd.read_excel(
        file_path,
        sheet_name=sheet_name,
        header=1,
    )

    if "County Name" in frame.columns:
        state_total_mask = frame["County Name"].astype(str).str.startswith("State Total")
        if not state_total_mask.any():
            raise ValueError(f"State Total boundary not found in workbook: {file_path.name}")

        state_total_index = frame.index[state_total_mask][0]
        frame = frame.loc[:state_total_index].copy()

    frame["report_month"] = _extract_reporting_period(file_path.name)
    frame["source_file"] = file_path.name
    return frame


def _read_timeliness_workbook(file_path: str | Path) -> pd.DataFrame:
    """Read a raw Timeliness workbook while preserving the workbook cell structure for later Module 2 cleaning.

    The workbook is kept as a flat tabular matrix, and each row is tagged with
    report_month and source_file metadata so the raw spreadsheet boundaries remain
    intact without performing any transformation beyond ingestion.
    """
    raw_frame = pd.read_excel(file_path, header=None)
    raw_frame = raw_frame.map(lambda value: "" if pd.isna(value) else str(value))
    raw_frame["report_month"] = _extract_reporting_period(file_path.name)
    raw_frame["source_file"] = file_path.name
    return raw_frame


def read_source_files(
    data_dir: str | Path = "data/raw/eligibility/2024",
    dataset_type: str = "eligibility",
) -> List[pd.DataFrame]:
    """Read monthly source workbooks for the requested dataset while preserving ingestion metadata."""
    source_dir = _resolve_existing_data_dir(data_dir)
    frames: List[pd.DataFrame] = []

    for file_path in sorted(source_dir.glob("*.xls" if dataset_type == "eligibility" else "*.xlsx")):
        if file_path.name.startswith("~$"):
            continue
        if dataset_type == "timeliness":
            frames.append(_read_timeliness_workbook(file_path))
        else:
            frames.append(_read_eligibility_workbook(file_path))

    return frames


def combine_source_files(frames: List[pd.DataFrame], dataset_type: str = "eligibility") -> pd.DataFrame:
    """Combine the monthly source files into one Bronze DataFrame.

    Eligibility Bronze stacks rows from each workbook. Timeliness Bronze preserves
    each raw workbook as a standalone record so the workbook section boundaries are not destroyed.
    """
    if not frames:
        return pd.DataFrame()

    if dataset_type == "timeliness":
        return pd.concat(frames, ignore_index=True)

    return pd.concat(frames, ignore_index=True)


def save_bronze_parquet(
    combined_df: pd.DataFrame,
    output_path: str | Path = "data/bronze/eligibility/snap_eligibility_2024.parquet",
) -> Path:
    """Save the combined Bronze dataset as a Parquet file without altering source values."""
    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    combined_df.to_parquet(target_path, index=False)
    return target_path


def main() -> None:
    """Run the Bronze ingestion pipeline for the raw eligibility files."""
    frames = read_source_files()
    combined_df = combine_source_files(frames)
    output_path = save_bronze_parquet(combined_df)

    print(f"Bronze ingestion complete: output={output_path}, rows={combined_df.shape[0]}, columns={combined_df.shape[1]}")

    if not combined_df.empty and "County Name" in combined_df.columns:
        print(combined_df["County Name"].unique())

if __name__ == "__main__":
    main()
