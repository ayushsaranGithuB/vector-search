import pytest

from app.ingestion.chunker import chunk_document
from app.ingestion.models import Document


def test_chunk_document_creates_overlapping_chunks():
    doc = Document(
        title="Test",
        content="a" * 2500,
        source_url="https://example.com",
        content_type="text/plain",
    )
    chunks = chunk_document(doc, chunk_size=1000, chunk_overlap=200)

    assert len(chunks) == 4
    assert chunks[0].content == "a" * 1000
    assert chunks[1].content.startswith("a" * 800)
    assert chunks[2].content.startswith("a" * 800)
    assert len(chunks[3].content) == 100


def test_chunk_document_empty():
    doc = Document(
        title="Empty",
        content="",
        source_url="https://example.com",
        content_type="text/plain",
    )
    chunks = chunk_document(doc)
    assert chunks == []


def test_chunk_document_single_paragraph():
    doc = Document(
        title="Small",
        content="Hello world. This is a small document.",
        source_url="https://example.com",
        content_type="text/plain",
    )
    chunks = chunk_document(doc, chunk_size=1000, chunk_overlap=200)
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].token_count > 0
