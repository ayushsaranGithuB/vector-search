from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from app.ingestion.models import Document, FetchResult


class ParserError(Exception):
    """Raised when a parser cannot process the fetched content."""

    def __init__(self, content_type: str, message: str = "") -> None:
        self.content_type = content_type
        detail = f"Parser failed for content type '{content_type}'"
        if message:
            detail += f": {message}"
        super().__init__(detail)


class BaseParser(ABC):
    """Abstract base class for all content-type-specific parsers.

    Subclasses must declare ``content_types`` (a list of MIME types they
    can handle) and implement ``parse()``.
    """

    content_types: ClassVar[list[str]] = []

    @abstractmethod
    async def parse(self, fetch_result: FetchResult) -> Document:
        """Parse a fetched result into a unified ``Document``.

        Parameters
        ----------
        fetch_result:
            The raw fetched data including body bytes and content type.

        Returns
        -------
        A ``Document`` with the extracted title, content, and metadata.

        Raises
        ------
        ParserError
            If the content cannot be parsed.
        """
        ...


# ---------------------------------------------------------------------------
# Parser registry: content-type → parser instance lookup
# ---------------------------------------------------------------------------

_parser_registry: dict[str, BaseParser] = {}


def register_parser(parser: BaseParser) -> None:
    """Register a parser instance for all content types it declares."""
    for ct in parser.content_types:
        _parser_registry[ct] = parser


def get_parser_for_content_type(content_type: str) -> BaseParser | None:
    """Look up a parser by MIME type.

    Returns ``None`` if no parser is registered for the given type.
    """
    return _parser_registry.get(content_type)