"""Compatibility exports for :mod:`backend.domain.validator`."""

from .domain.validator import (
    ValidationError,
    filing_url,
    normalize_cik,
    parse_filing_date,
    validate_investor,
    validate_submissions,
)

__all__ = [
    "ValidationError",
    "filing_url",
    "normalize_cik",
    "parse_filing_date",
    "validate_investor",
    "validate_submissions",
]
