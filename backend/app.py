"""Compatibility entry point for the FastAPI application.

Run the server with ``uvicorn backend.app:app``. Implementation lives under
``backend.api``.
"""

from .api.application import app, create_app
from .api.data import (
    DEFAULT_VERIFICATION_SAMPLE_PATH,
    _optional_number,
    _optional_sectors,
    load_investors,
    load_verification_sample,
)
from .api.routes import get_investors, get_metrics, get_scaling
from .api.scaling import _optional_nonnegative_float_env, _positive_int_env

__all__ = [
    "DEFAULT_VERIFICATION_SAMPLE_PATH",
    "app",
    "create_app",
    "get_investors",
    "get_metrics",
    "get_scaling",
    "load_investors",
    "load_verification_sample",
]
