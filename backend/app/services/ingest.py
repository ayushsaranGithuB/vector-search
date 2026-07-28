import json
import asyncio
from datetime import datetime
from io import BytesIO
import logging
import sys

import aio_pika
import boto3
import httpx
from botocore.config import Config
from pypdf import PdfReader

from app.core.config import get_settings
from app.db import prisma, get_database_url
from app.services.pinecone import embed_texts, pinecone_available, upsert_vectors

settings = get_settings()
logger = logging.getLogger(__name__)

# Ensure the logger actually prints to stdout
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_base_endpoint,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="us-east-1",
        config=Config(signature_version="s3v4"),
    )


def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(stream=BytesIO(file_bytes))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return ""


def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        start += chunk_size - chunk_overlap
    return [chunk for chunk in chunks if chunk]


async def download_source_from_r2(object_key: str) -> bytes:
    client = get_r2_client()

    def get_object_bytes() -> bytes:
        response = client.get_object(Bucket=settings.r2_bucket_name, Key=object_key)
        return response["Body"].read()

    return await asyncio.to_thread(get_object_bytes)


async def ingest_source(source_id: str) -> None:
    logger.info("Starting ingestion for source_id=%s", source_id)
    source = await prisma.source.find_unique(where={"id": source_id}, include={"project": True})
    if source is None:
        logger.warning("Source %s not found, skipping", source_id)
        return

    logger.info(
        "Ingesting source '%s' (type=%s, project=%s)",
        source.name, source.source_type, source.project.slug,
    )

    object_key = None
    if source.source_type == "PDF" and source.file_name:
        object_key = f"projects/{source.project.slug}/sources/{source.id}/{source.file_name}"
        logger.info("R2 object key: %s", object_key)
    elif source.source_type == "URL" and source.source_url:
        logger.info("URL source: %s", source.source_url)
        object_key = None

    await prisma.source.update(
        where={"id": source.id},
        data={"status": "PROCESSING"},
    )
    await prisma.ingestionrun.create(
        data={"source_id": source.id, "status": "RUNNING", "started_at": datetime.utcnow()},
    )
    logger.info("Source status updated to PROCESSING")

    try:
        if source.source_type == "PDF" and object_key:
            logger.info("Downloading PDF from R2...")
            file_bytes = await download_source_from_r2(object_key)
            logger.info("Downloaded %d bytes from R2", len(file_bytes))
            text = extract_text_from_pdf_bytes(file_bytes)
            logger.info("Extracted %d characters of text from PDF", len(text))
        elif source.source_type == "URL" and source.source_url:
            logger.info("Fetching URL content...")
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(source.source_url)
                response.raise_for_status()
                text = response.text
            logger.info("Fetched %d characters from URL", len(text))
        else:
            text = ""
            logger.warning("No content source found for source_id=%s", source_id)

        chunks = chunk_text(text)
        logger.info("Text split into %d chunks", len(chunks))

        # Create all chunks in DB first
        created_chunks = []
        for index, content in enumerate(chunks):
            chunk = await prisma.chunk.create(
                data={
                    "source_id": source.id,
                    "chunk_index": index,
                    "content": content,
                    "token_count": len(content.split()),
                }
            )
            created_chunks.append(chunk)
        logger.info("Created %d chunks in database", len(created_chunks))

        # Batch-embed and upsert to Pinecone
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
        else:
            logger.info("Pinecone not available or no chunks, skipping vector upsert")

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
    logger.info("Connecting to CloudAMQP queue...")
    connection = await aio_pika.connect_robust(settings.cloudamqp_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange("ingestion", aio_pika.ExchangeType.DIRECT, durable=True)
        queue = await channel.declare_queue("ingestion.queue", durable=True)
        await queue.bind(exchange, routing_key="source.ingest")
        logger.info("Worker is listening for ingestion messages on 'ingestion.queue'...")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    payload = json.loads(message.body.decode())
                    source_id = payload.get("source_id")
                    logger.info("Received ingestion message for source_id=%s", source_id)
                    if source_id:
                        await ingest_source(source_id)
