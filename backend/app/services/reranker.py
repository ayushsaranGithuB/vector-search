"""
Reranking pipeline for improved search result quality.

Strategy (in priority order):
1. OpenRouter Rerank API — routes Cohere's `rerank-v3.5` cross-encoder
   through the OpenRouter endpoint, so only one API key is needed.
   Returns relevance scores that are far more accurate than embedding
   cosine similarity alone.
2. Cohere Rerank API (direct) — fallback when OpenRouter isn't configured
   but a direct Cohere API key is.
3. Heuristic fallback — lightweight keyword-overlap scoring when no API
   key is configured.  Not as good as a cross-encoder but still useful
   for pushing exact keyword matches above purely semantic matches.
"""

from __future__ import annotations

import asyncio
import logging
import re
import sys
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def rerank(
    query: str,
    documents: list[dict[str, Any]],
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """Re-score *documents* against *query* and return the top *top_n*.

    Each document dict must have at least an ``"excerpt"`` key (the text to
    score against).  The returned list is sorted by descending relevance and
    each dict gains a ``"score"`` key (0.0–1.0).
    """
    if not documents:
        return []

    settings = get_settings()

    # 1. OpenRouter rerank (preferred — routes Cohere through the OR endpoint)
    if settings.openrouter_api_key:
        try:
            return await _openrouter_rerank(query, documents, top_n, settings.openrouter_api_key)
        except Exception:
            logger.exception("OpenRouter rerank failed, falling back")

    # 2. Direct Cohere rerank (fallback)
    if settings.cohere_api_key:
        try:
            return await _cohere_rerank(query, documents, top_n, settings.cohere_api_key)
        except Exception:
            logger.exception("Cohere rerank failed, falling back to heuristic")

    return _heuristic_rerank(query, documents, top_n)


# ---------------------------------------------------------------------------
# OpenRouter Rerank (preferred — routes Cohere through the OR endpoint)
# ---------------------------------------------------------------------------

_OPENROUTER_RERANK_URL = "https://openrouter.ai/api/v1/rerank"


async def _openrouter_rerank(
    query: str,
    documents: list[dict[str, Any]],
    top_n: int,
    api_key: str,
) -> list[dict[str, Any]]:
    """Call the OpenRouter Rerank API, which routes through Cohere rerank-v3.5."""
    texts = [doc.get("excerpt", "") for doc in documents]

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            _OPENROUTER_RERANK_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://vector-search.local",
            },
            json={
                "model": "cohere/rerank-v3.5",
                "query": query,
                "documents": texts,
                "top_n": min(top_n, len(documents)),
            },
        )
        response.raise_for_status()
        data = response.json()

    # Build a lookup: document index → relevance score
    score_map: dict[int, float] = {}
    for item in data.get("results", []):
        idx = item.get("index")
        if idx is not None:
            score_map[idx] = item.get("relevance_score", 0.0)

    # Reorder documents by score, attach the new score
    reranked: list[dict[str, Any]] = []
    for idx, score in sorted(score_map.items(), key=lambda x: x[1], reverse=True):
        doc = dict(documents[idx])
        doc["score"] = round(score, 4)
        reranked.append(doc)

    logger.info("OpenRouter reranked %d → %d results", len(documents), len(reranked))
    return reranked


# ---------------------------------------------------------------------------
# Cohere Rerank (direct fallback)

_COHERE_RERANK_URL = "https://api.cohere.com/v2/rerank"


async def _cohere_rerank(
    query: str,
    documents: list[dict[str, Any]],
    top_n: int,
    api_key: str,
) -> list[dict[str, Any]]:
    """Call the Cohere Rerank v2 API."""
    texts = [doc.get("excerpt", "") for doc in documents]

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            _COHERE_RERANK_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "rerank-v3.5",
                "query": query,
                "documents": texts,
                "top_n": min(top_n, len(documents)),
            },
        )
        response.raise_for_status()
        data = response.json()

    # Build a lookup: document index → relevance score
    score_map: dict[int, float] = {}
    for item in data.get("results", []):
        idx = item.get("index")
        if idx is not None:
            score_map[idx] = item.get("relevance_score", 0.0)

    # Reorder documents by Cohere score, attach the new score
    reranked: list[dict[str, Any]] = []
    for idx, score in sorted(score_map.items(), key=lambda x: x[1], reverse=True):
        doc = dict(documents[idx])
        doc["score"] = round(score, 4)
        reranked.append(doc)

    logger.info("Cohere reranked %d → %d results", len(documents), len(reranked))
    return reranked


# ---------------------------------------------------------------------------
# Heuristic fallback
# ---------------------------------------------------------------------------

# Words that carry little semantic weight for keyword-overlap scoring.
_HEURISTIC_STOP_WORDS: set[str] = {
    "a", "an", "the", "and", "or", "but", "nor", "so", "for", "yet",
    "is", "am", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing",
    "will", "would", "shall", "should", "can", "could", "may", "might", "must",
    "i", "me", "my", "we", "us", "our", "you", "your", "he", "she", "it", "they", "them",
    "this", "that", "these", "those",
    "at", "by", "in", "of", "on", "to", "with", "from", "about", "into", "through",
    "during", "before", "after", "above", "below", "between",
    "up", "down", "out", "off", "over", "under",
    "if", "then", "else", "when", "where", "why", "how",
    "all", "each", "every", "both", "few", "more", "most", "other", "some", "such",
    "no", "not", "only", "very", "just", "too", "also",
}


def _tokenize(text: str) -> set[str]:
    """Lowercase, split on non-alpha, drop stop words and short tokens."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return {t for t in tokens if t not in _HEURISTIC_STOP_WORDS and len(t) > 1}


def _heuristic_rerank(
    query: str,
    documents: list[dict[str, Any]],
    top_n: int,
) -> list[dict[str, Any]]:
    """Re-score using keyword overlap between query and document excerpt.

    Score = (matched query tokens / total query tokens).
    This is a simple but effective boost for exact keyword matches.
    """
    query_tokens = _tokenize(query)
    if not query_tokens:
        # Nothing to score on — return as-is with uniform scores
        for doc in documents:
            doc["score"] = 1.0
        return documents[:top_n]

    scored: list[tuple[float, dict[str, Any]]] = []
    for doc in documents:
        doc_tokens = _tokenize(doc.get("excerpt", ""))
        overlap = query_tokens & doc_tokens
        score = len(overlap) / len(query_tokens) if query_tokens else 0.0
        doc_copy = dict(doc)
        doc_copy["score"] = round(score, 4)
        scored.append((score, doc_copy))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored[:top_n]]