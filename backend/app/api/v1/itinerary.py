"""Itinerary API endpoints."""

import asyncio
import json
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent.graph import TravelPlannerAgent
from app.constraints.validator import ConstraintValidator
from app.models.itinerary import Itinerary
from app.retrieval.embedder import Embedder
from app.retrieval.hybrid import HybridSearcher
from app.retrieval.reranker import Reranker

router = APIRouter(prefix="/itinerary", tags=["itinerary"])


class ItineraryRequest(BaseModel):
    """Request model for itinerary generation."""

    destination: str = Field(
        ..., min_length=1, max_length=100, description="Destination city"
    )
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


# In-memory storage for itineraries
ITINERARIES: dict[str, dict] = {}


def _load_places() -> list[dict]:
    """Load places from seed data."""
    # Try wikivoyage data first, fall back to original seed data
    wikivoyage_file = Path("/app/seed_data/wikivoyage_places.json")
    if wikivoyage_file.exists():
        with open(wikivoyage_file) as f:
            return json.load(f)

    # Fall back to original seed data
    seed_file = Path("/app/seed_data/tokyo_places.json")
    with open(seed_file) as f:
        return json.load(f)


def _create_agent() -> TravelPlannerAgent:
    """Create agent with seed data indexed."""
    embedder = Embedder()
    searcher = HybridSearcher(embedder, qdrant_client=None)

    # Index seed data into BM25
    places = _load_places()
    searcher.index_places(places)

    reranker = Reranker()
    validator = ConstraintValidator()

    return TravelPlannerAgent(embedder, searcher, reranker, validator)


@router.post("", response_model=ItineraryResponse)
async def create_itinerary(request: ItineraryRequest) -> ItineraryResponse:
    """Generate an itinerary from preferences."""
    itinerary_id = str(uuid.uuid4())

    # Build user input string
    user_input = request.user_input or (
        f"{request.destination} {request.days} days, {request.people} people, "
        f"{request.budget} yen"
    )
    if request.preferences:
        for key, value in request.preferences.items():
            user_input += f", {key}: {value}"

    # Create pending record
    ITINERARIES[itinerary_id] = {
        "id": itinerary_id,
        "status": "processing",
        "destination": request.destination,
        "days": request.days,
        "people": request.people,
        "budget": request.budget,
        "preferences": request.preferences,
        "user_input": user_input,
        "itinerary": None,
        "error": None,
    }

    # Process itinerary synchronously (for demo)
    try:
        agent = _create_agent()
        result = await asyncio.to_thread(agent.run, user_input)

        if result.get("error"):
            ITINERARIES[itinerary_id]["status"] = "failed"
            ITINERARIES[itinerary_id]["error"] = result["error"]
        else:
            ITINERARIES[itinerary_id]["status"] = "completed"
            itinerary_data = result.get("itinerary_result")
            if itinerary_data:
                try:
                    itinerary_obj = Itinerary(**itinerary_data)
                    ITINERARIES[itinerary_id]["itinerary"] = itinerary_obj.model_dump()
                except Exception:
                    ITINERARIES[itinerary_id]["itinerary"] = itinerary_data
    except Exception as e:
        ITINERARIES[itinerary_id]["status"] = "failed"
        ITINERARIES[itinerary_id]["error"] = str(e)

    data = ITINERARIES[itinerary_id]
    return ItineraryResponse(
        id=data["id"],
        status=data["status"],
        destination=data["destination"],
        days=data["days"],
        itinerary=None,
        error=data.get("error"),
    )


@router.get("/{itinerary_id}", response_model=ItineraryResponse)
async def get_itinerary(itinerary_id: str) -> ItineraryResponse:
    """Get an existing itinerary by ID."""
    if itinerary_id not in ITINERARIES:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    data = ITINERARIES[itinerary_id]
    itinerary_obj = None
    if data.get("itinerary"):
        try:
            itinerary_obj = Itinerary(**data["itinerary"])
        except Exception:
            pass

    return ItineraryResponse(
        id=data["id"],
        status=data["status"],
        destination=data["destination"],
        days=data["days"],
        itinerary=itinerary_obj,
        error=data.get("error"),
    )


@router.get("/{itinerary_id}/places")
async def get_itinerary_places(itinerary_id: str):
    """Get places in an itinerary."""
    if itinerary_id not in ITINERARIES:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    return {"itinerary_id": itinerary_id, "places": []}
