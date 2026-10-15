"""Compatibility exports for the refactored :mod:`backend.collection` package."""

from .collection.client import SECClient, SECRequestError, _user_agent
from .collection.config import (
    CSV_FIELDS,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SEED_PATH,
    PUBLIC_FIELDS,
    SEC_SUBMISSIONS_FILES_URL,
)
from .collection.export import write_csv
from .collection.history import latest_13f_in_submissions
from .collection.seeds import load_seed_ciks
from .collection.service import (
    _subtract_months,
    collect_records,
    collect_to_csv,
    configured_active_months,
)

_latest_13f_in_submissions = latest_13f_in_submissions

__all__ = [
    "CSV_FIELDS",
    "DEFAULT_OUTPUT_PATH",
    "DEFAULT_SEED_PATH",
    "PUBLIC_FIELDS",
    "SEC_SUBMISSIONS_FILES_URL",
    "SECClient",
    "SECRequestError",
    "collect_records",
    "collect_to_csv",
    "configured_active_months",
    "load_seed_ciks",
    "write_csv",
]
