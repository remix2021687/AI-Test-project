"""Completeness and independently sampled accuracy metrics."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

AUDITABLE_FIELDS = frozenset(
    {
        "name",
        "latest_filing_date",
        "latest_filing_form",
        "is_active",
        "aum_usd",
        "check_size_min_usd",
        "check_size_max_usd",
        "target_sectors",
    }
)
_COMPLETENESS_FIELDS = (
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
)


def calculate_metrics(
    records: Iterable[dict[str, Any]],
    verification_checks: Iterable[dict[str, Any]] = (),
    as_of: date | None = None,
) -> dict[str, Any]:
    """Return record counts, completeness, and sampled field accuracy."""
    investors = list(records)
    total = len(investors)
    present = sum(
        record.get(field) not in (None, "", [])
        for record in investors
        for field in _COMPLETENESS_FIELDS
    )
    denominator = total * len(_COMPLETENESS_FIELDS)
    investors_by_cik = {record["cik"]: record for record in investors}
    checks = [
        check
        for check in verification_checks
        if check.get("cik") in investors_by_cik
    ]
    verified_ciks = {check["cik"] for check in checks}
    matches = sum(
        _normalized_value(check["field"], investors_by_cik[check["cik"]].get(check["field"]))
        == _normalized_value(check["field"], check["verified_value"])
        for check in checks
    )
    return {
        "total_records": total,
        "active_records": sum(record.get("is_active") is True for record in investors),
        "verified_records": len(verified_ciks),
        "accuracy_percent": round(matches / len(checks) * 100, 2) if checks else None,
        "accuracy_sample_size": len(verified_ciks),
        "completeness_percent": (
            round(present / denominator * 100, 2) if denominator else 0.0
        ),
        "as_of": (as_of or date.today()).isoformat(),
    }


def _normalized_value(field: str, value: Any) -> str | None:
    if value is None:
        return None
    if field == "target_sectors":
        if isinstance(value, str):
            sectors = value.split("|")
        elif isinstance(value, list) and all(isinstance(item, str) for item in value):
            sectors = value
        else:
            return None
        normalized = sorted(sector.strip().casefold() for sector in sectors if sector.strip())
        return "|".join(normalized) if normalized else None
    if field == "is_active":
        text = str(value).strip().casefold()
        return text if text in {"true", "false"} else None
    if field in {"aum_usd", "check_size_min_usd", "check_size_max_usd"}:
        try:
            number = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
        return str(number.normalize()) if number.is_finite() else None
    text = str(value).strip()
    if not text:
        return None
    if field == "latest_filing_date":
        try:
            return date.fromisoformat(text).isoformat()
        except ValueError:
            return None
    return " ".join(text.casefold().split())
