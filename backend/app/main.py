from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.db import prisma
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    await prisma.connect()
    keepalive = asyncio.create_task(_db_keepalive())
    try:
        yield
    finally:
        keepalive.cancel()
        await prisma.disconnect()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="FastAPI backend for the vector search SaaS demo",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
