import pytest
from datetime import datetime

from app.services.ingest import chunk_text, extract_text_from_pdf_bytes


def test_chunk_text_creates_overlapping_chunks():
    text = "a" * 2500
    chunks = chunk_text(text, chunk_size=1000, chunk_overlap=200)

    assert len(chunks) == 4
    assert chunks[0] == "a" * 1000
    assert chunks[1].startswith("a" * 800)
    assert chunks[2].startswith("a" * 800)
    assert len(chunks[3]) == 100


def test_extract_text_from_pdf_bytes_empty():
    # PDF extraction is best-effort; if no pages exist, it should not fail.
    result = extract_text_from_pdf_bytes(b"%PDF-1.4\n%EOF")
    assert isinstance(result, str)
