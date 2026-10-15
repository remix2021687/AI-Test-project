"""Build scaling scenario estimates from explicit environment assumptions."""

from __future__ import annotations

import os

from fastapi import HTTPException

from .data import load_investors


def build_scaling_estimate() -> dict[str, object]:
    current = len(load_investors())
    target = _positive_int_env("SCALING_TARGET_RECORDS", 10000)
    unit_cost = _optional_nonnegative_float_env("COST_PER_RECORD_USD")
    total_cost = target * unit_cost if unit_cost is not None else None
    if total_cost is not None and total_cost == float("inf"):
        raise HTTPException(
            status_code=500, detail="Estimated scaling cost exceeds numeric range"
        )
    return {
        "current_records": current,
        "target_records": target,
        "cost_per_record_usd": unit_cost,
        "estimated_total_cost_usd": (
            round(total_cost, 2) if total_cost is not None else None
        ),
        "assumptions": [
            "Target record count is configurable via SCALING_TARGET_RECORDS (default 10000).",
            "COST_PER_RECORD_USD is a user-supplied planning assumption; no cost is "
            "shown until one is configured.",
            "This is a linear scenario only, not a quote or validated forecast.",
        ],
    }


def _positive_int_env(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError as exc:
        raise HTTPException(
            status_code=500, detail=f"{name} must be a positive integer"
        ) from exc
    if value < 1:
        raise HTTPException(
            status_code=500, detail=f"{name} must be a positive integer"
        )
    return value


def _optional_nonnegative_float_env(name: str) -> float | None:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return None
    try:
        value = float(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=500, detail=f"{name} must be a non-negative number"
        ) from exc
    if value < 0 or value != value or value in (float("inf"), float("-inf")):
        raise HTTPException(
            status_code=500, detail=f"{name} must be finite and non-negative"
        )
    return value
