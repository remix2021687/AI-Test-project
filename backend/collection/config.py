"""Shared constants for SEC collection and CSV export."""

from pathlib import Path

DEFAULT_SEED_PATH = Path("data/seeds/seed_ciks.csv")
DEFAULT_OUTPUT_PATH = Path("data/processed/sample_investors.csv")
SEC_SUBMISSIONS_FILES_URL = "https://data.sec.gov/submissions/{name}"

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
    "accession_number",
    "filing_url",
]
PUBLIC_FIELDS = CSV_FIELDS[:10]
