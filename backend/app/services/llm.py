"""LLM service for generating grounded answers from search results.
Uses OpenRouter to support multiple models (Qwen, Gemini, etc.) for comparison."""

import json
import logging
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

settings = get_settings()

# ── Model Registry ──────────────────────────────────────────────────────────
# Each entry maps a short slug to an OpenRouter model ID and display label.
# Add new models here; the frontend will pick them up automatically via the
# /search/summary endpoint's model parameter.

MODEL_REGISTRY: dict[str, dict[str, str]] = {
    "qwen-3-8b": {
        "id": "qwen/qwen3-8b",
        "label": "Qwen 3 8B",
    },
    "gemini-flash-lite": {
        "id": "google/gemini-2.5-flash-lite",
        "label": "Gemini Flash Lite 2.5",
    },
}


def openrouter_available() -> bool:
    return bool(settings.openrouter_api_key)


def list_models() -> list[dict[str, str]]:
    """Return available models with slug and label, for the frontend."""
    return [
        {"slug": slug, "label": info["label"]}
        for slug, info in MODEL_REGISTRY.items()
    ]


SYSTEM_PROMPT = """You are a precise research assistant. Your job is to answer the user's question based *only* on the provided search result snippets.

Rules:
1. Answer in clear, well-structured paragraphs.
2. Use numbered citations like [1], [2], etc. to cite the source of each fact.
3. Each citation number corresponds to the numbered result list provided below.
4. If the snippets don't contain enough information to answer, say so — do not make up facts.
5. Always ground every factual claim in at least one citation.
6. Write in a neutral, informative tone."""


def build_context(results: list[dict[str, Any]]) -> str:
    """Build a numbered context block from search results for the LLM."""
    parts = []
    for i, result in enumerate(results, start=1):
        title = result.get("title", "Untitled")
        excerpt = result.get("excerpt", "")
        source = result.get("source", "Unknown")
        citation = result.get("citation", "")
        parts.append(
            f"[{i}] Title: {title}\n"
            f"    Source: {source} ({citation})\n"
            f"    Content: {excerpt}\n"
        )
    return "\n---\n".join(parts)


def _build_messages(query: str, context: str) -> list[dict[str, str]]:
    user_prompt = f"""## User Question

{query}

## Search Results

{context}

## Instructions

Write a concise, well-structured answer to the user's question using only the information above.
Use numbered citations like [1], [2] to reference the search result each fact comes from.
Group related facts into paragraphs. Do not use bullet points unless necessary."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


async def _call_openrouter(
    model_id: str,
    messages: list[dict[str, str]],
) -> str | None:
    """Make a single OpenRouter chat completion call."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://vector-search.local",  # OpenRouter requires this
                },
                json={
                    "model": model_id,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 1024,
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            logger.info(
                "OpenRouter %s — %d input results, %d output tokens",
                model_id,
                len(messages),
                data.get("usage", {}).get("completion_tokens", "?"),
            )
            return content.strip()

    except httpx.HTTPStatusError as exc:
        logger.error("OpenRouter API error (%s): %s - %s", model_id, exc, exc.response.text[:500])
        return None
    except httpx.RequestError as exc:
        logger.error("OpenRouter request failed (%s): %s", model_id, exc)
        return None
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        logger.error("Failed to parse OpenRouter response (%s): %s", model_id, exc)
        return None


async def generate_summary(
    query: str,
    results: list[dict[str, Any]],
    model_slug: str | None = None,
) -> str | None:
    """Generate a grounded summary with citations from search results.

    Args:
        query: The user's search query.
        results: List of search result dicts.
        model_slug: One of the keys in MODEL_REGISTRY. If None, uses the first available model.

    Returns:
        The generated summary text, or None if it failed.
    """
    if not openrouter_available():
        logger.warning("OpenRouter API key not configured, skipping summary generation")
        return None

    # Resolve model slug → model ID
    if model_slug is None or model_slug not in MODEL_REGISTRY:
        model_slug = next(iter(MODEL_REGISTRY))
    model_id = MODEL_REGISTRY[model_slug]["id"]

    context = build_context(results)
    messages = _build_messages(query, context)
    return await _call_openrouter(model_id, messages)