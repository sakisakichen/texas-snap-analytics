"""Silver-layer pipeline orchestration for standardized SNAP data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from src.transformation.structure_cleaning import clean_structure
from src.transformation.standardization import standardize_data
from src.transformation.type_conversion import convert_data
from src.validation.data_quality import validate_data


DEFAULT_BRONZE_PATH = Path("data/bronze/eligibility/snap_eligibility_2024.parquet")
DEFAULT_SILVER_PATH = Path("data/silver/texas_snap_eligibility_2024.parquet")
DEFAULT_QUALITY_REPORT_PATH = Path("data/quality_reports/silver_validation_report.json")


class ValidationError(ValueError):
    """Raised when the Silver dataset fails business validation."""


def run_silver_pipeline(
    bronze_path: str | Path = DEFAULT_BRONZE_PATH,
    silver_path: str | Path = DEFAULT_SILVER_PATH,
    quality_report_path: str | Path = DEFAULT_QUALITY_REPORT_PATH,
) -> Dict[str, Any]:
    """Run the Bronze-to-Silver pipeline via the existing public module APIs."""
    bronze_df = pd.read_parquet(bronze_path)

    cleaned_result = clean_structure(bronze_df)
    cleaned_df = cleaned_result["cleaned_df"]

    standardized_df, _ = standardize_data(cleaned_df)

    converted_result = convert_data(standardized_df)
    converted_df = converted_result["data"]

    validated_result = validate_data(converted_df)
    validation_summary = validated_result["summary"]

    if validation_summary["status"] == "PASS":
        silver_target = Path(silver_path)
        silver_target.parent.mkdir(parents=True, exist_ok=True)
        converted_df.to_parquet(silver_target, index=False)
        return {
            "data": converted_df,
            "summary": validation_summary,
        }

    quality_report_target = Path(quality_report_path)
    quality_report_target.parent.mkdir(parents=True, exist_ok=True)
    with quality_report_target.open("w", encoding="utf-8") as report_file:
        json.dump(validation_summary, report_file, indent=2, default=str)

    raise ValidationError(
        f"Silver validation failed. Report saved to {quality_report_target}."
    )


if __name__ == "__main__":
    run_silver_pipeline()
