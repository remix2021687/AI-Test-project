"""Inspect current and archived SEC submissions for the latest 13F filing."""

from __future__ import annotations

import logging
import re
from datetime import date
from typing import Any

from ..domain.parser import SUBMISSIONS_URL, parse_latest_13f
from ..domain.validator import ValidationError, parse_filing_date
from .client import SECClient, SECRequestError
from .config import SEC_SUBMISSIONS_FILES_URL

LOGGER = logging.getLogger(__name__)
_SUBMISSION_FILE_RE = re.compile(r"^[A-Za-z0-9._-]+\.json$")


def latest_13f_in_submissions(
    submissions: dict[str, Any], cik: str, client: SECClient
) -> dict[str, Any]:
    """Search recent submissions first, then SEC history chunks if needed."""
    parsed = parse_latest_13f(submissions, cik)
    if parsed["latest_filing_date"] or parsed.get("_history_complete") is False:
        return parsed

    filings = submissions.get("filings", {})
    files = filings.get("files", []) if isinstance(filings, dict) else []
    if not isinstance(files, list):
        parsed["_history_complete"] = False
        return parsed
    dated_files: list[tuple[date, str]] = []
    malformed_file_reference = False
    for item in files:
        if not isinstance(item, dict):
            malformed_file_reference = True
            continue
        name = item.get("name")
        end_date = item.get("filingTo")
        if (
            not isinstance(name, str)
            or not _SUBMISSION_FILE_RE.fullmatch(name)
            or not isinstance(end_date, str)
        ):
            malformed_file_reference = True
            continue
        try:
            dated_files.append((parse_filing_date(end_date), name))
        except ValidationError:
            malformed_file_reference = True
    if malformed_file_reference:
        parsed["_history_complete"] = False
        return parsed

    for _, name in sorted(dated_files, reverse=True):
        try:
            historical = client.get_json(SEC_SUBMISSIONS_FILES_URL.format(name=name))
            recent = historical.get("filings", {}).get("recent", historical)
            wrapped = {
                "cik": cik,
                "name": submissions.get("name"),
                "filings": {"recent": recent},
            }
            historical_record = parse_latest_13f(wrapped, cik)
        except SECRequestError as exc:
            LOGGER.warning("Unable to inspect SEC submission history %s: %s", name, exc)
            parsed["_history_complete"] = False
            break
        except (ValidationError, AttributeError, TypeError) as exc:
            LOGGER.warning("Unable to inspect SEC submission history %s: %s", name, exc)
            parsed["_history_complete"] = False
            break
        if historical_record["latest_filing_date"]:
            historical_record["source_url"] = SUBMISSIONS_URL.format(cik=cik)
            return historical_record
    return parsed
