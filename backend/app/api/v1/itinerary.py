"""Itinerary API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal

from app.models.itinerary import Itinerary


router = APIRouter(prefix="/itinerary", tags=["itinerary"])


class ItineraryRequest(BaseModel):
    """Request model for itinerary generation."""

    destination: str = Field(..., min_length=1, max_length=100, description="Destination city")
    days: int = Field(..., ge=1, le=30, description="Number of days")
    people: int = Field(default=1, ge=1, le=20, description="Number of people")
    budget: int = Field(..., ge=1000, description="Budget in JPY")
    preferences: dict | None = Field(default=None, description="Optional preferences")
    user_input: str | None = Field(default=None, description="Natural language input")


class ItineraryResponse(BaseModel):
    """Response model for itinerary."""

    id: str
    status: str
    destination: str
    days: int
    itinerary: Itinerary | None = None
    error: str | None = None


# In-memory storage for demo (replace with PostgreSQL in production)
ITINERARIES: dict[str, dict] = {}


@router.post("", response_model=ItineraryResponse)
async def create_itinerary(request: ItineraryRequest) -> ItineraryResponse:
    """Generate an itinerary from preferences.

    In production, this would:
    1. Save to PostgreSQL with pending status
    2. Trigger the agent async
    3. Return immediately with itinerary ID

    For now, returns a placeholder response.
    """
    import uuid

    itinerary_id = str(uuid.uuid4())

    # Create pending record
    ITINERARIES[itinerary_id] = {
        "id": itinerary_id,
        "status": "pending",
        "destination": request.destination,
        "days": request.days,
        "people": request.people,
        "budget": request.budget,
        "preferences": request.preferences,
        "user_input": request.user_input or f"{request.destination} {request.days} days",
    }

    return ItineraryResponse(
        id=itinerary_id,
        status="pending",
        destination=request.destination,
        days=request.days,
        itinerary=None,
        error=None,
    )


@router.get("/{itinerary_id}", response_model=ItineraryResponse)
async def get_itinerary(itinerary_id: str) -> ItineraryResponse:
    """Get an existing itinerary by ID."""
    if itinerary_id not in ITINERARIES:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    data = ITINERARIES[itinerary_id]
    return ItineraryResponse(
        id=data["id"],
        status=data["status"],
        destination=data["destination"],
        days=data["days"],
        itinerary=None,  # Would load from storage
        error=None,
    )


@router.get("/{itinerary_id}/places")
async def get_itinerary_places(itinerary_id: str):
    """Get places in an itinerary."""
    if itinerary_id not in ITINERARIES:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    return {"itinerary_id": itinerary_id, "places": []}
