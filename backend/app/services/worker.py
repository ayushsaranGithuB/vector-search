import asyncio

from app.services.ingest import consume_ingestion_queue


async def main() -> None:
    await consume_ingestion_queue()


if __name__ == "__main__":
    asyncio.run(main())
