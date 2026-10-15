"""FastAPI application factory and middleware configuration."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router


def create_app() -> FastAPI:
    application = FastAPI(title="Seeded SEC Investor Database", version="1.0.0")
    cors_origins = [
        origin.strip()
        for origin in os.environ.get("CORS_ORIGINS", "").split(",")
        if origin.strip()
    ]
    if cors_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_methods=["GET"],
            allow_headers=["Accept"],
        )
    application.include_router(router)
    return application


app = create_app()
