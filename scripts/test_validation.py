"""Simple manual tests for the validation module."""

from __future__ import annotations

import sys
from pathlib import Path
from pprint import pprint

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.validation.data_quality import validate_data


def run_case(title: str, data: object) -> None:
    """Run a single validation case and print the output."""
    print(f"\n{'=' * 60}")
    print(title)
    print(f"{'=' * 60}")

    try:
        result = validate_data(data)
    except Exception as exc:
        print(f"Error: {exc}")
        return

    print("Profile:")
    pprint(result["profile"])
    print("\nSummary:")
    pprint(result["summary"])
    print("\nIssues:")
    pprint(result["issues"])
    print("\nValidated DataFrame:")
    print(result["validated_df"])


if __name__ == "__main__":
    run_case("1. Normal DataFrame", pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}))
    run_case(
        "2. DataFrame with missing values",
        pd.DataFrame({"a": [1, None, 3], "b": [4, 5, None]}),
    )
    run_case(
        "3. DataFrame with duplicate rows",
        pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]}),
    )
    run_case("4. Empty DataFrame", pd.DataFrame(columns=["a", "b"]))
    run_case("5. Invalid input (not a DataFrame)", [1, 2, 3])
