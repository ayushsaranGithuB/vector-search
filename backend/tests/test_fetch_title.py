import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_fetch_returns_title():
    """fetch_title should extract the <title> from a known HTML page."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/fetch-title",
            params={"url": "https://prsindia.org/billtrack/the-motor-vehicles-amendment-bill-2019"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "The Motor Vehicles (Amendment) Bill, 2019"


@pytest.mark.asyncio
async def test_fetch_none_for_non_html():
    """fetch_title should return null for non-HTML content."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/fetch-title",
            params={"url": "https://www.google.com/favicon.ico"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] is None


@pytest.mark.asyncio
async def test_fetch_none_for_bogus_url():
    """fetch_title should gracefully return null for unreachable URLs."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/fetch-title",
            params={"url": "https://thissitedoesnotexist-hopefully.example.com"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] is None


@pytest.mark.asyncio
async def test_fetch_requires_url_param():
    """fetch_title should 422 if the url query param is missing."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/fetch-title")

    assert response.status_code == 422