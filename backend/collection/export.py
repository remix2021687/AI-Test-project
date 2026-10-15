"""Write collected investor records as an atomic CSV export."""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path
from typing import Any

from .config import CSV_FIELDS, DEFAULT_OUTPUT_PATH


def write_csv(
    records: list[dict[str, Any]], output_path: str | Path = DEFAULT_OUTPUT_PATH
) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
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
