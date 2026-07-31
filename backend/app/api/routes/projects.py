from fastapi import APIRouter, HTTPException, Query, status

from app.api.schemas import (
    ComparisonSummaryOut,
    ModelInfo,
    ProjectOut,
    SearchResultOut,
    SearchSummaryOut,
    SourceCreateInput,
    SourceOut,
)
from app.core.config import get_settings
from app.services.llm import list_models as llm_list_models
from app.services.projects import (
    compare_search_summaries,
    create_source_for_project,
    get_project_by_slug,
    list_projects,
    list_project_search_results,
    list_sources_for_project,
    summarize_search_results,
)
from app.services.query_normalizer import correct_query

router = APIRouter(prefix="/projects")


@router.get("", response_model=list[ProjectOut])
async def read_projects() -> list[ProjectOut]:
    """List all projects with their sources."""
    return await list_projects()


@router.get("/{slug}", response_model=ProjectOut)
async def read_project(slug: str) -> ProjectOut:
    """Get a single project by its slug."""
    project = await get_project_by_slug(slug)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("/{slug}/sources", response_model=list[SourceOut])
async def read_project_sources(slug: str) -> list[SourceOut]:
    """List all sources for a project."""
    return await list_sources_for_project(slug)


@router.get("/{slug}/search", response_model=list[SearchResultOut])
async def search_project(slug: str, q: str) -> list[SearchResultOut]:
    """Search a project's indexed content. Query is typo-corrected before searching."""
    from app.services.query_logger import QueryLogger

    corrected_q = correct_query(q)
    try:
        results = await list_project_search_results(slug, corrected_q)
    except Exception as exc:
        project = await get_project_by_slug(slug)
        await QueryLogger.log_error(
            project_id=project.id if project else None,
            query=corrected_q,
            error_message=str(exc),
            metadata={"route": "search", "slug": slug},
        )
        raise
    # Attach the corrected query so the frontend can highlight using
    # the corrected terms rather than the original misspelled ones.
    for r in results:
        r["corrected_query"] = corrected_q if corrected_q != q else None
    return results


@router.get("/{slug}/search/models", response_model=list[ModelInfo])
async def search_models() -> list[ModelInfo]:
    """List available LLM models for summary generation."""
    return llm_list_models()


@router.get("/{slug}/search/summary", response_model=SearchSummaryOut)
async def search_project_summary(
    slug: str,
    q: str,
    model: str = Query(default="", description="Model slug (e.g. qwen-3-8b, gemini-flash-lite)"),
) -> SearchSummaryOut:
    """Generate an LLM-grounded summary of search results for a query."""
    from app.services.query_logger import QueryLogger

    corrected_q = correct_query(q)
    try:
        return await summarize_search_results(slug, corrected_q, model_slug=model or None)
    except ValueError as exc:
        project = await get_project_by_slug(slug)
        await QueryLogger.log_error(
            project_id=project.id if project else None,
            query=corrected_q,
            error_message=str(exc),
            metadata={"route": "search_summary", "slug": slug, "model": model},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{slug}/search/summary/compare", response_model=ComparisonSummaryOut)
async def compare_project_summaries(
    slug: str,
    q: str,
    model_a: str = Query(default="qwen-3.7-flash", description="First model slug"),
    model_b: str = Query(default="qwen-3.7-flash", description="Second model slug"),
) -> ComparisonSummaryOut:
    """Generate summaries from two models side-by-side for comparison."""
    from app.services.query_logger import QueryLogger

    settings = get_settings()
    if not settings.enable_comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparison mode is not enabled. Set ENABLE_COMPARISON=true to use this feature.",
        )
    corrected_q = correct_query(q)
    try:
        return await compare_search_summaries(slug, corrected_q, model_a, model_b)
    except ValueError as exc:
        project = await get_project_by_slug(slug)
        await QueryLogger.log_error(
            project_id=project.id if project else None,
            query=corrected_q,
            error_message=str(exc),
            metadata={"route": "compare_summaries", "slug": slug, "model_a": model_a, "model_b": model_b},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{slug}/sources", response_model=SourceOut, status_code=status.HTTP_201_CREATED)
async def add_project_source(slug: str, payload: SourceCreateInput) -> SourceOut:
    """Create a new source for a project and enqueue it for ingestion."""
    try:
        return await create_source_for_project(slug, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
