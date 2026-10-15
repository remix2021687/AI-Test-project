"""Load and validate CSV-backed investor and verification records."""

from __future__ import annotations

import csv
import logging
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from fastapi import HTTPException

from ..collection.config import DEFAULT_OUTPUT_PATH, PUBLIC_FIELDS
from ..domain.metrics import AUDITABLE_FIELDS
from ..domain.validator import (
    ValidationError,
    normalize_cik,
    parse_filing_date,
    validate_investor,
)

LOGGER = logging.getLogger(__name__)
DEFAULT_VERIFICATION_SAMPLE_PATH = Path("data/processed/verification_sample.csv")


def load_investors(path: str | Path | None = None) -> list[dict[str, Any]]:
    csv_path = Path(path or os.environ.get("INVESTORS_CSV", DEFAULT_OUTPUT_PATH))
    if not csv_path.exists():
        return []
    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or not {"cik", "name"}.issubset(reader.fieldnames):
                raise HTTPException(
                    status_code=500,
                    detail="Investor dataset must contain cik and name columns",
                )
            records = []
            for row_number, row in enumerate(reader, start=2):
                try:
                    active_raw = str(row.get("is_active", "")).strip().lower()
                    if active_raw not in {"true", "false", ""}:
                        raise ValidationError("is_active must be true, false, or empty")
                    record = validate_investor(
                        {
                            "cik": row.get("cik"),
                            "name": row.get("name"),
                            "latest_filing_date": row.get("latest_filing_date") or None,
                            "latest_filing_form": row.get("latest_filing_form") or None,
                            "is_active": (
                                None if not active_raw else active_raw == "true"
                            ),
                            "source_url": row.get("source_url") or None,
                            "aum_usd": _optional_number(row.get("aum_usd")),
                            "check_size_min_usd": _optional_number(
                                row.get("check_size_min_usd")
                            ),
                            "check_size_max_usd": _optional_number(
                                row.get("check_size_max_usd")
                            ),
                            "target_sectors": _optional_sectors(
                                row.get("target_sectors")
                            ),
                            "accession_number": row.get("accession_number") or None,
                            "filing_url": row.get("filing_url") or None,
                        }
                    )
                    records.append(
                        {field: record.get(field) for field in PUBLIC_FIELDS}
                    )
                except (ValidationError, ValueError) as exc:
                    LOGGER.warning(
                        "Ignoring invalid investor CSV row %d: %s", row_number, exc
                    )
    except (OSError, csv.Error) as exc:
        LOGGER.exception("Could not read investor CSV %s", csv_path)
        raise HTTPException(
            status_code=500, detail="Investor dataset is unavailable"
        ) from exc
    return records


def _optional_number(value: Any) -> float | None:
    if value is None or not str(value).strip():
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Optional financial values must be numeric") from exc
    if number < 0 or number != number or number in (float("inf"), float("-inf")):
        raise ValidationError(
            "Optional financial values must be finite and non-negative"
        )
    return number


def _optional_sectors(value: Any) -> list[str]:
    if value is None or not str(value).strip():
        return []
    return [sector.strip() for sector in str(value).split("|") if sector.strip()]


def load_verification_sample(
    path: str | Path | None = None,
) -> list[dict[str, str]]:
    csv_path = Path(
        path
        or os.environ.get(
            "VERIFICATION_SAMPLE_CSV", DEFAULT_VERIFICATION_SAMPLE_PATH
        )
    )
    if not csv_path.exists():
        return []
    required_fields = {"cik", "field", "verified_value", "source_url", "verified_at"}
    checks: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or not required_fields.issubset(reader.fieldnames):
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Verification sample must contain cik, field, verified_value, "
                        "source_url, and verified_at columns"
                    ),
                )
            for row_number, row in enumerate(reader, start=2):
                try:
                    cik = normalize_cik(row.get("cik", ""))
                    field = str(row.get("field", "")).strip()
                    if field not in AUDITABLE_FIELDS:
                        raise ValidationError(
                            "field is not eligible for accuracy review"
                        )
                    verified_value = str(row.get("verified_value", "")).strip()
                    if not verified_value:
                        raise ValidationError("verified_value is required")
                    source_url = str(row.get("source_url", "")).strip()
                    parsed_url = urlsplit(source_url)
                    if (
                        parsed_url.scheme != "https"
                        or not parsed_url.hostname
                        or parsed_url.username is not None
                        or parsed_url.password is not None
                    ):
                        raise ValidationError("source_url must be an HTTPS source")
                    parse_filing_date(row.get("verified_at"))
                    key = (cik, field)
                    if key in seen:
                        raise ValidationError("duplicate CIK and field check")
                    seen.add(key)
                    checks.append(
                        {
                            "cik": cik,
                            "field": field,
                            "verified_value": verified_value,
                            "source_url": source_url,
                            "verified_at": str(row["verified_at"]).strip(),
                        }
                    )
                except (ValidationError, TypeError, ValueError) as exc:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Invalid verification sample row {row_number}: {exc}",
                    ) from exc
    except (OSError, csv.Error) as exc:
        LOGGER.exception("Could not read verification sample %s", csv_path)
        raise HTTPException(
            status_code=500, detail="Verification sample is unavailable"
        ) from exc
    return checks
