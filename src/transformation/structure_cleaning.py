"""Structure-cleaning utilities for the Silver layer.

This module is responsible only for tabular structure repair before
normalization, type conversion, and business validation are applied.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pandas as pd

TIMELINESS_HEADER = ["Region", "Disposed", "Timely", "Percent"]
TIMELINESS_SECTION_LABELS = {
    "APPLICATIONS": "Applications",
    "REDETERMINATIONS": "Redeterminations",
}


def _normalize_text(value: Any) -> str:
    """Convert an Excel cell value to a comparable text string."""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _looks_like_timeliness_workbook(df: pd.DataFrame) -> bool:
    """Detect Timeliness workbook layouts by business labels and the expected header."""
    normalized = df.fillna("").astype(str)
    combined = " ".join(
        cell.strip() for row in normalized.itertuples(index=False, name=None) for cell in row
    ).upper()
    header_tokens = ["REGION", "DISPOSED", "TIMELY", "PERCENT"]
    section_markers = ["TIMELINESS", "APPLICATIONS", "REDETERMINATIONS"]
    return any(marker in combined for marker in section_markers) and sum(
        1 for token in header_tokens if token in combined
    ) >= 3


def _row_has_section_marker(row: pd.Series, section_name: str) -> bool:
    """Check whether a given row contains the given section title."""
    return any(section_name in _normalize_text(value).upper() for value in row.tolist())


def _row_has_expected_header(row: pd.Series) -> bool:
    """Check whether a row matches the expected Timeliness table header."""
    non_empty = [
        _normalize_text(value) for value in row.tolist() if _normalize_text(value) != ""
    ]
    return non_empty == TIMELINESS_HEADER


def _row_to_timeliness_values(row: pd.Series) -> List[str]:
    """Return the row values aligned to the four Timeliness columns, preserving missing slots."""
    values = [_normalize_text(value) for value in row.tolist()]
    if len(values) < 4:
        values = values + [""] * (4 - len(values))
    return values[:4]


def _extract_timeliness_sections(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Extract analytic detail rows from Timeliness Applications and Redeterminations sections."""
    section_rows: Dict[str, int] = {}
    for position, row in df.reset_index(drop=True).iterrows():
        for section_key, section_label in TIMELINESS_SECTION_LABELS.items():
            if _row_has_section_marker(row, section_key):
                if section_label in section_rows:
                    raise ValueError(f"Timeliness section '{section_label}' appears more than once.")
                section_rows[section_label] = position

    if set(section_rows) != set(TIMELINESS_SECTION_LABELS.values()):
        missing = [label for label in TIMELINESS_SECTION_LABELS.values() if label not in section_rows]
        raise ValueError(f"Missing required Timeliness section(s): {', '.join(missing)}")

    detail_rows: List[Dict[str, Any]] = []
    totals: Dict[str, Dict[str, Any]] = {}
    ordered_sections = [label for label, _ in sorted(section_rows.items(), key=lambda item: item[1])]

    for section_index, section_label in enumerate(ordered_sections):
        start_index = section_rows[section_label]
        next_start_index = (
            section_rows[ordered_sections[section_index + 1]]
            if section_index + 1 < len(ordered_sections)
            else len(df)
        )
        section_block = df.iloc[start_index + 1 : next_start_index].copy().reset_index(drop=True)

        header_index = next(
            (idx for idx, row in section_block.iterrows() if _row_has_expected_header(row)),
            None,
        )
        if header_index is None:
            raise ValueError(
                f"Missing expected Timeliness table header for section '{section_label}'."
            )

        remaining_rows = section_block.iloc[header_index + 1 :].itertuples(index=False, name=None)
        for row in remaining_rows:
            values = _row_to_timeliness_values(pd.Series(row))
            if not any(values):
                continue

            if values[0].upper() == "TOTAL":
                totals[section_label] = {
                    "Region": "TOTAL",
                    "Disposed": values[1] if len(values) > 1 else "",
                    "Timely": values[2] if len(values) > 2 else "",
                    "Percent": values[3] if len(values) > 3 else "",
                }
                continue

            if values[0].upper() in {"REGION"}:
                continue
            if values[0].upper().startswith("NOTE") or values[0].upper().startswith("DEFINITION"):
                continue
            if len(values) >= 2 and (
                values[1].upper().startswith("NOTE")
                or values[1].upper().startswith("DEFINITION")
            ):
                continue

            region = values[0]
            if not region:
                continue

            detail_rows.append(
                {
                    "processing_type": section_label,
                    "Region": region,
                    "Disposed": values[1] if values[1] != "" else None,
                    "Timely": values[2] if values[2] != "" else None,
                    "Percent": values[3] if values[3] != "" else None,
                }
            )

    detail_df = pd.DataFrame(detail_rows, columns=["processing_type", "Region", "Disposed", "Timely", "Percent"])
    if detail_df.empty:
        raise ValueError("Timeliness detail extraction produced no analytical rows.")

    summary = {
        "input_row_count": int(df.shape[0]),
        "output_row_count": int(detail_df.shape[0]),
        "structure_issues": [],
        "timeliness_section_totals": totals,
    }
    return detail_df, summary


def _remove_empty_rows(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Remove rows whose cells are all missing values."""
    original_row_count = int(df.shape[0])
    cleaned_df = df.dropna(axis=0, how="all").copy()
    removed_row_count = original_row_count - int(cleaned_df.shape[0])
    return cleaned_df, removed_row_count


def _remove_empty_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Remove columns whose cells are all missing values."""
    original_column_count = int(df.shape[1])
    cleaned_df = df.dropna(axis=1, how="all").copy()
    removed_column_count = original_column_count - int(cleaned_df.shape[1])
    return cleaned_df, removed_column_count


def _detect_duplicated_header_rows(df: pd.DataFrame) -> List[str]:
    """Detect repeated header rows as a placeholder for future structure rules."""
    issues: List[str] = []

    if df.empty:
        return issues

    columns = list(df.columns)
    for idx, row in df.head(10).iterrows():
        row_values = [str(value).strip() for value in row.tolist()]
        if row_values and row_values == [str(col).strip() for col in columns]:
            issues.append(f"Duplicate header row detected at index {idx}.")

    return issues


def _validate_structure(df: pd.DataFrame) -> None:
    """Raise an error when the DataFrame is empty after structural cleaning."""
    if df.empty:
        raise ValueError("DataFrame is empty after structure cleaning.")


def clean_structure(df: pd.DataFrame) -> Dict[str, Any]:
    """Apply structure-only cleaning to a DataFrame.

    This function removes empty rows and columns and checks for duplicated header
    rows. It does not perform normalization, data type conversion, or business
    validation.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if _looks_like_timeliness_workbook(df):
        cleaned_df, summary = _extract_timeliness_sections(df)
        return {
            "cleaned_df": cleaned_df,
            "summary": summary,
        }

    working_df = df.copy()

    cleaned_df, removed_row_count = _remove_empty_rows(working_df)
    cleaned_df, removed_column_count = _remove_empty_columns(cleaned_df)
    structure_issues = _detect_duplicated_header_rows(cleaned_df)

    _validate_structure(cleaned_df)

    summary = {
        "input_row_count": int(df.shape[0]),
        "output_row_count": int(cleaned_df.shape[0]),
        "removed_row_count": removed_row_count,
        "removed_column_count": removed_column_count,
        "structure_issues": structure_issues,
    }

    return {
        "cleaned_df": cleaned_df,
        "summary": summary,
    }
