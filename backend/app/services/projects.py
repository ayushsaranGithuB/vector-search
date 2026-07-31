from app.api.schemas import ComparisonSummaryOut, ProjectOut, SearchSummaryOut, SourceOut, SourceStatusLabel, SourceTypeLabel
from app.db import prisma
from app.services.pinecone import pinecone_available, query_vectors
from app.services.query_logger import QueryLogger, timed_llm_call, timed_search
from app.services.queue import enqueue_ingestion_for_source
from app.services.reranker import rerank


async def list_projects() -> list[ProjectOut]:
    records = await prisma.project.find_many(include={"sources": True}, order={"created_at": "asc"})
    return [map_project(project) for project in records]


async def get_project_by_slug(slug: str) -> ProjectOut | None:
    record = await prisma.project.find_unique(where={"slug": slug}, include={"sources": True})
    if record is None:
        return None
    return map_project(record)


async def list_sources_for_project(slug: str) -> list[SourceOut]:
    project = await prisma.project.find_unique(where={"slug": slug}, include={"sources": True})
    if project is None:
        return []
    return [map_source(source) for source in sorted(project.sources, key=lambda item: item.created_at, reverse=True)]


async def create_source_for_project(slug: str, payload) -> SourceOut:
    project = await prisma.project.find_unique(where={"slug": slug})
    if project is None:
        raise ValueError("Project not found")

    normalized_type = payload.type.upper()
    source = await prisma.source.create(
        data={
            "project_id": project.id,
            "name": payload.name.strip(),
            "source_type": normalized_type,
            "source_url": payload.source if normalized_type == "URL" else None,
            "file_name": payload.source if normalized_type == "PDF" else None,
            "notes": payload.notes,
            "status": "QUEUED",
            "size_bytes": None,
            "chunk_count": 0,
            "chunk_size": None,
            "chunk_overlap": None,
            "last_synced_at": None,
        }
    )

    if normalized_type == "URL":
        await enqueue_ingestion_for_source(source.id)

    return map_source(source)


async def list_project_search_results(slug: str, query: str) -> list[dict]:
    project = await prisma.project.find_unique(where={"slug": slug})
    if project is None:
        return []

    async with timed_search(project_id=project.id, query=query) as source_ids:
        results = await _fetch_and_rerank(project, query, slug)
        source_ids.extend({r["source"] for r in results if r.get("source")})
        return results


def map_project(project) -> ProjectOut:
    sources = sorted(project.sources, key=lambda item: item.created_at, reverse=True)
    return ProjectOut(
        slug=project.slug,
        name=project.name,
        description=project.description,
        status=project_status_label(project.status),
        sources=[map_source(source) for source in sources],
    )


def map_source(source) -> SourceOut:
    return SourceOut(
        id=source.id,
        name=source.name,
        type=source_type_label(source.source_type),
        source=source.source_url or source.file_name or "Unknown source",
        addedAt=source.created_at.strftime("%Y-%m-%d"),
        size=format_bytes(source.size_bytes),
        chunks=source.chunk_count,
        status=source_status_label(source.status),
        lastSynced=source.last_synced_at.strftime("%Y-%m-%d %H:%M") if source.last_synced_at else "Queued for ingestion",
    )


def project_status_label(status: object) -> str:
    value = enum_value(status)
    if value == "LIVE_DEMO":
        return "Live"
    if value == "COMING_SOON":
        return "Coming Soon"
    return value.replace("_", " ").title()


def source_type_label(source_type: object) -> SourceTypeLabel:
    value = enum_value(source_type)
    return "pdf" if value == "PDF" else "url"


def source_status_label(status: object) -> SourceStatusLabel:
    value = enum_value(status)
    if value == "PROCESSED":
        return "processed"
    if value == "PROCESSING":
        return "processing"
    if value == "FAILED":
        return "failed"
    if value == "CANCELLED":
        return "cancelled"
    return "queued"


