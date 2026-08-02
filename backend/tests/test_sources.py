# Tests for source management: delete, cancel, and resync.
import pytest

from app.services.sources import resync_source


class FakeExchange:
    """Mock aio_pika exchange that counts published messages."""
    def __init__(self, published):
        self.published = published

    async def publish(self, message, routing_key):
        self.published["count"] += 1


class FakeChannel:
    """Mock aio_pika channel that returns a fake exchange."""
    def __init__(self, published):
        self.published = published

    async def declare_exchange(self, name, type, durable):
        return FakeExchange(self.published)


class FakeConnection:
    """Mock aio_pika connection that returns a fake channel."""
    def __init__(self, published):
        self.published = published

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def channel(self):
        return FakeChannel(self.published)


@pytest.mark.asyncio
async def test_resync_source_processed_source(monkeypatch):
    """Verify that resyncing a PROCESSED source resets it to QUEUED and enqueues it."""
    published = {"count": 0}
    deleted_chunks = []
    deleted_runs = []
    updated_source = {}

    class FakeSource:
        id = "source-123"
        name = "Test Source"
        status = "PROCESSED"
        project = type("FakeProject", (), {"slug": "test-project"})()

    class FakeChunk:
        def __init__(self, chunk_id):
            self.pinecone_vector_id = chunk_id

    async def fake_find_unique(where, include=None):
        return FakeSource()

    async def fake_delete_vectors_for_source(source_id):
        pass

    async def fake_delete_chunks(where):
        deleted_chunks.append(where)

    async def fake_delete_ingestion_runs(where):
        deleted_runs.append(where)

    async def fake_update(where, data):
        updated_source.update(data)

    async def fake_connect(url):
        return FakeConnection(published)

    monkeypatch.setattr("app.db.prisma.source.find_unique", fake_find_unique)
    monkeypatch.setattr("app.services.sources.delete_vectors_for_source", fake_delete_vectors_for_source)
    monkeypatch.setattr("app.db.prisma.chunk.delete_many", fake_delete_chunks)
    monkeypatch.setattr("app.db.prisma.ingestionrun.delete_many", fake_delete_ingestion_runs)
    monkeypatch.setattr("app.db.prisma.source.update", fake_update)
    monkeypatch.setattr("aio_pika.connect_robust", fake_connect)

    await resync_source("source-123")

    assert deleted_chunks == [{"source_id": "source-123"}]
    assert deleted_runs == [{"source_id": "source-123"}]
    assert updated_source["status"] == "QUEUED"
    assert published["count"] == 1


@pytest.mark.asyncio
async def test_resync_source_failed_source(monkeypatch):
    """Verify that resyncing a FAILED source also works."""
    published = {"count": 0}
    deleted_chunks = []
    deleted_runs = []
    updated_source = {}

    class FakeSource:
        id = "source-456"
        name = "Failed Source"
        status = "FAILED"
        project = type("FakeProject", (), {"slug": "test-project"})()

    async def fake_find_unique(where, include=None):
        return FakeSource()

    async def fake_delete_vectors_for_source(source_id):
        pass

    async def fake_delete_chunks(where):
        deleted_chunks.append(where)

    async def fake_delete_ingestion_runs(where):
        deleted_runs.append(where)

    async def fake_update(where, data):
        updated_source.update(data)

    async def fake_connect(url):
        return FakeConnection(published)

    monkeypatch.setattr("app.db.prisma.source.find_unique", fake_find_unique)
    monkeypatch.setattr("app.services.sources.delete_vectors_for_source", fake_delete_vectors_for_source)
    monkeypatch.setattr("app.db.prisma.chunk.delete_many", fake_delete_chunks)
    monkeypatch.setattr("app.db.prisma.ingestionrun.delete_many", fake_delete_ingestion_runs)
    monkeypatch.setattr("app.db.prisma.source.update", fake_update)
    monkeypatch.setattr("aio_pika.connect_robust", fake_connect)

    await resync_source("source-456")

    assert deleted_chunks == [{"source_id": "source-456"}]
    assert updated_source["status"] == "QUEUED"
    assert published["count"] == 1


@pytest.mark.asyncio
async def test_resync_source_not_found(monkeypatch):
    """Verify that resyncing a non-existent source raises ValueError."""
    async def fake_find_unique(where, include=None):
        return None

    monkeypatch.setattr("app.db.prisma.source.find_unique", fake_find_unique)

    with pytest.raises(ValueError, match="Source not found"):
        await resync_source("nonexistent")


@pytest.mark.asyncio
async def test_resync_source_invalid_status(monkeypatch):
    """Verify that resyncing a QUEUED source raises ValueError."""
    class FakeSource:
        id = "source-789"
        name = "Queued Source"
        status = "QUEUED"
        project = type("FakeProject", (), {"slug": "test-project"})()

    async def fake_find_unique(where, include=None):
        return FakeSource()

    monkeypatch.setattr("app.db.prisma.source.find_unique", fake_find_unique)

    with pytest.raises(ValueError, match="Cannot resync source with status 'QUEUED'"):
        await resync_source("source-789")


@pytest.mark.asyncio
async def test_resync_source_processing_status(monkeypatch):
    """Verify that resyncing a PROCESSING source raises ValueError."""
    class FakeSource:
        id = "source-abc"
        name = "Processing Source"
        status = "PROCESSING"
        project = type("FakeProject", (), {"slug": "test-project"})()

    async def fake_find_unique(where, include=None):
        return FakeSource()

    monkeypatch.setattr("app.db.prisma.source.find_unique", fake_find_unique)

    with pytest.raises(ValueError, match="Cannot resync source with status 'PROCESSING'"):
        await resync_source("source-abc")


@pytest.mark.asyncio
async def test_resync_source_cancelled_status(monkeypatch):
    """Verify that resyncing a CANCELLED source raises ValueError."""
    class FakeSource:
        id = "source-def"
        name = "Cancelled Source"
        status = "CANCELLED"
        project = type("FakeProject", (), {"slug": "test-project"})()

    async def fake_find_unique(where, include=None):
        return FakeSource()

    monkeypatch.setattr("app.db.prisma.source.find_unique", fake_find_unique)

    with pytest.raises(ValueError, match="Cannot resync source with status 'CANCELLED'"):
        await resync_source("source-def")
