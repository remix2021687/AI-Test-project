"""Parse SEC company submission responses."""

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
_FILING_FORMS = {"13F-HR", "13F-HR/A"}
_RECENT_COLUMNS = ("form", "filingDate", "accessionNumber", "primaryDocument")


def parse_latest_13f(payload: Any, requested_cik: str) -> dict[str, Any]:
    """Extract the newest 13F-HR (including amendments) in recent filings."""
    data = validate_submissions(payload)
    cik = normalize_cik(requested_cik)
    response_cik = data.get("cik")
    if response_cik is not None and normalize_cik(response_cik) != cik:
        raise ValidationError("SEC response CIK does not match requested CIK")

    recent = data["filings"]["recent"]
    if any(not isinstance(recent.get(column), list) for column in _RECENT_COLUMNS):
        raise ValidationError("SEC recent filing columns are malformed")
    if len({len(recent[column]) for column in _RECENT_COLUMNS}) != 1:
        raise ValidationError("SEC recent filing columns have inconsistent lengths")

    candidates = []
    complete = True
    for index, (form, filed, accession, document) in enumerate(
        zip(*(recent[column] for column in _RECENT_COLUMNS))
    ):
        if not isinstance(form, str):
            complete = False
            continue
        if form not in _FILING_FORMS:
            continue
        try:
            filed_date = parse_filing_date(filed)
            accession_number = str(accession)
            candidates.append(
                (
                    filed_date,
                    index,
                    {
                        "form": form,
                        "filing_date": filed_date.isoformat(),
                        "accession_number": accession_number,
                        "filing_url": filing_url(cik, accession_number, str(document)),
                    },
                )
            )
        except (ValidationError, TypeError):
            complete = False

    latest = max(candidates, key=lambda item: (item[0], -item[1]))[2] if candidates else {}
    result = {
        "cik": cik,
        "name": _safe_name(data.get("name"), cik),
        "latest_filing_date": latest.get("filing_date"),
        "latest_form": latest.get("form"),
        "accession_number": latest.get("accession_number"),
        "filing_url": latest.get("filing_url"),
        "source_url": SUBMISSIONS_URL.format(cik=cik),
    }
    if not complete:
        result["_history_complete"] = False
    return result


def _safe_name(value: Any, cik: str) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else f"CIK {cik}"
