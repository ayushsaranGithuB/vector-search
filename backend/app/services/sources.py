import logging
import sys

from app.db import prisma
from app.services.pinecone import delete_vectors_for_source
from app.services.storage import build_r2_object_key, get_r2_client
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


async def delete_source(source_id: str) -> None:
    """Delete a source and all its data: Pinecone vectors, DB records, and R2 file."""
    source = await prisma.source.find_unique(
        where={"id": source_id},
        include={"project": True},
    )
    if source is None:
        raise ValueError("Source not found")

    logger.info("Deleting source %s ('%s') from project %s", source_id, source.name, source.project.slug)

    # 1. Delete vectors from Pinecone (chunks must exist for delete_vectors_for_source to work)
    await delete_vectors_for_source(source_id)

    # 2. Delete the R2 object if it's a PDF
    if source.source_type == "PDF" and source.file_name:
        try:
            object_key = build_r2_object_key(source.project.slug, source.id, source.file_name)
            client = get_r2_client()
            client.delete_object(Bucket=settings.r2_bucket_name, Key=object_key)
            logger.info("Deleted R2 object: %s", object_key)
        except Exception as exc:
            logger.warning("Could not delete R2 object for source %s: %s", source_id, exc)

    # 3. Delete DB records (cascades to chunks and ingestion_runs)
    deleted = await prisma.source.delete(where={"id": source_id})
    logger.info("Deleted source %s from database", source_id)
    return deleted


async def cancel_source(source_id: str) -> None:
    """Cancel a source that is QUEUED or PROCESSING."""
    source = await prisma.source.find_unique(
        where={"id": source_id},
        include={"project": True},
    )
    if source is None:
        raise ValueError("Source not found")

    if source.status not in ("QUEUED", "PROCESSING"):
        raise ValueError(f"Cannot cancel source with status '{source.status}' — only QUEUED or PROCESSING sources can be cancelled")

    logger.info("Cancelling source %s ('%s') with status '%s'", source_id, source.name, source.status)

    # Mark source as cancelled
    await prisma.source.update(
        where={"id": source_id},
        data={"status": "CANCELLED"},
    )

    # Mark any running ingestion run as cancelled
    await prisma.ingestionrun.update_many(
        where={"source_id": source_id, "status": "RUNNING"},
        data={"status": "CANCELLED", "finished_at": None},
    )

    # If it was PROCESSING and already had chunks, clean up Pinecone
    if source.status == "PROCESSING":
        await delete_vectors_for_source(source_id)
        await prisma.chunk.delete_many(where={"source_id": source_id})

    logger.info("Source %s cancelled successfully", source_id)
