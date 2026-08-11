from pydantic import BaseModel, Field

from app.models.place import Place


class DayPlan(BaseModel):
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD")
    places: list[Place] = Field(default_factory=list)
    total_cost: int = Field(default=0, ge=0, description="Total cost in JPY")
    total_hours: float = Field(default=0, ge=0, le=24)
    travel_time_minutes: int = Field(default=0, ge=0)
    notes: str | None = None

    def calculate_totals(self) -> None:
        self.total_cost = sum(p.cost_estimate for p in self.places)
        self.total_hours = sum(p.duration_hours for p in self.places)
