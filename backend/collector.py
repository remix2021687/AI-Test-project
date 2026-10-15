"""Fetch SEC company submissions for configured seed CIKs and export records."""

from __future__ import annotations

import csv
import json
import logging
import os
import re
import tempfile
import time
from datetime import date
from itertools import chain
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .parser import SUBMISSIONS_URL, parse_latest_13f
from .validator import (
    ValidationError,
    normalize_cik,
    parse_filing_date,
    validate_investor,
)

LOGGER = logging.getLogger(__name__)
DEFAULT_SEED_PATH = Path("data/seeds/seed_ciks.csv")
DEFAULT_OUTPUT_PATH = Path("data/processed/sample_investors.csv")
SEC_SUBMISSIONS_FILES_URL = "https://data.sec.gov/submissions/{name}"
_SUBMISSION_FILE_RE = re.compile(r"^[A-Za-z0-9._-]+\.json$")
_CONTACT_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
CSV_FIELDS = [
    "cik",
    "name",
    "latest_filing_date",
    "latest_filing_form",
    "is_active",
    "source_url",
    "aum_usd",
    "check_size_min_usd",
    "check_size_max_usd",
    "target_sectors",
    # Useful traceability metadata; not part of the public Investor DTO.
    "accession_number",
    "filing_url",
]
PUBLIC_FIELDS = CSV_FIELDS[:10]


class SECRequestError(RuntimeError):
    """A network, HTTP, or JSON failure while requesting SEC data."""


def load_seed_ciks(path: str | Path = DEFAULT_SEED_PATH) -> list[str]:
    """Read a CSV whose CIKs are in a `cik` column or the first column."""
    seed_path = Path(path)
    if not seed_path.exists():
        LOGGER.info("Seed CSV %s not found; exporting an empty dataset", seed_path)
        return []
    ciks: list[str] = []
    seen: set[str] = set()
    try:
        with seed_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            first_row = next(reader, None)
            if first_row is None:
                return []
            header = [cell.strip().lower() for cell in first_row]
            cik_index = header.index("cik") if "cik" in header else 0
            rows = reader if "cik" in header else chain([first_row], reader)
            for line_number, row in enumerate(rows, start=2 if "cik" in header else 1):
                if not row or cik_index >= len(row) or not row[cik_index].strip():
                    continue
                try:
                    cik = normalize_cik(row[cik_index])
                except ValidationError as exc:
                    LOGGER.warning("Skipping invalid CIK at %s:%d: %s", seed_path, line_number, exc)
                    continue
                if cik not in seen:
                    seen.add(cik)
                    ciks.append(cik)
    except (OSError, csv.Error) as exc:
        raise ValueError(f"Unable to read seed CIK CSV {seed_path}: {exc}") from exc
    return ciks


def _user_agent() -> str:
    value = os.environ.get("SEC_USER_AGENT", "").strip()
    if not value:
        raise ValueError(
            "SEC_USER_AGENT is required for SEC requests. Set a truthful, "
            "descriptive application identity and contact address."
        )
    return value


