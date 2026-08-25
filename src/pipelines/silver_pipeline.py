"""Silver-layer pipeline orchestration for standardized SNAP data."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from src.transformation.structure_cleaning import clean_structure
from src.transformation.standardization import standardize_data
from src.transformation.type_conversion import convert_data
from src.validation.data_quality import validate_data


DEFAULT_BRONZE_PATH = Path("data/bronze/eligibility/snap_eligibility_2024.parquet")
DEFAULT_SILVER_PATH = Path("data/silver/eligibility/snap_eligibility_2024.parquet")
DEFAULT_QUALITY_REPORT_PATH = Path("data/quality_reports/silver_validation_report.json")

DEFAULT_TIMELINESS_BRONZE_PATH = Path("data/bronze/timeliness/timeliness_2024.parquet")
DEFAULT_TIMELINESS_SILVER_PATH = Path("data/silver/timeliness/timeliness_2024.parquet")
DEFAULT_TIMELINESS_QUALITY_REPORT_PATH = Path("data/quality_reports/timeliness_validation_report.json")


class ValidationError(ValueError):
    """Raised when the Silver dataset fails business validation."""


def _resolve_pipeline_paths(
    dataset_type: str,
    bronze_path: str | Path,
    silver_path: str | Path,
    quality_report_path: str | Path,
) -> tuple[Path, Path, Path]:
    """Resolve dataset-specific defaults while preserving the legacy eligibility defaults."""
    bronze_target = Path(bronze_path)
    silver_target = Path(silver_path)
    report_target = Path(quality_report_path)

    if dataset_type == "timeliness":
        if bronze_target == DEFAULT_BRONZE_PATH:
            bronze_target = DEFAULT_TIMELINESS_BRONZE_PATH
        if silver_target == DEFAULT_SILVER_PATH:
            silver_target = DEFAULT_TIMELINESS_SILVER_PATH
        if report_target == DEFAULT_QUALITY_REPORT_PATH:
            report_target = DEFAULT_TIMELINESS_QUALITY_REPORT_PATH

    return bronze_target, silver_target, report_target


def _infer_reporting_month_from_source(bronze_path: str | Path) -> str:
    """Infer reporting_month from explicit source metadata when it is not already present."""
    source_name = Path(bronze_path).name.lower()

    year_month_match = re.search(r"((?:19|20)\d{2})[-_](0[1-9]|1[0-2])", source_name)
    if year_month_match is not None:
        return f"{year_month_match.group(1)}-{year_month_match.group(2)}"

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
    month_match = re.search(
        r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\D*(\d{4})",
        source_name,
    )
    if month_match is not None:
        month_code = month_map.get(month_match.group(1), None)
        if month_code is not None:
            return f"{month_match.group(2)}-{month_code}"

    raise ValueError(
        "Unable to derive reporting_month from the Bronze source path. "
        "Provide reporting_month metadata in the source dataset or use a supported file naming convention."
    )


def _strip_metadata_columns(df: pd.DataFrame, dataset_type: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Keep legacy eligibility metadata intact while removing raw workbook metadata before Timeliness structure parsing."""
    metadata_columns = [column for column in ["report_month", "reporting_month", "source_file"] if column in df.columns]
    metadata_df = df[metadata_columns].copy() if metadata_columns else pd.DataFrame(index=df.index)

    if dataset_type == "timeliness":
        cleaned_df = df.drop(columns=metadata_columns, errors="ignore").copy()
    else:
        cleaned_df = df.copy()

    return cleaned_df, metadata_df


