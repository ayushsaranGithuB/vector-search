import json
import asyncio
from datetime import datetime
import logging
import sys

import aio_pika
import boto3
from botocore.config import Config

from app.core.config import get_settings
from app.db import prisma
from app.services.pinecone import embed_texts, pinecone_available, upsert_vectors, delete_vectors_by_ids
from app.ingestion.pipeline import run_pipeline
from app.ingestion.models import FetchResult
from app.ingestion.normalizer import normalize_document
from app.ingestion.chunker import chunk_document
from app.services.storage import build_r2_object_key

settings = get_settings()
logger = logging.getLogger(__name__)

# Ensure stdout is line-buffered even when piped (e.g. under goreman).
sys.stdout.reconfigure(line_buffering=True)

# Ensure the logger actually prints to stdout.
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def get_r2_client():
    """Return a boto3 S3 client configured for Cloudflare R2."""
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_base_endpoint,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="us-east-1",
        config=Config(signature_version="s3v4"),
    )


async def download_source_from_r2(object_key: str) -> bytes:
    """Download a PDF file from Cloudflare R2 as raw bytes."""
    client = get_r2_client()

    def get_object_bytes() -> bytes:
        response = client.get_object(Bucket=settings.r2_bucket_name, Key=object_key)
        return response["Body"].read()

    return await asyncio.to_thread(get_object_bytes)


