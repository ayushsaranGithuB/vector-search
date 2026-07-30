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


async def _db_keepalive():
    """Periodic keepalive to prevent Neon pooler from dropping idle connections."""
    while True:
        await asyncio.sleep(25)
        try:
            await prisma.execute_raw("SELECT 1")
        except Exception:
            logger.warning("DB keepalive failed, attempting reconnect...", exc_info=True)
            try:
                await prisma.disconnect()
                await prisma.connect()
                logger.info("DB reconnected successfully")
            except Exception as reconnect_error:
                logger.error("DB reconnect failed: %s", reconnect_error)
                # Don't break — keep retrying on next cycle


async def main() -> None:
    logger.info("=" * 60)
    logger.info("Ingestion Worker starting up")
    logger.info("=" * 60)
    await prisma.connect()
    logger.info("Connected to database")

    keepalive = asyncio.create_task(_db_keepalive())

    try:
        logger.info("Entering ingestion loop (waiting for messages)...")
        await consume_ingestion_queue()
    finally:
        keepalive.cancel()
        logger.info("Shutting down, disconnecting from database...")
        await prisma.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
