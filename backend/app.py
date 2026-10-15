"""FastAPI read-only API over the generated investor CSV."""

from __future__ import annotations

import csv
import logging
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .collector import DEFAULT_OUTPUT_PATH, PUBLIC_FIELDS
from .metrics import AUDITABLE_FIELDS, calculate_metrics as build_metrics
from .validator import (
    ValidationError,
    normalize_cik,
    parse_filing_date,
    validate_investor,
)

LOGGER = logging.getLogger(__name__)
DEFAULT_VERIFICATION_SAMPLE_PATH = Path("data/processed/verification_sample.csv")
app = FastAPI(title="Seeded SEC Investor Database", version="1.0.0")
cors_origins = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "").split(",")
    if origin.strip()
]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["GET"],
        allow_headers=["Accept"],
    )


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
                            "check_size_min_usd": _optional_number(row.get("check_size_min_usd")),
                            "check_size_max_usd": _optional_number(row.get("check_size_max_usd")),
                            "target_sectors": _optional_sectors(row.get("target_sectors")),
                            "accession_number": row.get("accession_number") or None,
                            "filing_url": row.get("filing_url") or None,
                        }
                    )
                    records.append({field: record.get(field) for field in PUBLIC_FIELDS})
                except (ValidationError, ValueError) as exc:
                    LOGGER.warning("Ignoring invalid investor CSV row %d: %s", row_number, exc)
    except (OSError, csv.Error) as exc:
        LOGGER.exception("Could not read investor CSV %s", csv_path)
        raise HTTPException(status_code=500, detail="Investor dataset is unavailable") from exc
    return records


def _optional_number(value: Any) -> float | None:
    if value is None or not str(value).strip():
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValidationError("Optional financial values must be numeric")
    if number < 0 or number != number or number in (float("inf"), float("-inf")):
        raise ValidationError("Optional financial values must be finite and non-negative")
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
                    detail="Verification sample must contain cik, field, verified_value, source_url, and verified_at columns",
                )
            for row_number, row in enumerate(reader, start=2):
                try:
                    cik = normalize_cik(row.get("cik", ""))
                    field = str(row.get("field", "")).strip()
                    if field not in AUDITABLE_FIELDS:
                        raise ValidationError("field is not eligible for accuracy review")
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
            status_code=500,
            detail="Verification sample is unavailable",
        ) from exc
    return checks


@app.get("/api/investors")
def get_investors() -> dict[str, Any]:
    """Return only configured-seed records and the shared Investor DTO."""
    return {"investors": load_investors()}


@app.get("/api/metrics")
def get_metrics() -> dict[str, Any]:
    investors = load_investors()
    checks = load_verification_sample()
    known_ciks = {record["cik"] for record in investors}
    stale_checks = sum(1 for check in checks if check["cik"] not in known_ciks)
    if stale_checks:
        LOGGER.warning(
            "Ignoring %d verification checks whose CIKs are not in the current dataset",
            stale_checks,
        )
    return build_metrics(investors, checks)


@app.get("/api/scaling")
def get_scaling() -> dict[str, Any]:
    current = len(load_investors())
    target = _positive_int_env("SCALING_TARGET_RECORDS", 10000)
    unit_cost = _optional_nonnegative_float_env("COST_PER_RECORD_USD")
    total_cost = target * unit_cost if unit_cost is not None else None
    if total_cost is not None and total_cost == float("inf"):
        raise HTTPException(status_code=500, detail="Estimated scaling cost exceeds numeric range")
    return {
        "current_records": current,
        "target_records": target,
        "cost_per_record_usd": unit_cost,
        "estimated_total_cost_usd": round(total_cost, 2) if total_cost is not None else None,
        "assumptions": [
            "Target record count is configurable via SCALING_TARGET_RECORDS (default 10000).",
            "COST_PER_RECORD_USD is a user-supplied planning assumption; no cost is "
            "shown until one is configured.",
            "This is a linear scenario only, not a quote or validated forecast.",
        ],
    }


def _positive_int_env(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=f"{name} must be a positive integer") from exc
    if value < 1:
        raise HTTPException(status_code=500, detail=f"{name} must be a positive integer")
    return value


def _optional_nonnegative_float_env(name: str) -> float | None:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return None
    try:
        value = float(raw)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=f"{name} must be a non-negative number") from exc
    if value < 0 or value != value or value in (float("inf"), float("-inf")):
        raise HTTPException(status_code=500, detail=f"{name} must be finite and non-negative")
    return value
