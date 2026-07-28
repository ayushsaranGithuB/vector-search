from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

SourceTypeLabel = Literal["pdf", "url"]
SourceStatusLabel = Literal["processed", "processing", "queued", "failed", "cancelled"]


class SearchResultOut(BaseModel):
    id: str
    title: str
    excerpt: str
    source: str
    score: float
    citation: str


class SourceCreateInput(BaseModel):
    name: str
    type: SourceTypeLabel
    source: str
    notes: str | None = None


class SourceUploadCreateInput(BaseModel):
    project: str
    name: str
    type: SourceTypeLabel
    source: str | None = None
    file_name: str | None = None
    notes: str | None = None


class SourceOut(BaseModel):
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
    source: SourceOut
    uploadUrl: str | None = None
    r2ObjectKey: str | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    slug: str
    name: str
    description: str
    status: str
    sources: list[SourceOut]
