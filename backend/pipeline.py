"""Compatibility CLI for ``python -m backend.pipeline``."""

from .commands.collect import main

__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
