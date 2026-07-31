from pydantic import BaseModel
from typing import Optional, Any

class LogEntry(BaseModel):
    id: str
    timestamp: str
    event: str
    query: Optional[str] = None
    source_ids: list[str] = []
    model_slug: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    latency_ms: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
