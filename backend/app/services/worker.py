import asyncio
import logging
import sys

from app.db import prisma
from app.services.ingest import consume_ingestion_queue

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


async def main() -> None:
    logger.info("=" * 60)
    logger.info("Ingestion Worker starting up")
    logger.info("=" * 60)
    await prisma.connect()
    logger.info("Connected to database")
    try:
        logger.info("Entering ingestion loop (waiting for messages)...")
        await consume_ingestion_queue()
    finally:
        logger.info("Shutting down, disconnecting from database...")
        await prisma.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
