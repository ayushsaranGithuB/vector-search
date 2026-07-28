from prisma import Prisma

from app.core.config import get_settings

settings = get_settings()
prisma = Prisma(datasource={"url": settings.database_url})


def get_database_url() -> str:
    return settings.database_url
