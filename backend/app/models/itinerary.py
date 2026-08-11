from pydantic import BaseModel, Field

from app.models.day_plan import DayPlan


class Itinerary(BaseModel):
    id: str | None = Field(default=None)
    days: list[DayPlan] = Field(default_factory=list)
    total_cost: int = Field(default=0, ge=0, description="Total cost in JPY")
    total_hours: float = Field(default=0, ge=0)
    constraints_satisfied: bool = Field(default=True)
    violations: list[str] = Field(default_factory=list)
    preferences_summary: str | None = None

    def calculate_totals(self) -> None:
        self.total_cost = sum(day.total_cost for day in self.days)
        self.total_hours = sum(day.total_hours for day in self.days)
