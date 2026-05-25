"""CSV validation helpers for semantic graph construction.

The validation step keeps the demo explainable: before rows become RDF
resources, the system checks that the tabular data can safely map to the
ontology's expected transaction fields.
"""

from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from .rdf_builder import REQUIRED_FIELDS


SUPPORTED_TRANSACTION_TYPES = {
    "contract_call",
    "exchange_deposit",
    "mixer_transfer",
    "mixer_withdrawal",
    "transfer",
}


def validate_transaction_csv(csv_path: str | Path) -> dict[str, Any]:
    """Validate transaction CSV structure before RDF generation.

    Returns a JSON-friendly report rather than raising for data-quality issues.
    The API can therefore show all problems at once in the Streamlit demo.
    """

    csv_path = Path(csv_path)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    row_count = 0

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        missing_columns = sorted(REQUIRED_FIELDS - fieldnames)
        extra_columns = sorted(fieldnames - REQUIRED_FIELDS)

        for column in missing_columns:
            errors.append({"row": None, "field": column, "message": "Required column is missing."})

        if extra_columns:
            warnings.append(
                {
                    "row": None,
                    "field": ", ".join(extra_columns),
                    "message": "Extra column will be ignored by RDF generation.",
                }
            )

        if missing_columns:
            return _report(row_count, errors, warnings)

        for row_number, row in enumerate(reader, start=2):
            row_count += 1
            cleaned = {key: (value or "").strip() for key, value in row.items()}
            _validate_required_values(cleaned, row_number, errors)
            _validate_amount(cleaned.get("amount", ""), row_number, errors)
            _validate_timestamp(cleaned.get("timestamp", ""), row_number, warnings)
            _validate_transaction_type(cleaned.get("transaction_type", ""), row_number, warnings)

    if row_count == 0:
        errors.append({"row": None, "field": None, "message": "CSV contains headers but no transaction rows."})

    return _report(row_count, errors, warnings)


def _validate_required_values(row: dict[str, str], row_number: int, errors: list[dict[str, Any]]) -> None:
    for field in sorted(REQUIRED_FIELDS):
        if not row.get(field):
            errors.append({"row": row_number, "field": field, "message": "Required value is empty."})


def _validate_amount(raw_amount: str, row_number: int, errors: list[dict[str, Any]]) -> None:
    if not raw_amount:
        return
    try:
        Decimal(raw_amount)
    except (InvalidOperation, TypeError):
        errors.append({"row": row_number, "field": "amount", "message": "Amount must be numeric."})


def _validate_timestamp(raw_timestamp: str, row_number: int, warnings: list[dict[str, Any]]) -> None:
    if not raw_timestamp:
        return
    try:
        datetime.fromisoformat(raw_timestamp)
    except ValueError:
        warnings.append(
            {
                "row": row_number,
                "field": "timestamp",
                "message": "Timestamp is not ISO-8601; RDF generation will still store it as xsd:dateTime text.",
            }
        )


def _validate_transaction_type(raw_type: str, row_number: int, warnings: list[dict[str, Any]]) -> None:
    if not raw_type:
        return
    if raw_type.lower() not in SUPPORTED_TRANSACTION_TYPES:
        warnings.append(
            {
                "row": row_number,
                "field": "transaction_type",
                "message": "Transaction type is not one of the documented sample categories.",
            }
        )


def _report(row_count: int, errors: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "valid": not errors,
        "row_count": row_count,
        "required_fields": sorted(REQUIRED_FIELDS),
        "errors": errors,
        "warnings": warnings,
    }
