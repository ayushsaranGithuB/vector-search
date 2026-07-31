# Tests for the ingestion queue: message publishing with mocked RabbitMQ.
import pytest

from app.services.queue import enqueue_ingestion_for_source


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
async def test_enqueue_ingestion_for_source(monkeypatch):
    """Verify that enqueuing a source ID publishes exactly one message."""
    published = {"count": 0}

    async def fake_connect(url):
        assert url is not None
        return FakeConnection(published)

    monkeypatch.setattr("aio_pika.connect_robust", fake_connect)

    await enqueue_ingestion_for_source("source-1")
    assert published["count"] == 1
