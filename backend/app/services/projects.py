from app.api.schemas import ProjectOut, SourceOut, SourceStatusLabel, SourceTypeLabel
from app.db import prisma
from app.services.queue import enqueue_ingestion_for_source


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

    chunks = await prisma.chunk.find_many(
        where={
            "source": {"project_id": project.id},
            "content": {"contains": query, "mode": "insensitive"},
        },
        order={"updated_at": "desc"},
        take=10,
    )

    results = []
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

        results.append(
            {
                "id": chunk.id,
                "title": source_name,
                "excerpt": excerpt,
                "source": source_name,
                "score": 1.0,
                "citation": f"chunk {chunk.chunk_index}",
            }
        )

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
