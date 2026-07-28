from __future__ import annotations

import logging
import re
import sys

import httpx
from fastapi import APIRouter, HTTPException, Query, status

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

router = APIRouter(prefix="/fetch-title", tags=["fetch-title"])


TITLE_RE = re.compile(rb"<title[^>]*>(.*?)</title>", re.IGNORECASE)


@router.get("", status_code=status.HTTP_200_OK)
async def fetch_title(url: str = Query(..., description="The URL to fetch the title from")):
    """Fetch a URL and extract its <title> tag.

    This is a lightweight endpoint used by the frontend to auto-populate
    the source name when adding a URL source. Only the `<title>` element
    is read — the full page body is not downloaded.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; VectorSearch/1.0; +https://vectorsearch.app)",
                "Accept": "text/html,application/xhtml+xml",
            })
            response.raise_for_status()

            # Only try to extract title from HTML responses
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                return {"title": None}

            match = TITLE_RE.search(response.content)
            if match:
                raw = match.group(1).strip()
                # Decode with the response encoding, fall back to utf-8
                try:
                    encoding = response.encoding or "utf-8"
                    title = raw.decode(encoding).strip()
                except (LookupError, UnicodeDecodeError):
                    title = raw.decode("utf-8", errors="replace").strip()
                # Clean up whitespace
                title = re.sub(r"\s+", " ", title)
                # Truncate overly long titles
                if len(title) > 200:
                    title = title[:200] + "…"
                return {"title": title if title else None}

            return {"title": None}

    except httpx.TimeoutException:
        logger.warning("Title fetch timed out for %s", url)
        return {"title": None}
    except httpx.HTTPStatusError as exc:
        logger.warning("Title fetch got HTTP %s for %s", exc.response.status_code, url)
        return {"title": None}
    except httpx.RequestError as exc:
        logger.warning("Title fetch failed for %s: %s", url, exc)
        return {"title": None}