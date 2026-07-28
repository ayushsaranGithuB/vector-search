from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.projects import router as projects_router
from app.api.routes.uploads import router as uploads_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["system"])
api_router.include_router(projects_router, tags=["projects"])
api_router.include_router(uploads_router, tags=["uploads"])
