"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.itinerary import router as itinerary_router
from app.api.v1.places import router as places_router


router = APIRouter(prefix="/api/v1")

router.include_router(itinerary_router)
router.include_router(places_router)
