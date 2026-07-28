from fastapi import APIRouter, HTTPException, status

from app.api.schemas import ProjectOut, SearchResultOut, SourceCreateInput, SourceOut
from app.services.projects import (
    create_source_for_project,
    get_project_by_slug,
    list_projects,
    list_project_search_results,
    list_sources_for_project,
)

router = APIRouter(prefix="/projects")


@router.get("", response_model=list[ProjectOut])
async def read_projects() -> list[ProjectOut]:
    return await list_projects()


@router.get("/{slug}", response_model=ProjectOut)
async def read_project(slug: str) -> ProjectOut:
    project = await get_project_by_slug(slug)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("/{slug}/sources", response_model=list[SourceOut])
async def read_project_sources(slug: str) -> list[SourceOut]:
    return await list_sources_for_project(slug)


@router.get("/{slug}/search", response_model=list[SearchResultOut])
async def search_project(slug: str, q: str) -> list[SearchResultOut]:
    return await list_project_search_results(slug, q)


@router.post("/{slug}/sources", response_model=SourceOut, status_code=status.HTTP_201_CREATED)
async def add_project_source(slug: str, payload: SourceCreateInput) -> SourceOut:
    try:
        return await create_source_for_project(slug, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
