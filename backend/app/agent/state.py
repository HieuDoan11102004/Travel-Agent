"""Agent state definition for LangGraph."""

from typing import Any

from typing_extensions import TypedDict

from app.models.day_plan import DayPlan
from app.models.preferences import UserPreferences


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
    # LLM-related state
    llm_extracted: dict[str, Any] | None
    current_llm_plan: dict[str, Any] | None
    llm_critique: dict[str, Any] | None
