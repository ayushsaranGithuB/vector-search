from __future__ import annotations

import logging
import sys
from typing import Any

import httpx

from app.ingestion.models import FetchResult

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


class FetchError(Exception):
    """Raised when the fetcher cannot retrieve the URL."""

    def __init__(self, url: str, status_code: int | None = None, message: str = "") -> None:
        self.url = url
        self.status_code = status_code
        detail = f"Fetch failed for {url}"
        if status_code:
            detail += f" (HTTP {status_code})"
        if message:
            detail += f": {message}"
        super().__init__(detail)


class FetchTimeoutError(FetchError):
    """Raised when the request times out."""

    def __init__(self, url: str, timeout: float) -> None:
        super().__init__(url, message=f"Request timed out after {timeout}s")


class FetchRedirectError(FetchError):
    """Raised when too many redirects are encountered."""

    def __init__(self, url: str) -> None:
        super().__init__(url, message="Too many redirects")


async def fetch_url(
    url: str,
    *,
    timeout: float = 30.0,
    max_redirects: int = 10,
    follow_redirects: bool = True,
    user_agent: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> FetchResult:
    """Fetch a URL and return the raw response.

    Parameters
    ----------
    url:
        The URL to fetch.
    timeout:
        Maximum time in seconds to wait for a response.
    max_redirects:
        Maximum number of redirects to follow.
    follow_redirects:
        Whether to automatically follow redirects.
    user_agent:
        Custom User-Agent header. Defaults to a sensible browser-like value.
    extra_headers:
        Additional HTTP headers to include in the request.

    Returns
    -------
    A ``FetchResult`` with the raw response data.

    Raises
    ------
    FetchTimeoutError
        If the request times out.
    FetchRedirectError
        If too many redirects are encountered.
    FetchError
        For any other HTTP or connection error.
    """
    headers: dict[str, str] = {
        "User-Agent": user_agent or "VectorSearchBot/1.0 (+https://github.com/vector-search)",
        "Accept": "text/html,application/pdf,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    if extra_headers:
        headers.update(extra_headers)

    client_args: dict[str, Any] = {
        "timeout": httpx.Timeout(timeout),
        "follow_redirects": follow_redirects,
        "headers": headers,
        "max_redirects": max_redirects,
    }

    logger.info("Fetching URL: %s (timeout=%ss, max_redirects=%d)", url, timeout, max_redirects)

    try:
        async with httpx.AsyncClient(**client_args) as client:
            response = await client.get(url)
    except httpx.TimeoutException as exc:
        logger.warning("Timeout fetching %s after %ss", url, timeout)
        raise FetchTimeoutError(url, timeout) from exc
    except httpx.TooManyRedirects as exc:
        logger.warning("Too many redirects for %s", url)
        raise FetchRedirectError(url) from exc
    except httpx.HTTPError as exc:
        logger.warning("HTTP error fetching %s: %s", url, exc)
        raise FetchError(url, message=str(exc)) from exc

    if response.is_error:
        logger.warning("Non-OK status %d for %s", response.status_code, url)
        raise FetchError(url, status_code=response.status_code)

    # Determine effective content type from the Content-Type header
    raw_content_type = response.headers.get("content-type", "")
    effective_content_type = raw_content_type.split(";")[0].strip().lower()
    encoding = response.encoding or "utf-8"

    logger.info(
        "Fetched %s — status=%d, type=%s, size=%d bytes",
        url,
        response.status_code,
        effective_content_type,
        len(response.content),
    )

    return FetchResult(
        url=str(response.url),  # final URL after redirects
        status_code=response.status_code,
        content_type=effective_content_type,
        body=response.content,
        headers=dict(response.headers),
        encoding=encoding,
    )