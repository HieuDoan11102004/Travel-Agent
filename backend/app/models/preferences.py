from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    destination: str = Field(..., min_length=1, max_length=100)
    days: int = Field(..., ge=1, le=30)
    people: int = Field(default=1, ge=1, le=20)
    budget: int = Field(..., ge=1000, description="Budget in JPY")
    categories: list[str] | None = Field(
        default=None,
        description="Preferred categories: attraction, restaurant, hotel, shopping"
    )
    style: str | None = Field(
        default=None,
        description="Travel style: cultural, foodie, nature, shopping, nightlife"
    )
    mobility: str | None = Field(
        default=None,
        description="Mobility preference: walking, public_transport, taxi, car"
    )

    @property
    def daily_budget(self) -> int:
        return self.budget // self.days
