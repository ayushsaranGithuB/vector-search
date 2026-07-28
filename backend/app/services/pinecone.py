import hashlib
import logging

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

try:
    import pinecone
except Exception:  # pragma: no cover
    pinecone = None


def pinecone_available() -> bool:
    return bool(
        pinecone
        and settings.pinecone_api_key
        and settings.pinecone_index
        and (settings.pinecone_environment or settings.pinecone_region)
    )


def embed_text(text: str) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return [byte / 255.0 for byte in digest[:64]]


def get_pinecone_index():
    if not pinecone_available():
        raise RuntimeError("Pinecone is not configured or available")

    pinecone.init(
        api_key=settings.pinecone_api_key,
        environment=settings.pinecone_environment or settings.pinecone_region,
    )
    return pinecone.Index(settings.pinecone_index)


def upsert_vectors(vectors: list[dict], namespace: str | None = None) -> None:
    if not pinecone_available():
        logger.warning("Pinecone unavailable, skipping vector upsert")
        return

    index = get_pinecone_index()
    index.upsert(vectors=vectors, namespace=namespace)


def query_vectors(query: str, top_k: int = 10, namespace: str | None = None) -> list[tuple[str, float]]:
    if not pinecone_available():
        return []

    index = get_pinecone_index()
    response = index.query(
        vector=embed_text(query),
        top_k=top_k,
        include_values=False,
        include_metadata=True,
        namespace=namespace,
    )

    return [(match.id, match.score or 0.0) for match in getattr(response, "matches", []) or []]
