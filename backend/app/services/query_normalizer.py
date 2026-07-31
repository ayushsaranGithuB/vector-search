"""
Query normalizer: corrects common typos in user search queries before
they are sent to Pinecone or PostgreSQL for retrieval.
"""

import re

from spellchecker import SpellChecker

# Lazy-initialised singleton — loading the dictionary is expensive (~1-2 s).
_spell: SpellChecker | None = None


def _get_spell() -> SpellChecker:
    global _spell
    if _spell is None:
        _spell = SpellChecker()
    return _spell


# Words we never want to "correct" because they are likely domain terms,
# acronyms, or proper nouns that pyspellchecker doesn't know.
_PRESERVE_WORDS = {
    # Common acronyms / tech terms
    "api", "css", "html", "http", "https", "json", "npm", "pdf", "png",
    "sql", "ssh", "svg", "url", "xml", "yaml", "yml", "js", "ts", "jsx",
    "tsx", "cli", "sdk", "ui", "ux", "cdn", "dom", "jwt", "oauth",
    # Project-specific terms that may appear in queries
    "pinecone", "prisma", "postgres", "postgresql", "fastapi", "nextjs",
    "vercel", "r2", "s3", "aws", "gcp", "azure",
}


def correct_query(query: str) -> str:
    """Return a typo-corrected version of *query*.

    Only words that are clearly misspelled are replaced; correctly-spelled
    words, domain terms, and acronyms are left untouched.
    """
    if not query or not query.strip():
        return query

    spell = _get_spell()

    # Split on word boundaries while preserving whitespace / punctuation.
    tokens = re.split(r"(\s+|[^\w\s]+)", query)
    corrected: list[str] = []

    for token in tokens:
        # Only attempt correction on pure alphabetic tokens of length >= 3.
        if re.fullmatch(r"[a-zA-Z]{3,}", token):
            lower = token.lower()
            # Skip domain terms and known words.
            if lower in _PRESERVE_WORDS:
                corrected.append(token)
                continue

            known = spell.known([lower])
            if known:
                corrected.append(token)
                continue

            # Otherwise, get the best correction, preserving case.
            candidate = spell.correction(lower)
            if candidate is not None and candidate != lower:
                if token[0].isupper():
                    candidate = candidate[0].upper() + candidate[1:]
                corrected.append(candidate)
            else:
                corrected.append(token)
        else:
            corrected.append(token)

    return "".join(corrected)