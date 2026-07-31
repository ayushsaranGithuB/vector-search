"""Tests for the reranking pipeline — heuristic fallback and tokenization."""

from app.services.reranker import _heuristic_rerank, _tokenize


class TestTokenize:
    """Test text tokenization: lowercasing, stop word removal, short token handling."""

    def test_lowercases_and_splits(self):
        tokens = _tokenize("Hello World API Test")
        assert "hello" in tokens
        assert "world" in tokens
        assert "api" in tokens
        assert "test" in tokens

    def test_drops_stop_words(self):
        tokens = _tokenize("the and of a an in")
        for t in ("the", "and", "of", "a", "an", "in"):
            assert t not in tokens

    def test_drops_short_tokens(self):
        tokens = _tokenize("a bc def ghij")
        assert "a" not in tokens  # length 1
        assert "bc" in tokens  # length 2
        assert "def" in tokens  # length 3
        assert "ghij" in tokens  # length 4

    def test_handles_numbers(self):
        tokens = _tokenize("test 123 hello")
        assert "test" in tokens
        assert "123" in tokens
        assert "hello" in tokens

    def test_empty_string(self):
        assert _tokenize("") == set()

    def test_only_stop_words(self):
        assert _tokenize("the and of") == set()


class TestHeuristicRerank:
    """Test keyword-overlap reranking: scoring, limits, and edge cases."""

    def test_reranks_by_keyword_overlap(self):
        docs = [
            {"excerpt": "The quick brown fox jumps over the lazy dog"},
            {"excerpt": "Python is a programming language"},
            {"excerpt": "Foxes are quick animals that hunt at night"},
        ]
        result = _heuristic_rerank("fox quick", docs, top_n=3)

        assert len(result) == 3
        # Doc 0 should score highest (2/2 match: "fox" + "quick").
        assert result[0]["score"] >= result[1]["score"]

    def test_top_n_limits_results(self):
        docs = [
            {"excerpt": "one two three four"},
            {"excerpt": "five six seven eight"},
            {"excerpt": "nine ten eleven twelve"},
        ]
        result = _heuristic_rerank("one", docs, top_n=2)
        assert len(result) == 2

    def test_returns_empty_for_empty_docs(self):
        assert _heuristic_rerank("test", [], top_n=5) == []

    def test_assigns_uniform_scores_when_no_query_tokens(self):
        docs = [
            {"excerpt": "Some content here"},
            {"excerpt": "More content here"},
        ]
        result = _heuristic_rerank("a an", docs, top_n=2)
        assert len(result) == 2
        assert result[0]["score"] == 1.0
        assert result[1]["score"] == 1.0

    def test_attaches_score_to_each_doc(self):
        docs = [
            {"excerpt": "Matching term here"},
            {"excerpt": "No match at all"},
        ]
        result = _heuristic_rerank("matching", docs, top_n=2)
        assert "score" in result[0]
        assert "score" in result[1]
        assert result[0]["score"] > result[1]["score"]