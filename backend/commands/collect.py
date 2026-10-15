"""CLI for collecting configured SEC CIK seeds."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from ..collection.config import DEFAULT_OUTPUT_PATH, DEFAULT_SEED_PATH
from ..collection.service import collect_to_csv


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect SEC 13F filing metadata for configured seed CIKs."
    )
    parser.add_argument(
        "--seeds",
        default=os.environ.get("SEED_CIK_CSV", str(DEFAULT_SEED_PATH)),
        help="CSV containing a CIK column (or CIKs in its first column).",
    )
    parser.add_argument(
        "--output",
        default=os.environ.get("OUTPUT_CSV", str(DEFAULT_OUTPUT_PATH)),
        help="Destination CSV (default: data/processed/sample_investors.csv).",
    )
    parser.add_argument(
        "--active-months",
        type=int,
        default=None,
        help="Active 13F threshold from 12 to 24 months; defaults to ACTIVE_MONTHS or 24.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        records = collect_to_csv(
            Path(args.seeds), Path(args.output), active_months=args.active_months
        )
    except (OSError, ValueError) as exc:
        logging.error("Collection/export failed: %s", exc)
        return 1
    logging.info("Exported %d records to %s", len(records), args.output)
    return 0
