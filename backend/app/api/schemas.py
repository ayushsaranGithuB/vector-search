from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

SourceTypeLabel = Literal["pdf", "url"]
SourceStatusLabel = Literal["processed", "processing", "queued", "failed", "cancelled"]


class SearchResultOut(BaseModel):
    """A single search result returned to the frontend."""
    id: str
    title: str
    excerpt: str
    source: str
    source_type: str = ""  # "url" or "pdf"
    source_url: str | None = None  # link to original document (URL or R2 PDF)
    score: float
    citation: str
    corrected_query: str | None = None  # typo-corrected version of the user's query


class SearchSummaryOut(BaseModel):
    """LLM-generated summary with citation metadata."""
    summary: str
    generated_from: int  # number of unique sources used
    model_slug: str = ""  # which model generated this summary
    model_label: str = ""  # human-readable model name


class ModelInfo(BaseModel):
    """Info about an available LLM model for the frontend."""
    slug: str
    label: str


class ComparisonSummaryOut(BaseModel):
    """Two summaries side-by-side for comparison."""
    model_a: SearchSummaryOut
    model_b: SearchSummaryOut


class SourceCreateInput(BaseModel):
    """Input for creating a new source (URL or PDF)."""
    name: str
    type: SourceTypeLabel
    source: str
    notes: str | None = None


class SourceUploadCreateInput(BaseModel):
    """Input for creating a source via upload with project context."""
    project: str
    name: str
    type: SourceTypeLabel
    source: str | None = None
    file_name: str | None = None
    notes: str | None = None


class SourceOut(BaseModel):
    """Source record returned to the frontend."""
    id: str
    name: str
    type: SourceTypeLabel
    source: str
    addedAt: str
    size: str
    chunks: int
    status: SourceStatusLabel
    lastSynced: str


class UploadCreateOut(BaseModel):
    """Result of creating a source upload, including optional presigned URL."""
    source: SourceOut
    uploadUrl: str | None = None
    r2ObjectKey: str | None = None


class ProjectOut(BaseModel):
    """Project record returned to the frontend with its sources."""
    model_config = ConfigDict(populate_by_name=True)

    slug: str
    name: str
    description: str
    status: str
    sources: list[SourceOut]
