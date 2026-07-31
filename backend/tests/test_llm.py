"""Tests for the LLM service — model registry, context building, cost estimation, and message formatting."""

import pytest

from app.services.llm import (
    MODEL_REGISTRY,
    build_context,
    list_models,
    _estimate_cost,
    _build_messages,
)


class TestModelRegistry:
    """Verify the model registry returns correct slugs and labels."""

    def test_list_models_returns_slugs_and_labels(self):
        models = list_models()
        assert len(models) >= 1
        for m in models:
            assert "slug" in m
            assert "label" in m
            assert m["slug"] in MODEL_REGISTRY

    def test_registry_has_qwen_3_7_flash(self):
        assert "qwen-3.7-flash" in MODEL_REGISTRY
        assert MODEL_REGISTRY["qwen-3.7-flash"]["id"] == "qwen/qwen3.7-flash"


class TestBuildContext:
    """Test the context builder that groups chunks by source."""

    def test_merges_chunks_from_same_source(self):
        results = [
            {"title": "Doc A", "source": "Source1", "citation": "cite1", "source_url": "https://a.com", "excerpt": "Content 1"},
            {"title": "Doc A", "source": "Source1", "citation": "cite1", "source_url": "https://a.com", "excerpt": "Content 2"},
            {"title": "Doc B", "source": "Source2", "citation": "cite2", "source_url": "https://b.com", "excerpt": "Content 3"},
        ]
        context = build_context(results)
        # Source1's excerpts should be merged into one entry.
        assert "[1]" in context
        assert "[2]" in context
        assert "Content 1" in context
        assert "Content 2" in context
        assert "Content 3" in context

    def test_handles_empty_results(self):
        assert build_context([]) == ""

    def test_handles_single_result(self):
        results = [
            {"title": "Doc", "source": "Source", "citation": "cite", "source_url": "https://x.com", "excerpt": "Single chunk"},
        ]
        context = build_context(results)
        assert "[1]" in context
        assert "Single chunk" in context

    def test_uses_defaults_for_missing_fields(self):
        results = [
            {"excerpt": "Only excerpt"},
        ]
        context = build_context(results)
        assert "[1]" in context
        assert "Untitled" in context
        assert "Unknown" in context


class TestBuildMessages:
    """Verify message formatting for the LLM chat completion."""

    def test_includes_system_and_user_role(self):
        messages = _build_messages("test query", "some context")
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_includes_query_in_user_message(self):
        messages = _build_messages("my test query", "context")
        assert "my test query" in messages[1]["content"]

    def test_includes_context_in_user_message(self):
        messages = _build_messages("query", "my context block")
        assert "my context block" in messages[1]["content"]


class TestEstimateCost:
    """Test cost estimation for known and unknown models."""

    def test_returns_cost_for_known_model(self):
        cost = _estimate_cost("qwen/qwen3.7-flash", 1000, 500)
        expected = (1000 * 0.03 + 500 * 0.13) / 1_000_000
        assert cost == pytest.approx(expected, rel=1e-6)

    def test_returns_none_for_unknown_model(self):
        assert _estimate_cost("unknown/model", 1000, 500) is None

    def test_zero_tokens(self):
        cost = _estimate_cost("qwen/qwen3.7-flash", 0, 0)
        assert cost == 0.0