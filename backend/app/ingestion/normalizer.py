from __future__ import annotations

import logging
import re
import sys

from app.ingestion.models import Document

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def normalize_document(document: Document) -> Document:
    """Normalize a document's content for consistent chunking.

    Applies the following transformations:
    - Collapses multiple blank lines into at most two
    - Strips leading/trailing whitespace from each line
    - Removes lines that are only whitespace or punctuation
    - Normalizes Unicode whitespace characters
    - Limits consecutive newlines to a maximum of two

    Parameters
    ----------
    document:
        The document to normalize.

    Returns
    -------
    A new ``Document`` with cleaned content.
    """
    content = document.content

    # Normalize Unicode whitespace (non-breaking spaces, thin spaces, etc.).
    content = re.sub(r"[\u00a0\u2000-\u200a\u202f\u205f\u3000]", " ", content)

    # Split into lines, strip each, and filter out empty/punctuation-only lines.
    lines = content.split("\n")
    cleaned_lines: list[str] = []
    consecutive_blanks = 0
    max_consecutive_blanks = 1  # at most one blank line between paragraphs.

    for line in lines:
        stripped = line.strip()

        # Skip lines that are only punctuation or whitespace.
        if stripped and re.match(r"^[^\w\s]+$", stripped):
            continue

        if not stripped:
            consecutive_blanks += 1
            if consecutive_blanks <= max_consecutive_blanks:
                cleaned_lines.append("")
        else:
            consecutive_blanks = 0
            cleaned_lines.append(stripped)

    # Remove leading/trailing blank lines.
    while cleaned_lines and cleaned_lines[0] == "":
        cleaned_lines.pop(0)
    while cleaned_lines and cleaned_lines[-1] == "":
        cleaned_lines.pop()

    normalized = "\n".join(cleaned_lines)

    logger.info(
        "Normalized document: length %d → %d chars (%.1f%% reduction)",
        len(document.content),
        len(normalized),
        (1 - len(normalized) / max(len(document.content), 1)) * 100,
    )

    return Document(
        title=document.title,
        content=normalized,
        source_url=document.source_url,
        content_type=document.content_type,
        metadata=document.metadata,
    )