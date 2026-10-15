"""Rate-limited SEC HTTP client with bounded retry behavior."""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


_CONTACT_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")


class SECRequestError(RuntimeError):
    """A network, HTTP, or JSON failure while requesting SEC data."""


def _user_agent() -> str:
    value = os.environ.get("SEC_USER_AGENT", "").strip()
    if not value:
        raise ValueError(
            "SEC_USER_AGENT is required for SEC requests. Set a truthful, "
            "descriptive application identity and contact address."
        )
    return value


class SECClient:
    def __init__(
        self,
        user_agent: str | None = None,
        timeout: float = 15.0,
        retries: int = 2,
        opener: Any = urlopen,
        sleeper: Any = time.sleep,
    ) -> None:
        self.user_agent = user_agent.strip() if user_agent else _user_agent()
        contact = _CONTACT_EMAIL_RE.search(self.user_agent)
        if not contact or not self.user_agent[:contact.start()].strip():
            raise ValueError(
                "SEC_USER_AGENT must include a descriptive application name "
                "and contact email address."
            )
        self.timeout = timeout
        self.retries = max(0, retries)
        self.opener = opener
        self.sleeper = sleeper
        self._last_request_at: float | None = None

    def get_json(self, url: str) -> dict[str, Any]:
        request = Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json",
            },
        )
        for attempt in range(self.retries + 1):
            if self._last_request_at is not None:
                elapsed = time.monotonic() - self._last_request_at
                if elapsed < 0.11:
                    self.sleeper(0.11 - elapsed)
            self._last_request_at = time.monotonic()
            try:
                with self.opener(request, timeout=self.timeout) as response:
                    status = getattr(response, "status", 200)
                    if status < 200 or status >= 300:
                        raise SECRequestError(f"SEC returned HTTP {status} for {url}")
                    raw = response.read()
                try:
                    result = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise SECRequestError(f"SEC returned invalid JSON for {url}") from exc
                if not isinstance(result, dict):
                    raise SECRequestError(f"SEC JSON response was not an object: {url}")
                return result
            except HTTPError as exc:
                retryable = exc.code == 429 or 500 <= exc.code < 600
                if retryable and attempt < self.retries:
                    self.sleeper(min(2**attempt, 8))
                    continue
                raise SECRequestError(f"SEC HTTP error {exc.code} for {url}") from exc
            except (URLError, TimeoutError, OSError) as exc:
                if attempt < self.retries:
                    self.sleeper(min(2**attempt, 8))
                    continue
                raise SECRequestError(
                    f"SEC network request failed for {url}: {exc}"
                ) from exc
        raise SECRequestError(f"SEC request failed for {url}")
