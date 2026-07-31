"""Tests for query normalizer — typo correction in user search queries."""

from app.services.query_normalizer import correct_query


class TestCorrectQuery:
    """Test typo correction, domain term preservation, and edge cases."""

    def test_corrects_obvious_typo(self):
        result = correct_query("lisense")
        assert result == "license"

    def test_corrects_multi_word_query(self):
        result = correct_query("learners lisense")
        assert result == "learners license"

    def test_preserves_correct_words(self):
        result = correct_query("driving license requirements")
        assert result == "driving license requirements"

    def test_preserves_domain_terms(self):
        result = correct_query("pinecone api setup")
        assert result == "pinecone api setup"

    def test_preserves_acronyms(self):
        result = correct_query("configure jwt token")
        assert result == "configure jwt token"

    def test_preserves_capitalization(self):
        result = correct_query("FastAPI setup")
        assert "FastAPI" in result

    def test_returns_empty_string_unchanged(self):
        assert correct_query("") == ""

    def test_returns_whitespace_only_unchanged(self):
        assert correct_query("   ") == "   "

    def test_handles_punctuation(self):
        result = correct_query("learner's lisense")
        assert "license" in result
        assert "'" in result

    def test_skips_short_words(self):
        result = correct_query("a ok test")
        assert result == "a ok test"