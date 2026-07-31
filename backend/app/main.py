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
            # On failure, attempt a full reconnect and continue retrying.
            logger.warning("DB keepalive failed, attempting reconnect...", exc_info=True)
            try:
                await prisma.disconnect()
                await prisma.connect()
                logger.info("DB reconnected successfully")
            except Exception as reconnect_error:
                logger.error("DB reconnect failed: %s", reconnect_error)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to Prisma on startup and start the keepalive background task.
    await prisma.connect()
    keepalive = asyncio.create_task(_db_keepalive())
    try:
        yield
    finally:
        # Clean up on shutdown: cancel keepalive and disconnect from DB.
        keepalive.cancel()
        await prisma.disconnect()


# Create the FastAPI application with CORS and all route modules.
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
