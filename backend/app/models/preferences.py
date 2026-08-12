from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    destination: str = Field(..., min_length=1, max_length=100)
    days: int = Field(..., ge=1, le=30)
    people: int = Field(default=1, ge=1, le=20)
    budget: int = Field(..., ge=1000, description="Budget in JPY")
    categories: list[str] | None = Field(
        default=None,
        description="Preferred categories: attraction, restaurant, hotel, shopping",
    )
    style: str | None = Field(
        default=None,
        description="Travel style: cultural, foodie, nature, shopping, nightlife",
    )
    mobility: str | None = Field(
        default=None,
        description="Mobility preference: walking, public_transport, taxi, car",
    )
    # LLM-extracted fields for richer preference capture
    implicit_preferences: str | None = Field(
        default=None,
        description="What user cares about: vibe, pace, crowd tolerance, interests",
    )
    planning_notes: str | None = Field(
        default=None,
        description="Specific constraints or wishes for how to plan",
    )

    @property
    def daily_budget(self) -> int:
        return self.budget // self.days

    def summary(self) -> str:
        """Create a human-readable summary of preferences."""
        parts = [f"{self.days} days in {self.destination}"]
        if self.people > 1:
            parts.append(f"for {self.people} people")
        if self.style:
            parts.append(f"({self.style})")
        if self.implicit_preferences:
            parts.append(f"- {self.implicit_preferences}")
        return " ".join(parts)
