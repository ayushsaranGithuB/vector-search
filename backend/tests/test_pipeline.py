"""Tests for the ingestion pipeline modules: fetcher, parsers, normalizer, chunker, and pipeline orchestrator."""

import pytest

from app.ingestion.models import Document, FetchResult
from app.ingestion.normalizer import normalize_document
from app.ingestion.chunker import chunk_document
from app.ingestion.parsers.html_parser import HTMLParser
from app.ingestion.parsers.pdf_parser import PDFParser
from app.ingestion.parsers.base import get_parser_for_content_type


# ── Normalizer Tests ───────────────────────────────────────────────────


class TestNormalizer:
    def test_collapses_extra_blank_lines(self):
        doc = Document(
            title="Test",
            content="Line 1\n\n\n\n\nLine 2\n\n\nLine 3",
            source_url="https://example.com",
            content_type="text/plain",
        )
        result = normalize_document(doc)
        assert result.content == "Line 1\n\nLine 2\n\nLine 3"

    def test_strips_leading_trailing_blank_lines(self):
        doc = Document(
            title="Test",
            content="\n\n\nHello world\n\n\n",
            source_url="https://example.com",
            content_type="text/plain",
        )
        result = normalize_document(doc)
        assert result.content == "Hello world"

    def test_removes_punctuation_only_lines(self):
        doc = Document(
            title="Test",
            content="Hello\n---\nWorld\n***\n!",
            source_url="https://example.com",
            content_type="text/plain",
        )
        result = normalize_document(doc)
        assert result.content == "Hello\nWorld"

    def test_normalizes_unicode_whitespace(self):
        doc = Document(
            title="Test",
            content="Hello\u00a0World\u2003Test",
            source_url="https://example.com",
            content_type="text/plain",
        )
        result = normalize_document(doc)
        assert "Hello World Test" in result.content

    def test_does_not_modify_single_line(self):
        doc = Document(
            title="Test",
            content="This is a single line of text.",
            source_url="https://example.com",
            content_type="text/plain",
        )
        result = normalize_document(doc)
        assert result.content == "This is a single line of text."


# ── Chunker Tests ──────────────────────────────────────────────────────


class TestChunker:
    def test_single_chunk_for_small_document(self):
        doc = Document(
            title="Small",
            content="Hello world. This is a small document.",
            source_url="https://example.com",
            content_type="text/plain",
        )
        chunks = chunk_document(doc, chunk_size=1000, chunk_overlap=200)
        assert len(chunks) == 1
        assert chunks[0].chunk_index == 0

    def test_multiple_chunks_with_overlap(self):
        doc = Document(
            title="Long",
            content="a" * 2500,
            source_url="https://example.com",
            content_type="text/plain",
        )
        chunks = chunk_document(doc, chunk_size=1000, chunk_overlap=200)
        assert len(chunks) == 4
        # Each chunk content should be non-empty
        for c in chunks:
            assert len(c.content) > 0

    def test_chunks_have_token_count(self):
        doc = Document(
            title="Count",
            content="one two three four five",
            source_url="https://example.com",
            content_type="text/plain",
        )
        chunks = chunk_document(doc, chunk_size=1000, chunk_overlap=200)
        assert len(chunks) == 1
        assert chunks[0].token_count == 5

    def test_empty_document_returns_empty_list(self):
        doc = Document(
            title="Empty",
            content="",
            source_url="https://example.com",
            content_type="text/plain",
        )
        chunks = chunk_document(doc)
        assert chunks == []

    def test_paragraph_boundary_split(self):
        """Chunks should prefer splitting at paragraph boundaries."""
        text = "\n\n".join(["p" * 600 for _ in range(5)])
        doc = Document(
            title="Paragraphs",
            content=text,
            source_url="https://example.com",
            content_type="text/plain",
        )
        chunks = chunk_document(doc, chunk_size=1000, chunk_overlap=200)
        assert len(chunks) > 1


# ── Parser Registry Tests ──────────────────────────────────────────────


class TestParserRegistry:
    def test_get_parser_for_html(self):
        parser = get_parser_for_content_type("text/html")
        assert parser is not None
        assert isinstance(parser, HTMLParser)

    def test_get_parser_for_xhtml(self):
        parser = get_parser_for_content_type("application/xhtml+xml")
        assert parser is not None
        assert isinstance(parser, HTMLParser)

    def test_get_parser_for_pdf(self):
        parser = get_parser_for_content_type("application/pdf")
        assert parser is not None
        assert isinstance(parser, PDFParser)

    def test_get_parser_for_unknown_type(self):
        parser = get_parser_for_content_type("application/docx")
        assert parser is None

    def test_get_parser_for_unknown_markdown(self):
        parser = get_parser_for_content_type("text/markdown")
        assert parser is None


