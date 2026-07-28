import json

import aio_pika

from app.core.config import get_settings

settings = get_settings()


async def enqueue_ingestion_for_source(source_id: str) -> None:
    connection = await aio_pika.connect_robust(settings.cloudamqp_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange("ingestion", aio_pika.ExchangeType.DIRECT, durable=True)
        message = aio_pika.Message(body=json.dumps({"source_id": source_id}).encode())
        await exchange.publish(message, routing_key="source.ingest")