class SECClient:
    def __init__(
        self,
        user_agent: str | None = None,
        timeout: float = 15.0,
        retries: int = 2,
        opener: Any = urlopen,
        sleeper: Any = time.sleep,
    ) -> None:
        self.user_agent = user_agent.strip() if user_agent else _user_agent()
        contact = _CONTACT_EMAIL_RE.search(self.user_agent)
        if not contact or not self.user_agent[:contact.start()].strip():
            raise ValueError(
                "SEC_USER_AGENT must include a descriptive application name "
                "and contact email address."
            )
        self.timeout = timeout
        self.retries = max(0, retries)
        self.opener = opener
        self.sleeper = sleeper
        self._last_request_at: float | None = None

    def get_json(self, url: str) -> dict[str, Any]:
        request = Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json",
            },
        )
        for attempt in range(self.retries + 1):
            if self._last_request_at is not None:
                elapsed = time.monotonic() - self._last_request_at
                if elapsed < 0.11:
                    self.sleeper(0.11 - elapsed)
            self._last_request_at = time.monotonic()
            try:
                with self.opener(request, timeout=self.timeout) as response:
                    status = getattr(response, "status", 200)
                    if status < 200 or status >= 300:
                        raise SECRequestError(f"SEC returned HTTP {status} for {url}")
                    raw = response.read()
                try:
                    result = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise SECRequestError(f"SEC returned invalid JSON for {url}") from exc
                if not isinstance(result, dict):
                    raise SECRequestError(f"SEC JSON response was not an object: {url}")
                return result
            except HTTPError as exc:
                retryable = exc.code == 429 or 500 <= exc.code < 600
                if retryable and attempt < self.retries:
                    self.sleeper(min(2**attempt, 8))
                    continue
                raise SECRequestError(f"SEC HTTP error {exc.code} for {url}") from exc
            except (URLError, TimeoutError, OSError) as exc:
                if attempt < self.retries:
                    self.sleeper(min(2**attempt, 8))
                    continue
                raise SECRequestError(f"SEC network request failed for {url}: {exc}") from exc
        raise SECRequestError(f"SEC request failed for {url}")


def _subtract_months(day: date, months: int) -> date:
    month_index = day.year * 12 + day.month - 1 - months
    year, month_zero = divmod(month_index, 12)
    month = month_zero + 1
    # Clamp end-of-month dates, e.g. March 31 minus one month -> February 28.
    from calendar import monthrange

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
            parsed = _latest_13f_in_submissions(submissions, cik, client)
            history_complete = parsed.pop("_history_complete", True)
            filed_date = date.fromisoformat(parsed["latest_filing_date"]) if parsed["latest_filing_date"] else None
            record = {
                "cik": parsed["cik"],
                "name": parsed["name"],
                "latest_filing_date": parsed["latest_filing_date"],
                "latest_filing_form": parsed["latest_form"],
                "is_active": (
                    bool(filed_date and filed_date >= cutoff) if history_complete else None
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


def _latest_13f_in_submissions(
    submissions: dict[str, Any], cik: str, client: SECClient
) -> dict[str, Any]:
    """Search recent submissions first, then SEC history chunks if needed."""
    parsed = parse_latest_13f(submissions, cik)
    if (
        parsed["latest_filing_date"]
        or parsed.get("_history_complete") is False
    ):
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
            continue
    if malformed_file_reference:
        parsed["_history_complete"] = False
        return parsed

    # SEC archive chunks are date-ranged. The most recent ranges are searched
    # first, stopping at the first chunk containing a 13F-HR.
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
            # Do not select an older chunk when a newer one could not be read.
            parsed["_history_complete"] = False
            break
        except (ValidationError, AttributeError, TypeError) as exc:
            LOGGER.warning("Unable to inspect SEC submission history %s: %s", name, exc)
            parsed["_history_complete"] = False
            break
        if historical_record["latest_filing_date"]:
            # Keep source_url pointing to the canonical company submissions
            # resource; filing_url identifies the actual archived filing.
            historical_record["source_url"] = SUBMISSIONS_URL.format(cik=cik)
            return historical_record
    return parsed


def write_csv(records: list[dict[str, Any]], output_path: str | Path = DEFAULT_OUTPUT_PATH) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Atomic replacement prevents the API from observing a partially written file.
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="",
            dir=destination.parent,
            delete=False,
        ) as handle:
            temp_name = handle.name
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="ignore")
            writer.writeheader()
            for record in records:
                row = {field: record.get(field) for field in CSV_FIELDS}
                if isinstance(row.get("target_sectors"), list):
                    row["target_sectors"] = "|".join(row["target_sectors"])
                writer.writerow(row)
        os.replace(temp_name, destination)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)
    return destination


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
        records = collect_records(
            seeds,
            client or SECClient(),
            active_months if active_months is not None else configured_active_months(),
        )
    write_csv(records, output_path)
    return records
