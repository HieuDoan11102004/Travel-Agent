"""Places search API endpoints."""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Literal

from app.models.place import Place


router = APIRouter(prefix="/places", tags=["places"])


class PlaceSearchRequest(BaseModel):
    """Request for place search."""

    query: str = Query(..., min_length=1, description="Search query")
    categories: list[str] | None = None
    limit: int = Query(default=20, ge=1, le=100)


class PlaceSearchResponse(BaseModel):
    """Response for place search."""

    results: list[dict]
    count: int
    query: str


# Placeholder for search functionality
@router.post("/search", response_model=PlaceSearchResponse)
async def search_places(request: PlaceSearchRequest) -> PlaceSearchResponse:
    """Search for places using hybrid search.

    In production, this would use the actual search pipeline.
    """
    # Placeholder results
    return PlaceSearchResponse(
        results=[],
        count=0,
        query=request.query,
    )


@router.get("/categories")
async def get_categories():
    """Get available place categories."""
    return {
        "categories": [
            {"id": "attraction", "name": "Attractions", "icon": "🏛️"},
            {"id": "restaurant", "name": "Restaurants", "icon": "🍽️"},
            {"id": "hotel", "name": "Hotels", "icon": "🏨"},
            {"id": "shopping", "name": "Shopping", "icon": "🛍️"},
            {"id": "transport", "name": "Transport", "icon": "🚇"},
        ]
    }
