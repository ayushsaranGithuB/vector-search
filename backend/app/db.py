from prisma import Prisma

from app.core.config import get_settings

# Load settings and initialise the Prisma ORM client with the Neon connection string.
settings = get_settings()
prisma = Prisma(datasource={"url": settings.database_url})


def get_database_url() -> str:
    """Return the current database URL from settings."""
    return settings.database_url