def _ensure_dataset_metadata(df: pd.DataFrame, bronze_path: str | Path, dataset_type: str, metadata_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Guarantee the metadata required by the current dataset contract before validation."""
    working_df = df.copy()

    if dataset_type == "eligibility":
        if "report_month" not in working_df.columns and metadata_df is not None and "report_month" in metadata_df.columns:
            working_df["report_month"] = metadata_df["report_month"].copy()
        if "report_month" not in working_df.columns:
            working_df["report_month"] = _infer_reporting_month_from_source(bronze_path)
        if "source_file" not in working_df.columns and metadata_df is not None and "source_file" in metadata_df.columns:
            working_df["source_file"] = metadata_df["source_file"].copy()
        if "source_file" not in working_df.columns:
            working_df["source_file"] = Path(bronze_path).name
        return working_df

    if metadata_df is not None and not metadata_df.empty:
        if "report_month" in metadata_df.columns and "reporting_month" not in working_df.columns:
            report_month_values = metadata_df["report_month"].dropna()
            if not report_month_values.empty:
                working_df["reporting_month"] = report_month_values.iloc[0]
        if "reporting_month" in metadata_df.columns and "reporting_month" not in working_df.columns:
            report_month_values = metadata_df["reporting_month"].dropna()
            if not report_month_values.empty:
                working_df["reporting_month"] = report_month_values.iloc[0]
        if "source_file" in metadata_df.columns and "source_file" not in working_df.columns:
            source_values = metadata_df["source_file"].dropna()
            if not source_values.empty:
                working_df["source_file"] = source_values.iloc[0]

    if "report_month" in working_df.columns and "reporting_month" not in working_df.columns:
        working_df["reporting_month"] = working_df["report_month"]

    if "reporting_month" not in working_df.columns:
        working_df["reporting_month"] = _infer_reporting_month_from_source(bronze_path)

    if "source_file" not in working_df.columns:
        working_df["source_file"] = Path(bronze_path).name

    if "reporting_month" in working_df.columns and working_df["reporting_month"].nunique() == 1:
        working_df["reporting_month"] = working_df["reporting_month"].iloc[0]
    if "source_file" in working_df.columns and working_df["source_file"].nunique() == 1:
        working_df["source_file"] = working_df["source_file"].iloc[0]

    return working_df


def _write_validation_report(
    quality_report_path: str | Path,
    report_payload: Dict[str, Any],
) -> Path:
    """Write the validation report for every pipeline run."""
    report_target = Path(quality_report_path)
    report_target.parent.mkdir(parents=True, exist_ok=True)
    with report_target.open("w", encoding="utf-8") as report_file:
        json.dump(report_payload, report_file, indent=2, default=str)
    return report_target


def _timeliness_month_column(df: pd.DataFrame) -> str | None:
    """Return the canonical month metadata column name for Timeliness records."""
    for candidate in ("report_month", "reporting_month"):
        if candidate in df.columns:
            return candidate
    return None


def _clean_timeliness_workbook(workbook_df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """Process one Timeliness workbook at a time, preserving workbook metadata and returning the structural control summary."""
    month_column = _timeliness_month_column(workbook_df)
    workbook_structure_df = workbook_df.drop(columns=["report_month", "reporting_month", "source_file"], errors="ignore").copy()
    cleaned_result = clean_structure(workbook_structure_df)
    cleaned_df = cleaned_result["cleaned_df"].copy()
    structure_summary = cleaned_result.get("summary", {})

    if month_column is not None:
        cleaned_df["reporting_month"] = workbook_df[month_column].iloc[0]
    if "source_file" in workbook_df.columns:
        cleaned_df["source_file"] = workbook_df["source_file"].iloc[0]

    return cleaned_df, structure_summary


def _combine_timeliness_workbooks(bronze_df: pd.DataFrame) -> tuple[pd.DataFrame, list[Dict[str, Any]]]:
    """Split a combined Timeliness Bronze dataset into workbook-level structure-cleaning units."""
    if bronze_df.empty:
        return bronze_df.copy(), []

    workbook_frames: list[pd.DataFrame] = []
    workbook_summaries: list[Dict[str, Any]] = []

    for source_file, group in bronze_df.groupby("source_file", sort=True):
        group = group.copy()
        month_column = _timeliness_month_column(group)
        if month_column is None:
            raise ValueError(
                f"Timeliness workbook '{source_file}' is missing both report_month and reporting_month metadata."
            )

        unique_months = group[month_column].dropna().astype(str).unique().tolist()
        if len(set(unique_months)) > 1:
            raise ValueError(
                f"Timeliness workbook '{source_file}' contains multiple distinct report_month values: {unique_months}."
            )

        workbook_df, structure_summary = _clean_timeliness_workbook(group)
        workbook_frames.append(workbook_df)
        workbook_summaries.append(
            {
                "source_file": source_file,
                "reporting_month": unique_months[0] if unique_months else None,
                "timeliness_section_totals": structure_summary.get("timeliness_section_totals"),
            }
        )

    if not workbook_frames:
        return bronze_df.copy(), workbook_summaries

    combined_cleaned_df = pd.concat(workbook_frames, ignore_index=True)
    return combined_cleaned_df, workbook_summaries


def run_silver_pipeline(
    bronze_path: str | Path = DEFAULT_BRONZE_PATH,
    silver_path: str | Path = DEFAULT_SILVER_PATH,
    quality_report_path: str | Path = DEFAULT_QUALITY_REPORT_PATH,
    dataset_type: str = "eligibility",
) -> Dict[str, Any]:
    """Run the Bronze-to-Silver pipeline via the existing public module APIs."""
    bronze_target, silver_target, report_target = _resolve_pipeline_paths(
        dataset_type=dataset_type,
        bronze_path=bronze_path,
        silver_path=silver_path,
        quality_report_path=quality_report_path,
    )

    bronze_df = pd.read_parquet(bronze_target)

    if dataset_type == "timeliness":
        clean_df, workbook_summaries = _combine_timeliness_workbooks(bronze_df)
        structure_summary = {"timeliness_workbooks": workbook_summaries}
    else:
        bronze_structure_df, metadata_df = _strip_metadata_columns(bronze_df, dataset_type)
        cleaned_result = clean_structure(bronze_structure_df)
        clean_df = cleaned_result["cleaned_df"]
        structure_summary = cleaned_result.get("summary", {})
        metadata_df = metadata_df

    standardized_df, _ = standardize_data(clean_df)

    converted_result = convert_data(standardized_df)
    converted_df = converted_result["data"]

    if dataset_type == "eligibility":
        bronze_structure_df, metadata_df = _strip_metadata_columns(bronze_df, dataset_type)
        converted_df = _ensure_dataset_metadata(converted_df, bronze_target, dataset_type, metadata_df)
    else:
        converted_df = _ensure_dataset_metadata(converted_df, bronze_target, dataset_type, pd.DataFrame({}))

    validated_result = validate_data(converted_df)
    validation_summary = validated_result["summary"]

    report_payload = {
        "dataset_type": dataset_type,
        "summary": validation_summary,
        "structure_summary": structure_summary,
        "timeliness_section_totals": structure_summary.get("timeliness_section_totals"),
        "timeliness_workbooks": structure_summary.get("timeliness_workbooks", []),
        "source_metadata": {
            "bronze_path": str(bronze_target),
            "silver_path": str(silver_target),
            "report_path": str(report_target),
            "reporting_month": converted_df["reporting_month"].iloc[0] if "reporting_month" in converted_df.columns and not converted_df.empty else None,
            "source_file": converted_df["source_file"].iloc[0] if "source_file" in converted_df.columns and not converted_df.empty else None,
        },
        "input_row_count": int(bronze_df.shape[0]),
        "output_row_count": int(converted_df.shape[0]),
    }

    _write_validation_report(report_target, report_payload)

    if validation_summary["status"] == "FAIL":
        raise ValidationError(
            f"Silver validation failed. Report saved to {report_target}."
        )

    silver_target = Path(silver_target)
    silver_target.parent.mkdir(parents=True, exist_ok=True)
    converted_df.to_parquet(silver_target, index=False)
    return {
        "data": converted_df,
        "summary": validation_summary,
        "report": report_payload,
    }


if __name__ == "__main__":
    run_silver_pipeline()
