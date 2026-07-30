# LLM service for generating grounded answers from search results.
# Uses OpenRouter to support multiple models (Qwen, Gemini, etc.) for comparison.

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
    "qwen-3.7-flash": {
        "id": "qwen/qwen3.7-flash",
        "label": "Qwen 3.7 Flash",
    },
    # ── Archived models (re-enable for comparison mode) ──
    # "qwen-3-8b": {
    #     "id": "qwen/qwen3-8b",
    #     "label": "Qwen 3 8B",
    # },
    # "gemini-flash-lite": {
    #     "id": "google/gemini-2.5-flash-lite",
    #     "label": "Gemini Flash Lite 2.5",
    # },
}


def openrouter_available() -> bool:
    return bool(settings.openrouter_api_key)


def list_models() -> list[dict[str, str]]:
    """Return available models with slug and label, for the frontend."""
    return [
        {"slug": slug, "label": info["label"]}
        for slug, info in MODEL_REGISTRY.items()
    ]


SYSTEM_PROMPT = """
You are a precise research assistant. Your job is to answer the user's question using ONLY the provided search results.

Rules:

1. Never use knowledge outside the provided search results.
2. Write in a neutral, factual tone.
3. Organize related facts into short paragraphs.
4. Each paragraph must contain no more than 25 words.
5. Do NOT repeat the same citation number within a paragraph.
6. Place ALL citations for a paragraph at the very end of that paragraph only — never inline within the sentence.
7. Format the end of each paragraph like this: sentence text. [1][3][5]
8. Use numbered citations like [1], [2], [3].
9. Do not include the source name or URL inline. The frontend will resolve citation numbers into hyperlinks.
10. Cite every factual statement, but consolidate citations whenever possible.
11. Never invent citations or infer unsupported information.
12. If the provided search results do not fully answer the question, explicitly state that.
13. Prefer combining multiple sources into a single citation list, for example: [1][3][5].
"""


def build_context(results: list[dict[str, Any]]) -> str:
    """Build a numbered context block from search results for the LLM.

    Groups chunks by source so each unique source gets one citation number,
    preventing the LLM from treating every chunk as a distinct source.
    """
    # Group results by source name
    from collections import OrderedDict

    grouped: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for result in results:
        source = result.get("source", "Unknown")
        if source not in grouped:
            grouped[source] = {
                "title": result.get("title", "Untitled"),
                "source": source,
                "citation": result.get("citation", ""),
                "source_url": result.get("source_url") or "",
                "excerpts": [],
            }
        grouped[source]["excerpts"].append(result.get("excerpt", ""))

    parts = []
    for i, (source_name, entry) in enumerate(grouped.items(), start=1):
        merged_content = "\n\n".join(entry["excerpts"])
        parts.append(
            f"[{i}] Title: {entry['title']}\n"
            f"    Source: {entry['source']}\n"
            f"    Citation: {entry['citation']}\n"
            f"    URL: {entry['source_url']}\n"
            f"    Content: {merged_content}\n"
        )
    return "\n---\n".join(parts)


def _build_messages(query: str, context: str) -> list[dict[str, str]]:
    user_prompt = f"""## User Question

{query}

## Search Results

{context}

## Instructions

Answer using only the search results.

- Keep paragraphs under 25 words.
- Never repeat the same citation number within a paragraph.
- Place ALL citations at the very end of the paragraph — never inside a sentence.
- Example of correct format: "Drivers must be at least 18 years old. [1][3]"
- Example of WRONG format (do not do this): "Drivers must be at least 18 years old [1] and pass a test [3]."
- Group related information together.
- Return Markdown only.
- Start the answer with a brief summary of the findings, then provide a detailed answer with citations.

Example: "According to the Motor Vehicles Act 1989, heavy vehicles are defined as.......

"""
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