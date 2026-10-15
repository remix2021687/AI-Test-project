"""Validation and normalization for SEC submissions data and investor records."""

from __future__ import annotations

import re
from datetime import date
from typing import Any
from urllib.parse import quote, urlsplit


_CIK_RE = re.compile(r"^\d{1,10}$")
_ACCESSION_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SUBMISSIONS_URL_RE = re.compile(r"^/submissions/CIK\d{10}\.json$")
_ARCHIVE_URL_RE = re.compile(
    r"^/Archives/edgar/data/\d+/\d{18}/[A-Za-z0-9._%\-]+$"
)


class ValidationError(ValueError):
    """Raised when an input cannot safely be interpreted as SEC data."""


def normalize_cik(value: Any) -> str:
    """Return a zero-padded SEC CIK, rejecting malformed values."""
    text = str(value).strip()
    if not _CIK_RE.fullmatch(text):
        raise ValidationError(f"Invalid CIK: {text!r}")
    return text.zfill(10)


def parse_filing_date(value: Any) -> date:
    text = str(value or "").strip()
    if not _DATE_RE.fullmatch(text):
        raise ValidationError(f"Invalid filing date: {text!r}")
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValidationError(f"Invalid filing date: {text!r}") from exc


def validate_submissions(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValidationError("SEC submissions response must be a JSON object")
    if not isinstance(payload.get("filings"), dict):
        raise ValidationError("SEC submissions response is missing filings")
    recent = payload["filings"].get("recent")
    if not isinstance(recent, dict):
        raise ValidationError("SEC submissions response is missing recent filings")
    return payload


def filing_url(cik: str, accession: str, primary_document: str) -> str:
    """Build an Archives URL only from validated SEC identifiers."""
    normalized_cik = normalize_cik(cik)
    if not _ACCESSION_RE.fullmatch(accession):
        raise ValidationError(f"Invalid accession number: {accession!r}")
    document = str(primary_document or "").strip()
    # SEC document names are path components. Do not allow path traversal.
    if not document or document in {".", ".."} or "/" in document or "\\" in document:
        raise ValidationError("Invalid primary document name")
    archive_accession = accession.replace("-", "")
    return (
        f"https://www.sec.gov/Archives/edgar/data/{int(normalized_cik)}/"
        f"{archive_accession}/{quote(document, safe='._-')}"
    )


def validate_investor(record: Any) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValidationError("Investor record must be an object")
    cik = normalize_cik(record.get("cik", ""))
    name = record.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValidationError("Investor name is required")
    filing_date = record.get("latest_filing_date")
    if filing_date is not None:
        parse_filing_date(filing_date)
    allowed_sources = {
        "source_url": ("data.sec.gov", _SUBMISSIONS_URL_RE),
        "filing_url": ("www.sec.gov", _ARCHIVE_URL_RE),
    }
    for key, (host, path_pattern) in allowed_sources.items():
        value = record.get(key)
        if value is not None:
            if not isinstance(value, str):
                raise ValidationError(f"{key} must be an SEC URL or null")
            try:
                parsed_url = urlsplit(value)
                port = parsed_url.port
            except ValueError as exc:
                raise ValidationError(f"{key} must be an SEC URL or null") from exc
            if (
                parsed_url.scheme != "https"
                or parsed_url.hostname != host
                or parsed_url.username is not None
                or parsed_url.password is not None
                or port is not None
                or parsed_url.query
                or parsed_url.fragment
                or not path_pattern.fullmatch(parsed_url.path)
            ):
                raise ValidationError(f"{key} must be a canonical SEC URL or null")
    return {**record, "cik": cik, "name": name.strip()}
