import json
from typing import Any

from fastapi import APIRouter, Query

from app.api.schemas_logs import LogEntry
from app.services.query_logger import QUERY_LOG_FILE

router = APIRouter()


def _read_logs(limit: int, event_filter: str | None) -> list[dict[str, Any]]:
    """Parse the JSONL log file and return recent entries, optionally filtered by event type."""
    if not QUERY_LOG_FILE.exists():
        return []

    logs: list[dict[str, Any]] = []
    with QUERY_LOG_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            # loguru's serialize=True wraps the payload under "record".
            payload = record.get("record", {}).get("extra", {})
            analytics_event = payload.get("analytics_event")
            if analytics_event is None:
                continue
            if event_filter and analytics_event.upper() != event_filter.upper():
                continue

            logs.append(
                {
                    "id": f"{record.get('record', {}).get('time', {}).get('timestamp', '')}-{len(logs)}",
                    "timestamp": payload.get("timestamp") or record.get("record", {}).get("time", {}).get("repr", ""),
                    "event": analytics_event,
                    "query": payload.get("query"),
                    "source_ids": payload.get("source_ids", []),
                    "model_slug": payload.get("model_slug"),
                    "input_tokens": payload.get("input_tokens"),
                    "output_tokens": payload.get("output_tokens"),
                    "cost_usd": payload.get("cost_usd"),
                    "latency_ms": payload.get("latency_ms"),
                    "error_message": payload.get("error_message"),
                    "metadata": payload.get("metadata", {}),
                }
            )

    # Return most recent entries first, capped at the requested limit.
    logs.reverse()
    return logs[:limit]


@router.get("/logs", response_model=list[LogEntry])
async def get_logs(
    limit: int = Query(default=100, ge=1, le=500),
    event: str | None = Query(default=None),
):
    """Return analytics log entries (search, LLM calls, errors) for the observability dashboard."""
    return _read_logs(limit=limit, event_filter=event)
