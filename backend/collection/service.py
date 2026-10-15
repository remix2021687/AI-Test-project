"""Coordinate seed loading, SEC collection, validation, and CSV export."""

from __future__ import annotations

import logging
import os
from calendar import monthrange
from datetime import date
from pathlib import Path
from typing import Any

from ..domain.parser import SUBMISSIONS_URL
from ..domain.validator import ValidationError, normalize_cik, validate_investor
from .client import SECClient, SECRequestError
from .config import DEFAULT_OUTPUT_PATH, DEFAULT_SEED_PATH
from .export import write_csv
from .history import latest_13f_in_submissions
from .seeds import load_seed_ciks

LOGGER = logging.getLogger(__name__)


def _subtract_months(day: date, months: int) -> date:
    month_index = day.year * 12 + day.month - 1 - months
    year, month_zero = divmod(month_index, 12)
    month = month_zero + 1
    return date(year, month, min(day.day, monthrange(year, month)[1]))


def collect_records(
    seed_ciks: list[str],
    client: SECClient,
    active_months: int = 24,
    as_of: date | None = None,
) -> list[dict[str, Any]]:
    if not 12 <= active_months <= 24:
        raise ValueError("active_months must be between 12 and 24")
    today = as_of or date.today()
    cutoff = _subtract_months(today, active_months)
    output: list[dict[str, Any]] = []
    for raw_cik in seed_ciks:
        cik = normalize_cik(raw_cik)
        url = SUBMISSIONS_URL.format(cik=cik)
        try:
            submissions = client.get_json(url)
            parsed = latest_13f_in_submissions(submissions, cik, client)
            history_complete = parsed.pop("_history_complete", True)
            filed_date = (
                date.fromisoformat(parsed["latest_filing_date"])
                if parsed["latest_filing_date"]
                else None
            )
            record = {
                "cik": parsed["cik"],
                "name": parsed["name"],
                "latest_filing_date": parsed["latest_filing_date"],
                "latest_filing_form": parsed["latest_form"],
                "is_active": (
                    bool(filed_date and filed_date >= cutoff)
                    if history_complete
                    else None
                ),
                "source_url": parsed["source_url"],
                "aum_usd": None,
                "check_size_min_usd": None,
                "check_size_max_usd": None,
                "target_sectors": None,
                "accession_number": parsed["accession_number"],
                "filing_url": parsed["filing_url"],
            }
            validated = validate_investor(record)
            if validated["is_active"] is not True:
                LOGGER.info(
                    "Excluding seed CIK %s because recent 13F activity was not verified",
                    cik,
                )
                continue
            output.append(validated)
        except (SECRequestError, ValidationError, ValueError) as exc:
            LOGGER.error("Unable to collect seed CIK %s: %s", cik, exc)
    return output


def configured_active_months() -> int:
    raw = os.environ.get("ACTIVE_MONTHS", "24")
    try:
        months = int(raw)
    except ValueError as exc:
        raise ValueError("ACTIVE_MONTHS must be an integer between 12 and 24") from exc
    if not 12 <= months <= 24:
        raise ValueError("ACTIVE_MONTHS must be between 12 and 24")
    return months


def collect_to_csv(
    seed_path: str | Path = DEFAULT_SEED_PATH,
    output_path: str | Path = DEFAULT_OUTPUT_PATH,
    active_months: int | None = None,
    client: SECClient | None = None,
) -> list[dict[str, Any]]:
    months = active_months if active_months is not None else configured_active_months()
    if not 12 <= months <= 24:
        raise ValueError("active_months must be between 12 and 24")
    seeds = load_seed_ciks(seed_path)
    if not seeds:
        records: list[dict[str, Any]] = []
    else:
        records = collect_records(seeds, client or SECClient(), months)
    write_csv(records, output_path)
    return records
