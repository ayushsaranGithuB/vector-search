"""Lightweight query analytics logger backed by Prisma.

Records search queries, LLM calls (with tokens/cost/latency), and errors so
that the observability dashboard can surface real usage metrics.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Any

from app.db import prisma


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
        try:
            await prisma.querylog.create(
                data={
                    "project_id": project_id,
                    "event": "SEARCH",
                    "query": query,
                    "source_ids": source_ids or [],
                    "latency_ms": latency_ms,
                    "metadata": metadata or {},
                }
            )
        except Exception:
            # Logging must never break the user-facing request path.
            pass

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
        try:
            await prisma.querylog.create(
                data={
                    "project_id": project_id,
                    "event": "LLM_CALL",
                    "query": query,
                    "model_slug": model_slug,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": cost_usd,
                    "latency_ms": latency_ms,
                    "metadata": metadata or {},
                }
            )
        except Exception:
            pass

    @staticmethod
    async def log_error(
        *,
        project_id: str | None,
        error_message: str,
        query: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        try:
            await prisma.querylog.create(
                data={
                    "project_id": project_id,
                    "event": "ERROR",
                    "query": query,
                    "error_message": error_message,
                    "metadata": metadata or {},
                }
            )
        except Exception:
            pass


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
