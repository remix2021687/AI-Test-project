"""Parsing routines for company submissions API responses."""

from __future__ import annotations

from datetime import date
from typing import Any

from .validator import (
    ValidationError,
    filing_url,
    normalize_cik,
    parse_filing_date,
    validate_submissions,
)

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"


def parse_latest_13f(payload: Any, requested_cik: str) -> dict[str, Any]:
    """Extract the newest 13F-HR (including amendments) listed in `recent`."""
    data = validate_submissions(payload)
    cik = normalize_cik(requested_cik)
    response_cik = data.get("cik")
    if response_cik is not None and normalize_cik(response_cik) != cik:
        raise ValidationError("SEC response CIK does not match requested CIK")

    recent = data["filings"]["recent"]
    columns = ("form", "filingDate", "accessionNumber", "primaryDocument")
    if any(not isinstance(recent.get(column), list) for column in columns):
        raise ValidationError("SEC recent filing columns are malformed")
    lengths = {len(recent[column]) for column in columns}
    if len(lengths) != 1:
        raise ValidationError("SEC recent filing columns have inconsistent lengths")

    candidates: list[tuple[date, int, dict[str, str]]] = []
    complete = True
    for index, (form, filed, accession, document) in enumerate(
        zip(*(recent[column] for column in columns))
    ):
        if not isinstance(form, str):
            complete = False
            continue
        if form not in {"13F-HR", "13F-HR/A"}:
            continue
        try:
            filed_date = parse_filing_date(filed)
            accession_number = str(accession)
            primary_document = str(document)
            archive_url = filing_url(cik, accession_number, primary_document)
            candidates.append(
                (
                    filed_date,
                    index,
                    {
                        "form": str(form),
                        "filing_date": filed_date.isoformat(),
                        "accession_number": accession_number,
                        "primary_document": primary_document,
                        "filing_url": archive_url,
                    },
                )
            )
        except (ValidationError, TypeError):
            # A malformed 13F entry must not hide another usable filing.
            complete = False
            continue

    if not candidates:
        result = {
            "cik": cik,
            "name": _safe_name(data.get("name"), cik),
            "latest_filing_date": None,
            "latest_form": None,
            "accession_number": None,
            "filing_url": None,
            "source_url": SUBMISSIONS_URL.format(cik=cik),
        }
        if not complete:
            result["_history_complete"] = False
        return result

    _, _, latest = max(candidates, key=lambda item: (item[0], -item[1]))
    result = {
        "cik": cik,
        "name": _safe_name(data.get("name"), cik),
        "latest_filing_date": latest["filing_date"],
        "latest_form": latest["form"],
        "accession_number": latest["accession_number"],
        "filing_url": latest["filing_url"],
        "source_url": SUBMISSIONS_URL.format(cik=cik),
    }
    if not complete:
        result["_history_complete"] = False
    return result


def _safe_name(value: Any, cik: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return f"CIK {cik}"
