"""HTTP endpoints for investor records, quality metrics, and scaling."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

from ..domain.metrics import calculate_metrics
from .data import load_investors, load_verification_sample
from .scaling import build_scaling_estimate

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


@router.get("/investors")
def get_investors() -> dict[str, Any]:
    """Return configured-seed records using the public investor contract."""
    return {"investors": load_investors()}


@router.get("/metrics")
def get_metrics() -> dict[str, Any]:
    investors = load_investors()
    checks = load_verification_sample()
    known_ciks = {record["cik"] for record in investors}
    stale_checks = sum(1 for check in checks if check["cik"] not in known_ciks)
    if stale_checks:
        LOGGER.warning(
            "Ignoring %d verification checks whose CIKs are not in the current dataset",
            stale_checks,
        )
    return calculate_metrics(investors, checks)


@router.get("/scaling")
def get_scaling() -> dict[str, object]:
    return build_scaling_estimate()
