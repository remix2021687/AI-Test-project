"""Read and normalize configured SEC seed CIKs."""

from __future__ import annotations

import csv
import logging
from itertools import chain
from pathlib import Path

from ..domain.validator import ValidationError, normalize_cik
from .config import DEFAULT_SEED_PATH

LOGGER = logging.getLogger(__name__)


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
            for line_number, row in enumerate(
                rows, start=2 if "cik" in header else 1
            ):
                if not row or cik_index >= len(row) or not row[cik_index].strip():
                    continue
                try:
                    cik = normalize_cik(row[cik_index])
                except ValidationError as exc:
                    LOGGER.warning(
                        "Skipping invalid CIK at %s:%d: %s",
                        seed_path,
                        line_number,
                        exc,
                    )
                    continue
                if cik not in seen:
                    seen.add(cik)
                    ciks.append(cik)
    except (OSError, csv.Error) as exc:
        raise ValueError(f"Unable to read seed CIK CSV {seed_path}: {exc}") from exc
    return ciks