def format_bytes(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "Pending"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def enum_value(value: object) -> str:
    return getattr(value, "value", str(value))


async def _fetch_and_rerank(project, query: str, slug: str) -> list[dict]:
    """Fetch chunks via Pinecone (or keyword fallback), format them, then
    re-rank with the configured reranker for improved result quality."""
    from app.core.config import get_settings
    from app.services.uploads import build_r2_object_key

    settings = get_settings()

    # Fetch more candidates than we need — the reranker will pick the best
    fetch_k = settings.rerank_top_k

    chunks: list = []
    if query and pinecone_available():
        try:
            matches = await query_vectors(query, top_k=fetch_k, namespace=slug)
            chunk_ids = [chunk_id for chunk_id, score in matches]
            if chunk_ids:
                found_chunks = await prisma.chunk.find_many(
                    where={"id": {"in": chunk_ids}},
                )
                chunk_map = {chunk.id: chunk for chunk in found_chunks}
                ordered = [chunk_map[chunk_id] for chunk_id in chunk_ids if chunk_id in chunk_map]
                chunks = ordered
        except Exception:
            chunks = []

    if not chunks:
        chunks = await prisma.chunk.find_many(
            where={
                "source": {"project_id": project.id},
                "content": {"contains": query, "mode": "insensitive"},
            },
            order={"updated_at": "desc"},
            take=10,
        )

    # Build result dicts from chunks
    results: list[dict] = []
    for chunk in chunks:
        source = await prisma.source.find_unique(where={"id": chunk.source_id})
        source_name = source.name if source is not None else "Unknown source"
        excerpt = chunk.content
        if query:
            lower_query = query.lower()
            lower_content = chunk.content.lower()
            position = lower_content.find(lower_query)
            if position != -1:
                start = max(0, position - 100)
                end = min(len(chunk.content), position + 100)
                excerpt = f"...{chunk.content[start:end].strip()}..."

        source_url: str | None = None
        if source is not None:
            if source.source_type == "URL":
                source_url = source.source_url
            elif source.source_type == "PDF" and source.file_name and settings.r2_public_url:
                object_key = build_r2_object_key(slug, source.id, source.file_name)
                source_url = f"{settings.r2_public_url}/{object_key}"

        results.append({
            "id": chunk.id,
            "title": source_name,
            "excerpt": excerpt,
            "source": source_name,
            "source_type": source.source_type.lower() if source else "",
            "source_url": source_url,
            "score": 1.0,
            "citation": f"chunk {chunk.chunk_index}",
        })

    # Re-rank for better relevance ordering
    if results and query:
        try:
            results = await rerank(query, results, top_n=10)
        except Exception:
            pass  # keep original ordering on rerank failure

    return results


async def _fetch_search_results(project, query: str) -> list[dict]:
    """Shared helper: fetch and format search results for a project + query."""
    return await _fetch_and_rerank(project, query, project.slug)


async def summarize_search_results(
    slug: str,
    query: str,
    model_slug: str | None = None,
) -> SearchSummaryOut:
    """Search for results and generate an LLM-grounded summary with citations."""
    from app.services.llm import MODEL_REGISTRY, generate_summary

    project = await prisma.project.find_unique(where={"slug": slug})
    if project is None:
        raise ValueError("Project not found")

    if not query.strip():
        raise ValueError("Query is required")

    results = await _fetch_search_results(project, query)

    if not results:
        raise ValueError("No results found to summarize")

    # Resolve which model to use
    effective_slug = model_slug if model_slug in MODEL_REGISTRY else next(iter(MODEL_REGISTRY))
    model_info = MODEL_REGISTRY[effective_slug]

    # Count unique sources for the generated_from display
    unique_sources = len({r["source"] for r in results})

    async with timed_llm_call(
        project_id=project.id, query=query, model_slug=effective_slug
    ) as llm_info:
        summary = await generate_summary(query, results, model_slug=effective_slug, llm_info=llm_info)
        if summary is None:
            raise ValueError("Failed to generate summary — check that OPENROUTER_API_KEY is configured")

    return SearchSummaryOut(
        summary=summary,
        generated_from=unique_sources,
        model_slug=effective_slug,
        model_label=model_info["label"],
    )


async def compare_search_summaries(
    slug: str,
    query: str,
    model_a_slug: str,
    model_b_slug: str,
) -> ComparisonSummaryOut:
    """Generate summaries from two models for side-by-side comparison."""
    from app.services.llm import MODEL_REGISTRY, generate_summary

    project = await prisma.project.find_unique(where={"slug": slug})
    if project is None:
        raise ValueError("Project not found")

    if not query.strip():
        raise ValueError("Query is required")

    if model_a_slug not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model_a: {model_a_slug}")
    if model_b_slug not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model_b: {model_b_slug}")

    results = await _fetch_search_results(project, query)
    if not results:
        raise ValueError("No results found to summarize")

    model_a_info = MODEL_REGISTRY[model_a_slug]
    model_b_info = MODEL_REGISTRY[model_b_slug]

    # Run both models in parallel
    import asyncio

    async with timed_llm_call(
        project_id=project.id, query=query, model_slug=model_a_slug
    ) as info_a, timed_llm_call(
        project_id=project.id, query=query, model_slug=model_b_slug
    ) as info_b:
        summary_a_task = generate_summary(query, results, model_slug=model_a_slug, llm_info=info_a)
        summary_b_task = generate_summary(query, results, model_slug=model_b_slug, llm_info=info_b)
        summaries = await asyncio.gather(summary_a_task, summary_b_task)

    summary_a, summary_b = summaries

    if summary_a is None:
        raise ValueError(f"Failed to generate summary with model '{model_a_info['label']}'")
    if summary_b is None:
        raise ValueError(f"Failed to generate summary with model '{model_b_info['label']}'")

    return ComparisonSummaryOut(
        model_a=SearchSummaryOut(
            summary=summary_a,
            generated_from=len(results),
            model_slug=model_a_slug,
            model_label=model_a_info["label"],
        ),
        model_b=SearchSummaryOut(
            summary=summary_b,
            generated_from=len(results),
            model_slug=model_b_slug,
            model_label=model_b_info["label"],
        ),
    )