async def ingest_source(source_id: str) -> None:
    """Ingest a single source: fetch, parse, chunk, embed, and upsert to Pinecone."""
    logger.info("Starting ingestion for source_id=%s", source_id)

    # --- Idempotency & pre-checks ---
    source = await prisma.source.find_unique(where={"id": source_id}, include={"project": True})
    if source is None:
        logger.warning("Source %s not found, skipping", source_id)
        return

    if source.status == "PROCESSED":
        logger.info("Source %s already PROCESSED, skipping (idempotent guard)", source_id)
        return

    logger.info(
        "Ingesting source '%s' (type=%s, project=%s)",
        source.name, source.source_type, source.project.slug,
    )

    object_key = None
    if source.source_type == "PDF" and source.file_name:
        object_key = build_r2_object_key(source.project.slug, source.id, source.file_name)
        logger.info("R2 object key: %s", object_key)
    elif source.source_type == "URL" and source.source_url:
        logger.info("URL source: %s", source.source_url)
        object_key = None

    # Clean slate: delete old Pinecone vectors first, then DB records.
    existing_chunks = await prisma.chunk.find_many(
        where={"source_id": source.id},
    )
    old_vector_ids = [
        c.pinecone_vector_id for c in existing_chunks if c.pinecone_vector_id
    ]
    if old_vector_ids:
        logger.info("Deleting %d old Pinecone vectors before re-ingestion", len(old_vector_ids))
        await asyncio.to_thread(
            delete_vectors_by_ids, old_vector_ids, namespace=source.project.slug
        )
    await prisma.chunk.delete_many(where={"source_id": source.id})
    await prisma.ingestionrun.delete_many(where={"source_id": source.id})

    await prisma.source.update(
        where={"id": source.id},
        data={"status": "PROCESSING"},
    )
    # Create a new ingestion run record.
    await prisma.ingestionrun.create(
        data={"source_id": source.id, "status": "RUNNING", "started_at": datetime.utcnow()},
    )
    logger.info("Source status updated to PROCESSING")

    # Periodic keepalive to prevent Neon pooler from dropping the connection.
    async def _keepalive():
        while True:
            await asyncio.sleep(15)
            try:
                await prisma.execute_raw("SELECT 1")
            except Exception:
                logger.warning("Ingestion keepalive failed, attempting reconnect...", exc_info=True)
                try:
                    await prisma.disconnect()
                    await prisma.connect()
                    logger.info("Ingestion keepalive reconnected successfully")
                except Exception as reconnect_error:
                    logger.error("Ingestion keepalive reconnect failed: %s", reconnect_error)
                    # Don't break — keep retrying on next cycle

    keepalive_task = asyncio.create_task(_keepalive())

    try:
        if source.source_type == "URL" and source.source_url:
            # ── Use the modular pipeline for URL sources ────────────────
            outcome = await run_pipeline(
                source.source_url,
                timeout=30,
                chunk_size=1000,
                chunk_overlap=200,
            )

            if not outcome.success:
                error_details = "; ".join(f"[{e.step}] {e.message}" for e in outcome.errors)
                raise RuntimeError(f"Pipeline failed: {error_details}")

            document = outcome.document
            chunks = outcome.chunks
            text = document.content if document else ""

        elif source.source_type == "PDF" and object_key:
            # ── PDF: download from R2, then parse + normalize + chunk ──
            logger.info("Downloading PDF from R2...")
            file_bytes = await download_source_from_r2(object_key)
            logger.info("Downloaded %d bytes from R2", len(file_bytes))

            # Reuse the PDF parser by constructing a minimal FetchResult.
            from app.ingestion.parsers.pdf_parser import PDFParser

            fetch_result = FetchResult(
                url=source.source_url or f"r2://{object_key}",
                status_code=200,
                content_type="application/pdf",
                body=file_bytes,
                headers={},
                encoding="utf-8",
            )
            parser = PDFParser()
            document = await parser.parse(fetch_result)
            document = normalize_document(document)
            text = document.content
            chunks = chunk_document(document, chunk_size=1000, chunk_overlap=200)
        else:
            text = ""
            chunks = []
            logger.warning("No content source found for source_id=%s", source_id)

        logger.info("Text split into %d chunks", len(chunks))

        # Create all chunks in DB first, then embed and upsert to Pinecone.
        created_chunks = []
        for chunk in chunks:
            db_chunk = await prisma.chunk.create(
                data={
                    "source_id": source.id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "token_count": chunk.token_count,
                }
            )
            created_chunks.append(db_chunk)
        logger.info("Created %d chunks in database", len(created_chunks))

        # Batch-embed and upsert to Pinecone.
        if pinecone_available() and created_chunks:
            logger.info("Pinecone is available, generating embeddings for %d chunks...", len(created_chunks))
            contents = [c.content for c in created_chunks]
            embeddings = await embed_texts(contents)
            logger.info("Generated %d embeddings (dim=%d)", len(embeddings), len(embeddings[0]) if embeddings else 0)

            pinecone_vectors = [
                {
                    "id": chunk.id,
                    "values": emb,
                    "metadata": {
                        "source_id": source.id,
                        "source_name": source.name,
                        "chunk_index": chunk.chunk_index,
                        "content": chunk.content[:500],
                    },
                }
                for chunk, emb in zip(created_chunks, embeddings)
            ]
            logger.info("Upserting %d vectors to Pinecone namespace=%s ...", len(pinecone_vectors), source.project.slug)
            await asyncio.to_thread(upsert_vectors, pinecone_vectors, namespace=source.project.slug)
            logger.info("Pinecone upsert complete!")

            # Populate pinecone_vector_id on each chunk so we can cross-reference.
            for chunk in created_chunks:
                await prisma.chunk.update(
                    where={"id": chunk.id},
                    data={"pinecone_vector_id": chunk.id},
                )
            logger.info("Populated pinecone_vector_id on %d chunks", len(created_chunks))
        else:
            logger.info("Pinecone not available or no chunks, skipping vector upsert")

        keepalive_task.cancel()
        # Mark the source as processed with updated metadata.
        await prisma.source.update(
            where={"id": source.id},
            data={
                "status": "PROCESSED",
                "chunk_count": len(chunks),
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "last_synced_at": datetime.utcnow(),
                "size_bytes": len(text.encode("utf-8")),
            },
        )
        await prisma.ingestionrun.update_many(
            where={"source_id": source.id, "status": "RUNNING"},
            data={"status": "COMPLETED", "finished_at": datetime.utcnow(), "chunk_count": len(chunks)},
        )
        logger.info("Ingestion complete for source '%s' — %d chunks processed", source.name, len(chunks))

    except Exception as exc:
        keepalive_task.cancel()
        # On failure, mark the source as FAILED so it can be retried manually.
        logger.error("Ingestion failed for source '%s': %s", source.name, exc, exc_info=True)
        await prisma.source.update(
            where={"id": source.id},
            data={"status": "FAILED"},
        )
        await prisma.ingestionrun.update_many(
            where={"source_id": source.id, "status": "RUNNING"},
            data={"status": "FAILED", "finished_at": datetime.utcnow(), "error_message": str(exc)},
        )
        raise


async def consume_ingestion_queue() -> None:
    """Listen for ingestion messages on the CloudAMQP queue and process each source."""
    logger.info("Connecting to CloudAMQP queue...")
    connection = await aio_pika.connect_robust(settings.cloudamqp_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange("ingestion", aio_pika.ExchangeType.DIRECT, durable=True)
        queue = await channel.declare_queue("ingestion.queue", durable=True)
        await queue.bind(exchange, routing_key="source.ingest")
        logger.info("Worker is listening for ingestion messages on 'ingestion.queue'...")

        # Process messages one at a time; acknowledge on completion.
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    payload = json.loads(message.body.decode())
                    source_id = payload.get("source_id")
                    logger.info("Received ingestion message for source_id=%s", source_id)
                    if source_id:
                        try:
                            await ingest_source(source_id)
                        except Exception:
                            # Acknowledge on failure too — no infinite retries.
                            logger.exception(
                                "Ingestion failed for source_id=%s — message acknowledged (won't retry)",
                                source_id,
                            )
