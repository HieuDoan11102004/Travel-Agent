from typing import Literal

from pydantic import BaseModel, Field


class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class Place(BaseModel):
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., max_length=200)
    category: Literal[
        "attraction",
        "restaurant",
        "hotel",
        "transport",
        "shopping",
        "nature",
        "cultural",
        "entertainment",
    ]
    subcategory: str = Field(..., max_length=100)
    location: Location
    cost_estimate: int = Field(..., ge=0, description="Cost in JPY")
    duration_hours: float = Field(..., gt=0, le=24)
    opening_hours: dict[str, str] | None = None
    popularity: Literal["high", "medium", "low"]
    rating: float = Field(..., ge=0, le=5)
    description: str | None = Field(default=None, max_length=500)
    address: str | None = None
