from __future__ import annotations

import logging
import sys
from dataclasses import dataclass

from app.ingestion.models import Document, FetchResult, PipelineResult, ChunkResult
from app.ingestion.fetcher import fetch_url, FetchError, FetchTimeoutError, FetchRedirectError
from app.ingestion.parsers import get_parser_for_content_type, ParserError
from app.ingestion.parsers.html_parser import HTMLParser  # noqa: F401 — force registration
from app.ingestion.parsers.pdf_parser import PDFParser  # noqa: F401 — force registration
from app.ingestion.normalizer import normalize_document
from app.ingestion.chunker import chunk_document

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


@dataclass
class PipelineStepResult:
    """Result of a single pipeline step, with optional error context."""

    success: bool
    error: str | None = None
    error_type: str | None = None  # "fetch" | "parse" | "normalize" | "chunk"


@dataclass
class PipelineError:
    """Details about a pipeline failure."""

    step: str
    message: str
    error_type: str


@dataclass
class PipelineOutcome:
    """Complete result of a pipeline run, including partial failures."""

    success: bool
    document: Document | None = None
    chunks: list[ChunkResult] | None = None
    errors: list[PipelineError] = None

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []


async def run_pipeline(
    url: str,
    *,
    timeout: float = 30.0,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    max_redirects: int = 10,
    user_agent: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> PipelineOutcome:
    """Run the full ingestion pipeline: Fetcher → Parser → Normalizer → Chunker.

    Parameters
    ----------
    url:
        The URL to fetch and process.
    timeout:
        HTTP request timeout in seconds.
    chunk_size:
        Character limit per chunk.
    chunk_overlap:
        Character overlap between consecutive chunks.
    max_redirects:
        Maximum number of HTTP redirects to follow.
    user_agent:
        Custom User-Agent header.
    extra_headers:
        Additional HTTP headers.

    Returns
    -------
    A ``PipelineOutcome`` with the result (or errors).
    """
    outcome = PipelineOutcome(success=True)

    # ── Step 1: Fetch ──────────────────────────────────────────────────
    fetch_result: FetchResult | None = None
    try:
        fetch_result = await fetch_url(
            url,
            timeout=timeout,
            max_redirects=max_redirects,
            user_agent=user_agent,
            extra_headers=extra_headers,
        )
    except FetchTimeoutError as exc:
        return _fail(outcome, "fetch", str(exc), "timeout")
    except FetchRedirectError as exc:
        return _fail(outcome, "fetch", str(exc), "redirect")
    except FetchError as exc:
        return _fail(outcome, "fetch", str(exc), "http_error")
    except Exception as exc:
        return _fail(outcome, "fetch", f"Unexpected fetch error: {exc}", "unexpected")

    # ── Step 2: Parse ──────────────────────────────────────────────────
    parser = get_parser_for_content_type(fetch_result.content_type)
    if parser is None:
        return _fail(
            outcome,
            "parse",
            f"No parser registered for content type '{fetch_result.content_type}' (url={url})",
            "unsupported_type",
        )

    document: Document | None = None
    try:
        document = await parser.parse(fetch_result)
    except ParserError as exc:
        return _fail(outcome, "parse", str(exc), "parse_error")
    except Exception as exc:
        return _fail(outcome, "parse", f"Unexpected parse error: {exc}", "unexpected")

    # ── Step 3: Normalize ──────────────────────────────────────────────
    try:
        document = normalize_document(document)
    except Exception as exc:
        return _fail(outcome, "normalize", f"Normalization failed: {exc}", "unexpected")

    if not document.content.strip():
        return _fail(outcome, "normalize", "Document is empty after normalization", "empty_content")

    # ── Step 4: Chunk ──────────────────────────────────────────────────
    try:
        chunks = chunk_document(document, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    except Exception as exc:
        return _fail(outcome, "chunk", f"Chunking failed: {exc}", "unexpected")

    if not chunks:
        return _fail(outcome, "chunk", "Chunker produced no chunks", "empty_chunks")

    outcome.document = document
    outcome.chunks = chunks
    outcome.success = True

    logger.info(
        "Pipeline completed successfully: url=%s, type=%s, chunks=%d, total_chars=%d",
        url,
        document.content_type,
        len(chunks),
        len(document.content),
    )

    return outcome


def _fail(outcome: PipelineOutcome, step: str, message: str, error_type: str) -> PipelineOutcome:
    """Record a failure and return the outcome."""
    outcome.success = False
    outcome.errors.append(PipelineError(step=step, message=message, error_type=error_type))
    logger.warning("Pipeline step '%s' failed: %s", step, message)
    return outcome