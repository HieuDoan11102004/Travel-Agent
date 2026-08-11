"""Tests for API endpoints."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest_asyncio.fixture
async def client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_root(client):
    """Test root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Travel Planner Agent"


@pytest.mark.asyncio
async def test_create_itinerary(client):
    """Test itinerary creation."""
    response = await client.post(
        "/api/v1/itinerary",
        json={
            "destination": "Tokyo",
            "days": 3,
            "people": 2,
            "budget": 500000,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"
    assert data["destination"] == "Tokyo"


@pytest.mark.asyncio
async def test_create_itinerary_with_preferences(client):
    """Test itinerary creation with preferences."""
    response = await client.post(
        "/api/v1/itinerary",
        json={
            "destination": "Tokyo",
            "days": 5,
            "people": 1,
            "budget": 200000,
            "preferences": {
                "style": "foodie",
                "mobility": "walking",
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["destination"] == "Tokyo"
    assert data["days"] == 5


@pytest.mark.asyncio
async def test_get_itinerary_not_found(client):
    """Test getting non-existent itinerary."""
    response = await client.get("/api/v1/itinerary/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_categories(client):
    """Test getting categories."""
    response = await client.get("/api/v1/places/categories")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert len(data["categories"]) == 5


@pytest.mark.asyncio
async def test_search_places(client):
    """Test place search."""
    response = await client.post(
        "/api/v1/places/search",
        json={
            "query": "temple shrine",
            "limit": 10,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "count" in data
