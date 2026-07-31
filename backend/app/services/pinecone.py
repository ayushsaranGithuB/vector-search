import logging
import sys

from pinecone import Pinecone as PineconeClient

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

# Lazy-init globals so we don't connect at import time
_pinecone_client: PineconeClient | None = None
_pinecone_index = None


def _get_client() -> PineconeClient | None:
    global _pinecone_client
    if _pinecone_client is None and settings.pinecone_api_key:
        _pinecone_client = PineconeClient(api_key=settings.pinecone_api_key)
    return _pinecone_client


def pinecone_available() -> bool:
    return bool(
        settings.pinecone_api_key
        and settings.pinecone_index
        and _get_client() is not None
    )


def _get_index():
    global _pinecone_index
    if _pinecone_index is None:
        client = _get_client()
        if client is None:
            raise RuntimeError("Pinecone client is not configured")
        _pinecone_index = client.Index(settings.pinecone_index)
    return _pinecone_index


def embed_text(text: str, input_type: str = "passage") -> list[float]:
    """Embed text using Pinecone Inference."""
    client = _get_client()
    if client is None:
        raise RuntimeError("Pinecone client is not configured")

    result = client.inference.embed(
        model="multilingual-e5-large",
        inputs=[text],
        parameters={"input_type": input_type, "truncate": "END"},
    )
    return result[0]["values"]


async def embed_texts(texts: list[str], input_type: str = "passage") -> list[list[float]]:
    """Embed multiple texts in one API call using Pinecone Inference (runs sync call in thread).
    Batches automatically to stay within the model's input limit (96 for multilingual-e5-large).
    """
    import asyncio

    client = _get_client()
    if client is None:
        raise RuntimeError("Pinecone client is not configured")

    # Pinecone's multilingual-e5-large has a 96 input limit per request
    batch_size = 96
    all_embeddings: list[list[float]] = [None] * len(texts)  # type: ignore

    def _sync_embed_batch(batch_texts: list[str], offset: int):
        result = client.inference.embed(
            model="multilingual-e5-large",
            inputs=batch_texts,
            parameters={"input_type": input_type, "truncate": "END"},
        )
        for i, r in enumerate(result):
            all_embeddings[offset + i] = r["values"]

    tasks = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        tasks.append(asyncio.to_thread(_sync_embed_batch, batch, i))

    await asyncio.gather(*tasks)
    return all_embeddings  # type: ignore


def upsert_vectors(vectors: list[dict], namespace: str | None = None) -> None:
    if not pinecone_available():
        logger.warning("Pinecone unavailable, skipping vector upsert")
        return

    index = _get_index()
    logger.info("Upserting %d vectors to namespace='%s'", len(vectors), namespace or "(default)")
    index.upsert(vectors=vectors, namespace=namespace)
    logger.info("Upsert successful for namespace='%s'", namespace or "(default)")


async def query_vectors(query: str, top_k: int = 10, namespace: str | None = None) -> list[tuple[str, float]]:
    if not pinecone_available():
        return []

    import asyncio

    def _sync_query():
        embedding = embed_text(query, input_type="query")
        index = _get_index()
        response = index.query(
            vector=embedding,
            top_k=top_k,
            include_values=False,
            include_metadata=True,
            namespace=namespace,
        )
        return [(match.id, match.score or 0.0) for match in getattr(response, "matches", []) or []]

    return await asyncio.to_thread(_sync_query)


def delete_vectors_by_ids(vector_ids: list[str], namespace: str | None = None) -> None:
    """Delete vectors from Pinecone by their IDs."""
    if not pinecone_available():
        logger.warning("Pinecone unavailable, skipping vector deletion")
        return

    index = _get_index()
    logger.info("Deleting %d vectors from namespace='%s'", len(vector_ids), namespace or "(default)")
    index.delete(ids=vector_ids, namespace=namespace)
    logger.info("Vector deletion complete")


async def delete_vectors_for_source(source_id: str) -> None:
    """Delete all vectors for a given source from Pinecone.
    Since Pinecone doesn't support deletion by metadata, we need the chunk IDs.
    This is called after reading the chunks from the DB.
    """
    import asyncio

    from app.db import prisma

    chunks = await prisma.chunk.find_many(where={"source_id": source_id})
    if not chunks:
        logger.info("No chunks found for source %s, nothing to delete from Pinecone", source_id)
        return

    vector_ids = [
        chunk.pinecone_vector_id or chunk.id
        for chunk in chunks
        if chunk.pinecone_vector_id or chunk.id
    ]
    # Look up the project namespace
    source = await prisma.source.find_unique(where={"id": source_id}, include={"project": True})
    namespace = source.project.slug if source else None

    logger.info("Deleting %d vectors for source %s from namespace=%s", len(vector_ids), source_id, namespace)
    await asyncio.to_thread(delete_vectors_by_ids, vector_ids, namespace=namespace)