# ── PDF Parser Tests ───────────────────────────────────────────────────


class TestPDFParser:
    @pytest.mark.asyncio
    async def test_parse_empty_body_raises_error(self):
        parser = PDFParser()
        fetch_result = FetchResult(
            url="https://example.com/test.pdf",
            status_code=200,
            content_type="application/pdf",
            body=b"",
            headers={},
        )
        from app.ingestion.parsers.base import ParserError

        with pytest.raises(ParserError, match="Empty response body"):
            await parser.parse(fetch_result)

    @pytest.mark.asyncio
    async def test_parse_invalid_pdf_raises_error(self):
        parser = PDFParser()
        fetch_result = FetchResult(
            url="https://example.com/test.pdf",
            status_code=200,
            content_type="application/pdf",
            body=b"this is not a pdf",
            headers={},
        )
        from app.ingestion.parsers.base import ParserError

        with pytest.raises(ParserError, match="pypdf failed to read PDF"):
            await parser.parse(fetch_result)


# ── HTML Parser Tests ──────────────────────────────────────────────────


class TestHTMLParser:
    @pytest.mark.asyncio
    async def test_parse_empty_body_raises_error(self):
        parser = HTMLParser()
        fetch_result = FetchResult(
            url="https://example.com/page",
            status_code=200,
            content_type="text/html",
            body=b"",
            headers={},
        )
        from app.ingestion.parsers.base import ParserError

        with pytest.raises(ParserError, match="Empty response body"):
            await parser.parse(fetch_result)

    @pytest.mark.asyncio
    async def test_parse_simple_html(self):
        parser = HTMLParser()
        html = b"<html><head><title>Test Page</title></head><body><article><p>Hello world</p></article></body></html>"
        fetch_result = FetchResult(
            url="https://example.com/page",
            status_code=200,
            content_type="text/html",
            body=html,
            headers={},
        )
        doc = await parser.parse(fetch_result)
        assert doc.title == "Test Page"
        assert "Hello world" in doc.content
        assert doc.source_url == "https://example.com/page"
        assert doc.content_type == "text/html"

    @pytest.mark.asyncio
    async def test_parse_html_without_title(self):
        parser = HTMLParser()
        html = b"<html><body><h1>Header Title</h1><p>Content here</p></body></html>"
        fetch_result = FetchResult(
            url="https://example.com/page",
            status_code=200,
            content_type="text/html",
            body=html,
            headers={},
        )
        doc = await parser.parse(fetch_result)
        # Should fall back to h1 or readability title
        assert doc.title is not None
        assert "Content here" in doc.content

    @pytest.mark.asyncio
    async def test_parse_strips_script_and_style(self):
        parser = HTMLParser()
        html = b"""
        <html><head><title>Clean</title></head>
        <body>
            <article>
                <p>Visible text</p>
                <script>alert('hidden')</script>
                <style>.hidden{}</style>
                <nav>Navigation</nav>
            </article>
        </body></html>
        """
        fetch_result = FetchResult(
            url="https://example.com/page",
            status_code=200,
            content_type="text/html",
            body=html,
            headers={},
        )
        doc = await parser.parse(fetch_result)
        assert "Visible text" in doc.content
        assert "alert" not in doc.content
        assert ".hidden" not in doc.content


# ── Fetcher Tests ──────────────────────────────────────────────────────


class TestFetcher:
    @pytest.mark.asyncio
    async def test_fetch_url_http_error(self):
        from app.ingestion.fetcher import fetch_url, FetchError

        with pytest.raises(FetchError, match="Fetch failed"):
            await fetch_url("https://nonexistent.example.com/404", timeout=5)

    @pytest.mark.asyncio
    async def test_fetch_url_timeout(self):
        from app.ingestion.fetcher import fetch_url, FetchTimeoutError

        # This should trigger a timeout quickly
        with pytest.raises(FetchTimeoutError, match="timed out"):
            await fetch_url("https://10.255.255.1/", timeout=0.1)

    @pytest.mark.asyncio
    async def test_fetch_content_type_detection(self):
        """Fetch from a known HTML page and verify content type detection."""
        from app.ingestion.fetcher import fetch_url

        result = await fetch_url("https://example.com/", timeout=15)
        assert result.status_code == 200
        assert "text/html" in result.content_type
        assert len(result.body) > 0
        assert result.url == "https://example.com/"