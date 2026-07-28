from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """Unified document model returned by any parser, regardless of source type."""

    title: str
    content: str
    source_url: str
    content_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FetchResult:
    """Raw result from the fetcher before parsing."""

    url: str
    status_code: int
    content_type: str
    body: bytes
    headers: dict[str, str]
    encoding: str = "utf-8"


@dataclass
class ChunkResult:
    """A single chunk produced by the chunker."""

    content: str
    chunk_index: int
    token_count: int


@dataclass
class PipelineResult:
    """Final result of running the full ingestion pipeline."""

    document: Document
    chunks: list[ChunkResult]