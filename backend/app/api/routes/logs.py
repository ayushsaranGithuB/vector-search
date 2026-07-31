from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query

from app.api.schemas_logs import LogEntry
from app.db import prisma

router = APIRouter()


def _serialize_log(log) -> dict[str, Any]:
    return {
        "id": log.id,
        "timestamp": log.created_at.isoformat(),
        "event": log.event.value if hasattr(log.event, "value") else str(log.event),
        "query": log.query,
        "source_ids": log.source_ids,
        "model_slug": log.model_slug,
        "input_tokens": log.input_tokens,
        "output_tokens": log.output_tokens,
        "cost_usd": log.cost_usd,
        "latency_ms": log.latency_ms,
        "error_message": log.error_message,
        "metadata": log.metadata,
    }


@router.get("/logs", response_model=list[LogEntry])
async def get_logs(
    limit: int = Query(default=100, ge=1, le=500),
    event: str | None = Query(default=None),
):
    where: dict[str, Any] = {}
    if event:
        where["event"] = event.upper()

    logs = await prisma.querylog.find_many(
        where=where,
        order={"created_at": "desc"},
        take=limit,
        include={"project": True},
    )
    return [_serialize_log(log) for log in logs]
