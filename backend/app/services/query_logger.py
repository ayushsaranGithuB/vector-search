"""Lightweight query analytics logger that writes to a local JSONL file.

Records search queries, LLM calls (with tokens/cost/latency), and errors so
that the observability dashboard can surface real usage metrics.
"""

from __future__ import annotations

import json
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

# Store logs alongside the app so they survive restarts and are easy to inspect.
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
QUERY_LOG_FILE = LOG_DIR / "query_analytics.jsonl"

# Add a dedicated sink for query analytics so we can read it back as structured JSONL.
logger.add(
    QUERY_LOG_FILE,
    serialize=True,
    rotation="1 day",
    retention="30 days",
    enqueue=True,
    filter=lambda record: record["extra"].get("analytics") is True,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write(event: str, payload: dict[str, Any]) -> None:
    try:
        logger.bind(analytics=True).info(
            event,
            **{"analytics_event": event, **payload},
        )
    except Exception:
        # Logging must never break the user-facing request path.
        pass


class QueryLogger:
    """Async query/LLM analytics logger."""

    @staticmethod
    async def log_search(
        *,
        project_id: str | None,
        query: str | None,
        source_ids: list[str] | None = None,
        latency_ms: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        _write(
            "SEARCH",
            {
                "timestamp": _now(),
                "project_id": project_id,
                "query": query,
                "source_ids": source_ids or [],
                "latency_ms": latency_ms,
                "metadata": metadata or {},
            },
        )

    @staticmethod
    async def log_llm(
        *,
        project_id: str | None,
        query: str | None,
        model_slug: str | None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        cost_usd: float | None = None,
        latency_ms: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        _write(
            "LLM_CALL",
            {
                "timestamp": _now(),
                "project_id": project_id,
                "query": query,
                "model_slug": model_slug,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost_usd,
                "latency_ms": latency_ms,
                "metadata": metadata or {},
            },
        )

    @staticmethod
    async def log_error(
        *,
        project_id: str | None,
        error_message: str,
        query: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        _write(
            "ERROR",
            {
                "timestamp": _now(),
                "project_id": project_id,
                "query": query,
                "error_message": error_message,
                "metadata": metadata or {},
            },
        )


@asynccontextmanager
async def timed_search(project_id: str | None, query: str | None):
    """Context manager that yields a list of source ids and logs search latency."""
    start = time.perf_counter()
    source_ids: list[str] = []
    try:
        yield source_ids
    finally:
        latency_ms = int((time.perf_counter() - start) * 1000)
        await QueryLogger.log_search(
            project_id=project_id,
            query=query,
            source_ids=source_ids or None,
            latency_ms=latency_ms,
        )


@asynccontextmanager
async def timed_llm_call(
    project_id: str | None,
    query: str | None,
    model_slug: str | None,
):
    """Context manager that yields a dict for token/cost info and logs the LLM call."""
    start = time.perf_counter()
    info: dict[str, Any] = {}
    try:
        yield info
    finally:
        latency_ms = int((time.perf_counter() - start) * 1000)
        await QueryLogger.log_llm(
            project_id=project_id,
            query=query,
            model_slug=model_slug,
            input_tokens=info.get("input_tokens"),
            output_tokens=info.get("output_tokens"),
            cost_usd=info.get("cost_usd"),
            latency_ms=latency_ms,
        )
