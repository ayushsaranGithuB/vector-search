import pytest
from datetime import datetime

from app.api.schemas import SourceUploadCreateInput
from app.db import prisma
from app.services.uploads import (
    create_upload_for_project,
    finalize_uploaded_source,
    upload_source_file_to_r2,
)


class FakeProject:
    id = "project-1"
    slug = "proj-1"


class FakeSource:
    id = "source-1"
    name = "Test source"
    source_type = "URL"
    source_url = "https://example.com"
    file_name = None
    notes = "note"
    status = "QUEUED"
    size_bytes = None
    chunk_count = 0
    chunk_size = None
    chunk_overlap = None
    last_synced_at = None
    created_at = datetime.utcnow()
    updated_at = datetime.utcnow()


class FakePdfSource(FakeSource):
    source_type = "PDF"
    source_url = None
    file_name = "test.pdf"


@pytest.mark.asyncio
async def test_create_upload_for_project_url(monkeypatch):
    enqueued = {"called": False}

    async def fake_find_unique(where):
        return FakeProject()

    async def fake_source_create(data):
        return FakeSource()

    async def fake_enqueue(source_id: str):
        enqueued["called"] = True

    class FakePrisma:
        project = type("P", (), {"find_unique": staticmethod(fake_find_unique)})
        source = type("S", (), {"create": staticmethod(fake_source_create)})

    monkeypatch.setattr("app.services.uploads.prisma", FakePrisma())
    monkeypatch.setattr("app.services.uploads.enqueue_ingestion_for_source", fake_enqueue)

    payload = SourceUploadCreateInput(
        project="proj-1",
        name="Test source",
        type="url",
        source="https://example.com",
        notes="note",
    )

    result = await create_upload_for_project(payload)

    assert result.source.name == "Test source"
    assert result.uploadUrl is None
    assert enqueued["called"] is True


@pytest.mark.asyncio
async def test_upload_source_file_to_r2(monkeypatch):
    fake_source = FakePdfSource()
    fake_source.project = FakeProject()
    uploaded = {}

    async def fake_find_unique(where, include=None):
        return fake_source

    class FakeR2Client:
        def put_object(self, Bucket, Key, Body, ContentType):
            uploaded["bucket"] = Bucket
            uploaded["key"] = Key
            uploaded["body"] = Body
            uploaded["content_type"] = ContentType

    class FakePrisma:
        source = type("S", (), {"find_unique": staticmethod(fake_find_unique)})

    monkeypatch.setattr("app.services.uploads.prisma", FakePrisma())
    monkeypatch.setattr("app.services.uploads.get_r2_client", lambda: FakeR2Client())

    await upload_source_file_to_r2("source-1", b"mock-bytes", "application/pdf", "test.pdf")

    assert uploaded["bucket"] == "vector-search"
    assert uploaded["key"].endswith("test.pdf")
    assert uploaded["body"] == b"mock-bytes"
    assert uploaded["content_type"] == "application/pdf"


@pytest.mark.asyncio
async def test_finalize_uploaded_source_for_pdf(monkeypatch):
    fake_source = FakePdfSource()
    fake_project = FakeProject()
    fake_source.project = fake_project

    async def fake_find_unique(where, include=None):
        return fake_source

    async def fake_update(where, data):
        assert where == {"id": fake_source.id}
        assert data["status"] == "QUEUED"
        return fake_source

    class FakeR2Client:
        def head_object(self, Bucket, Key):
            assert Bucket == "vector-search"
            assert Key.endswith("test.pdf")
            return {"ContentLength": 1024}

    enqueue_called = {"value": False}

    async def fake_enqueue(source_id: str):
        assert source_id == fake_source.id
        enqueue_called["value"] = True

    class FakePrisma:
        source = type(
            "S",
            (),
            {
                "find_unique": staticmethod(fake_find_unique),
                "update": staticmethod(fake_update),
            },
        )

    monkeypatch.setattr("app.services.uploads.prisma", FakePrisma())
    monkeypatch.setattr("app.services.uploads.get_r2_client", lambda: FakeR2Client())
    monkeypatch.setattr("app.services.uploads.enqueue_ingestion_for_source", fake_enqueue)

    result = await finalize_uploaded_source("source-1")
    assert result.id == "source-1"
    assert result.status == "queued"
    assert enqueue_called["value"] is True
