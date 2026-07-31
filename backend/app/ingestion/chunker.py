from __future__ import annotations

import logging
import sys
from typing import Callable

from app.ingestion.models import ChunkResult, Document

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def chunk_document(
    document: Document,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    tokenizer: Callable[[str], int] | None = None,
) -> list[ChunkResult]:
    """Split a document's content into overlapping chunks.

    This is a sliding-window character-level chunker. It splits on
    paragraph boundaries (double newlines) when possible, falling back
    to sentence boundaries and then exact character positions.

    Parameters
    ----------
    document:
        The normalized document to chunk.
    chunk_size:
        Maximum number of characters per chunk.
    chunk_overlap:
        Number of characters of overlap between consecutive chunks.
    tokenizer:
        Optional callable that returns a token count for a string.
        If provided, ``token_count`` on each ``ChunkResult`` is set
        accordingly. Defaults to word-count via ``len(text.split())``.

    Returns
    -------
    A list of ``ChunkResult`` objects.
    """
    text = document.content
    if not text:
        return []

    # Split into paragraphs first, preserving paragraph boundaries for splitting.
    paragraphs = text.split("\n\n")
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks: list[str] = []

    if not paragraphs:
        return []

    current_chunk = ""

    for para in paragraphs:
        # If adding this paragraph doesn't exceed the limit, append it.
        if not current_chunk:
            current_chunk = para
        elif len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk += "\n\n" + para
        else:
            # Current chunk is full; save it and start a new one with overlap.
            chunks.append(current_chunk.strip())

            if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                overlap_text = _find_paragraph_boundary(current_chunk, chunk_overlap)
                current_chunk = overlap_text + "\n\n" + para
            else:
                current_chunk = para

    # Don't forget the last chunk.
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # If any chunk still exceeds the limit, split it by exact character positions.
    final_chunks: list[str] = []
    for chunk in chunks:
        if len(chunk) > chunk_size:
            final_chunks.extend(_split_by_chars(chunk, chunk_size, chunk_overlap))
        else:
            final_chunks.append(chunk)

    # Build ChunkResult objects with token counts.
    tokenizer = tokenizer or (lambda s: len(s.split()))
    results: list[ChunkResult] = []
    for index, content in enumerate(final_chunks):
        results.append(
            ChunkResult(
                content=content,
                chunk_index=index,
                token_count=tokenizer(content),
            )
        )

    logger.info(
        "Chunked document into %d chunks (size=%d, overlap=%d)",
        len(results),
        chunk_size,
        chunk_overlap,
    )

    return results


def _find_paragraph_boundary(text: str, target_chars: int) -> str:
    """Find a good split point near ``target_chars`` characters from the end.

    Prefers splitting at a paragraph boundary (``\\n\\n``) or sentence
    boundary (``. ``). Falls back to the exact character position.
    """
    if len(text) <= target_chars:
        return text

    start = len(text) - target_chars

    # Try to find a paragraph boundary after the start point.
    para_boundary = text.find("\n\n", start)
    if para_boundary != -1 and para_boundary < len(text) - 1:
        return text[para_boundary + 2 :]

    # Try to find a sentence boundary.
    sentence_boundary = text.find(". ", start)
    if sentence_boundary != -1 and sentence_boundary < len(text) - 1:
        return text[sentence_boundary + 2 :]

    # Fall back to exact character position.
    return text[start:]


def _split_by_chars(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Fallback: split text by exact character positions with sliding window."""
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        start += chunk_size - chunk_overlap
    return [c for c in chunks if c]