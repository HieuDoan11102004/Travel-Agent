"""Agent state definition for LangGraph."""

from typing import TypedDict
from app.models.preferences import UserPreferences
from app.models.place import Place
from app.models.day_plan import DayPlan


class AgentState(TypedDict, total=False):
    """State for the travel planner agent."""

    user_input: str
    preferences: UserPreferences | None
    retrieved_places: list[dict]
    current_day: int
    day_plans: list[DayPlan]
    violations: list[str]
    iteration: int
    itinerary_result: dict | None
    error: str | None
