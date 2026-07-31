from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.projects import router as projects_router
from app.api.routes.uploads import router as uploads_router
from app.api.routes.sources import router as sources_router
from app.api.routes.fetch_title import router as fetch_title_router
from app.api.routes.logs import router as logs_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["system"])
api_router.include_router(projects_router, tags=["projects"])
api_router.include_router(uploads_router, tags=["uploads"])
api_router.include_router(sources_router, tags=["sources"])
api_router.include_router(fetch_title_router, tags=["fetch-title"])
api_router.include_router(logs_router, tags=["logs"])
