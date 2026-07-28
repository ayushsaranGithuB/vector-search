import hashlib
import json
import asyncio
from datetime import datetime
from io import BytesIO
import logging

import aio_pika
import boto3
import httpx
from botocore.config import Config
from pypdf import PdfReader

from app.core.config import get_settings
from app.db import prisma
from app.services.pinecone import embed_text, pinecone_available, upsert_vectors

settings = get_settings()
logger = logging.getLogger(__name__)


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
    source = await prisma.source.find_unique(where={"id": source_id}, include={"project": True})
    if source is None:
        return

    object_key = None
    if source.source_type == "PDF" and source.file_name:
        object_key = f"projects/{source.project.slug}/sources/{source.id}/{source.file_name}"
    elif source.source_type == "URL" and source.source_url:
        object_key = None

    await prisma.source.update(
        where={"id": source.id},
        data={"status": "PROCESSING"},
    )
    await prisma.ingestion_run.create(
        data={"source_id": source.id, "status": "RUNNING", "started_at": datetime.utcnow()},
    )

    try:
        if source.source_type == "PDF" and object_key:
            file_bytes = await download_source_from_r2(object_key)
            text = extract_text_from_pdf_bytes(file_bytes)
        elif source.source_type == "URL" and source.source_url:
            async with httpx.AsyncClient() as client:
                response = await client.get(source.source_url)
                response.raise_for_status()
                text = response.text
        else:
            text = ""

        chunks = chunk_text(text)
        vector_payload = []
        for index, content in enumerate(chunks):
            chunk = await prisma.chunk.create(
                data={
                    "source_id": source.id,
                    "chunk_index": index,
                    "content": content,
                    "token_count": len(content.split()),
                }
            )
            if pinecone_available():
                vector_payload.append(
                    {
                        "id": chunk.id,
                        "text": content,
                        "metadata": {
                            "source_id": source.id,
                            "source_name": source.name,
                            "chunk_index": index,
                        },
                    }
                )

        if vector_payload:
            try:
                await asyncio.to_thread(upsert_vectors, vector_payload, namespace=source.project.slug)
            except Exception as exc:
                logger.exception("Unable to upsert vectors to Pinecone")

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
        await prisma.ingestion_run.update_many(
            where={"source_id": source.id, "status": "RUNNING"},
            data={"status": "COMPLETED", "finished_at": datetime.utcnow(), "chunk_count": len(chunks)},
        )
    except Exception as exc:
        await prisma.source.update(
            where={"id": source.id},
            data={"status": "FAILED"},
        )
        await prisma.ingestion_run.update_many(
            where={"source_id": source.id, "status": "RUNNING"},
            data={"status": "FAILED", "finished_at": datetime.utcnow(), "error_message": str(exc)},
        )
        raise


async def consume_ingestion_queue() -> None:
    connection = await aio_pika.connect_robust(settings.cloudamqp_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange("ingestion", aio_pika.ExchangeType.DIRECT, durable=True)
        queue = await channel.declare_queue("ingestion.queue", durable=True)
        await queue.bind(exchange, routing_key="source.ingest")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    payload = json.loads(message.body.decode())
                    source_id = payload.get("source_id")
                    if source_id:
                        await ingest_source(source_id)
