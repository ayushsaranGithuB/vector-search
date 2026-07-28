from __future__ import annotations

import logging
import sys
from io import BytesIO
from typing import ClassVar

from app.ingestion.models import Document, FetchResult
from app.ingestion.parsers.base import BaseParser, ParserError, register_parser

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


class PDFParser(BaseParser):
    """Parse PDF content into a ``Document`` using ``pypdf``."""

    content_types: ClassVar[list[str]] = [
        "application/pdf",
    ]

    async def parse(self, fetch_result: FetchResult) -> Document:
        body = fetch_result.body
        url = fetch_result.url

        if not body:
            raise ParserError(fetch_result.content_type, "Empty response body")

        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ParserError(
                fetch_result.content_type,
                "Missing dependency: install 'pypdf'",
            ) from exc

        try:
            reader = PdfReader(stream=BytesIO(body))
        except Exception as exc:
            raise ParserError(fetch_result.content_type, f"pypdf failed to read PDF: {exc}") from exc

        if reader.pages is None or len(reader.pages) == 0:
            raise ParserError(fetch_result.content_type, "PDF has no pages")

        # Extract text from each page
        pages_text: list[str] = []
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
                pages_text.append(text)
            except Exception as exc:
                logger.warning("Failed to extract text from page %d of %s: %s", i, url, exc)
                pages_text.append("")

        content = "\n\n".join(pages_text).strip()

        if not content:
            raise ParserError(fetch_result.content_type, "No extractable text content found in PDF")

        # Extract title from PDF metadata or fall back to the URL
        title = _extract_pdf_title(reader, url)

        num_pages = len(reader.pages)

        logger.info(
            "PDF parsed: title='%s', pages=%d, content_length=%d, url=%s",
            title, num_pages, len(content), url,
        )

        metadata: dict = {
            "num_pages": num_pages,
            "pdf_version": reader.metadata.get("/Version", None) if reader.metadata else None,
        }

        return Document(
            title=title,
            content=content,
            source_url=url,
            content_type="application/pdf",
            metadata=metadata,
        )


def _extract_pdf_title(reader, fallback_url: str) -> str:
    """Extract the PDF document title from metadata."""
    try:
        if reader.metadata and reader.metadata.title:
            title = reader.metadata.title.strip()
            if title:
                return title
    except Exception:
        pass
    # Fall back to the last segment of the URL
    import urllib.parse
    path = urllib.parse.urlparse(fallback_url).path
    filename = path.rstrip("/").split("/")[-1] if path else ""
    if filename:
        # Remove extension
        name, _ = filename.rsplit(".", 1) if "." in filename else (filename, None)
        return name.replace("-", " ").replace("_", " ").strip().title()
    return fallback_url


# Auto-register
register_parser(PDFParser())