from __future__ import annotations

import logging
import sys
from typing import ClassVar
from urllib.parse import urlparse

from app.ingestion.models import Document, FetchResult
from app.ingestion.parsers.base import BaseParser, ParserError, register_parser

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


class HTMLParser(BaseParser):
    """Parse HTML content into a ``Document``.

    Uses ``readability-lxml`` to extract the main article content, then
    cleans it with ``BeautifulSoup`` to remove script, style, and nav
    elements.
    """

    content_types: ClassVar[list[str]] = [
        "text/html",
        "application/xhtml+xml",
    ]

    async def parse(self, fetch_result: FetchResult) -> Document:
        body = fetch_result.body
        url = fetch_result.url
        encoding = fetch_result.encoding or "utf-8"

        if not body:
            raise ParserError(fetch_result.content_type, "Empty response body")

        try:
            import readability
            import bs4
        except ImportError as exc:
            raise ParserError(
                fetch_result.content_type,
                "Missing dependencies: install 'readability-lxml' and 'beautifulsoup4'",
            ) from exc

        # Decode body to string — readability-lxml expects str, not bytes.
        try:
            html_str = body.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            html_str = body.decode("utf-8", errors="replace")

        # --- Step 1: Extract title from raw HTML (before readability mangles it) ---
        title = _extract_title(body, encoding, url)

        # --- Step 2: Use readability-lxml to extract the main article ---
        summary_html = None
        try:
            doc = readability.Document(html_str)
            summary_html = doc.summary()
            # Use readability's title detection as fallback.
            readability_title = doc.title()
            if title is None and readability_title:
                title = readability_title
        except Exception:
            logger.info("readability-lxml failed, falling back to BeautifulSoup extraction")
            summary_html = None

        # --- Step 3: Fallback to BeautifulSoup if readability didn't produce content ---
        if not summary_html or not summary_html.strip():
            try:
                soup = bs4.BeautifulSoup(html_str, "lxml")
                # Remove unwanted elements (scripts, nav, etc.).
                for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "form"]):
                    tag.decompose()
                # Try to find a main content area, or fall back to body.
                main = soup.find("article") or soup.find("main") or soup.find("body") or soup
                content = main.get_text(separator="\n", strip=True)
                if not content.strip():
                    raise ParserError(fetch_result.content_type, "No extractable text content found")
                logger.info(
                    "HTML parsed via BeautifulSoup fallback: title='%s', content_length=%d, url=%s",
                    title, len(content), url,
                )
                metadata: dict = {
                    "source_domain": urlparse(url).netloc,
                    "charset": encoding,
                    "parser": "beautifulsoup_fallback",
                }
                return Document(
                    title=title or url,
                    content=content,
                    source_url=url,
                    content_type="text/html",
                    metadata=metadata,
                )
            except ParserError:
                raise
            except Exception as exc:
                raise ParserError(fetch_result.content_type, f"BeautifulSoup fallback failed: {exc}") from exc

        # --- Step 4: Clean the readability-extracted HTML with BeautifulSoup ---
        try:
            soup = bs4.BeautifulSoup(summary_html, "lxml")
        except Exception as exc:
            raise ParserError(fetch_result.content_type, f"BeautifulSoup parsing failed: {exc}") from exc

        # Remove unwanted elements from the article HTML.
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "form"]):
            tag.decompose()

        # Extract clean text from the cleaned article.
        content = soup.get_text(separator="\n", strip=True)

        if not content.strip():
            raise ParserError(fetch_result.content_type, "No extractable text content found after cleaning")

        logger.info(
            "HTML parsed via readability: title='%s', content_length=%d, url=%s",
            title, len(content), url,
        )

        # --- Step 5: Build metadata with source domain and parser info ---
        metadata: dict = {
            "source_domain": urlparse(url).netloc,
            "charset": encoding,
            "parser": "readability",
        }

        return Document(
            title=title or url,
            content=content,
            source_url=url,
            content_type="text/html",
            metadata=metadata,
        )


def _extract_title(body: bytes, encoding: str, fallback_url: str) -> str | None:
    """Extract the <title> from raw HTML without running readability."""
    import bs4
    try:
        soup = bs4.BeautifulSoup(body, "lxml", from_encoding=encoding)
    except Exception:
        return None
    # Try <title> first, then fall back to <h1>.
    title_tag = soup.find("title")
    if title_tag and title_tag.get_text(strip=True):
        return title_tag.get_text(strip=True)
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    return None


# Auto-register this parser with the global parser registry.
register_parser(HTMLParser())